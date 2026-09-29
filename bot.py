"""Bot do Telegram do Triagem Fácil.

O bot é um segundo canal do mesmo registro da tela. Cada mensagem de texto recebida em
conversa privada passa por chamados.analisar_e_registrar(texto, origem), a mesma função
usada por app.py: chama a IA, valida a resposta e grava o chamado no banco com um protocolo.

Executar: python bot.py   (Ctrl+C para encerrar)
O bot usa long polling: ele só funciona enquanto este programa estiver rodando.
"""

import asyncio
import logging
import sys
import time

from telegram import Update
from telegram.error import InvalidToken, TelegramError
from telegram.ext import Application, CommandHandler, MessageHandler, filters

import chamados
# Importar triagem também carrega o .env da pasta do aplicativo (inclusive TELEGRAM_BOT_TOKEN).
import triagem

logger = logging.getLogger("bot")

TEXTO_INICIAL = (
    "Envie uma mensagem de cliente para registrar uma solicitação. Cada mensagem de texto válida "
    "vira um chamado: você recebe o protocolo, o setor responsável, a categoria, a prioridade, "
    "o resumo e a justificativa.\n"
    "Para acompanhar, envie o protocolo (ex.: status do pedido TF-20260929-ABC234)."
)
TEXTO_COMANDO_DESCONHECIDO = "Comando não reconhecido. Use /start para ver como usar o bot."
TEXTO_PEDIR_TEXTO = (
    "Envie a mensagem do cliente como texto. "
    "Áudio, foto, documento e outros conteúdos não são analisados."
)
TEXTO_ANALISANDO = "Analisando mensagem..."
TEXTO_TENTAR_DE_NOVO = "Para tentar novamente, envie a mensagem outra vez."
TEXTO_ERRO_INESPERADO = "Ocorreu um erro inesperado na análise. O motivo foi registrado no terminal do bot."

# Só mensagens NOVAS (edições ficam de fora) em conversa PRIVADA (grupos ficam de fora).
CONVERSA_PRIVADA = filters.ChatType.PRIVATE & filters.UpdateType.MESSAGE


# ---------- Respostas do bot ----------

async def iniciar(update, context):
    """/start: explica o uso. Não chama a IA e não grava chamado."""
    await update.message.reply_text(TEXTO_INICIAL)


async def comando_desconhecido(update, context):
    """Qualquer outro comando: orienta a usar /start."""
    await update.message.reply_text(TEXTO_COMANDO_DESCONHECIDO)


async def pedir_texto(update, context):
    """Áudio, foto, documento, figurinha etc.: pede texto, sem chamar a IA."""
    await update.message.reply_text(TEXTO_PEDIR_TEXTO)


def formatar_confirmacao(chamado, novo, duracao=None):
    """Monta a resposta em texto simples: registro, protocolo, setor, análise e tempo da triagem.

    Informa que a solicitação foi registrada e está na fila; não diz que o problema foi resolvido.
    """
    inicio = "Solicitação registrada." if novo else "Esta mensagem já tinha sido registrada."
    # O tempo (em segundos) só aparece para o chamado novo: na reentrega, nenhuma triagem foi feita agora.
    tempo = ""
    if novo and duracao is not None:
        tempo = f"Tempo da triagem automática: {chamados.formatar_duracao(duracao)}\n"
    return (
        f"{inicio}\n"
        f"Protocolo: {chamado['protocolo']}\n"
        f"Setor responsável: {chamado['setor']}\n\n"
        f"Categoria: {chamado['categoria']}\n"
        f"Prioridade: {chamado['prioridade']}\n"
        f"Resumo: {chamado['resumo']}\n"
        f"Justificativa: {chamado['justificativa']}\n"
        f"{tempo}\n"
        "A solicitação está na fila do setor responsável. "
        "Informe o protocolo se precisar falar sobre ela."
    )


def formatar_consulta(situacoes):
    """Resposta a uma mensagem que cita protocolos: a situação de cada um, em texto simples."""
    return "Situação da solicitação:\n" + "\n".join(situacoes)


async def analisar_texto(update, context):
    """Texto do cliente: valida, avisa, analisa e registra, e responde no mesmo chat."""
    texto = update.message.text
    # Identifica esta mensagem: se o Telegram entregar a mesma atualização de novo,
    # o chamado já gravado é reaproveitado, sem nova chamada à IA e sem duplicar.
    origem = f"telegram:{update.effective_chat.id}:{update.message.message_id}"
    try:
        # Mensagem vazia ou acima de 3.000 caracteres para aqui, sem chamar a IA.
        triagem.validar_mensagem(texto)
    except triagem.TriagemError as erro:
        await update.message.reply_text(str(erro))
        return

    try:
        # Mensagem que cita um protocolo é consulta: responde a situação, sem IA e sem chamado novo.
        situacoes = await asyncio.to_thread(chamados.consultar_status, texto)
    except triagem.TriagemError as erro:
        await update.message.reply_text(f"{erro}\n{TEXTO_TENTAR_DE_NOVO}")
        return
    if situacoes:
        await update.message.reply_text(formatar_consulta(situacoes))
        return

    await update.message.reply_text(TEXTO_ANALISANDO)
    try:
        # analisar_e_registrar usa requests e SQLite, que bloqueiam enquanto esperam.
        # asyncio.to_thread a executa em outra thread para não travar o bot.
        # Cronometra a triagem automática (IA, validação e gravação) para mostrar na confirmação.
        inicio = time.perf_counter()
        chamado, novo = await asyncio.to_thread(chamados.analisar_e_registrar, texto, origem)
        duracao = time.perf_counter() - inicio
    except triagem.RegistroError as erro:
        # RegistroError vem antes: é um tipo especial de TriagemError (a IA respondeu, o banco falhou).
        await update.message.reply_text("Falha no registro: " + str(erro))
        return
    except triagem.TriagemError as erro:
        await update.message.reply_text(f"{erro}\n{TEXTO_TENTAR_DE_NOVO}")
        return
    except Exception as erro:
        # Erro não previsto: sem esta resposta, a conversa ficaria parada em "Analisando mensagem...".
        logger.error("Erro inesperado na análise: %s: %s", type(erro).__name__, erro)
        await update.message.reply_text(f"{TEXTO_ERRO_INESPERADO}\n{TEXTO_TENTAR_DE_NOVO}")
        return

    await enviar_confirmacao(update, chamado, novo, duracao)


