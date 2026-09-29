"""Tela do Triagem Fácil (Streamlit).

A tela só cuida da interface. A análise com IA, a validação e o CSV ficam em
triagem.py, na mesma função usada pelo bot: triagem.analisar_e_registrar(texto).

Executar: python -m streamlit run app.py
"""

import streamlit as st

import triagem

# Rótulos fixos exibidos acima de cada campo do resultado.
ROTULOS = {
    "categoria": "Categoria",
    "prioridade": "Prioridade",
    "resumo": "Resumo",
    "justificativa": "Justificativa",
}

# Chaves do st.session_state onde fica o último envio (resultado OU erro).
CHAVES_DO_ENVIO = ("resultado", "erro_registro", "erro")


def avisar_se_falta_configuracao():
    """Mostra no topo a instrução de configuração do .env; a tela continua abrindo."""
    try:
        triagem.configuracao_provedor()
    except triagem.TriagemError as erro:
        st.warning(str(erro))


def analisar(texto):
    """Processa um envio e guarda na sessão o resultado ou o erro."""
    # Apaga o envio anterior: se este falhar, o resultado antigo não aparece.
    for chave in CHAVES_DO_ENVIO:
        st.session_state.pop(chave, None)

    try:
        triagem.validar_mensagem(texto)  # Mensagem vazia para aqui, sem chamar a API.
        with st.spinner("Analisando mensagem..."):
            st.session_state["resultado"] = triagem.analisar_e_registrar(texto)
    except triagem.RegistroError as erro:
        # RegistroError vem antes: é um tipo especial de TriagemError.
        st.session_state["erro_registro"] = str(erro)
    except triagem.TriagemError as erro:
        st.session_state["erro"] = str(erro)


def mostrar_ultimo_envio():
    """Mostra o que está na sessão; um rerun comum não chama a API nem grava de novo."""
    if "resultado" in st.session_state:
        resultado = st.session_state["resultado"]
        st.subheader("Resultado da análise")
        for campo, rotulo in ROTULOS.items():
            st.markdown(f"**{rotulo}**")
            # st.text mostra o valor da IA como texto puro (sem Markdown nem HTML).
            st.text(resultado[campo])
        st.success("Análise registrada no histórico")
    elif "erro_registro" in st.session_state:
        st.error("Falha no registro: " + st.session_state["erro_registro"])
    elif "erro" in st.session_state:
        st.error(st.session_state["erro"])
        st.info("Para tentar novamente, clique em “Analisar e registrar”.")


def main():
    st.set_page_config(page_title="Triagem Fácil")
    st.title("Triagem Fácil")
    st.write(
        "Cole a mensagem de um cliente: a IA sugere categoria, prioridade, resumo "
        "e justificativa, e a análise é registrada no histórico CSV."
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


# O Streamlit executa este arquivo com __name__ == "__main__".
if __name__ == "__main__":
    main()
