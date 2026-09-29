# Triagem Fácil — como configurar e executar

O projeto classifica mensagens de clientes com Python e **Gemini ou OpenRouter** e registra cada mensagem como um **chamado** em um banco **SQLite**. Cada chamado recebe um **protocolo**, vai para a **fila do setor responsável** (Atendimento, Financeiro, Logística ou Suporte Técnico) e é acompanhado na **área de gestão** da tela, com os status Aberto, Em atendimento e Resolvido. As mensagens chegam pela **tela web** (Streamlit) ou pelo **bot do Telegram**, que usam a mesma lógica de registro e podem funcionar ao mesmo tempo. Escolha **Windows, Linux ou Docker**. Configure somente um provedor de IA por execução.

**Fluxo:** mensagem digitada na tela ou enviada ao bot → chamada à IA → validação da resposta → chamado gravado no banco com protocolo, status Aberto e setor sugerido → protocolo e setor informados no mesmo canal → acompanhamento na fila de chamados. A IA interpreta o texto e sugere categoria, prioridade, setor, resumo e justificativa; o Python valida a resposta, gera o protocolo, controla data/hora e grava o banco.

| Arquivo | Função |
|---|---|
| `triagem.py` | Classificação: prompt, chamada à IA e validação da resposta (categoria, prioridade, setor, resumo e justificativa). |
| `chamados.py` | Registro dos chamados em SQLite: fluxo compartilhado `analisar_e_registrar`, protocolo, fila, acompanhamento, exportação CSV e importação do histórico CSV anterior. |
| `app.py` | Tela Streamlit com duas abas: **Registrar mensagem** e **Fila de chamados** (área de gestão). |
| `bot.py` | Bot do Telegram (long polling), usando a mesma função de registro de `chamados.py`. |
| `.streamlit/config.toml` | Faz a tela aceitar conexões somente deste computador ao executar localmente. |
| `.env.example` | Modelo de configuração, somente com placeholders. |
| `Dockerfile`, `compose.yaml`, `.dockerignore` | Execução com Docker Compose. |

## 1. Preparar as credenciais

### Gemini — opção com camada gratuita

