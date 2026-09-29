"""Tela do Triagem Fácil (Streamlit): registro de mensagens e área de gestão dos chamados.

A tela só cuida da interface. A análise com IA fica em triagem.py e o registro dos chamados
(SQLite, protocolo e fila) em chamados.py, na mesma função usada pelo bot:
chamados.analisar_e_registrar(texto).

Executar: python -m streamlit run app.py
A área de gestão é de uso local: .streamlit/config.toml faz a tela aceitar conexões
somente deste computador (localhost).
"""

import time
from datetime import datetime

import streamlit as st

import chamados
import triagem

# Rótulos fixos exibidos acima de cada campo do resultado.
ROTULOS = {
    "protocolo": "Protocolo",
    "setor": "Setor responsável",
    "categoria": "Categoria",
    "prioridade": "Prioridade",
    "resumo": "Resumo",
    "justificativa": "Justificativa",
}

# Chaves do st.session_state onde fica o último envio (chamado e tempo da triagem, consulta de protocolo OU erro).
CHAVES_DO_ENVIO = ("chamado", "duracao_triagem", "consulta", "erro_registro", "erro")


def mostrar_campos(chamado, campos):
    """Mostra cada campo com rótulo em negrito e valor como texto puro (sem Markdown nem HTML)."""
    for campo, rotulo in campos:
        st.markdown(f"**{rotulo}**")
        st.text(chamado[campo])


# ---------- Aba "Registrar mensagem" ----------

def avisar_se_falta_configuracao():
    """Mostra no topo a instrução de configuração do .env; a tela continua abrindo."""
    try:
        triagem.configuracao_provedor()
    except triagem.TriagemError as erro:
        st.warning(str(erro))


def analisar(texto):
    """Processa um envio e guarda na sessão o chamado registrado ou o erro."""
    # Apaga o envio anterior: se este falhar, o resultado antigo não aparece.
    for chave in CHAVES_DO_ENVIO:
        st.session_state.pop(chave, None)

    try:
        triagem.validar_mensagem(texto)  # Mensagem vazia para aqui, sem chamar a API.
        # Mensagem que cita um protocolo é consulta: mostra a situação, sem IA e sem chamado novo.
        situacoes = chamados.consultar_status(texto)
        if situacoes:
            st.session_state["consulta"] = situacoes
            return
        with st.spinner("Analisando mensagem..."):
            # Cronometra a triagem automática (IA, validação e gravação) para mostrar na confirmação.
            inicio = time.perf_counter()
            chamado, _novo = chamados.analisar_e_registrar(texto)
            duracao = time.perf_counter() - inicio
        st.session_state["chamado"] = chamado
        st.session_state["duracao_triagem"] = duracao
    except triagem.RegistroError as erro:
        # RegistroError vem antes: é um tipo especial de TriagemError.
        st.session_state["erro_registro"] = str(erro)
    except triagem.TriagemError as erro:
        st.session_state["erro"] = str(erro)


def mostrar_ultimo_envio():
    """Mostra o que está na sessão; um rerun comum não chama a API nem grava de novo."""
    if "chamado" in st.session_state:
        chamado = st.session_state["chamado"]
        # Protocolo e tempo (gerados pelo Python) e setor (validado contra a lista) são valores seguros.
        mensagem = (
            f"Solicitação registrada com o protocolo {chamado['protocolo']} "
            f"e encaminhada para a fila do setor {chamado['setor']}."
        )
        # Uma sessão aberta antes desta versão do app não tem o tempo guardado: mostra sem ele.
        if "duracao_triagem" in st.session_state:
            tempo = chamados.formatar_duracao(st.session_state["duracao_triagem"])
            mensagem += f" Triagem automática concluída em {tempo}."
        st.success(mensagem)
        st.subheader("Resultado da análise")
        mostrar_campos(chamado, ROTULOS.items())
    elif "consulta" in st.session_state:
        st.info("Consulta de protocolo: nenhum chamado novo foi registrado.")
        for situacao in st.session_state["consulta"]:
            st.text(situacao)
    elif "erro_registro" in st.session_state:
        st.error("Falha no registro: " + st.session_state["erro_registro"])
    elif "erro" in st.session_state:
        st.error(st.session_state["erro"])
        st.info("Para tentar novamente, clique em “Analisar e registrar”.")


