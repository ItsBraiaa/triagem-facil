# Como executar o Triagem Fácil

O Triagem Fácil lê a mensagem de um cliente, usa inteligência artificial para dizer do que ela trata e qual setor deve cuidar dela, e registra um chamado com número de protocolo.

> **Aviso:** projeto desenvolvido com auxílio de inteligência artificial, apenas como prova de conceito (PoC) para um trabalho da faculdade. Não é uma solução homologada nem 100% segura: não deve ser usado em produção.

## Sumário

1. [O que você vai precisar](#precisar)
2. [Baixar o projeto](#baixar)
3. [Criar a chave da IA (Gemini)](#chave)
4. [(Opcional) Criar o bot do Telegram](#telegram)
5. [O que colocar no arquivo .env (consulta)](#env)
6. [Caminho A: Windows (PowerShell)](#windows)
7. [Caminho A: Linux (terminal)](#linux)
8. [Caminho B: Docker (Windows ou Linux)](#docker)
9. [Usando o sistema](#usando)
10. [Onde ficam os dados e como fazer cópia de segurança](#dados)
11. [Problemas comuns](#problemas)
12. [O que já foi testado](#testado)

### Como ler este guia

- Faça um passo de cada vez, na ordem.
- Terminal é a janela onde você digita comandos. No Windows, usamos o **PowerShell**.
- As caixas cinzas têm três usos:
  - Caixa logo depois de "rode", "Confira" ou do texto de um passo: é um **comando**. Copie, cole no terminal e aperte **Enter**. Cada caixa tem um comando só.
  - Caixa logo depois de **"Você deve ver"**: é só o que deve aparecer na tela. **Não digite.**
  - Caixa da [seção 5](#env): mostra linhas do arquivo `.env`. **Não vai no terminal.**
- Para colar no PowerShell (Windows), use **Ctrl+V** ou o botão direito do mouse. No terminal do Linux, use **Ctrl+Shift+V**.
- **"Você deve ver"** mostra o resultado esperado. **"Se não vir"** diz o que fazer quando o resultado for diferente.
- Se você abrir este arquivo no Bloco de Notas, não vai ver caixas: os comandos são as linhas entre as marcas ```` ``` ````.

---

<a id="precisar"></a>

## 1. O que você vai precisar

- Um computador com **Windows** ou **Linux**.
- **Internet.** A IA e o Telegram funcionam pela internet.
- Uma **conta Google**, para criar a chave do Gemini (a IA). O Gemini tem uma camada gratuita, mas ela tem **limites de uso (cotas)**. Não é uso ilimitado.
- **(Opcional)** O **Telegram**, no celular ou no computador, para testar o bot.

### Escolha um caminho

| Caminho | Para quem | O que instalar |
|---|---|---|
| **A: com Python** (recomendado para quem vai só testar) | Quem quer o jeito mais direto. | O Python. |
| **B: com Docker** | Quem já usa Docker. Para quem nunca usou, instalar o Docker dá mais trabalho que instalar o Python. | O Docker. |

Os dois caminhos fazem a mesma coisa. Escolha **um** só.

Faça os passos 2 e 3 (e o 4, se for usar o Telegram). Não precisa ler a seção 5 agora: os passos A6, L5 e D3 mandam você para lá na hora certa. Depois, siga só a seção do seu caminho:

- Caminho A no Windows: [seção 6](#windows).
- Caminho A no Linux: [seção 7](#linux).
- Caminho B, em qualquer sistema: [seção 8](#docker).

---

<a id="baixar"></a>

## 2. Baixar o projeto

### Se você recebeu uma pasta ou um arquivo ZIP

Para baixar o ZIP pelo site do GitHub: abra o repositório, confira no botão do canto esquerdo, acima da lista de arquivos, se o branch é o que a equipe indicou (hoje, `feature/chamados-sqlite`) e clique no botão verde **Code** → **Download ZIP**. O branch `main` pode ter uma versão antiga, sem o `chamados.py` e sem a pasta `.streamlit`.

1. Se for um arquivo **.zip**, extraia:
   - **Windows:** clique com o botão direito no arquivo e escolha **Extrair tudo...**.
   - **Linux:** clique com o botão direito e escolha **Extrair aqui** (o nome pode variar).
2. Coloque a pasta num lugar fácil do próprio computador (não numa pasta de rede).
   - **Windows:** use uma pasta fora do OneDrive, por exemplo `C:\Users\voce\triagem-facil`. A pasta **Documentos** pode estar no OneDrive, que sincroniza os arquivos com a internet e pode travar o banco de dados. Se o caminho da pasta tiver `OneDrive`, mova a pasta.
   - **Linux:** por exemplo, `~/Documentos/triagem-facil`.
3. Abra a pasta e confira se ela tem estes arquivos:
   - `app.py`, `bot.py`, `chamados.py`, `triagem.py`
   - `requirements.txt`, `.env.example`
   - `compose.yaml`, `Dockerfile`
   - a pasta `.streamlit`

   **Se não vir:**
   - Os arquivos podem estar numa pasta dentro da pasta. Entre nela até ver o `app.py`. Essa é a **pasta do projeto**.
   - No Linux, nomes que começam com ponto (`.env.example`, `.streamlit`) ficam escondidos. Aperte **Ctrl+H** no gerenciador de arquivos para mostrá-los.
   - Se `.env.example` ou `.streamlit` não vieram, peça a pasta completa a quem enviou.
4. Se a pasta veio com coisas do computador de outra pessoa, apague antes de continuar:
   - a pasta `.venv`: ela só funciona no computador onde foi criada. Você cria a sua no passo A4 (Windows) ou L3 (Linux);
   - o arquivo `.env`: ele tem a chave e o token de outra pessoa. Crie o seu no passo A6, L5 ou D3. **Nunca use a chave de outra pessoa.**

### Se você sabe usar o git

Se você tem acesso ao repositório, rode:

```text
git clone -b feature/chamados-sqlite https://github.com/ItsBraiaa/triagem-facil.git
```

Se a equipe indicar outro branch, troque o nome que vem depois do `-b`. Depois, entre na pasta criada:

```text
cd triagem-facil
```

### Se você vai enviar o projeto para alguém

Não compacte a sua pasta de trabalho. Ela tem o seu `.env` (com a sua chave e o seu token), a `.venv` (que só funciona no seu computador) e o `triagem.db` (com os seus chamados de teste).

- O jeito mais seguro é enviar o link do repositório ou o ZIP baixado do GitHub (veja acima).
- Se precisar enviar a sua pasta, compacte uma **cópia** e apague da cópia: `.env`, `.venv`, `__pycache__`, `triagem.db`, a pasta `data`, `README-2.md` e `PROMPT_EVOLUCAO_TRIAGEM_FACIL.md` (o `README-2.md` é um rascunho antigo e contradiz este guia).

---

<a id="chave"></a>

## 3. Criar a chave da IA (Gemini)

A chave é uma senha que deixa o programa usar a IA do Google. **Ela é secreta:** não mostre, não envie e não coloque em apresentações.

1. Abra o [Google AI Studio](https://aistudio.google.com/apikey) e entre com sua conta Google.
2. Clique no botão de criar chave (em inglês, **Create API key**). Se a página pedir, escolha ou crie um projeto.
3. Copie a chave. Ela é um texto longo. Guarde por enquanto num lugar seguro: você vai colar no arquivo `.env` na [seção 5](#env).
4. Escolha o **modelo** (qual versão da IA usar):
   - O nome do modelo precisa estar **disponível para a sua conta**.
   - Exemplo testado em 29/09/2026: **`gemini-3.1-flash-lite`**.
   - **Atenção:** modelos antigos, como `gemini-2.5-flash-lite`, podem responder **erro 404** para chaves novas.
   - Veja a [lista de modelos](https://ai.google.dev/gemini-api/docs/models), a [tabela de preços](https://ai.google.dev/gemini-api/docs/pricing) e os [limites de uso](https://ai.google.dev/gemini-api/docs/rate-limits).

**Sobre a camada gratuita:**

- Ela vale para alguns modelos e tem cotas. Confira os limites antes da apresentação.
- Não é preciso ativar o faturamento para tentar a camada gratuita.
- Use mensagens **fictícias** nos testes. Segundo a tabela de preços do Google, o conteúdo enviado na camada gratuita pode ser usado para melhorar os produtos do Google.

### Alternativa: OpenRouter

Use o OpenRouter só se não quiser usar o Gemini. Configure **um provedor por vez**.

1. Crie uma conta no [OpenRouter](https://openrouter.ai/).
2. Em [API Keys](https://openrouter.ai/settings/keys), crie uma chave.
3. No [catálogo de modelos](https://openrouter.ai/models), escolha um modelo e copie o nome completo dele.
4. Confira o preço e o saldo necessário. Não conte que qualquer modelo é gratuito.
5. No `.env` ([seção 5](#env)), use `AI_PROVIDER=openrouter` e preencha `OPENROUTER_API_KEY` e `OPENROUTER_MODEL`.

---

<a id="telegram"></a>

## 4. (Opcional) Criar o bot do Telegram

Pule esta seção se você vai usar só a tela no navegador.

1. No Telegram, abra o [@BotFather](https://t.me/BotFather). É o bot oficial do Telegram para criar bots.
2. Envie `/newbot`.
3. Responda o que ele pedir: um nome para o bot e um nome de usuário (username), que precisa terminar em `bot`.
4. O @BotFather responde com um **token**, um texto com números e letras.
5. Copie o token e guarde num lugar seguro. Você vai colar no `.env` na [seção 5](#env).
6. Guarde também o link do bot (`t.me/...`), para abrir a conversa depois.

**O token é secreto.** Quem tem o token controla o bot. Não mostre o token em fotos da tela e não envie a ninguém. Se ele vazar, peça um token novo no @BotFather (comando `/revoke`).

---

<a id="env"></a>

## 5. O que colocar no arquivo .env (consulta)

O `.env` é um arquivo de texto com as configurações e as senhas do programa. Ele fica **na pasta do projeto** e o nome é exatamente `.env`, sem `.txt` no fim.

**Você cria o `.env` durante o seu caminho** (passo A6 no Windows, L5 no Linux ou D3 no Docker), a partir do modelo `.env.example`. Esses passos trazem os comandos e mandam você para cá. Esta seção só explica o que colocar no arquivo.

### O que cada linha significa

| Variável | Para que serve | O que colocar |
|---|---|---|
| `AI_PROVIDER` | Qual IA usar. | `gemini` (padrão) ou `openrouter`. |
| `GEMINI_API_KEY` | Chave do Gemini. | A chave da [seção 3](#chave). |
| `GEMINI_MODEL` | Modelo do Gemini. | Por exemplo, `gemini-3.1-flash-lite`. |
| `OPENROUTER_API_KEY` | Chave do OpenRouter. | Só se usar `AI_PROVIDER=openrouter`. Senão, deixe vazio. |
| `OPENROUTER_MODEL` | Modelo do OpenRouter. | Só se usar `AI_PROVIDER=openrouter`. Senão, deixe vazio. |
| `TELEGRAM_BOT_TOKEN` | Liga o bot e o aviso ao cliente no Telegram quando o status do chamado muda (a tela também usa o token para esse aviso). | O token da [seção 4](#telegram). Se for usar só a tela, sem Telegram, deixe a linha como está. |
| `DB_PATH` (opcional) | Outro lugar para o banco de dados. | Em geral, não mexa. Sem ele, o banco `triagem.db` fica na pasta do projeto. |
| `CSV_PATH` (opcional) | Onde está o `historico.csv` da versão anterior (só para importar). | Em geral, não mexa. Sem ele, o programa procura `historico.csv` na pasta do projeto. |

### Como deve ficar

O arquivo começa com os valores `COLE_...`. O programa trata `COLE_...` como "não configurado". Em cada linha que você vai usar, apague **todo** o texto depois do `=` (o `COLE_...` inteiro) e cole o seu valor no lugar.

Veja como as linhas ficam antes (como vêm no arquivo) e depois (preenchidas). Os valores do "Depois" são só exemplos: use a sua chave e o seu token. Não copie esta caixa para o arquivo.

```text
Antes:  GEMINI_API_KEY=COLE_SUA_CHAVE_GEMINI_AQUI
Depois: GEMINI_API_KEY=EXEMPLO-cole-aqui-a-sua-chave

Antes:  GEMINI_MODEL=COLE_O_IDENTIFICADOR_DO_MODELO_GEMINI_AQUI
Depois: GEMINI_MODEL=gemini-3.1-flash-lite

Antes:  TELEGRAM_BOT_TOKEN=COLE_O_TOKEN_DO_BOT_AQUI
Depois: TELEGRAM_BOT_TOKEN=EXEMPLO-cole-aqui-o-token-do-bot
```

- As linhas `AI_PROVIDER=gemini`, `OPENROUTER_API_KEY=` e `OPENROUTER_MODEL=` já vêm certas para o Gemini. Não mexa nelas.
- Não vai usar o Telegram? Deixe a linha `TELEGRAM_BOT_TOKEN` como está, com o `COLE_...`, ou apague o que vem depois do `=`. Os dois contam como "não configurado".

Regras simples:

- Uma configuração por linha, no formato `NOME=valor`.
- Sem espaços antes ou depois do `=` e sem aspas.
- Linhas que começam com `#` são comentários: o programa ignora. Pode deixá-las.
- Para usar `DB_PATH` ou `CSV_PATH`, apague o `#` do começo da linha e escreva o caminho depois do `=`. No Docker, não precisa: o `compose.yaml` já define os dois.
- Cole a chave direto do site. Chave copiada do Word ou do WhatsApp pode trazer aspas curvas, e o programa recusa.

### Como abrir o .env para editar

- **Windows:** no PowerShell, na pasta do projeto, rode `notepad .env`. O Bloco de Notas abre o arquivo. Edite, salve com **Ctrl+S** e feche.
- **Linux:** no terminal, na pasta do projeto, rode `nano .env`. Edite como explica o passo [L5](#l5), salve com **Ctrl+O** e **Enter**, e saia com **Ctrl+X**. Se preferir um editor com janela, abra o arquivo pelo gerenciador de arquivos (aperte **Ctrl+H** para ver os arquivos escondidos).

### Cuidados importantes

- **O `.env` é secreto.** Não envie, não mostre na apresentação e não coloque no repositório. O projeto já deixa o `.env` fora do git e fora da imagem do Docker.
- **Reinicie o programa depois de mudar o `.env`.** Ele é lido só quando o programa começa.
- Se uma variável com o mesmo nome já existir nas configurações do sistema, ela vale mais que o `.env`.

---

<a id="windows"></a>

## 6. Caminho A: Windows (PowerShell)

### A1. Instale o Python (só na primeira vez)

1. Abra [python.org/downloads](https://www.python.org/downloads/).
2. Na página, **não** clique em **Download Python install manager**. Clique no link logo abaixo dele: **Or get the standalone installer for Python 3.14...** (o número final pode mudar). Serve qualquer versão **3.11 ou mais nova**.
3. Abra o arquivo baixado (termina em `.exe`).
4. Na primeira tela, marque a caixa **Add python.exe to PATH**. Ela fica embaixo. **Este é o detalhe mais importante.**
5. Clique em **Install Now** e espere.

**Você deve ver:** a tela **Setup was successful**. Clique em **Close**.

**Se não vir:** se você já tinha instalado o **Python install manager**, tudo bem: feche e abra o PowerShell e faça o teste do passo A3. Se `python --version` mostrar 3.11 ou mais nova, pode seguir. Se não mostrar, instale pelo link **standalone installer** do passo 2.

<a id="a2"></a>

### A2. Abra o PowerShell na pasta do projeto

1. Abra o **Explorador de Arquivos** e entre na pasta do projeto (a que tem o `app.py`).
2. Clique na **barra de endereço** (onde aparece o caminho da pasta).
3. Apague o texto, digite `powershell` e aperte **Enter**.

**Você deve ver:** uma janela de texto com uma linha parecida com `PS C:\Users\voce\triagem-facil>`.

4. Confira se está na pasta certa:

```powershell
dir
```

**Você deve ver:** na lista, `app.py`, `bot.py`, `requirements.txt` e `.env.example`.

**Se não vir:** o PowerShell abriu em outra pasta. Feche a janela e repita este passo.

### A3. Confira o Python

```powershell
python --version
```

**Você deve ver:** algo como `Python 3.12.6`. Serve qualquer versão **3.11 ou mais nova**.

**Se não vir:**

- Se aparecer que o Python não foi encontrado, ou se abrir a Microsoft Store: instale o Python de novo (passo A1) **marcando Add python.exe to PATH**. Depois, feche o PowerShell e abra de novo (passo A2).
- Se o comando `py -3 --version` funcionar, use `py -3` no lugar de `python` no passo A4.

### A4. Crie o ambiente virtual (só na primeira vez)

O ambiente virtual é a pasta `.venv`. Nela ficam as bibliotecas do projeto, separadas do resto do computador.

```powershell
python -m venv .venv
```

**Você deve ver:** nenhuma mensagem. Depois de alguns segundos, a linha `PS ...>` volta. Rode `dir` e confira que apareceu a pasta `.venv`.

**Se não vir:** confira o passo A3.

### A5. Instale as bibliotecas (só na primeira vez)

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Pode levar alguns minutos. Espere até a linha `PS ...>` voltar.

**Você deve ver:** no fim, uma linha que começa com `Successfully installed`, citando `streamlit-1.64.0` e `python-telegram-bot-22.8`, entre outras.

- Um aviso `[notice] A new release of pip is available` pode ser ignorado.

**Se não vir:**

- Mensagem dizendo que o termo `.\.venv\Scripts\python.exe` **não é reconhecido**: a `.venv` não foi criada ou você está em outra pasta. Volte ao passo A2 e depois ao A4.
- Erro de conexão: confira a internet e rode o comando de novo.

Não é preciso "ativar" o ambiente virtual nem mudar a política de execução do PowerShell. Os comandos deste guia já usam o Python da `.venv`.

### A6. Crie e preencha o .env (só na primeira vez)

**Atenção:** se você já preencheu o seu `.env`, pule o primeiro comando. Ele troca o arquivo sem perguntar.

```powershell
Copy-Item .env.example .env
```

**Você deve ver:** nenhuma mensagem.

```powershell
notepad .env
```

**Você deve ver:** o Bloco de Notas abre o arquivo, com linhas como `AI_PROVIDER=gemini`.

Preencha como explica a [seção 5](#env). Salve com **Ctrl+S** e feche o Bloco de Notas.

<a id="a7"></a>

### A7. Ligue a tela

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Na primeira vez, o Streamlit pode mostrar **Welcome to Streamlit!** e pedir um **Email**. Não precisa preencher: aperte **Enter**.

**Você deve ver:**

```text
  You can now view your Streamlit app in your browser.

  URL: http://localhost:8501
```

1. O navegador pode abrir sozinho. Se não abrir, abra [http://localhost:8501](http://localhost:8501).
2. Na página, confira o título **Triagem Fácil** e as abas **Registrar mensagem** e **Fila de chamados**.

**Se não vir:**

- Aviso amarelo **Configuração incompleta...**: o `.env` não está preenchido. Corrija o arquivo (passo A6), pare a tela com **Ctrl+C** e rode o comando de novo.
- O endereço mostrado termina em `8502` (ou outro número): a porta 8501 já estava em uso. Use o endereço que aparecer na linha `URL`.
- `Error: Invalid value: File does not exist: app.py`, ou o termo `.\.venv\Scripts\python.exe` **não é reconhecido** (no Linux, `No such file or directory`): o terminal não está na pasta do projeto. Volte ao passo A2 (L2 no Linux) e rode o comando de novo.
- Apareceram `Local URL` e `Network URL` em vez de uma linha só `URL`: falta a pasta `.streamlit` (com o arquivo `config.toml`) ao lado do `app.py`. Sem ela, a tela aceita conexões de outros computadores da rede. Pare com **Ctrl+C**, confira a lista de arquivos da [seção 2](#baixar) (no Linux, **Ctrl+H** mostra os arquivos escondidos) e, se a pasta não veio, peça a pasta completa a quem enviou.

**Deixe esta janela aberta.** Enquanto a tela estiver ligada, a janela fica "ocupada", e isso é normal. Fechar a janela desliga a tela.

### A8. (Opcional) Ligue o bot do Telegram

O bot roda numa **segunda janela** do PowerShell. A tela pode continuar ligada.

1. Abra outro PowerShell na pasta do projeto (repita o passo A2).
2. Rode:

```powershell
.\.venv\Scripts\python.exe bot.py
```

**Você deve ver:** duas linhas parecidas com estas (data, hora e caminho mudam):

```text
... INFO bot: Iniciando o bot (provedor de IA: gemini; banco: C:\...\triagem.db). Pressione Ctrl+C para encerrar.
... INFO telegram.ext.Application: Application started
```

3. No Telegram, abra o seu bot e envie `/start`.

**Você deve ver:** o bot responde com a explicação de uso, começando com "Envie uma mensagem de cliente para registrar uma solicitação.".

**Se não vir:**

- Se o terminal mostrar **Bot não iniciado: ...**, a própria mensagem diz o que falta. Veja também os [Problemas comuns](#problemas).
- `can't open file ... bot.py`: o terminal não está na pasta do projeto. Volte ao passo A2.

Tela e bot gravam no mesmo banco. Os chamados do bot aparecem na fila da tela.

### A9. Como parar

Clique na janela que você quer parar e aperte **Ctrl+C**.

- A tela mostra `Stopping...`.
- O bot mostra `Application is stopping. This might take a moment.` e depois `Bot encerrado.`.
- Se a linha `PS ...>` não voltar, aperte **Ctrl+C** mais uma vez ou feche a janela.

Os chamados continuam salvos.

### A10. Nas próximas vezes

1. Abra o PowerShell na pasta do projeto (passo A2).
2. Ligue a tela (passo A7).
3. Se quiser o bot, abra outra janela e ligue o bot (passo A8).

Não repita os passos A1, A4, A5 e A6. A `.venv` e o `.env` já estão prontos.

---

<a id="linux"></a>

## 7. Caminho A: Linux (terminal)

### L1. Confira ou instale o Python (só na primeira vez)

Abra um terminal e rode:

```bash
python3 --version
```

**Você deve ver:** algo como `Python 3.12.3`. Serve qualquer versão **3.11 ou mais nova**.

**Se não vir:** se aparecer 3.10 ou uma versão menor (o Ubuntu 22.04, por exemplo, vem com o 3.10), este caminho não serve. Use o [Caminho B (Docker)](#docker).

No Ubuntu ou Debian, instale também o `venv` (mesmo que o Python já exista). Rode um comando de cada vez:

```bash
sudo apt update
```

```bash
sudo apt install python3 python3-venv python3-pip
```

- O `sudo` pede a sua senha. Enquanto você digita, nada aparece na tela: isso é normal. Aperte **Enter** no fim.
- Se perguntar se deseja continuar, confirme.
- Outras distribuições usam outro gerenciador de pacotes.

<a id="l2"></a>

### L2. Abra o terminal na pasta do projeto

- No gerenciador de arquivos, entre na pasta do projeto, clique com o botão direito num espaço vazio e escolha **Abrir no terminal** (o nome pode variar).
- Ou, no terminal, entre na pasta com `cd`. Exemplo (troque pelo seu caminho):

```bash
cd ~/Documentos/triagem-facil
```

Confira:

```bash
ls -a
```

**Você deve ver:** `app.py`, `bot.py`, `requirements.txt` e `.env.example`.

**Se não vir:** você está em outra pasta. Use `cd` com o caminho certo.

### L3. Crie o ambiente virtual (só na primeira vez)

```bash
python3 -m venv .venv
```

**Você deve ver:** nenhuma mensagem. Depois, `ls -a` mostra a pasta `.venv`.

**Se não vir:** se aparecer `ensurepip is not available`, falta o pacote `python3-venv`. Instale:

```bash
sudo apt install python3-venv
```

Depois, crie a `.venv` de novo:

```bash
python3 -m venv --clear .venv
```

### L4. Instale as bibliotecas (só na primeira vez)

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Pode levar alguns minutos.

**Você deve ver:** no fim, uma linha que começa com `Successfully installed`, citando `streamlit-1.64.0` e `python-telegram-bot-22.8`, entre outras. Um aviso `[notice] A new release of pip is available` pode ser ignorado.

**Se não vir:** `No such file or directory` indica que a `.venv` não existe ou que você está em outra pasta. Volte aos passos L2 e L3.

<a id="l5"></a>

### L5. Crie e preencha o .env (só na primeira vez)

**Atenção:** se você já preencheu o seu `.env`, pule o primeiro comando. Ele troca o arquivo sem perguntar.

```bash
cp .env.example .env
```

**Você deve ver:** nenhuma mensagem.

```bash
nano .env
```

**Você deve ver:** o editor `nano` com linhas como `AI_PROVIDER=gemini`.

Preencha como explica a [seção 5](#env). No `nano`:

- O mouse não move o cursor. Use as **setas do teclado** para ir até o começo do `COLE_...`.
- Apague o texto até o fim da linha com a tecla **Delete**.
- Cole a chave com **Ctrl+Shift+V**. Cada linha deve ficar só com `NOME=seu-valor`.
- Salve com **Ctrl+O** e **Enter**, e saia com **Ctrl+X**.

### L6. Ligue a tela

```bash
.venv/bin/python -m streamlit run app.py
```

Se o Streamlit pedir um **Email**, aperte **Enter** para pular.

**Você deve ver:**

```text
  You can now view your Streamlit app in your browser.

  URL: http://localhost:8501
```

Abra [http://localhost:8501](http://localhost:8501) (o navegador pode abrir sozinho). Confira o título **Triagem Fácil** e as abas **Registrar mensagem** e **Fila de chamados**.

**Se não vir:** veja o "Se não vir" do [passo A7](#a7). É igual no Linux.

Deixe o terminal aberto. Fechar o terminal desliga a tela.

### L7. (Opcional) Ligue o bot do Telegram

Abra um **segundo terminal** na pasta do projeto (passo L2) e rode:

```bash
.venv/bin/python bot.py
```

**Você deve ver:** as linhas `Iniciando o bot (provedor de IA: ...; banco: .../triagem.db)` e `Application started`. No Telegram, envie `/start` ao seu bot e veja a resposta.

**Se não vir:**

- Leia a mensagem **Bot não iniciado: ...** e veja os [Problemas comuns](#problemas).
- `can't open file ... bot.py` ou `No such file or directory`: o terminal não está na pasta do projeto. Volte ao passo L2.

### L8. Como parar e nas próximas vezes

- Para parar, aperte **Ctrl+C** em cada terminal. Os chamados continuam salvos.
- Nas próximas vezes, faça só os passos L2, L6 e (se quiser) L7.

---

<a id="docker"></a>

## 8. Caminho B: Docker (Windows ou Linux)

Neste caminho, você não instala o Python. O Docker roda o programa num "contêiner", que já vem com tudo. O `.env` não entra na imagem: as senhas são lidas só na hora de rodar.

### D1. Instale e ligue o Docker (só na primeira vez)

- **Windows:** instale o [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/) e siga o instalador. Use o modo de contêineres Linux, que é o padrão. O instalador pode pedir para instalar o WSL e para reiniciar o computador: aceite. Se aparecer um erro de virtualização, use o Caminho A. Depois, abra o Docker Desktop e espere ele terminar de iniciar.
- **Linux, com Docker Desktop:**
  1. Ligue o serviço (ele é do seu usuário, sem `sudo`):

     ```bash
     systemctl --user start docker-desktop
     ```

  2. Só na primeira vez, aponte o comando `docker` para o Docker Desktop:

     ```bash
     docker context use desktop-linux
     ```

     **Você deve ver:** `Current context is now "desktop-linux"`.
- **Linux, com Docker Engine:** instale o [Docker Engine](https://docs.docker.com/engine/install/) e o [plugin Compose](https://docs.docker.com/compose/install/linux/). Para ligar: `sudo systemctl start docker`.

### D2. Confira se o Docker está funcionando

Abra o terminal na pasta do projeto ([passo A2](#a2) no Windows, [passo L2](#l2) no Linux) e rode:

```text
docker version
```

**Você deve ver:** duas partes, **Client** e **Server**.

Depois, rode:

```text
docker compose version
```

**Você deve ver:** uma linha como `Docker Compose version v...`.

**Se não vir:** se faltar a parte **Server** e aparecer `failed to connect to the docker API` (ou `Cannot connect to the Docker daemon`), o Docker não está ligado ou o comando aponta para o lugar errado. Volte ao passo D1.

### D3. Crie o .env e a pasta de dados (só na primeira vez)

1. Crie o `.env` (pule se você já preencheu o seu):
   - Windows: `Copy-Item .env.example .env`
   - Linux: `cp .env.example .env`
2. Preencha o `.env` como explica a [seção 5](#env) (para abrir o arquivo, veja "Como abrir o .env para editar"). Não precisa mexer em `DB_PATH` e `CSV_PATH`.
3. Crie a pasta `data`, onde ficará o banco de dados.

No Windows (PowerShell):

```powershell
New-Item -ItemType Directory -Force data
```

**Você deve ver:** uma pequena tabela com o nome `data` na última coluna. Não é erro.

No Linux:

```bash
mkdir -p data
```

**Você deve ver:** nenhuma mensagem.

Se você tem o `historico.csv` da versão anterior, coloque-o dentro de `data`.

### D4. Confira a configuração

Este comando confere o `compose.yaml` e o `.env` sem mostrar as suas senhas:

```text
docker compose config --quiet
```

**Você deve ver:** nenhuma mensagem. Isso quer dizer que está tudo certo.

**Se não vir:** a mensagem `env file ... .env not found` indica que falta o `.env` nesta pasta. Volte ao passo D3.

### D5. Ligue o que você quer usar

Escolha **uma** das opções. Na primeira vez, o Docker baixa e prepara tudo, e isso pode levar vários minutos.

**Só a tela:**

```text
docker compose up --build web
```

**Você deve ver:** várias linhas de preparação e, no fim, `You can now view your Streamlit app in your browser.`. Abra [http://localhost:8501](http://localhost:8501).

- Ignore as linhas `Network URL` e `External URL`, se aparecerem. São endereços internos do contêiner.
- A tela fica disponível só neste computador.

**Só o bot:**

```text
docker compose up --build bot
```

**Você deve ver:** as linhas `Iniciando o bot (provedor de IA: ...; banco: /app/data/triagem.db)` e `Application started`. No Telegram, envie `/start` ao seu bot.

**Tela e bot juntos (mesmo banco):**

```text
docker compose --profile telegram up --build
```

Deixe o terminal aberto. Para parar, aperte **Ctrl+C** e espere terminar.

### D6. Rodar em segundo plano (depois que tudo funcionar)

Assim, você pode fechar o terminal e o programa continua ligado. Escolha **uma** das opções.

**Só a tela** (sem Telegram):

```text
docker compose up -d --build web
```

Para ver as mensagens da tela:

```text
docker compose logs -f web
```

**Tela e bot:**

```text
docker compose --profile telegram up -d --build
```

Para ver as mensagens dos dois:

```text
docker compose --profile telegram logs -f
```

**Ctrl+C** só fecha a visualização das mensagens. O programa continua ligado.

Sem o `TELEGRAM_BOT_TOKEN` no `.env`, use a opção **Só a tela**. Na outra, o bot desliga logo depois de ligar e as mensagens mostram **Bot não iniciado: TELEGRAM_BOT_TOKEN não configurado**.

### D7. Parar sem perder dados

```text
docker compose --profile telegram down
```

Esse comando desliga a tela e o bot. **A pasta `data` e os chamados continuam no computador.**

### Dicas do Docker

- Mudou o `.env`? Rode o `down` (passo D7) e ligue de novo (passo D5).
- Atualizou o código? Mantenha o `--build` nos comandos.
- **Rode um bot só por token.** Não ligue o bot do Docker e o bot do Caminho A ao mesmo tempo.
- O banco do Docker (`data/triagem.db`) é diferente do banco do Caminho A (`triagem.db`). Os chamados de um não aparecem no outro.
- No Docker, os horários ficam em UTC (3 horas a mais que o horário de Brasília).
- O computador e o Docker precisam continuar ligados para o bot responder.

---

<a id="usando"></a>

## 9. Usando o sistema

### 9.1 Registrar uma mensagem pela tela

1. Abra a aba **Registrar mensagem**.
2. Escreva ou cole a mensagem no campo **Mensagem do cliente** (até 3.000 caracteres).
3. Clique em **Analisar e registrar**.

**Você deve ver:** primeiro, **Analisando mensagem...**. Depois, uma caixa verde como esta (os valores mudam):

```text
Solicitação registrada com o protocolo TF-20260929-7STU8D e encaminhada para a fila do setor Logística. Triagem automática concluída em 3,2 s.
```

Abaixo, em **Resultado da análise**: Protocolo, Setor responsável, Categoria, Prioridade, Resumo e Justificativa.

- O tempo da triagem é o tempo que a IA e o programa levaram. No teste real, cada mensagem levou de 2 a 12 segundos.
- Cada clique registra um chamado novo, mesmo com o mesmo texto.

**Se não vir:** aparece uma mensagem vermelha com o motivo. Nesse caso, nada foi gravado: corrija o que a mensagem pede e clique em **Analisar e registrar** de novo. Veja os [Problemas comuns](#problemas).

### 9.2 A aba Fila de chamados

É a área de gestão. Ela não tem login e foi feita para uso neste computador.

**Visão geral (painel de números):**

- Quadros **Aberto**, **Em atendimento**, **Resolvido** e **Total**.
- Quadros **Pendentes · Atendimento**, **Pendentes · Financeiro**, **Pendentes · Logística** e **Pendentes · Suporte Técnico**. Pendente é o chamado Aberto ou Em atendimento.
- O painel conta todos os chamados. Os filtros da fila não mudam esses números.

**Fila:**

- Colunas: Protocolo, Resumo, Setor, Prioridade, Status e Criado em.
- Ordem: prioridade **Alta → Média → Baixa**. Na mesma prioridade, do chamado mais antigo para o mais novo.
- Filtros **Setor**, **Prioridade** e **Status**. Filtro vazio significa "todos".
- Por padrão, a fila mostra só os chamados **Aberto** e **Em atendimento**. Para ver os encerrados, inclua **Resolvido** no filtro Status.

**Atualização automática:**

- O painel e a fila **se atualizam sozinhos a cada 30 segundos**. Os chamados que chegam pelo bot aparecem sem ninguém clicar.
- O botão **Atualizar fila** recarrega a tela na hora.
- A atualização automática não apaga o que você estiver digitando numa observação.

<a id="acompanhar"></a>

### 9.3 Abrir um chamado e acompanhar

1. Escolha um chamado em **Abrir detalhes de um chamado da fila**.
   - Ou digite o protocolo em **Localizar chamado pelo protocolo** e clique em **Localizar**. Funciona também para chamados fora dos filtros. Maiúsculas, minúsculas e espaços nas pontas não atrapalham.
2. Os detalhes aparecem mais abaixo: **Chamado TF-...**, datas, status, setor, prioridade, categoria, mensagem original, resumo e justificativa.
3. Em **Acompanhamento**, mude o que precisar:
   - **Status:** Aberto, Em atendimento ou Resolvido (Resolvido encerra o chamado).
   - **Setor responsável** e **Prioridade**, se a IA errou.
   - **Observação / justificativa** (opcional, até 1.000 caracteres). Exemplo: "cliente contatado por telefone".
4. Clique em **Salvar alterações**.

**Você deve ver:** a mensagem verde **Chamado atualizado e registrado no histórico.** Se nada mudou, aparece **Nenhuma alteração para salvar.**

**Histórico:** abaixo do formulário, cada gravação aparece com a data, o que mudou (por exemplo, `Status: Aberto → Em atendimento`) e a observação. A mais recente fica em cima.

- Você pode salvar só uma observação, sem mudar nada.
- O histórico não pode ser editado nem apagado pela tela.
- As observações são internas: o cliente não vê.
- A mensagem original e a análise da IA não mudam.

### 9.4 Aviso automático ao cliente no Telegram

Quando você muda o **status** de um chamado que foi aberto **pelo bot**, a tela avisa o cliente no Telegram.

**Você deve ver:** **Avisando o cliente no Telegram...** e depois **Chamado atualizado e registrado no histórico. Cliente avisado no Telegram.**

O cliente recebe só o protocolo e o novo status:

```text
Atualização da sua solicitação TF-20260929-7STU8D:
Novo status: Em atendimento.
Informe o protocolo se precisar falar sobre ela.
```

Regras do aviso:

- Só quando o **status** muda. Mudar setor, prioridade ou observação não gera aviso.
- Só para chamados abertos pelo bot. Chamados da tela ou importados do CSV não têm conversa no Telegram para avisar.
- A tela não mostra por onde o chamado chegou. Para testar o aviso, use o protocolo que o bot respondeu no Telegram: digite-o em **Localizar chamado pelo protocolo** e clique em **Localizar**.
- A tela precisa do `TELEGRAM_BOT_TOKEN` no `.env`, lido quando a tela liga. Se você preencheu o token depois, reinicie a tela.
- **Não clique em nada** enquanto aparece "Avisando o cliente no Telegram...".
- Se o aviso falhar, aparece um alerta amarelo. **O novo status continua salvo.** Nesse caso, avise o cliente por outro canal.

### 9.5 Usar o bot do Telegram

1. Abra o seu bot e envie `/start`. O bot explica como usar.
2. Envie uma mensagem de cliente, como se fosse o cliente.

**Você deve ver:** **Analisando mensagem...** e depois uma resposta como esta (os valores mudam):

```text
Solicitação registrada.
Protocolo: TF-20260929-7STU8D
Setor responsável: Logística

Categoria: Reclamação
Prioridade: Alta
Resumo: ...
Justificativa: ...
Tempo da triagem automática: 3,2 s

A solicitação está na fila do setor responsável. Informe o protocolo se precisar falar sobre ela.
```

**Consultar um chamado:** envie uma mensagem com o protocolo, por exemplo `status do pedido TF-20260929-7STU8D`.

**Você deve ver:**

```text
Situação da solicitação:
TF-20260929-7STU8D: Em atendimento, setor Logística (atualizado em 29/09/2026 13:21)
```

A consulta também funciona na aba **Registrar mensagem** da tela.

Bom saber:

- **Toda mensagem com um protocolo é uma consulta.** Ela não chama a IA e não abre chamado. Para registrar um problema novo, envie a mensagem sem o protocolo.
- Protocolo que não existe recebe "não encontrado. Confira se o protocolo está correto.".
- A consulta mostra só status, setor e data. Nunca mostra a mensagem original.
- O bot só lê texto. Áudio, foto e documento recebem um pedido para enviar texto.
- O bot atende só conversas privadas. Grupos e mensagens editadas são ignorados.
- Mensagens enviadas com o bot desligado são descartadas quando ele liga. Envie uma mensagem nova depois de ligar.

### 9.6 Exportar os chamados em CSV

1. Na aba **Fila de chamados**, clique em **Atualizar fila**. Assim o arquivo inclui os chamados que acabaram de chegar pelo bot: a atualização automática recarrega só o painel e a fila, não o arquivo da exportação.
2. Desça até **Exportar e importar**.
3. Clique em **Exportar chamados em CSV**.

**Você deve ver:** o navegador baixa um arquivo `chamados_AAAAMMDD-HHMM.csv` com todos os chamados. Ele abre no Excel com os acentos certos. As observações do histórico não vão para o CSV.

- No Linux (LibreOffice Calc), aparece a janela **Importar texto**: marque **Ponto e vírgula** como separador e clique em **OK**.

### 9.7 Importar o historico.csv da versão anterior

Só para quem usou a versão antiga, que gravava um `historico.csv`.

1. Coloque o `historico.csv` na pasta do projeto (no Docker, dentro de `data`).
2. Na aba **Fila de chamados**, abra **Importar histórico CSV da versão anterior**.
3. Confira o caminho em **Arquivo:** e clique em **Importar histórico CSV**.

**Você deve ver:** uma mensagem verde como "3 chamado(s) importado(s), 0 já existia(m) no banco e 0 linha(s) inválida(s) ignorada(s). O arquivo original não foi alterado."

- Os chamados importados entram como **Aberto** na fila de **Atendimento**.
- Pode importar de novo: o programa não duplica os chamados.

**Se não vir:** a mensagem "Nenhum histórico CSV encontrado nesse caminho." indica que o arquivo não está no lugar mostrado em **Arquivo:**. Se você colocou o arquivo com a tela já aberta, clique em **Atualizar fila** e abra a seção de novo.

### 9.8 Mensagens de exemplo para testar

Use mensagens fictícias. O resultado é o **esperado**, mas a IA decide e pode variar. Se o setor não for o esperado, corrija nos detalhes do chamado.

| Mensagem | Categoria esperada | Prioridade esperada | Setor esperado |
|---|---|---|---|
| "Vocês aceitam pagamento por cartão?" | Dúvida | Baixa | Financeiro |
| "Meu produto chegou quebrado e quero fazer a troca." | Reclamação | Média | Logística |
| "Meu pedido está atrasado e preciso receber ainda hoje para um evento." | Reclamação | Alta | Logística |

<a id="teste"></a>

**Teste rápido antes da apresentação:**

1. Ligue a tela e, se for usar, o bot. Para o aviso ao cliente, o `TELEGRAM_BOT_TOKEN` precisa estar no `.env` **antes** de ligar a tela.
2. Se for usar o Telegram, envie `/start` ao bot.
3. Envie as três mensagens, uma de cada vez (pela tela ou pelo bot). Confira protocolo, setor, categoria, prioridade, resumo, justificativa e o tempo da triagem automática. Se usar o Telegram, anote um protocolo que o bot respondeu.
4. Na aba **Fila de chamados**, confira o painel **Visão geral** e a ordem da fila: a mensagem de prioridade Alta aparece primeiro.
5. Com a aba aberta, envie mais uma mensagem pelo bot e não clique em nada: em até 30 segundos o chamado aparece no painel e na fila.
6. Digite o protocolo que o bot respondeu em **Localizar chamado pelo protocolo** e clique em **Localizar**. Mude o status para **Em atendimento**, escreva uma observação e clique em **Salvar alterações**. Confira "Cliente avisado no Telegram." na tela, a mensagem de atualização no celular (sem a observação) e a entrada no **Histórico**.
7. Marque outro chamado como **Resolvido** e confira que ele sai da fila padrão e que os números do painel mudam.
8. No bot, envie `status do pedido` seguido do protocolo do passo 6. A resposta mostra o novo status.
9. Pare os programas, ligue de novo e confira que os chamados continuam na fila.
10. Se houver `historico.csv` da versão anterior, importe-o duas vezes e confira que a segunda importação não cria chamados.

### 9.9 Tema claro ou escuro

A tela abre seguindo o tema do seu computador (claro ou escuro). Para trocar:

1. Clique nos três pontinhos **⋮** no canto superior direito da tela.
2. Escolha **Light** (claro), **Dark** (escuro) ou **System** (igual ao computador).

Você deve ver as cores mudarem na hora, sem perder o que está na tela.

---

<a id="dados"></a>

## 10. Onde ficam os dados e como fazer cópia de segurança

| Como você roda | Banco de dados (chamados e histórico) | historico.csv antigo (só para importar) |
|---|---|---|
| Caminho A (Windows ou Linux) | `triagem.db` na pasta do projeto, ou o caminho de `DB_PATH` | `historico.csv` na pasta do projeto, ou o caminho de `CSV_PATH` |
| Caminho B (Docker) | `data/triagem.db` na pasta do projeto | `data/historico.csv` |

- O banco é criado sozinho no primeiro uso.
- Tudo fica num arquivo só: os chamados e o histórico de alterações.
- Parar ou recriar o contêiner do Docker **não apaga** a pasta `data`.
- **Não apague o `triagem.db`.** Se ele for apagado, os chamados somem e o programa começa um banco vazio.

**Como fazer cópia de segurança:**

1. Pare a tela e o bot (**Ctrl+C**, ou o passo D7 no Docker).
2. Copie o arquivo `triagem.db` (ou a pasta `data`, no Docker) para outro lugar, como um pen drive.
3. Ligue os programas de novo.

Não copie o banco com a tela ou o bot ligados: a cópia pode sair incompleta.

Para voltar uma cópia, pare os programas e coloque o arquivo no mesmo lugar, com o mesmo nome.

---

<a id="problemas"></a>

## 11. Problemas comuns

Depois de mudar o `.env`, sempre reinicie o programa.

### Instalação

| Sintoma | O que fazer |
|---|---|
| `python` não encontrado no Windows, ou abre a Microsoft Store | Instale o Python 3.11+ pelo [python.org](https://www.python.org/downloads/) marcando **Add python.exe to PATH**. Feche e abra o PowerShell de novo. Se `py -3 --version` funcionar, use `py -3` no lugar de `python` para criar a `.venv`. |
| Termo `.\.venv\Scripts\python.exe` **não é reconhecido** | Você está fora da pasta do projeto ou a `.venv` não foi criada. Refaça os passos A2 e A4. |
| Linux: `ensurepip is not available` ao criar a `.venv` | Falta o pacote `python3-venv`. Rode `sudo apt install python3-venv` e depois `python3 -m venv --clear .venv`. |
| `No module named streamlit` (ou outro módulo) | Instale as bibliotecas com o Python da `.venv` (passo A5 ou L4) e ligue a tela com o mesmo Python (`.\.venv\Scripts\python.exe` ou `.venv/bin/python`). |
| Streamlit pede **Email** no terminal | Aperte **Enter** para pular. Isso aparece só na primeira vez. |

### Configuração e IA

| Sintoma | O que fazer |
|---|---|
| Aviso **Configuração incompleta para AI_PROVIDER=...** | Confira o `.env` na pasta do projeto: nomes certos e valores `COLE_...` trocados. Reinicie. No Windows, confira com `dir` se o arquivo não virou `.env.txt`. |
| **AI_PROVIDER inválido** | Use só `gemini` ou `openrouter`. |
| Chave **tem caracteres inválidos** | Copie a chave de novo, direto do site, para o `.env`. Aspas curvas vindas do Word ou do WhatsApp não são aceitas. Reinicie. |
| **O provedor recusou a requisição (HTTP 404)**, principalmente com um modelo antigo | O modelo não está disponível para a sua chave. Para chaves novas, o Google responde que modelos antigos, como `gemini-2.5-flash-lite`, estão "no longer available to new users" (a tela e o bot mostram só o HTTP 404). Troque `GEMINI_MODEL` por um modelo atual, como `gemini-3.1-flash-lite`, e reinicie. |
| **O provedor recusou a requisição (HTTP 400)** | Confira o nome do modelo e a chave. O Gemini também responde 400 para chave inválida. |
| Erro com **HTTP 401** ou **403** | A chave foi recusada. Confira a chave do provedor escolhido em `AI_PROVIDER`. |
| Erro com **HTTP 402** | Falta saldo no OpenRouter. Confira a conta e o preço do modelo. |
| Erro com **HTTP 429** (cota) | O limite de uso acabou. Espere a cota liberar. Para trocar de provedor, mude o `.env` e reinicie. |
| Erro com **HTTP 5xx**, "não respondeu em 30 segundos" ou "Não foi possível conectar ao serviço de IA" | O serviço está fora do ar ou a internet está instável. Tente de novo em alguns minutos. |
| "Resposta inesperada", "resposta incompleta", "formato JSON esperado" ou campo "longo demais" | Envie de novo. Se repetir, escolha outro modelo. Nada é gravado nesses casos. |
| O setor sugerido não faz sentido | Corrija o setor nos detalhes do chamado ([9.3](#acompanhar)). |
| A nova chave não fez efeito | Reinicie o programa. No Docker, rode `down` e `up` de novo. Confira também se a variável não está definida nas configurações do sistema, que valem mais que o `.env`. |

### Tela e banco de dados

| Sintoma | O que fazer |
|---|---|
| Endereço termina em **8502** em vez de 8501 | A porta 8501 já estava em uso, e a tela escolheu outra. Use o endereço mostrado na linha `URL`, ou pare o outro programa que usa a 8501. |
| Docker não liga a tela porque a **porta 8501 está ocupada** | Pare a tela do Caminho A (ou outro contêiner) que está usando a 8501 e rode o comando de novo. |
| `Error: Invalid value: File does not exist: app.py` | O terminal não está na pasta do projeto. Refaça o passo A2 (L2 no Linux). |
| Apareceram **Local URL** e **Network URL** no terminal (Caminho A) | Falta a pasta `.streamlit` ao lado do `app.py` e, sem ela, a tela aceita conexões de outros computadores da rede. Pare com **Ctrl+C** e confira a lista de arquivos da [seção 2](#baixar). No Docker, ignore essas linhas. |
| **Falha no registro** ou **Não foi possível acessar o banco de dados** | Confira se a pasta do banco existe e permite gravação. Com tela e bot ligados, tente de novo: uma gravação pode ter esperado demais pela outra. No Linux com Docker Engine, os arquivos de `data/` pertencem ao root. |
| O chamado não aparece na fila | Espere até 30 segundos ou clique em **Atualizar fila**. Confira os filtros: Resolvido fica escondido por padrão. Tela e bot precisam usar o mesmo banco: os dois no Caminho A, ou os dois no Docker. |
| Importação: **Nenhum histórico CSV encontrado** | Coloque o `historico.csv` na pasta do projeto (`data/` no Docker) ou confira `CSV_PATH`. |
| Importação: **não tem as colunas do histórico anterior** ou **Não foi possível ler** | O arquivo precisa ser o CSV da versão anterior. Um CSV salvo de novo pelo Excel pode ter mudado. Feche o arquivo se ele estiver aberto em outro programa. |
| Horários 3 horas adiantados | No Docker, os horários ficam em UTC. É o comportamento esperado. |

### Telegram

| Sintoma | O que fazer |
|---|---|
| **Bot não iniciado: TELEGRAM_BOT_TOKEN não configurado** | Coloque o token do @BotFather no `.env` e ligue o bot de novo. |
| **Bot não iniciado: o Telegram recusou o TELEGRAM_BOT_TOKEN** | Copie o token de novo do @BotFather para o `.env`. |
| **Bot não iniciado: não foi possível conectar ao Telegram (TimedOut)**, ou o bot responde às vezes sim, às vezes não | A rede não alcançou o Telegram a tempo. Algumas redes bloqueiam ou limitam o Telegram de vez em quando. Ligue o bot de novo. Se continuar, teste abrir [api.telegram.org](https://api.telegram.org) no navegador ou use outra rede (por exemplo, o roteador do celular). |
| O bot não responde | Confira o token, se o bot está ligado (terminal aberto), se é uma conversa privada com o bot certo e se a mensagem foi enviada depois de ligar o bot. |
| Bot responde **Ocorreu um erro inesperado na análise** | Veja a linha "Erro inesperado na análise" no terminal do bot e envie a mensagem de novo. |
| Erro **Conflict** no terminal do bot | Outro bot está ligado com o mesmo token. Pare o outro (Caminho A ou Docker). |
| **Cliente não avisado no Telegram: o TELEGRAM_BOT_TOKEN não está configurado** | Coloque o token no `.env` e reinicie a tela. O status já foi salvo: avise o cliente por outro canal. |
| **Cliente não avisado no Telegram: a mensagem não foi entregue** | Falha de conexão ou recusa do Telegram. O motivo fica no terminal da tela. O status já foi salvo: avise o cliente por outro canal. |
| **Não foi possível confirmar o aviso ao cliente no Telegram** | Alguém clicou na tela durante o envio. O status foi salvo. Na dúvida, avise o cliente por outro canal. |
| O cliente não recebeu aviso e não apareceu alerta | O aviso só sai quando o **status** muda e só para chamados abertos pelo bot. Chamados da tela ou do CSV não geram aviso. |

### Docker

| Sintoma | O que fazer |
|---|---|
| `failed to connect to the docker API`, `Cannot connect to the Docker daemon` ou falta a parte **Server** | O Docker não está ligado. Abra o Docker Desktop. No Linux com Docker Desktop: `systemctl --user start docker-desktop` e, uma vez, `docker context use desktop-linux`. Com Docker Engine: `sudo systemctl start docker`. |
| `Unit docker.service not found` (ou `could not be found`) | Você usa o Docker Desktop, que não cria o `docker.service`. Use `systemctl --user start docker-desktop` e `docker context use desktop-linux`. |
| Linux com Docker Engine: `permission denied ... docker.sock` | Rode os comandos do Docker com `sudo` na frente (por exemplo, `sudo docker compose up --build web`). Ou siga "Manage Docker as a non-root user" em [docs.docker.com/engine/install/linux-postinstall](https://docs.docker.com/engine/install/linux-postinstall/) e depois saia e entre de novo na sua sessão do Linux. |
| `env file ... .env not found` | Crie o `.env` na pasta do projeto (passo D3). |

---

<a id="testado"></a>

## 12. O que já foi testado

- **Testes automáticos com respostas simuladas** (sem IA e sem Telegram reais), no Linux, com Python 3.14 e 3.11: 473 checagens em cada versão, todas passando.
- **Teste real em 29/09/2026:** o Gemini, com o modelo `gemini-3.1-flash-lite`, classificou corretamente as três mensagens de exemplo (de 2 a 12 segundos cada). O bot conectou ao Telegram.
- **Navegador:** o painel e a fila se atualizaram sozinhos, e o texto de uma observação não salva foi mantido.
- **Docker:** testado no Linux (Docker Desktop 29.6.1) antes das melhorias desta rodada (tema, tempo da triagem, aviso no Telegram e painel).
- **Ainda não testado nesta versão:** o Windows (os comandos foram testados na versão anterior, no Windows 11 com Python 3.12), o aviso no Telegram com um cliente real, o tempo da triagem exibido numa triagem com a IA real e, no Docker, o tema e o aviso no Telegram.
