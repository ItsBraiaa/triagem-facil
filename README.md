# Triagem Fácil — como configurar e executar

O projeto classifica mensagens de clientes com Python e **Gemini ou OpenRouter**, registra os resultados em CSV e oferece uma tela web ou um bot do Telegram. Escolha **Windows, Linux ou Docker** e execute **um canal por vez**. Configure somente um provedor de IA por execução.

**Fluxo:** mensagem digitada na tela ou enviada ao bot → chamada à IA → validação da resposta → linha gravada no CSV → resultado mostrado no mesmo canal. A IA interpreta o texto; o Python cuida da validação, da data/hora e do arquivo.

| Arquivo | Função |
|---|---|
| `triagem.py` | Núcleo compartilhado: prompt, chamada à IA, validação da resposta e gravação do CSV (`analisar_e_registrar`). |
| `app.py` | Tela Streamlit: formulário, carregamento, resultado e mensagens de erro. |
| `bot.py` | Bot do Telegram (long polling), usando a mesma função de `triagem.py`. |
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

Em cada opção de instalação abaixo, copie `.env.example` para `.env` **somente na primeira configuração**, evitando sobrescrever suas credenciais. Preencha o arquivo com um editor de texto:

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

Opcional: `CSV_PATH=caminho/do/arquivo.csv` grava o histórico em outro local (a pasta é criada se não existir). Sem essa variável, o arquivo fica na pasta do aplicativo.

## 2. Windows — PowerShell