def aba_registro():
    st.write(
        "Cole a mensagem de um cliente: a IA sugere categoria, prioridade, setor responsável, "
        "resumo e justificativa, e o chamado é registrado com um protocolo."
    )
    avisar_se_falta_configuracao()

    # O formulário só envia quando o botão é clicado (digitar não dispara a análise).
    with st.form("formulario"):
        texto = st.text_area("Mensagem do cliente", max_chars=triagem.MAX_CARACTERES)
        enviado = st.form_submit_button("Analisar e registrar")

    # Cada clique é uma nova análise, mesmo que o texto seja igual ao anterior.
    if enviado:
        analisar(texto)
    mostrar_ultimo_envio()


# ---------- Aba "Fila de chamados" (área de gestão) ----------

def abrir_chamado(protocolo):
    """Define qual chamado aparece no painel de detalhes."""
    st.session_state["protocolo_aberto"] = protocolo


def localizar_chamado():
    """Busca um chamado pelo protocolo, inclusive os que estão fora dos filtros da fila."""
    with st.form("localizar"):
        protocolo = st.text_input("Localizar chamado pelo protocolo", placeholder="TF-AAAAMMDD-XXXXXX")
        buscar = st.form_submit_button("Localizar")
    if not buscar:
        return
    try:
        chamado = chamados.buscar_por_protocolo(protocolo)
    except triagem.TriagemError as erro:
        st.error(str(erro))
        return
    if chamado is None:
        st.warning("Nenhum chamado encontrado com esse protocolo.")
    else:
        abrir_chamado(chamado["protocolo"])


def escolher_na_fila():
    """Abre o chamado escolhido no seletor da fila e pede para recarregar a tela inteira.

    O seletor fica dentro do fragmento da fila: uma escolha ali re-executa só o fragmento, e os
    detalhes, que ficam fora dele, só aparecem quando a tela inteira é recarregada.
    """
    abrir_chamado(st.session_state["seletor_chamado"])
    st.session_state["recarregar_tela"] = True


# De quanto em quanto tempo o painel e a fila se atualizam sozinhos, trazendo os chamados novos
# recebidos pelo bot sem ninguém precisar clicar.
INTERVALO_ATUALIZACAO_SEGUNDOS = 30


@st.fragment(run_every=INTERVALO_ATUALIZACAO_SEGUNDOS)
def painel_e_fila():
    """Painel e fila, que o Streamlit re-executa sozinhos a cada INTERVALO_ATUALIZACAO_SEGUNDOS.

    Só esta parte da tela é recarregada: localizar, detalhes e exportação ficam fora do fragmento,
    para o operador que estiver digitando uma observação não perder o texto.
    """
    if st.session_state.pop("recarregar_tela", False):
        st.rerun()  # A escolha no seletor precisa da tela inteira para os detalhes aparecerem.
    mostrar_painel()
    mostrar_fila()


def mostrar_painel():
    """Visão geral com os números de todos os chamados; não depende dos filtros da fila."""
    st.subheader("Visão geral")
    try:
        numeros = chamados.contar_chamados()
    except triagem.TriagemError as erro:
        st.error(str(erro))
        return
    por_status = numeros["por_status"]
    colunas = st.columns(len(por_status) + 1)  # Uma coluna para cada status e uma para o total.
    for coluna, (status, quantidade) in zip(colunas, por_status.items()):
        coluna.metric(status, quantidade, border=True)
    colunas[-1].metric("Total", sum(por_status.values()), border=True)

    pendentes = numeros["pendentes_por_setor"]
    st.caption(f"Pendentes por setor: chamados com status {' ou '.join(chamados.STATUS_PENDENTES)}.")
    for coluna, (setor, quantidade) in zip(st.columns(len(pendentes)), pendentes.items()):
        coluna.metric(f"Pendentes · {setor}", quantidade, border=True)


