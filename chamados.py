"""Chamados do Triagem Fácil: registro em SQLite, protocolo, fila, acompanhamento e CSV.

A tela (app.py) e o bot (bot.py) registram pela mesma função: analisar_e_registrar(texto, origem).
Fluxo: validar a mensagem -> classificar com a IA (triagem.py) -> gravar o chamado com um
protocolo novo e status Aberto, na fila do setor sugerido.
Antes de registrar, os dois canais chamam consultar_status(texto): mensagem que cita um protocolo
(ex.: "status do pedido TF-20260929-7STU8D") é uma consulta, respondida sem IA e sem novo chamado.

Cada operação abre e fecha a própria conexão com o banco. Assim a tela e o bot podem rodar ao
mesmo tempo: se os dois gravarem juntos, o SQLite faz um esperar o outro terminar.
"""

import csv
import hashlib
import io
import logging
import os
import re
import secrets
import sqlite3
from collections import Counter
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import requests

import triagem

logger = logging.getLogger(__name__)

STATUS = ("Aberto", "Em atendimento", "Resolvido")
STATUS_INICIAL = "Aberto"
MAX_CARACTERES_OBSERVACAO = 1000

# Protocolo no formato TF-AAAAMMDD-XXXXXX, gerado pelo Python. O sufixo é sorteado sem 0/O e 1/I,
# fáceis de confundir ao ditar. A coluna é UNIQUE: se um sorteio repetir, sorteia de novo.
ALFABETO_PROTOCOLO = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
TAMANHO_SUFIXO_PROTOCOLO = 6
TENTATIVAS_PROTOCOLO = 5
# Protocolo citado em qualquer parte de uma mensagem, em maiúsculas ou minúsculas. O sufixo aceita
# qualquer letra ou número, para um protocolo digitado errado (ex.: O no lugar de 0) virar
# "não encontrado" em vez de um chamado novo.
PADRAO_PROTOCOLO = re.compile(r"\bTF-\d{8}-[A-Z0-9]{6}\b", re.IGNORECASE)

# Se a tela e o bot gravarem ao mesmo tempo, um espera até 15 segundos pelo outro.
TIMEOUT_BANCO_SEGUNDOS = 15

# Colunas do historico.csv da versão anterior (lido só para importação).
COLUNAS_HISTORICO = ["data_hora", "mensagem", "categoria", "prioridade", "resumo", "justificativa"]
COLUNAS_EXPORTACAO = [
    "protocolo", "criado_em", "atualizado_em", "mensagem", "categoria",
    "prioridade", "resumo", "justificativa", "setor", "status",
]

CRIAR_TABELA = """
CREATE TABLE IF NOT EXISTS chamados (
    id INTEGER PRIMARY KEY,
    protocolo TEXT NOT NULL UNIQUE,
    criado_em TEXT NOT NULL,
    atualizado_em TEXT NOT NULL,
    mensagem TEXT NOT NULL,
    categoria TEXT NOT NULL,
    prioridade TEXT NOT NULL,
    resumo TEXT NOT NULL,
    justificativa TEXT NOT NULL,
    setor TEXT NOT NULL,
    status TEXT NOT NULL,
    -- Identifica a mensagem de origem (Telegram ou linha do CSV importado) para não duplicar o
    -- chamado. Fica vazia (NULL) nos envios pela tela: cada clique no botão é um chamado novo.
    origem TEXT UNIQUE
)"""

# Cada alteração feita na área de gestão vira uma linha aqui, com a observação de quem alterou.
CRIAR_HISTORICO = """
CREATE TABLE IF NOT EXISTS historico (
    id INTEGER PRIMARY KEY,
    protocolo TEXT NOT NULL REFERENCES chamados(protocolo),
    registrado_em TEXT NOT NULL,
    -- O que mudou, em texto (ex.: "Status: Aberto → Em atendimento"); vazio se houve só observação.
    alteracoes TEXT NOT NULL,
    observacao TEXT NOT NULL
)"""