Pré-requisitos: Python 3.11 ou superior instalado pelo [site oficial](https://www.python.org/downloads/), com comando `python` disponível, e internet. Abra o PowerShell na pasta que contém `app.py`, `bot.py` e `requirements.txt`.

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Salve o `.env` preenchido. Não é necessário ativar o ambiente virtual nem alterar a política de execução do PowerShell. Se `python` não for encontrado, veja a seção 8.

**Tela web:**

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Na primeira execução, o Streamlit pode pedir um e-mail no terminal: pressione `Enter` para pular. Abra [http://localhost:8501](http://localhost:8501). Se faltar configuração, a tela abre com um aviso indicando o que preencher no `.env`. Para encerrar, pressione `Ctrl+C` no terminal.

**Bot do Telegram:** depois de encerrar a tela, execute:

```powershell
.\.venv\Scripts\python.exe bot.py
```

Abra seu bot no Telegram, envie `/start` e depois uma mensagem de cliente. Mantenha o terminal aberto enquanto estiver usando o bot. Encerre com `Ctrl+C`. Sem token ou sem configuração da IA, o bot não inicia e mostra no terminal o que falta.

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

**Tela web:**

```bash
.venv/bin/python -m streamlit run app.py
```

Se o Streamlit pedir um e-mail no terminal, pressione `Enter` para pular. Abra [http://localhost:8501](http://localhost:8501). Encerre com `Ctrl+C` antes de iniciar o bot.

**Bot do Telegram:**

```bash
.venv/bin/python bot.py
```

Abra seu bot, envie `/start` e uma mensagem de cliente. Encerre com `Ctrl+C`. Nas próximas execuções, use apenas o comando do canal escolhido.

## 4. Docker — Windows ou Linux

Nesta opção, não é necessário instalar Python no computador. É necessário ter Docker e Compose funcionando, além de internet. No Windows, use [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/) em modo de contêineres Linux; no Linux, siga a instalação do [Docker Engine](https://docs.docker.com/engine/install/) e do [plugin Compose](https://docs.docker.com/compose/install/linux/). A imagem usa `python:3.11-slim` e as versões fixadas em `requirements.txt`; o `.env` não entra na imagem, as credenciais são lidas só na execução.

Abra o terminal na pasta com `compose.yaml` e `Dockerfile`. Verifique:

```text
docker version
docker compose version
```

Crie o `.env` conforme a seção 1 (o Compose exige que ele exista). No PowerShell, use `Copy-Item .env.example .env`; no Linux, use `cp .env.example .env`. Se já estiver configurado, preserve o arquivo.

Crie a pasta que armazenará os dados:

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

Abra [http://localhost:8501](http://localhost:8501). A porta é publicada só em `127.0.0.1`, isto é, apenas este computador acessa a tela. A primeira construção baixa a imagem e as dependências, podendo demorar mais.

**Trocar da tela para o bot:** pressione `Ctrl+C`, encerre os serviços e inicie somente o bot:

```text
docker compose --profile telegram down
docker compose up --build bot
```

Abra seu bot no Telegram e envie `/start`. O bot não precisa de porta publicada, webhook ou URL pública. O serviço `bot` pertence ao profile `telegram` e só sobe quando chamado pelo nome. Os serviços não dependem um do outro: para trocar novamente de canal, pare o anterior antes de iniciar o próximo.

**Executar em segundo plano, depois de confirmar que está funcionando:**

```text
docker compose up -d bot
docker compose logs -f bot
```

`Ctrl+C` encerra o acompanhamento dos logs, mas o bot em segundo plano continua ativo. Para encerrar de fato:

```text
docker compose --profile telegram down
```

Esse comando encerra a tela e o bot sem apagar a pasta `data`. Para a tela em segundo plano, substitua `bot` por `web` nos comandos de início e logs, com o canal anterior parado. O Docker e o computador precisam continuar ligados.

## 5. Onde fica o histórico

| Execução | Local no computador |
|---|---|
| Windows ou Linux com Python | `historico.csv` na pasta do aplicativo (ao lado de `triagem.py`), ou o caminho de `CSV_PATH` |
| Docker | `data/historico.csv` na pasta do projeto (`CSV_PATH=/app/data/historico.csv`, definido no `compose.yaml`) |

O arquivo é criado após a primeira análise válida, com as colunas `data_hora;mensagem;categoria;prioridade;resumo;justificativa`. Ele usa ponto e vírgula e UTF-8 com BOM, para o Excel abrir com acentos. Abra-o no Excel, LibreOffice ou editor de texto. Textos que começam com `=`, `+`, `-` ou `@` recebem um apóstrofo no início para a planilha não tratá-los como fórmula. Respostas inválidas da IA não são gravadas. Se a planilha bloquear a gravação, a tela ou o bot mostra "Falha no registro": feche o arquivo e envie novamente.

No Docker, `./data` fica vinculada à pasta `/app/data` do contêiner. Parar ou recriar o contêiner preserva o histórico no computador. As execuções local e Docker usam arquivos separados por padrão. Horários são registrados em ISO 8601 com offset; no Docker, o contêiner registra em UTC (`+00:00`), e na execução local usa o fuso do computador (ex.: `-03:00`).

## 6. Demonstração

### Exemplos

Use estas mensagens fictícias. Os resultados são **expectativas** para orientar o ensaio, não valores fixos no programa: a IA decide e pode variar.

| Mensagem | Categoria esperada | Prioridade esperada |
|---|---|---|
| “Vocês aceitam pagamento por cartão?” | Dúvida | Baixa |
| “Meu produto chegou quebrado e quero fazer a troca.” | Reclamação | Média |
| “Meu pedido está atrasado e preciso receber ainda hoje para um evento.” | Reclamação | Alta |

### Teste antes da apresentação

1. Inicie apenas o canal escolhido.
2. Se usar Telegram, envie `/start` primeiro.
3. Envie as três mensagens acima, uma por vez. Confira categoria, prioridade, resumo e justificativa.
4. Abra o CSV e confira que os três envios geraram três novos registros.
5. Encerre o programa e confirme que o arquivo permanece salvo.

O bot é um classificador: cada mensagem é independente. Mensagens enviadas enquanto o bot estava desligado são descartadas na inicialização; envie uma mensagem nova após iniciar o processo.

### Roteiro de 10 a 15 minutos

| Tempo | O que fazer |
|---|---|
| 0–2 min | **Problema:** a loja lê, classifica e anota cada mensagem manualmente. Mostre como seria a triagem manual de uma mensagem. |
| 2–4 min | **Solução:** entrada (tela ou Telegram) → processamento (`triagem.py` chama a IA e valida o JSON) → saída (resultado no canal e linha no CSV). Explique que a IA interpreta o texto e o Python controla validação, data/hora e gravação. |
| 4–10 min | **Ao vivo:** envie as três mensagens pelo Telegram (celular ou Telegram Desktop) ou pela tela. Mostre categoria, prioridade, resumo e justificativa e comente se bateram com a expectativa. |
| 10–12 min | **Saída:** abra o CSV e mostre as linhas criadas automaticamente, com data/hora. |
| 12–15 min | **Benefícios e limitações** (seção 7) e perguntas. |

Plano B: se o Telegram falhar, use a tela Streamlit; os dois canais dependem da API de IA. Se quiser apresentar economia de tempo, cronometre a triagem manual e a automática e use essas medidas reais, ou identifique claramente o valor como estimativa.

| Critério da rubrica | Evidência na apresentação |
|---|---|
| Interação da IA com o ambiente / entrada | Mensagem digitada ao vivo na tela ou enviada ao bot. |
| Processamento e uso adequado da IA | Interpretação de texto livre: categoria, prioridade, resumo e justificativa. |
| Resultado final da automação / saída | Resultado no canal e linha criada automaticamente no CSV. |
| Problema e benefícios | Tarefa manual comparada ao trabalho automatizado. |
| Demonstração prática ao vivo | Fluxo executado com conexão real à API. |

## 7. Limitações

- Exige internet e a API do provedor disponível, com cota ou saldo; não há retentativa nem troca automática de provedor.
- As classificações são produzidas pela IA e podem variar entre envios. A prioridade é uma **sugestão** de triagem, não uma decisão de atendimento.
- Um canal por vez: tela e bot gravam no mesmo CSV, sem controle de gravação simultânea.
- O bot só funciona enquanto o processo (`bot.py` ou o contêiner) estiver em execução. Mensagens enviadas com o bot desligado são descartadas ao iniciar. Use uma única instância por token.
- Apenas texto, até 3.000 caracteres por mensagem; o bot atende só conversas privadas e ignora grupos e mensagens editadas.
- No Docker, o horário do CSV fica em UTC (`+00:00`).
- Sem login, banco de dados ou histórico de conversa: cada mensagem é analisada isoladamente.

## 8. Problemas comuns

| Sintoma | O que verificar |
|---|---|
| `python` não encontrado no Windows | Instale o Python 3.11+ pelo [python.org](https://www.python.org/downloads/) marcando **"Add python.exe to PATH"** no instalador; feche e reabra o terminal. Se houver launcher `py`, use `py -3` nos comandos iniciais. |
| Streamlit pede e-mail no terminal | Pressione `Enter` para pular; o pedido aparece só na primeira execução local. |
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
| Bot responde "Ocorreu um erro inesperado" | Veja a linha "Erro inesperado na análise" no terminal do bot e envie a mensagem de novo. |
| "Falha no registro" / CSV não grava | Feche o arquivo no Excel e confira permissões da pasta. No Linux, arquivos criados pelo Docker em `data/` pertencem ao root. |
| Bot não responde | Token correto, processo ativo, conversa privada com o bot certo e mensagem nova após iniciar. |
| "o Telegram recusou o TELEGRAM_BOT_TOKEN" | Copie novamente o token do @BotFather para o `.env`. |
| Conflito de recepção no Telegram (`Conflict`) | Encerre outra instância local ou Docker usando o mesmo token. |
| Docker não conecta ao daemon | Abra o Docker Desktop ou inicie o serviço Docker conforme a instalação. |
| Acesso negado ao Docker no Linux | Confira as permissões exigidas pela instalação oficial; não altere permissões do socket indiscriminadamente. |
| Porta 8501 ocupada | Encerre a outra instância local/Docker antes de iniciar a tela. |
| Nova chave não foi aplicada | Reinicie o processo local; no Docker, execute `down` e depois `up` do serviço. |

## 9. Verificação realizada

**Verificado com respostas simuladas** (Windows 11 Pro, Python 3.12.14 em venv, streamlit 1.64.0, requests 2.34.2, python-dotenv 1.2.3, python-telegram-bot 22.8; sem nenhuma chamada real à IA ou ao Telegram). Um script de verificação temporário, fora do projeto, executou 138 checagens sem falhas; depois da revisão do código, ele foi executado de novo (138 sem falhas) junto com 16 checagens das correções, também sem falhas:

- Mensagem vazia ou acima de 3.000 caracteres: recusada sem chamar a API e sem criar arquivo.
- JSON válido aceito, inclusive dentro de um único bloco de código; categoria/prioridade fora das opções, campo ausente, valor não texto, texto vazio e resposta não JSON: recusados sem gravação.
- Tempo esgotado, falha de conexão, HTTP 400/401/402/403/429/500/503 e corpo inesperado: erro claro, exatamente uma chamada ao provedor selecionado (sem fallback), nada gravado e nenhuma chave na mensagem.
- Gemini e OpenRouter: endpoint, `Authorization: Bearer`, modelo e timeout de 30 s corretos; a falta da chave do provedor não selecionado não impede o uso; `AI_PROVIDER` inválido, chave/modelo ausente ou placeholder geram instrução de configuração.
- CSV: dois envios geram um cabeçalho e duas linhas, BOM só no início, acentos, aspas, `;` e quebras de linha preservados, neutralização de `=`, `+`, `-` e `@`, data/hora ISO 8601 com offset e criação da pasta de `CSV_PATH`. Falha de gravação mostra "Falha no registro" e nenhuma confirmação.
- Tela (Streamlit AppTest): atualizar a tela não repete chamada nem registro; um novo clique com o mesmo texto conta como nova análise; uma falha não mostra o resultado anterior; valores da IA aparecem como texto literal. A tela iniciou com `streamlit run` e respondeu `ok` em `/_stcore/health`.
- Bot: `/start` sem IA nem CSV; texto válido gera uma análise, uma linha e a resposta; conteúdo não textual, mensagem longa, comando desconhecido e erro de API têm resposta compreensível; se o envio da resposta falhar após gravar, nada é reprocessado; grupos e edições são ignorados; sem token, o bot sai com mensagem clara; `run_polling` com Telegram simulado descarta pendentes (`drop_pending_updates`) e o token não aparece no terminal.
- Tela e bot usam as mesmas funções de `triagem.py`; varredura sem chaves ou tokens nos arquivos do projeto.
- Correções da revisão: categoria e prioridade em maiúsculas/minúsculas diferentes (ex.: "reclamação", "ALTA") viram o valor oficial, e valores fora das opções continuam recusados; chave com aspas curvas gera instrução de configuração na tela e no bot, sem traceback e sem chamar a API; resumo ou justificativa acima de 500 caracteres é recusado sem gravação, mantendo a resposta do bot abaixo do limite de 4096 caracteres do Telegram; no bot, um erro inesperado recebe resposta na conversa em vez de silêncio.

**Não testado neste ambiente:** Linux (comandos da seção 3) e Docker (`docker compose config`, construção da imagem, tela no contêiner e persistência do bind mount), pois o Docker não estava instalado. Os arquivos Docker foram apenas revisados. A execução em Python 3.11 não foi feita: foram conferidas a sintaxe do código e a versão mínima exigida pelas dependências fixadas (3.10).

**Pendente de credenciais:** chamada real ao Gemini, chamada real ao OpenRouter e bot real no Telegram. Para concluir, preencha o `.env`, envie as três mensagens de exemplo por cada canal disponível e confira as linhas no CSV.

## 10. Referências

- [OpenRouter: integração](https://openrouter.ai/docs/quickstart).
- [Gemini: chaves da API](https://ai.google.dev/gemini-api/docs/api-key), [preços](https://ai.google.dev/gemini-api/docs/pricing) e [compatibilidade de chat](https://ai.google.dev/gemini-api/docs/openai).
- [Telegram: criação do bot](https://core.telegram.org/bots/tutorial).
- [python-telegram-bot](https://docs.python-telegram-bot.org/).
- [Python: ambientes virtuais](https://docs.python.org/3/library/venv.html).
- [Streamlit em Docker](https://docs.streamlit.io/deploy/tutorials/docker).
- [Docker Compose: serviços e perfis](https://docs.docker.com/compose/how-tos/profiles/).