def mostrar_fila():
    """Filtros, tabela da fila e seleção do chamado para abrir os detalhes."""
    st.subheader("Fila")
    if st.button("Atualizar fila"):
        st.rerun()  # O clique recarrega a tela inteira: painel, fila, detalhes e exportação.
    st.caption(f"O painel e a fila se atualizam sozinhos a cada {INTERVALO_ATUALIZACAO_SEGUNDOS} segundos.")
    colunas = st.columns(3)
    setores = colunas[0].multiselect("Setor", triagem.SETORES, placeholder="Todos")
    prioridades = colunas[1].multiselect("Prioridade", triagem.PRIORIDADES, placeholder="Todas")
    # Por padrão a fila mostra o que ainda precisa de atenção; inclua "Resolvido" para ver os encerrados.
    status = colunas[2].multiselect(
        "Status", chamados.STATUS, default=["Aberto", "Em atendimento"], placeholder="Todos"
    )

    try:
        fila = chamados.listar_fila(setores, prioridades, status)
    except triagem.TriagemError as erro:
        st.error(str(erro))
        return
    if not fila:
        st.info("Nenhum chamado com esses filtros.")
        return

    st.caption(
        f"{len(fila)} chamado(s), ordenados por prioridade (Alta, Média, Baixa) e, "
        "na mesma prioridade, do mais antigo para o mais novo."
    )
    st.dataframe(
        [
            {
                "Protocolo": chamado["protocolo"],
                "Resumo": chamado["resumo"],
                "Setor": chamado["setor"],
                "Prioridade": chamado["prioridade"],
                "Status": chamado["status"],
                "Criado em": chamados.formatar_data(chamado["criado_em"]),
            }
            for chamado in fila
        ],
        hide_index=True,
    )

    # Só protocolo e resumo, que nunca mudam depois do registro. Se o rótulo mudasse (com a prioridade,
    # por exemplo), a tela devolveria o rótulo antigo na atualização automática e fecharia os detalhes.
    rotulos = {c["protocolo"]: f"{c['protocolo']} · {c['resumo'][:60]}" for c in fila}
    st.selectbox(
        "Abrir detalhes de um chamado da fila",
        [None, *rotulos],
        format_func=lambda protocolo: "Selecione um chamado" if protocolo is None else rotulos[protocolo],
        key="seletor_chamado",
        on_change=escolher_na_fila,
    )