1. Acesse o [Google AI Studio](https://aistudio.google.com/apikey) com sua conta Google.
2. Crie uma chave da Gemini API, selecionando ou criando o projeto conforme as instruções da página.
3. Copie a chave para `GEMINI_API_KEY` no `.env`.
4. Consulte os [modelos](https://ai.google.dev/gemini-api/docs/models) e a [tabela de preços](https://ai.google.dev/gemini-api/docs/pricing). Escolha um modelo de texto disponível para seu projeto cuja modalidade de uso possua camada gratuita e copie seu identificador para `GEMINI_MODEL`.
5. Configure `AI_PROVIDER=gemini`. As variáveis do OpenRouter podem ficar vazias.

A Gemini Developer API possui camada gratuita para determinados modelos, sujeita a disponibilidade e cotas. Confira os [limites do projeto](https://ai.google.dev/gemini-api/docs/rate-limits) antes da apresentação. Não é uso ilimitado, nem todo modelo/modalidade é gratuito; não é necessário ativar faturamento para tentar um projeto elegível na camada gratuita. Use mensagens fictícias na demonstração: a tabela de preços informa que conteúdo da camada gratuita pode ser usado para melhorar os produtos do Google.

### OpenRouter — alternativa ao Gemini

1. Acesse [OpenRouter](https://openrouter.ai/) e entre na sua conta.
2. Em [API Keys](https://openrouter.ai/settings/keys), crie uma chave para o projeto.
3. Escolha um modelo no [catálogo](https://openrouter.ai/models) e copie seu identificador completo para `OPENROUTER_MODEL`.
4. Confira as condições de uso e o saldo necessário para o modelo escolhido. Não presuma que qualquer modelo é gratuito.
5. Configure `AI_PROVIDER=openrouter`. As variáveis do Gemini podem ficar vazias.

### Telegram — necessário apenas para o bot

1. No Telegram, abra o [BotFather oficial](https://t.me/BotFather).
2. Envie `/newbot` e siga as instruções de nome e username.
3. Copie o token recebido para `TELEGRAM_BOT_TOKEN` no arquivo local `.env`.
4. Guarde o link ou username do bot para abrir a conversa durante o teste.

O token é secreto: não o mostre em capturas de tela nem o envie a ninguém.

### Arquivo `.env`

Em cada opção de instalação abaixo, copie `.env.example` para `.env` **somente na primeira configuração**, evitando sobrescrever suas credenciais. Quem já usava a versão anterior mantém o `.env` atual: as variáveis novas são opcionais. Preencha o arquivo com um editor de texto:

```dotenv
AI_PROVIDER=gemini
GEMINI_API_KEY=COLE_SUA_CHAVE_GEMINI_AQUI
GEMINI_MODEL=COLE_O_IDENTIFICADOR_DO_MODELO_GEMINI_AQUI
OPENROUTER_API_KEY=
OPENROUTER_MODEL=
TELEGRAM_BOT_TOKEN=COLE_O_TOKEN_DO_BOT_AQUI
```

Os valores `COLE_...` são placeholders e contam como "não configurado": substitua-os pelos seus. Para usar somente a tela, o token do Telegram pode ficar vazio ou com o placeholder. Mantenha `.env` local; não o inclua em apresentações ou no repositório.

O `.env` é lido uma única vez, quando o programa inicia: **reinicie o programa após alterar a configuração**. Variáveis já definidas no ambiente do sistema têm precedência sobre o `.env`.

Para usar OpenRouter, altere `AI_PROVIDER` para `openrouter` e preencha `OPENROUTER_API_KEY` e `OPENROUTER_MODEL`. O programa exige somente a chave e o modelo do provedor selecionado; um valor diferente de `gemini` ou `openrouter` é recusado com uma mensagem de configuração. A escolha vale igualmente para tela, Telegram, Windows, Linux e Docker. A troca é manual, sem migração automática para um provedor pago quando uma cota acabar.

Opcionais:

- `DB_PATH=caminho/do/banco.db` grava o banco em outro local (a pasta é criada se não existir). Sem essa variável, o banco `triagem.db` fica na pasta do aplicativo.
- `CSV_PATH=caminho/do/historico.csv` indica onde está o histórico CSV da versão anterior, usado **apenas** pela importação (seção 6). Sem essa variável, o arquivo procurado é `historico.csv` na pasta do aplicativo.

## 2. Windows — PowerShell

Pré-requisitos: Python 3.11 ou superior instalado pelo [site oficial](https://www.python.org/downloads/), com comando `python` disponível, e internet. Abra o PowerShell na pasta que contém `app.py`, `bot.py` e `requirements.txt`.

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Salve o `.env` preenchido. Não é necessário ativar o ambiente virtual nem alterar a política de execução do PowerShell. Se `python` não for encontrado, veja a seção 9. Quem atualiza a partir da versão anterior não precisa recriar a `.venv`: as dependências não mudaram.

**Tela web (registro e área de gestão):**

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Na primeira execução, o Streamlit pode pedir um e-mail no terminal: pressione `Enter` para pular. Abra [http://localhost:8501](http://localhost:8501). A tela aceita conexões apenas deste computador (arquivo `.streamlit/config.toml`), por isso execute o comando **dentro da pasta do projeto**. Se faltar configuração da IA, a aba de registro mostra um aviso indicando o que preencher no `.env`; a fila continua acessível. Para encerrar, pressione `Ctrl+C` no terminal.

**Bot do Telegram:**

```powershell
.\.venv\Scripts\python.exe bot.py
```

Abra seu bot no Telegram, envie `/start` e depois uma mensagem de cliente. Mantenha o terminal aberto enquanto estiver usando o bot. Encerre com `Ctrl+C`. Sem token, sem configuração da IA ou sem permissão de gravação na pasta do banco, o bot não inicia e mostra no terminal o que falta.

**Tela e bot ao mesmo tempo:** abra dois terminais na pasta do projeto e execute um comando em cada um. Os dois gravam no mesmo banco; os chamados recebidos pelo bot aparecem na fila ao clicar em **Atualizar fila**.

Nas próximas execuções, basta abrir a pasta do projeto e executar o comando do canal desejado. Não recrie a `.venv` ou o `.env`.

## 3. Linux — terminal

Pré-requisitos: Python 3.11 ou superior, `venv` e internet. Verifique:

```bash
python3 --version
```

Em Ubuntu 24.04 ou outra versão compatível de Debian/Ubuntu, os pacotes podem ser instalados com:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

Confira a versão instalada: distribuições antigas podem fornecer Python anterior a 3.11. Nesse caso, instale uma versão compatível ou utilize a opção Docker. Outras distribuições usam seus próprios gerenciadores de pacotes.

Dentro da pasta que contém `app.py`, `bot.py` e `requirements.txt`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Abra `.env` no editor de sua preferência, preencha os valores da seção 1 e salve.

**Tela web (registro e área de gestão):**

```bash
.venv/bin/python -m streamlit run app.py
```

Se o Streamlit pedir um e-mail no terminal, pressione `Enter` para pular. Abra [http://localhost:8501](http://localhost:8501). Execute o comando dentro da pasta do projeto, para valer a restrição de acesso local. Encerre com `Ctrl+C`.

**Bot do Telegram:**

```bash
.venv/bin/python bot.py
```

Abra seu bot, envie `/start` e uma mensagem de cliente. Encerre com `Ctrl+C`. Para usar tela e bot ao mesmo tempo, execute cada comando em um terminal. Nas próximas execuções, use apenas os comandos dos canais escolhidos.

## 4. Docker — Windows ou Linux

Nesta opção, não é necessário instalar Python no computador. É necessário ter Docker e Compose funcionando, além de internet. No Windows, use [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/) em modo de contêineres Linux; no Linux, siga a instalação do [Docker Engine](https://docs.docker.com/engine/install/) e do [plugin Compose](https://docs.docker.com/compose/install/linux/). A imagem usa `python:3.11-slim` e as versões fixadas em `requirements.txt`; o `.env` não entra na imagem, as credenciais são lidas só na execução.

Abra o terminal na pasta com `compose.yaml` e `Dockerfile`. Verifique:

```text
docker version
docker compose version
```

Se `docker version` não mostrar a parte **Server**, o Docker não está em execução. No Docker Desktop, abra o aplicativo; no Linux, também é possível usar `systemctl --user start docker-desktop` (o Docker Desktop não cria o serviço `docker.service`, que existe apenas no Docker Engine: `sudo systemctl start docker`).

Crie o `.env` conforme a seção 1 (o Compose exige que ele exista). No PowerShell, use `Copy-Item .env.example .env`; no Linux, use `cp .env.example .env`. Se já estiver configurado, preserve o arquivo.

Crie a pasta que armazenará os dados (o banco `triagem.db` e, se existir, o `historico.csv` da versão anterior):

```powershell
# Windows / PowerShell
New-Item -ItemType Directory -Force data
```

```bash
# Linux
mkdir -p data
```

Os próximos comandos são iguais nos dois sistemas.

**Conferir a configuração sem mostrar as credenciais:**

```text
docker compose config --quiet
```

**Construir e iniciar a tela web:**

```text
docker compose up --build web
```

Abra [http://localhost:8501](http://localhost:8501). A porta é publicada só em `127.0.0.1`, isto é, apenas este computador acessa a tela e a área de gestão. A primeira construção baixa a imagem e as dependências, podendo demorar mais. Depois de atualizar o código, mantenha o `--build` para a imagem receber os arquivos novos.

**Iniciar somente o bot:**

```text
docker compose up --build bot
```

Abra seu bot no Telegram e envie `/start`. O bot não precisa de porta publicada, webhook ou URL pública. O serviço `bot` pertence ao profile `telegram` e só sobe quando chamado pelo nome ou com o profile.

**Tela e bot juntos, usando o mesmo banco:**

```text
docker compose --profile telegram up --build
```

**Executar em segundo plano, depois de confirmar que está funcionando:**

```text
docker compose --profile telegram up -d --build
docker compose --profile telegram logs -f
```

`Ctrl+C` encerra o acompanhamento dos logs, mas os serviços em segundo plano continuam ativos. Para encerrar de fato:

```text
docker compose --profile telegram down
```

Esse comando encerra a tela e o bot sem apagar a pasta `data`. Os serviços não dependem um do outro: use `web`, `bot` ou o profile conforme o canal desejado. Execute uma única instância do bot por token (não rode o bot local e o do Docker juntos). O Docker e o computador precisam continuar ligados.

## 5. Onde ficam os dados

| Execução | Banco de dados (chamados) | Histórico CSV anterior (só para importação) |
|---|---|---|
| Windows ou Linux com Python | `triagem.db` na pasta do aplicativo, ou o caminho de `DB_PATH` | `historico.csv` na pasta do aplicativo, ou o caminho de `CSV_PATH` |
| Docker | `data/triagem.db` na pasta do projeto (`DB_PATH=/app/data/triagem.db`) | `data/historico.csv` (`CSV_PATH=/app/data/historico.csv`) |

O banco é criado no primeiro acesso. Cada chamado guarda: protocolo, data de criação, data da última atualização, mensagem original, categoria, prioridade, resumo, justificativa, setor responsável e status. Respostas inválidas da IA não são gravadas. Se a gravação falhar, a tela ou o bot mostra "Falha no registro" e nenhum protocolo é informado.

**O CSV deixou de ser gravado a cada análise.** O `historico.csv` da versão anterior não é alterado, movido nem apagado; seu conteúdo entra no banco pela importação explícita da seção 6. Para obter um CSV atualizado, use **Exportar chamados em CSV** na área de gestão.

No Docker, `./data` fica vinculada à pasta `/app/data` do contêiner. Parar ou recriar o contêiner preserva o banco no computador. As execuções local e Docker usam bancos separados por padrão. Horários são registrados em ISO 8601 com offset; no Docker, o contêiner registra em UTC (`+00:00`), e na execução local usa o fuso do computador (ex.: `-03:00`). A ordem da fila considera o instante real, mesmo com offsets diferentes.

**Cópia de segurança:** com os programas encerrados, copie o arquivo `triagem.db` (ou a pasta `data`). Não copie o banco enquanto a tela ou o bot estiverem gravando.

## 6. Área de gestão — fila de chamados

Abra a tela e clique na aba **Fila de chamados**. A área é destinada ao uso local e não possui login.

- **Fila:** mostra protocolo, resumo, setor, prioridade, status e data de criação. A ordem é prioridade **Alta → Média → Baixa** e, dentro da mesma prioridade, **do chamado mais antigo para o mais novo**.
- **Filtros:** setor, prioridade e status. Filtro vazio significa "todos". Por padrão, a fila mostra os chamados **Aberto** e **Em atendimento**; inclua **Resolvido** no filtro de status para ver os encerrados.
- **Atualizar fila:** recarrega a tela para exibir chamados recebidos pelo bot desde a última atualização.
- **Detalhes:** escolha um chamado em **Abrir detalhes de um chamado da fila**, ou digite o protocolo em **Localizar chamado pelo protocolo** (vale também para chamados fora dos filtros; maiúsculas/minúsculas e espaços nas pontas são aceitos).
- **Acompanhamento:** nos detalhes, altere o **status** (Aberto, Em atendimento, Resolvido) e corrija o **setor** ou a **prioridade**; clique em **Salvar alterações**. A data da última atualização é registrada. A mensagem original, a categoria, o resumo e a justificativa da IA não são alterados.
- **Exportar chamados em CSV:** baixa todos os chamados, do mais antigo para o mais novo, com as colunas `protocolo;criado_em;atualizado_em;mensagem;categoria;prioridade;resumo;justificativa;setor;status`. O arquivo usa ponto e vírgula e UTF-8 com BOM, para o Excel abrir com acentos. Textos que começam com `=`, `+`, `-` ou `@` recebem um apóstrofo no início para a planilha não tratá-los como fórmula.
- **Importar histórico CSV da versão anterior:** mostra o caminho procurado e, se o arquivo existir, o botão **Importar histórico CSV**. Os registros entram como chamados **Aberto** na fila de **Atendimento** (o CSV antigo não tinha setor nem status), com protocolo novo e a data original como data de criação. A importação pode ser repetida: linhas já importadas são reconhecidas e não geram chamados duplicados; linhas novas acrescentadas ao CSV são importadas. O arquivo é aberto somente para leitura. Linhas com data, categoria ou prioridade inválidas são ignoradas e contadas no resultado.

**Protocolo:** formato `TF-AAAAMMDD-XXXXXX`, com a data de criação e seis caracteres sorteados pelo Python (sem `0`, `O`, `1` e `I`, para evitar confusão ao ditar). O banco não aceita protocolos repetidos; se um sorteio coincidir com um existente, o Python sorteia outro.

**Setores:** a IA sugere o setor pela mensagem, seguindo as regras do prompt em `triagem.py`: Atendimento (informações gerais), Financeiro (pagamentos, cobranças, reembolsos, notas fiscais), Logística (entregas, atrasos, frete, trocas e devoluções) e Suporte Técnico (defeitos, instalação, uso de produto, problemas no site ou aplicativo). Essas regras foram definidas nesta implementação; ajuste-as no `PROMPT_SISTEMA` de `triagem.py` para a realidade da loja. Se a mensagem não tiver informação suficiente, ou se a IA sugerir um setor fora da lista, o chamado vai para **Atendimento**. Categoria e setor são campos separados.

## 7. Demonstração

### Exemplos

Use estas mensagens fictícias. Os resultados são **expectativas** para orientar o ensaio, não valores fixos no programa: a IA decide e pode variar. Se o setor sugerido não for o esperado, corrija-o na área de gestão durante a demonstração.

| Mensagem | Categoria esperada | Prioridade esperada | Setor esperado |
|---|---|---|---|
| “Vocês aceitam pagamento por cartão?” | Dúvida | Baixa | Financeiro |
| “Meu produto chegou quebrado e quero fazer a troca.” | Reclamação | Média | Logística |
| “Meu pedido está atrasado e preciso receber ainda hoje para um evento.” | Reclamação | Alta | Logística |

### Teste antes da apresentação

1. Inicie a tela e, se usar Telegram, o bot (seções 2 a 4).
2. Se usar Telegram, envie `/start` primeiro.
3. Envie as três mensagens acima, uma por vez. Confira protocolo, setor, categoria, prioridade, resumo e justificativa na resposta.
4. Na aba **Fila de chamados**, clique em **Atualizar fila** e confira a ordem: a mensagem de prioridade Alta aparece primeiro.
5. Abra um chamado, mude o status para **Em atendimento** e salve; depois marque outro como **Resolvido** e confira que ele sai da fila padrão.
6. Localize um chamado pelo protocolo recebido no Telegram.
7. Encerre os programas, inicie de novo e confirme que os chamados continuam na fila.
8. Se houver `historico.csv` da versão anterior, importe-o duas vezes e confira que a segunda importação não cria chamados.

O bot é um classificador: cada mensagem é independente. Mensagens enviadas enquanto o bot estava desligado são descartadas na inicialização; envie uma mensagem nova após iniciar o processo. Se o Telegram entregar a mesma mensagem de novo, o bot responde com o protocolo já registrado, sem nova análise.

### Roteiro de 10 a 15 minutos

| Tempo | O que fazer |
|---|---|
| 0–2 min | **Problema:** a loja lê, classifica, anota e encaminha cada mensagem manualmente. Mostre como seria a triagem manual de uma mensagem. |
| 2–4 min | **Solução:** entrada (tela ou Telegram) → processamento (`triagem.py` chama a IA e valida o JSON) → saída (chamado no banco, protocolo e setor no canal, fila por setor). Explique que a IA interpreta o texto e o Python controla validação, protocolo, data/hora e gravação. |
| 4–9 min | **Ao vivo:** envie as três mensagens pelo Telegram (celular ou Telegram Desktop) ou pela tela. Mostre o protocolo, o setor e a análise, e comente se bateram com a expectativa. |
| 9–12 min | **Gestão:** mostre a fila ordenada por prioridade, filtre por setor, abra um chamado, altere o status e localize outro pelo protocolo. Exporte o CSV. |
| 12–15 min | **Benefícios e limitações** (seção 8) e perguntas. |

Plano B: se o Telegram falhar, use a aba de registro da tela; os dois canais dependem da API de IA. Se quiser apresentar economia de tempo, cronometre a triagem manual e a automática e use essas medidas reais, ou identifique claramente o valor como estimativa.

| Critério da rubrica | Evidência na apresentação |
|---|---|
| Interação da IA com o ambiente / entrada | Mensagem digitada ao vivo na tela ou enviada ao bot. |
| Processamento e uso adequado da IA | Interpretação de texto livre: categoria, prioridade, setor, resumo e justificativa. |
| Resultado final da automação / saída | Protocolo e setor no canal, chamado na fila do setor e CSV exportado. |
| Problema e benefícios | Tarefa manual comparada ao trabalho automatizado. |
| Demonstração prática ao vivo | Fluxo executado com conexão real à API. |

## 8. Limitações

- Exige internet e a API do provedor disponível, com cota ou saldo; não há retentativa nem troca automática de provedor.
- As classificações e o setor são produzidos pela IA e podem variar entre envios. A prioridade e o setor são **sugestões** de triagem, corrigíveis na área de gestão.
- A área de gestão não tem login: é destinada ao uso local, neste computador. Login, WhatsApp, envio de e-mail e hospedagem ficam fora desta versão.
- A fila não se atualiza sozinha: clique em **Atualizar fila** para ver chamados novos do bot.
- O protocolo é informado na confirmação, mas o cliente não consulta o andamento pelo bot; a consulta por protocolo é feita pela equipe na área de gestão.
- O bot só funciona enquanto o processo (`bot.py` ou o contêiner) estiver em execução. Mensagens enviadas com o bot desligado são descartadas ao iniciar. Use uma única instância por token.
- Apenas texto, até 3.000 caracteres por mensagem; o bot atende só conversas privadas e ignora grupos e mensagens editadas.
- SQLite grava um chamado por vez: tela e bot podem funcionar juntos, e uma gravação espera a outra por até 15 segundos. Mantenha o banco em disco local (não em pasta de rede).
- No Docker, o horário fica em UTC (`+00:00`).

## 9. Problemas comuns

| Sintoma | O que verificar |
|---|---|
| `python` não encontrado no Windows | Instale o Python 3.11+ pelo [python.org](https://www.python.org/downloads/) marcando **"Add python.exe to PATH"** no instalador; feche e reabra o terminal. Se houver launcher `py`, use `py -3` nos comandos iniciais. |
| Streamlit pede e-mail no terminal | Pressione `Enter` para pular; o pedido aparece só na primeira execução local. |
| Tela acessível pela rede ou "Network URL" no terminal | Execute o `streamlit run` dentro da pasta do projeto, onde está `.streamlit/config.toml`. |
| Erro ao criar `.venv` no Linux | Versão do Python e instalação do pacote `python3-venv`. |
| Módulo não encontrado | Instale `requirements.txt` usando o mesmo Python da `.venv` usado para executar. |
| Aviso "Configuração incompleta" | `.env` na pasta do aplicativo, nomes corretos e placeholders `COLE_...` substituídos; reinicie o programa. |
| "AI_PROVIDER inválido" | Use apenas `gemini` ou `openrouter`. |
| Chave "tem caracteres inválidos" | Copie a chave de novo, direto do site do provedor, para o `.env`: aspas curvas ou acentos vindos do Word/WhatsApp não são aceitos. Reinicie o programa. |
| Mensagem com HTTP 401 ou 403 | Chave recusada ou sem permissão: confira a chave do provedor selecionado. |
| Mensagem com HTTP 400 ou 404 | Identificador do modelo e chave (o Gemini também responde 400 para chave inválida). |
| Mensagem com HTTP 402 | Saldo ou créditos insuficientes (OpenRouter): confira a conta e o custo do modelo. |
| Mensagem com HTTP 429 / cota esgotada | Confira os limites do provedor e aguarde a liberação; se quiser trocar de provedor, altere o `.env` e reinicie. |
| Mensagem com HTTP 5xx, tempo esgotado ou falha de conexão | Serviço indisponível ou internet instável; tente novamente em alguns minutos. |
| "Resposta inesperada", "incompleta", "longo demais" ou fora do formato | Envie novamente; se repetir, escolha outro modelo. Nada é gravado nesses casos. |
| Setor sugerido não faz sentido | Corrija o setor nos detalhes do chamado. Para mudar o critério, ajuste as regras de setor no `PROMPT_SISTEMA` de `triagem.py`. |
| Bot responde "Ocorreu um erro inesperado" | Veja a linha "Erro inesperado na análise" no terminal do bot e envie a mensagem de novo. |
| "Falha no registro" ou "Não foi possível acessar o banco de dados" | Confira se a pasta do banco existe e permite gravação. No Linux com Docker Engine, arquivos criados pelo contêiner em `data/` pertencem ao root (com Docker Desktop, pertencem ao seu usuário). Se a mensagem se repetir com tela e bot abertos, tente novamente: uma gravação longa de outro processo pode ter excedido a espera. |
| Chamado não aparece na fila | Clique em **Atualizar fila** e confira os filtros (por padrão, chamados Resolvidos ficam ocultos). Tela e bot precisam usar o mesmo banco: local com local, ou Docker com Docker. |
| Importação: "Nenhum histórico CSV encontrado" | Confira `CSV_PATH` ou coloque o `historico.csv` antigo na pasta do aplicativo (`data/` no Docker). |
| Importação: "não tem as colunas do histórico anterior" ou "Não foi possível ler" | O arquivo precisa ser o CSV da versão anterior (UTF-8, ponto e vírgula, colunas `data_hora;mensagem;categoria;prioridade;resumo;justificativa`). Um CSV salvo de novo pelo Excel pode ter mudado a codificação ou as datas. |
| Bot não responde | Token correto, processo ativo, conversa privada com o bot certo e mensagem nova após iniciar. |
| "Bot não iniciado: não foi possível conectar ao Telegram (TimedOut)" | A rede não alcançou `api.telegram.org` a tempo. Algumas redes bloqueiam ou limitam o Telegram de forma intermitente; teste no navegador ou com `curl -4 https://api.telegram.org`, execute o bot de novo ou use outra rede (ex.: roteador do celular). |
| "o Telegram recusou o TELEGRAM_BOT_TOKEN" | Copie novamente o token do @BotFather para o `.env`. |
| Conflito de recepção no Telegram (`Conflict`) | Encerre outra instância local ou Docker usando o mesmo token. |
| Docker não conecta ao daemon / `Unit docker.service not found` | Abra o Docker Desktop (no Linux: `systemctl --user start docker-desktop`) ou, com Docker Engine, `sudo systemctl start docker`. |
| Acesso negado ao Docker no Linux | Confira as permissões exigidas pela instalação oficial; não altere permissões do socket indiscriminadamente. |
| Porta 8501 ocupada | Encerre a outra instância local/Docker antes de iniciar a tela. |
| Nova chave não foi aplicada | Reinicie o processo local; no Docker, execute `down` e depois `up` do serviço. |

## 10. Verificação realizada

### Evolução: banco, protocolo, setores, fila e acompanhamento

**Verificado com respostas simuladas** (Linux, Python 3.14.4 e Python 3.11.16, streamlit 1.64.0, requests 2.34.2, python-dotenv 1.2.3, python-telegram-bot 22.8; sem nenhuma chamada real à IA ou ao Telegram). Scripts de verificação temporários, fora do projeto, executaram **114 checagens do núcleo e do bot** e **42 checagens da tela (Streamlit AppTest)**, todas sem falhas nas duas versões do Python:

- **Setor:** o prompt pede o setor como quinta chave; setores válidos são aceitos sem diferenciar maiúsculas/minúsculas; setor ausente, vazio, não texto ou fora da lista vai para Atendimento; categoria continua separada e validada como antes.
- **Registro:** mensagem vazia ou longa não chama a API nem cria o banco; um envio gera uma chamada à IA e um chamado com protocolo `TF-AAAAMMDD-XXXXXX`, status Aberto e o setor sugerido; timeout, falha de conexão, HTTP 401/429/500 e respostas inválidas não gravam nada.
- **Persistência:** um chamado gravado é lido por outro processo Python, com o mesmo conteúdo.
- **Unicidade:** 300 protocolos distintos; índice UNIQUE no banco; um sorteio repetido gera novo sorteio; colisão permanente gera "Falha no registro" sem gravação.
- **Fila:** ordem por prioridade e, na mesma prioridade, do mais antigo para o mais novo, inclusive com horários em offsets diferentes (`-03:00` e `+00:00`); filtros por setor, prioridade, status e combinados.
- **Acompanhamento:** alterar status, setor e prioridade registra a última atualização e preserva mensagem, categoria, resumo, justificativa e data de criação; salvar sem mudança mantém a data; valores fora das listas e protocolo inexistente são recusados; Resolvido sai da fila padrão e aparece no filtro Resolvido.
- **Importação:** um `historico.csv` gerado pelo código da versão anterior (com fórmulas neutralizadas, aspas, `;`, quebra de linha e acentos) é importado; a segunda importação não cria chamados; o arquivo continua idêntico (mesmo hash e data de modificação); linhas idênticas legítimas são importadas uma vez cada; linha inválida é ignorada e contada; uma linha nova acrescentada ao CSV é importada sozinha; cabeçalho errado, arquivo inexistente e CSV não UTF-8 são recusados sem gravar.
- **Exportação:** BOM só no início, todas as colunas e linhas, neutralização de fórmulas, acentos e quebras de linha preservados.
- **Telegram:** a mesma atualização recebida duas vezes gera um único chamado e uma única chamada à IA, e a segunda resposta informa o protocolo existente; outra mensagem com o mesmo texto gera outro chamado; uma gravação concorrente com a mesma origem é barrada pela restrição UNIQUE; na tela, cada envio é um chamado novo.
- **Acesso simultâneo:** três processos gravando e lendo o mesmo banco ao mesmo tempo registraram 180 chamados sem erro.
- **Falha no banco:** pasta sem permissão gera "Falha no registro" na tela, aviso no bot antes de chamar a IA e mensagem clara na fila; o bot não inicia sem banco gravável.
- **Bot:** `/start` sem IA e sem banco; confirmação com protocolo, setor e "Solicitação registrada.", sem prometer resolução e abaixo de 4096 caracteres; falha ao responder não reprocessa; mensagem longa, erro 429, conteúdo não textual e comando desconhecido têm resposta compreensível.
- **Tela (AppTest):** abas Registrar mensagem e Fila de chamados; sucesso com protocolo e setor; atualizar a tela não repete chamada nem registro; novo clique com o mesmo texto gera novo chamado; falha não mostra o resultado anterior; texto da IA exibido literalmente; fila ordenada, filtros, abrir detalhes, alterar status/setor, aviso "Chamado atualizado.", localizar pelo protocolo, importação repetida sem duplicar e botão de exportação.
- **Servidor real:** `streamlit run` dentro da pasta do projeto respondeu `ok` em `/_stcore/health` e escutou somente em `127.0.0.1`. No navegador, a aba Fila de chamados continuou selecionada após abrir detalhes e salvar uma alteração de status.
- **Docker** (Docker Desktop 29.6.1 no Linux, cópia temporária do projeto com credenciais falsas): `docker compose config --quiet` sem erros; imagem construída; `docker compose up --build web` iniciou só a tela, com `ok` em `/_stcore/health` e porta publicada apenas em `127.0.0.1:8501`; dentro do contêiner (Python 3.11.16, IA simulada), registro com protocolo e horário em UTC, reentrega do Telegram sem duplicar e importação repetida sem duplicar, com `data/triagem.db` criado no computador e o `historico.csv` intacto; após `docker compose --profile telegram down` e nova subida, os chamados continuavam no banco; `docker compose up --build bot` iniciou só o bot, sem portas, preparou o banco em `/app/data/triagem.db` e encerrou com "o Telegram recusou o TELEGRAM_BOT_TOKEN" (token falso), sem mostrar o token no log; `docker compose --profile telegram up` iniciou os dois serviços. Na rede usada no teste, a conexão com `api.telegram.org` falhou de forma intermitente também fora do Docker (3 de 6 tentativas pelo computador), e uma das execuções do bot encerrou com a mensagem de falha de conexão.

**Não testado nesta evolução:** Windows (os comandos da seção 2 não mudaram, mas não foram executados de novo).

**Pendente de credenciais:** chamada real ao Gemini, chamada real ao OpenRouter e bot real no Telegram. Para concluir, preencha o `.env`, envie as três mensagens de exemplo por cada canal disponível, confira protocolo e setor e acompanhe os chamados na fila.

### Versão anterior (CSV)

Na versão anterior, 138 checagens simuladas mais 16 checagens de correções passaram em Windows 11 Pro com Python 3.12.14, cobrindo validação da mensagem e da resposta da IA, erros HTTP, seleção de provedor, gravação CSV, tela e bot. Os comportamentos preservados (validação, erros da IA, provedores, tela e bot) foram verificados de novo nesta evolução, como descrito acima.

## 11. Referências

- [OpenRouter: integração](https://openrouter.ai/docs/quickstart).
- [Gemini: chaves da API](https://ai.google.dev/gemini-api/docs/api-key), [preços](https://ai.google.dev/gemini-api/docs/pricing) e [compatibilidade de chat](https://ai.google.dev/gemini-api/docs/openai).
- [Telegram: criação do bot](https://core.telegram.org/bots/tutorial).
- [python-telegram-bot](https://docs.python-telegram-bot.org/).
- [Python: sqlite3](https://docs.python.org/3/library/sqlite3.html) e [ambientes virtuais](https://docs.python.org/3/library/venv.html).
- [Streamlit em Docker](https://docs.streamlit.io/deploy/tutorials/docker).
- [Docker Compose: serviços e perfis](https://docs.docker.com/compose/how-tos/profiles/).
