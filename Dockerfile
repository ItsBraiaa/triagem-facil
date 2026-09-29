# Imagem do Triagem Fácil. A mesma imagem serve a tela (web) e o bot do Telegram.
FROM python:3.11-slim

WORKDIR /app

# Dependências primeiro: se só o código mudar, o Docker reaproveita esta etapa (cache).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Apenas o código. O .env não entra na imagem: as credenciais chegam na execução
# (env_file do compose.yaml).
COPY triagem.py chamados.py app.py bot.py ./

# Tema e barra de ferramentas da tela (.streamlit/config.toml). O address = "localhost" desse
# arquivo não vale no contêiner: o --server.address=0.0.0.0 da linha de comando (compose.yaml
# e CMD abaixo) tem precedência sobre o arquivo.
COPY .streamlit ./.streamlit

EXPOSE 8501

# Comando padrão: a tela. O serviço "bot" do compose.yaml troca por "python bot.py".
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