def mostrar_detalhes():
    """Painel do chamado aberto: dados originais, análise da IA e formulário de acompanhamento."""
    protocolo = st.session_state.get("protocolo_aberto")
    if not protocolo:
        return
    try:
        chamado = chamados.buscar_por_protocolo(protocolo)
    except triagem.TriagemError as erro:
        st.error(str(erro))
        return
    if chamado is None:
        st.warning(f"O chamado {protocolo} não foi encontrado.")
        return

    st.divider()
    area_avisos = st.container()  # Os avisos do último salvar aparecem aqui (preenchida depois do formulário).
    st.subheader(f"Chamado {chamado['protocolo']}")
    st.caption(
        f"Criado em {chamados.formatar_data(chamado['criado_em'])} · "
        f"Última atualização em {chamados.formatar_data(chamado['atualizado_em'])}"
    )
    campos = (("status", "Status"), ("setor", "Setor responsável"), ("prioridade", "Prioridade"), ("categoria", "Categoria"))
    for coluna, (campo, rotulo) in zip(st.columns(4), campos):
        with coluna:
            mostrar_campos(chamado, [(campo, rotulo)])
    mostrar_campos(chamado, [
        ("mensagem", "Mensagem original"),
        ("resumo", "Resumo"),
        ("justificativa", "Justificativa da prioridade sugerida pela IA"),
    ])

    # A data da última atualização e o número de gravações da sessão entram nas chaves: depois de
    # salvar, os campos recomeçam com os valores do banco e a observação volta em branco (mesmo que
    # duas gravações caiam no mesmo segundo).
    versao = f"{protocolo}_{chamado['atualizado_em']}_{st.session_state.get('gravacoes', 0)}"
    with st.form(f"acompanhamento_{protocolo}"):
        st.markdown("**Acompanhamento**")
        colunas = st.columns(3)
        status = colunas[0].selectbox(
            "Status", chamados.STATUS, index=chamados.STATUS.index(chamado["status"]), key=f"status_{versao}"
        )
        setor = colunas[1].selectbox(
            "Setor responsável", triagem.SETORES, index=triagem.SETORES.index(chamado["setor"]), key=f"setor_{versao}"
        )
        prioridade = colunas[2].selectbox(
            "Prioridade", triagem.PRIORIDADES, index=triagem.PRIORIDADES.index(chamado["prioridade"]),
            key=f"prioridade_{versao}",
        )
        observacao = st.text_area(
            "Observação / justificativa (opcional, fica salva no histórico)",
            max_chars=chamados.MAX_CARACTERES_OBSERVACAO,
            placeholder="Ex.: cliente contatado por telefone; troca autorizada.",
            key=f"observacao_{versao}",
        )
        salvar = st.form_submit_button("Salvar alterações")
    if salvar:
        salvar_acompanhamento(protocolo, chamado["status"], status, setor, prioridade, observacao)
    # Os avisos só são lidos numa execução que não está salvando (o salvar termina com st.rerun()):
    # um segundo clique em "Salvar alterações" durante o envio ao Telegram não apaga o alerta do
    # primeiro. As chaves levam o protocolo: o aviso de um chamado nunca aparece sobre outro.
    with area_avisos:
        aviso = st.session_state.pop(f"aviso_detalhes_{protocolo}", None)
        if aviso:
            st.success(aviso)
        # O status foi salvo, mas o cliente do Telegram ficou sem aviso: a gestão precisa avisá-lo.
        alerta = st.session_state.pop(f"alerta_detalhes_{protocolo}", None)
        if alerta:
            st.warning(alerta)
    mostrar_historico(protocolo)


def salvar_acompanhamento(protocolo, status_anterior, status, setor, prioridade, observacao):
    """Grava as alterações e a observação; em caso de sucesso, recarrega a tela.

    Se o status mudou, avisa o cliente que abriu o chamado pelo Telegram. Setor, prioridade e
    observação são assuntos internos da gestão e não geram aviso.
    """
    try:
        chamado, alterado = chamados.atualizar_chamado(protocolo, status, setor, prioridade, observacao)
    except triagem.TriagemError as erro:
        st.error(str(erro))
        return
    # Chaves com o protocolo: se outro chamado for aberto durante o envio, estes avisos não aparecem
    # nele; ficam guardados até este chamado ser aberto de novo.
    chave_aviso, chave_alerta = f"aviso_detalhes_{protocolo}", f"alerta_detalhes_{protocolo}"
    aviso = "Chamado atualizado e registrado no histórico." if alterado else "Nenhuma alteração para salvar."
    st.session_state[chave_aviso] = aviso
    if alterado:
        st.session_state["gravacoes"] = st.session_state.get("gravacoes", 0) + 1
    if alterado and status != status_anterior:
        # Um clique na tela durante o envio interrompe este código, mas o que já está na sessão
        # aparece na próxima execução. Por isso este alerta é gravado antes e trocado pelo resultado.
        st.session_state[chave_alerta] = (
            "Não foi possível confirmar o aviso ao cliente no Telegram: a tela foi usada durante o envio "
            "(falhas ficam registradas no terminal). O novo status continua salvo; na dúvida, avise o "
            "cliente por outro canal."
        )
        # O aviso vem depois da gravação: se o Telegram falhar, o novo status continua salvo.
        with st.spinner("Avisando o cliente no Telegram..."):
            resultado = chamados.avisar_cliente_telegram(chamado)
        alerta = None  # "enviado" e "sem_telegram" (chamado da tela ou do CSV) não geram alerta.
        if resultado == "enviado":
            st.session_state[chave_aviso] = aviso + " Cliente avisado no Telegram."
        elif resultado == "sem_token":
            alerta = (
                "Cliente não avisado no Telegram: o TELEGRAM_BOT_TOKEN não está configurado no arquivo .env "
                "(depois de preencher, reinicie o programa). O novo status continua salvo; avise o cliente "
                "por outro canal."
            )
        elif resultado == "falhou":
            alerta = (
                "Cliente não avisado no Telegram: a mensagem não foi entregue (falha de conexão ou recusa "
                "do Telegram; o motivo ficou registrado no terminal). O novo status continua salvo; "
                "avise o cliente por outro canal."
            )
        st.session_state[chave_alerta] = alerta
    st.rerun()  # Recarrega a fila e os detalhes com os valores gravados.