INSERIR = """
INSERT INTO chamados (protocolo, criado_em, atualizado_em, mensagem, categoria, prioridade,
                      resumo, justificativa, setor, status, origem)
VALUES (:protocolo, :criado_em, :atualizado_em, :mensagem, :categoria, :prioridade,
        :resumo, :justificativa, :setor, :status, :origem)"""


class BancoError(triagem.TriagemError):
    """Falha ao abrir, ler ou gravar o banco de dados."""


# ---------- Caminhos e conexão ----------

def caminho_banco():
    """Destino do banco: DB_PATH, se definido; senão triagem.db ao lado deste arquivo."""
    destino = os.getenv("DB_PATH", "").strip()
    return Path(destino) if destino else Path(__file__).with_name("triagem.db")


def caminho_csv():
    """Histórico CSV da versão anterior: CSV_PATH, se definido; senão historico.csv ao lado deste arquivo."""
    destino = os.getenv("CSV_PATH", "").strip()
    return Path(destino) if destino else Path(__file__).with_name("historico.csv")


def agora_iso():
    """Data/hora local com offset, em ISO 8601 (ex.: 2026-09-29T14:03:00-03:00)."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def formatar_data(iso):
    """Mostra a data ISO gravada no banco como dd/mm/aaaa hh:mm."""
    return datetime.fromisoformat(iso).strftime("%d/%m/%Y %H:%M")


def formatar_duracao(segundos):
    """Mostra uma duração em segundos com uma casa decimal e vírgula (ex.: 3.24 -> "3,2 s")."""
    return f"{segundos:.1f} s".replace(".", ",")


def erro_de_banco(caminho, erro):
    """Registra o detalhe técnico no terminal e devolve uma mensagem curta para o usuário."""
    logger.warning("Falha no banco de dados %s: %s: %s", caminho, type(erro).__name__, erro)
    return BancoError(
        f"Não foi possível acessar o banco de dados ({caminho}). "
        "Confira se a pasta existe e permite gravação e tente novamente."
    )


@contextmanager
def abrir_banco():
    """Abre uma conexão, cria a tabela se preciso e, no fim, confirma tudo (commit).

    Se algo falhar no meio, nada é gravado (rollback) e o erro vira BancoError.
    """
    caminho = caminho_banco()
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        conexao = sqlite3.connect(caminho, timeout=TIMEOUT_BANCO_SEGUNDOS)
    except (sqlite3.Error, OSError) as erro:
        raise erro_de_banco(caminho, erro) from erro
    conexao.row_factory = sqlite3.Row  # permite ler as colunas pelo nome
    try:
        with conexao:  # commit se o bloco terminar bem; rollback se houver erro
            conexao.execute(CRIAR_TABELA)
            conexao.execute(CRIAR_HISTORICO)  # bancos criados antes do histórico ganham a tabela aqui
            yield conexao
    except (sqlite3.Error, OSError) as erro:
        raise erro_de_banco(caminho, erro) from erro
    finally:
        conexao.close()


def preparar_banco():
    """Cria o banco e a tabela, se ainda não existirem, e devolve o caminho (usado ao iniciar o bot)."""
    with abrir_banco():
        pass
    return caminho_banco()


def ler_chamado(conexao, coluna, valor):
    """Busca um chamado por "protocolo" ou "origem" (colunas UNIQUE). Devolve dict ou None."""
    linha = conexao.execute(f"SELECT * FROM chamados WHERE {coluna} = ?", (valor,)).fetchone()
    return dict(linha) if linha is not None else None


# ---------- Protocolo e gravação ----------

def gerar_protocolo(criado_em):
    """Sorteia um protocolo TF-AAAAMMDD-XXXXXX usando a data de criação do chamado."""
    data = criado_em[:10].replace("-", "")
    sufixo = "".join(secrets.choice(ALFABETO_PROTOCOLO) for _ in range(TAMANHO_SUFIXO_PROTOCOLO))
    return f"TF-{data}-{sufixo}"


def normalizar_protocolo(texto):
    """Aceita o protocolo digitado com espaços nas pontas ou em minúsculas."""
    return (texto or "").strip().upper()


def inserir(conexao, campos):
    """Grava um chamado com protocolo único. Devolve (chamado, novo).

    Se a origem já estiver no banco (a mesma mensagem recebida de novo), não grava outra vez:
    devolve o chamado existente com novo=False.
    """
    for _ in range(TENTATIVAS_PROTOCOLO):
        chamado = {"protocolo": gerar_protocolo(campos["criado_em"]), **campos}
        try:
            conexao.execute(INSERIR, chamado)
            return chamado, True
        except sqlite3.IntegrityError:
            # Uma coluna UNIQUE barrou a gravação: a origem já existe ou o protocolo sorteado já existe.
            if campos["origem"] is not None:
                existente = ler_chamado(conexao, "origem", campos["origem"])
                if existente is not None:
                    return existente, False
            # Protocolo repetido: o laço sorteia outro.
    raise sqlite3.IntegrityError("não foi possível sortear um protocolo livre")


def salvar_chamado(mensagem, resultado, origem=None):
    """Grava a mensagem analisada como chamado Aberto na fila do setor sugerido. Devolve (chamado, novo)."""
    agora = agora_iso()
    campos = {
        "criado_em": agora,
        "atualizado_em": agora,
        "mensagem": mensagem,
        "categoria": resultado["categoria"],
        "prioridade": resultado["prioridade"],
        "resumo": resultado["resumo"],
        "justificativa": resultado["justificativa"],
        "setor": resultado["setor"],
        "status": STATUS_INICIAL,
        "origem": origem,
    }
    try:
        with abrir_banco() as conexao:
            return inserir(conexao, campos)
    except BancoError:
        raise triagem.RegistroError(
            "A análise foi feita, mas não foi possível gravar o chamado no banco de dados. "
            "Confira se a pasta de dados permite gravação e envie novamente."
        )


def analisar_e_registrar(texto, origem=None):
    """Fluxo único da tela e do bot: validar -> classificar com a IA -> gravar o chamado.

    origem identifica a mensagem no canal de entrada (o bot usa "telegram:<chat>:<mensagem>").
    Se a mesma origem chegar de novo, devolve o chamado já gravado, sem chamar a IA nem gravar.
    A tela não informa origem: cada envio explícito é um chamado novo.
    Devolve (chamado, novo).
    """
    mensagem = triagem.validar_mensagem(texto)
    if origem is not None:
        existente = buscar_por_origem(origem)
        if existente is not None:
            return existente, False
    resultado = triagem.classificar(mensagem)
    return salvar_chamado(mensagem, resultado, origem)


# ---------- Consulta, fila e acompanhamento ----------

def buscar_por_protocolo(protocolo):
    """Devolve o chamado com esse protocolo, ou None se não existir."""
    with abrir_banco() as conexao:
        return ler_chamado(conexao, "protocolo", normalizar_protocolo(protocolo))


def buscar_por_origem(origem):
    """Devolve o chamado criado a partir dessa origem, ou None."""
    with abrir_banco() as conexao:
        return ler_chamado(conexao, "origem", origem)


def consultar_status(texto):
    """Se a mensagem citar protocolos, devolve uma linha de situação para cada um; senão, None.

    Ex.: "status do pedido TF-20260929-7STU8D" -> ["TF-20260929-7STU8D: Em atendimento, setor ..."].
    Não chama a IA e não grava chamado. Mostra só status, setor e data, nunca o conteúdo da mensagem.
    """
    # dict.fromkeys tira repetições mantendo a ordem em que os protocolos aparecem.
    protocolos = list(dict.fromkeys(p.upper() for p in PADRAO_PROTOCOLO.findall(texto or "")))
    if not protocolos:
        return None
    situacoes = []
    with abrir_banco() as conexao:
        for protocolo in protocolos:
            chamado = ler_chamado(conexao, "protocolo", protocolo)
            if chamado is None:
                situacoes.append(f"{protocolo}: não encontrado. Confira se o protocolo está correto.")
            else:
                situacoes.append(
                    f"{protocolo}: {chamado['status']}, setor {chamado['setor']} "
                    f"(atualizado em {formatar_data(chamado['atualizado_em'])})"
                )
    return situacoes


def ordem_na_fila(chamado):
    """Chave de ordenação: prioridade (Alta, Média, Baixa) e, na mesma prioridade, o mais antigo primeiro."""
    return (
        triagem.PRIORIDADES.index(chamado["prioridade"]),
        datetime.fromisoformat(chamado["criado_em"]),
        chamado["id"],
    )


def listar_fila(setores=(), prioridades=(), status=()):
    """Chamados que passam nos filtros (filtro vazio = todos), na ordem de atendimento da fila."""
    condicoes, parametros = [], []
    for coluna, valores in (("setor", setores), ("prioridade", prioridades), ("status", status)):
        if valores:
            # Os nomes das colunas são fixos no código; os valores vão como parâmetros (?).
            condicoes.append(f"{coluna} IN ({', '.join('?' for _ in valores)})")
            parametros.extend(valores)
    sql = "SELECT * FROM chamados"
    if condicoes:
        sql += " WHERE " + " AND ".join(condicoes)
    with abrir_banco() as conexao:
        encontrados = [dict(linha) for linha in conexao.execute(sql, parametros)]
    return sorted(encontrados, key=ordem_na_fila)


# Pendentes são os chamados que ainda precisam de atenção: todos os status menos o último (Resolvido).
STATUS_PENDENTES = STATUS[:-1]


def contar_chamados():
    """Números do painel da gestão: chamados por status e pendentes por setor, sem os filtros da fila.

    Opções sem chamados aparecem com zero. Ex.:
    {"por_status": {"Aberto": 2, "Em atendimento": 1, "Resolvido": 4},
     "pendentes_por_setor": {"Atendimento": 1, "Financeiro": 0, "Logística": 2, "Suporte Técnico": 0}}
    """
    marcadores = ", ".join("?" for _ in STATUS_PENDENTES)
    with abrir_banco() as conexao:
        # Cada linha do GROUP BY é um par (opção, quantidade); dict() junta os pares num dicionário.
        por_status = dict(conexao.execute("SELECT status, COUNT(*) FROM chamados GROUP BY status"))
        por_setor = dict(conexao.execute(
            f"SELECT setor, COUNT(*) FROM chamados WHERE status IN ({marcadores}) GROUP BY setor",
            STATUS_PENDENTES,
        ))
    # Percorre as listas oficiais: a ordem é a mesma da tela e o que não tem chamado aparece com zero.
    return {
        "por_status": {status: por_status.get(status, 0) for status in STATUS},
        "pendentes_por_setor": {setor: por_setor.get(setor, 0) for setor in triagem.SETORES},
    }


def atualizar_chamado(protocolo, status, setor, prioridade, observacao=""):
    """Altera status, setor e prioridade e registra no histórico o que mudou, com a observação.

    Aceita também só a observação, sem mudar campos. A mensagem original e a análise da IA não mudam.
    Devolve (chamado, alterado). Sem mudança e sem observação, nada é gravado e a data é mantida.
    """
    campos = (
        ("status", "Status", status, STATUS),
        ("setor", "Setor", setor, triagem.SETORES),
        ("prioridade", "Prioridade", prioridade, triagem.PRIORIDADES),
    )
    for _campo, nome, valor, opcoes in campos:
        if valor not in opcoes:
            raise triagem.TriagemError(f"{nome} inválido: escolha uma das opções da lista.")
    observacao = (observacao or "").strip()
    if len(observacao) > MAX_CARACTERES_OBSERVACAO:
        raise triagem.TriagemError(
            f"A observação tem {len(observacao)} caracteres; o limite é {MAX_CARACTERES_OBSERVACAO}."
        )

    with abrir_banco() as conexao:
        atual = ler_chamado(conexao, "protocolo", protocolo)
        if atual is None:
            raise triagem.TriagemError(f"Chamado {protocolo} não encontrado.")
        alteracoes = "; ".join(
            f"{nome}: {atual[campo]} → {valor}" for campo, nome, valor, _opcoes in campos if atual[campo] != valor
        )
        if not alteracoes and not observacao:
            return atual, False
        agora = agora_iso()
        conexao.execute(
            "UPDATE chamados SET status = ?, setor = ?, prioridade = ?, atualizado_em = ? WHERE protocolo = ?",
            (status, setor, prioridade, agora, protocolo),
        )
        conexao.execute(
            "INSERT INTO historico (protocolo, registrado_em, alteracoes, observacao) VALUES (?, ?, ?, ?)",
            (protocolo, agora, alteracoes, observacao),
        )
        return ler_chamado(conexao, "protocolo", protocolo), True


def listar_historico(protocolo):
    """Alterações e observações do chamado, da mais recente para a mais antiga."""
    with abrir_banco() as conexao:
        linhas = conexao.execute("SELECT * FROM historico WHERE protocolo = ? ORDER BY id DESC", (protocolo,))
        return [dict(linha) for linha in linhas]


# ---------- Aviso ao cliente pelo Telegram ----------

# Tempo curto: a tela de gestão espera o envio, e o status já está salvo antes do aviso.
TIMEOUT_TELEGRAM_SEGUNDOS = 10


def avisar_cliente_telegram(chamado):
    """Avisa no Telegram que o status mudou, se o chamado foi aberto pelo bot.

    Devolve "enviado", "falhou", "sem_token" (TELEGRAM_BOT_TOKEN não configurado) ou
    "sem_telegram" (chamado da tela ou importado do CSV: não há conversa para avisar).
    A mensagem leva só o protocolo e o status: as observações da gestão são internas.
    """
    origem = chamado["origem"] or ""
    if not origem.startswith("telegram:"):
        return "sem_telegram"
    token = triagem.ler_variavel("TELEGRAM_BOT_TOKEN")
    if token is None:
        return "sem_token"
    protocolo = chamado["protocolo"]
    chat_id = origem.split(":")[1]  # o bot grava a origem como "telegram:<chat_id>:<message_id>"
    texto = (
        f"Atualização da sua solicitação {protocolo}:\n"
        f"Novo status: {chamado['status']}.\n"
        "Informe o protocolo se precisar falar sobre ela."
    )
    # A URL contém o token do bot, e o texto das exceções do requests repete a URL. Por isso o log
    # mostra só o protocolo e o tipo do erro (ou o status HTTP), nunca o texto da exceção.
    try:
        resposta = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": texto},  # sem parse_mode: vai como texto simples
            timeout=TIMEOUT_TELEGRAM_SEGUNDOS,
        )
    except requests.RequestException as erro:
        logger.warning("Chamado %s: aviso não enviado ao Telegram (%s).", protocolo, type(erro).__name__)
        return "falhou"
    try:
        # O Telegram confirma o envio com {"ok": true}; qualquer outra resposta conta como falha.
        confirmado = resposta.status_code == 200 and resposta.json()["ok"] is True
    except (ValueError, KeyError, TypeError):
        confirmado = False
    if not confirmado:
        logger.warning("Chamado %s: o Telegram não confirmou o aviso (HTTP %s).", protocolo, resposta.status_code)
        return "falhou"
    return "enviado"


# ---------- CSV: exportação e importação do histórico anterior ----------

def neutralizar_formula(valor):
    """Prefixa apóstrofo em textos iniciados por =, +, - ou @ para a planilha não tratá-los como fórmula."""
    if valor.startswith(("=", "+", "-", "@")):
        return "'" + valor
    return valor


def desfazer_neutralizacao(valor):
    """O historico.csv antigo gravava um apóstrofo antes de =, +, - e @; na importação ele sai."""
    if valor[:1] == "'" and valor[1:2] in ("=", "+", "-", "@"):
        return valor[1:]
    return valor


def exportar_csv():
    """Gera o CSV de todos os chamados, do mais antigo para o mais novo, pronto para o Excel."""
    with abrir_banco() as conexao:
        todos = [dict(linha) for linha in conexao.execute("SELECT * FROM chamados")]
    todos.sort(key=lambda chamado: (datetime.fromisoformat(chamado["criado_em"]), chamado["id"]))

    saida = io.StringIO()
    escritor = csv.DictWriter(saida, fieldnames=COLUNAS_EXPORTACAO, delimiter=";")
    escritor.writeheader()
    for chamado in todos:
        escritor.writerow({coluna: neutralizar_formula(chamado[coluna]) for coluna in COLUNAS_EXPORTACAO})
    # "utf-8-sig" grava o BOM no início, para o Excel reconhecer os acentos.
    return saida.getvalue().encode("utf-8-sig")


def campos_do_historico(linha, agora):
    """Converte uma linha do historico.csv antigo nos campos de um chamado; None se a linha for inválida."""
    valores = [linha.get(coluna) for coluna in COLUNAS_HISTORICO]
    if not all(isinstance(valor, str) and valor.strip() for valor in valores):
        return None
    data_hora, mensagem, categoria, prioridade, resumo, justificativa = valores
    categoria = triagem.opcao_permitida(categoria.strip(), triagem.CATEGORIAS)
    prioridade = triagem.opcao_permitida(prioridade.strip(), triagem.PRIORIDADES)
    try:
        criado = datetime.fromisoformat(data_hora.strip())
    except ValueError:
        return None
    if categoria is None or prioridade is None:
        return None
    if criado.tzinfo is None:  # data sem offset: considera o fuso deste computador
        criado = criado.astimezone()
    return {
        "criado_em": criado.isoformat(timespec="seconds"),
        "atualizado_em": agora,
        "mensagem": desfazer_neutralizacao(mensagem),
        "categoria": categoria,
        "prioridade": prioridade,
        "resumo": desfazer_neutralizacao(resumo),
        "justificativa": desfazer_neutralizacao(justificativa),
        # O CSV antigo não tinha setor nem status: o chamado entra Aberto na fila de Atendimento.
        "setor": triagem.SETOR_PADRAO,
        "status": STATUS_INICIAL,
    }


def importar_historico_csv(caminho=None):
    """Copia para o banco os registros do historico.csv da versão anterior. Pode ser repetida.

    O arquivo é aberto só para leitura: não é alterado, movido nem apagado. Cada linha recebe
    uma origem calculada do próprio conteúdo; ao importar de novo, a origem já existe e a linha
    é contada como já importada, sem duplicar o chamado.
    Devolve as quantidades: {"importados", "ja_existiam", "invalidas"}.
    """
    caminho = Path(caminho) if caminho else caminho_csv()
    try:
        with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
            leitor = csv.DictReader(arquivo, delimiter=";")
            if leitor.fieldnames != COLUNAS_HISTORICO:
                raise triagem.TriagemError(
                    f"O arquivo {caminho} não tem as colunas do histórico anterior "
                    f"({';'.join(COLUNAS_HISTORICO)}). Nada foi importado."
                )
            linhas = list(leitor)
    except FileNotFoundError:
        raise triagem.TriagemError(f"Nenhum histórico CSV encontrado em {caminho}.")
    except (OSError, UnicodeDecodeError, csv.Error) as erro:
        logger.warning("Falha ao ler o histórico %s: %s: %s", caminho, type(erro).__name__, erro)
        raise triagem.TriagemError(
            f"Não foi possível ler {caminho} (esperado: CSV UTF-8 separado por ponto e vírgula). "
            "Feche o arquivo se estiver aberto em outro programa e tente novamente."
        )

    agora = agora_iso()
    ocorrencias = Counter()
    totais = {"importados": 0, "ja_existiam": 0, "invalidas": 0}
    with abrir_banco() as conexao:  # uma única transação: importa todas as linhas válidas ou nenhuma
        for linha in linhas:
            campos = campos_do_historico(linha, agora)
            if campos is None:
                totais["invalidas"] += 1
                continue
            # A mesma linha gera sempre a mesma origem. Linhas idênticas (improváveis, mas possíveis)
            # são diferenciadas pelo número da ocorrência dentro do arquivo.
            conteudo = "\x1f".join(linha[coluna] for coluna in COLUNAS_HISTORICO)
            assinatura = hashlib.sha256(conteudo.encode("utf-8")).hexdigest()
            ocorrencias[assinatura] += 1
            campos["origem"] = f"csv:{assinatura}:{ocorrencias[assinatura]}"
            _, novo = inserir(conexao, campos)
            totais["importados" if novo else "ja_existiam"] += 1
    return totais