async def enviar_confirmacao(update, chamado, novo, duracao):
    """Envia a confirmação; se o Telegram falhar, apenas registra no terminal."""
    try:
        await update.message.reply_text(formatar_confirmacao(chamado, novo, duracao))
    except TelegramError as erro:
        # O chamado já está no banco: não repetimos a análise nem a gravação.
        logger.warning(
            "O chamado %s foi registrado, mas a resposta não foi enviada ao Telegram (%s: %s).",
            chamado["protocolo"],
            type(erro).__name__,
            erro,
        )


async def registrar_erro(update, context):
    """Handler global: qualquer erro não tratado vira uma linha curta no terminal."""
    erro = context.error
    logger.error("Erro no bot: %s: %s", type(erro).__name__, erro)


# ---------- Inicialização ----------

def ler_token():
    """Lê TELEGRAM_BOT_TOKEN; sem token (ou com o valor COLE_...) encerra com instrução."""
    token = triagem.ler_variavel("TELEGRAM_BOT_TOKEN")
    if token is None:
        sys.exit(
            "Bot não iniciado: TELEGRAM_BOT_TOKEN não configurado. Crie o bot com o @BotFather "
            "(/newbot), coloque o token no arquivo .env (TELEGRAM_BOT_TOKEN=...) e execute o bot novamente."
        )
    return token


def conferir_provedor():
    """Confere a configuração da IA antes de ligar o bot; se faltar algo, encerra com instrução."""
    try:
        nome, _url, _chave, _modelo = triagem.configuracao_provedor()
    except triagem.TriagemError as erro:
        sys.exit(f"Bot não iniciado: {erro}")
    return nome


def conferir_banco():
    """Cria o banco, se preciso, antes de ligar o bot; se a pasta não permitir gravação, encerra."""
    try:
        return chamados.preparar_banco()
    except triagem.TriagemError as erro:
        sys.exit(f"Bot não iniciado: {erro}")


def configurar_logs(token):
    """Mostra os logs no terminal sem nunca exibir o token do bot."""
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
    # O httpx registra em INFO cada URL chamada, e a URL do Telegram contém o token.
    logging.getLogger("httpx").setLevel(logging.WARNING)

    def esconder_token(registro):
        # Com token recusado, a própria biblioteca escreve o token no texto do erro.
        # Este filtro resume o erro em uma linha (sem traceback) e troca o token por "<token>".
        texto = registro.getMessage()
        if registro.exc_info:
            erro = registro.exc_info[1]
            texto += f" ({type(erro).__name__}: {erro})"
            registro.exc_info = None
        registro.msg = texto.replace(token, "<token>")
        registro.args = ()
        return True

    for manipulador in logging.getLogger().handlers:
        manipulador.addFilter(esconder_token)


def criar_aplicacao(token):
    """Monta o bot e liga cada tipo de mensagem à sua função (vale o primeiro handler que servir)."""
    # Sem concurrent_updates: as mensagens são processadas uma de cada vez.
    aplicacao = Application.builder().token(token).build()
    aplicacao.add_handler(CommandHandler("start", iniciar, filters=CONVERSA_PRIVADA))
    aplicacao.add_handler(MessageHandler(CONVERSA_PRIVADA & filters.TEXT & ~filters.COMMAND, analisar_texto))
    aplicacao.add_handler(MessageHandler(CONVERSA_PRIVADA & filters.COMMAND, comando_desconhecido))
    aplicacao.add_handler(MessageHandler(CONVERSA_PRIVADA, pedir_texto))
    aplicacao.add_error_handler(registrar_erro)
    return aplicacao


def main():
    token = ler_token()
    configurar_logs(token)
    nome_provedor = conferir_provedor()
    caminho_banco = conferir_banco()
    aplicacao = criar_aplicacao(token)

    logger.info(
        "Iniciando o bot (provedor de IA: %s; banco: %s). Pressione Ctrl+C para encerrar.",
        nome_provedor,
        caminho_banco,
    )
    try:
        # drop_pending_updates: mensagens enviadas com o bot desligado são descartadas.
        # allowed_updates: o Telegram envia só mensagens novas (sem edições, botões etc.).
        aplicacao.run_polling(drop_pending_updates=True, allowed_updates=[Update.MESSAGE])
    except InvalidToken:
        sys.exit(
            "Bot não iniciado: o Telegram recusou o TELEGRAM_BOT_TOKEN. "
            "Confira o token do @BotFather no arquivo .env e execute o bot novamente."
        )
    except TelegramError as erro:
        sys.exit(
            f"Bot não iniciado: não foi possível conectar ao Telegram ({type(erro).__name__}). "
            "Verifique a internet e execute o bot novamente."
        )
    logger.info("Bot encerrado.")


if __name__ == "__main__":
    main()