def mostrar_historico(protocolo):
    """Lista as alterações e observações do chamado, da mais recente para a mais antiga."""
    st.markdown("**Histórico**")
    try:
        historico = chamados.listar_historico(protocolo)
    except triagem.TriagemError as erro:
        st.error(str(erro))
        return
    if not historico:
        st.caption("Nenhuma alteração ou observação registrada ainda.")
        return
    for item in historico:
        with st.container(border=True):
            st.caption(chamados.formatar_data(item["registrado_em"]))
            # Texto puro: a observação é digitada livremente e não deve ser interpretada como Markdown.
            if item["alteracoes"]:
                st.text(item["alteracoes"])
            if item["observacao"]:
                st.text("Observação: " + item["observacao"])


def exportar_e_importar():
    """Exportação de todos os chamados em CSV e importação explícita do historico.csv anterior."""
    st.divider()
    st.subheader("Exportar e importar")
    try:
        dados = chamados.exportar_csv()
    except triagem.TriagemError as erro:
        st.error(str(erro))
    else:
        st.download_button(
            "Exportar chamados em CSV",
            data=dados,
            file_name=f"chamados_{datetime.now():%Y%m%d-%H%M}.csv",
            mime="text/csv",
        )

    with st.expander("Importar histórico CSV da versão anterior"):
        caminho = chamados.caminho_csv()
        st.write(
            "Copia para o banco os registros do historico.csv gerado antes da troca para o banco de dados. "
            "Os chamados importados entram como Aberto na fila de Atendimento. Pode ser repetida sem "
            "duplicar registros, e o arquivo original não é alterado."
        )
        st.text(f"Arquivo: {caminho}")
        aviso = st.session_state.pop("aviso_importacao", None)
        if aviso:
            st.success(aviso)
        if not caminho.exists():
            st.info("Nenhum histórico CSV encontrado nesse caminho.")
            return
        if st.button("Importar histórico CSV"):
            try:
                totais = chamados.importar_historico_csv(caminho)
            except triagem.TriagemError as erro:
                st.error(str(erro))
                return
            st.session_state["aviso_importacao"] = (
                f"{totais['importados']} chamado(s) importado(s), {totais['ja_existiam']} já existia(m) no banco "
                f"e {totais['invalidas']} linha(s) inválida(s) ignorada(s). O arquivo original não foi alterado."
            )
            st.rerun()  # Recarrega a fila com os chamados importados.


def aba_gestao():
    st.caption("Área de gestão para uso local: fila por setor, detalhes e acompanhamento dos chamados.")
    painel_e_fila()
    localizar_chamado()
    mostrar_detalhes()
    exportar_e_importar()


def main():
    st.set_page_config(page_title="Triagem Fácil", layout="wide")
    st.title("Triagem Fácil")
    registro, gestao = st.tabs(["Registrar mensagem", "Fila de chamados"])
    with registro:
        aba_registro()
    with gestao:
        aba_gestao()


# O Streamlit executa este arquivo com __name__ == "__main__".
if __name__ == "__main__":
    main()
