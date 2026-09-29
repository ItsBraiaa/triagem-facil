# Triagem Fácil — especificação e plano de implementação

## Instrução para o Claude

Implemente o projeto descrito neste documento. O escopo já foi escolhido pelo usuário: uma aplicação local simples para um trabalho acadêmico, com entrega em **29/09/2026 às 19h, horário de Brasília**. Priorize concluir o fluxo completo e demonstrável. Este arquivo contém a especificação e o plano; não é necessário produzir novos documentos de planejamento antes de programar.

> **Estado atual (evolução entregue):** o sistema final ampliou este escopo com banco SQLite, protocolo, setores responsáveis, fila de chamados e acompanhamento. As seções abaixo foram atualizadas para refletir o sistema final, e a seção 14 descreve a evolução. Nos pontos de conflito, vale a seção 14.

Trabalhe na pasta `triagem-facil/`, criada ao lado deste documento, preservando arquivos existentes. Tome decisões rotineiras dentro deste escopo. Ao terminar, informe os arquivos entregues, os comandos para executar, as verificações realizadas e qualquer dependência ainda pendente. A implementação deve ser compreensível para alunos explicarem durante a apresentação.

## 1. Objetivo e problema

Uma pequena loja recebe mensagens de clientes. A leitura, classificação e anotação manual de cada mensagem consomem tempo. O sistema recebe uma mensagem, usa IA para interpretar seu conteúdo e registra a classificação automaticamente.

**Fluxo compartilhado:** receber mensagem pela tela ou pelo bot do Telegram → chamar a IA → validar resposta → gravar o chamado no SQLite com protocolo, status Aberto e setor sugerido → informar protocolo e setor no mesmo canal de entrada → acompanhar o chamado na fila do setor.

A IA interpreta linguagem natural. O Python controla interface, validação, protocolo, data/hora e persistência. A prioridade e o setor são sugestões de triagem, corrigíveis na área de gestão, não decisões definitivas de atendimento.

## 2. Escopo da entrega

- Uma tela local em português, com Streamlit.
- Um bot do Telegram para receber texto em conversa privada e responder com a classificação, reutilizando a lógica da tela.
- Um campo de texto e um botão “Analisar e registrar”.
- Classificação via Gemini ou OpenRouter, selecionado por configuração; usar um provedor por execução.
- Resultado com categoria, prioridade, resumo, justificativa e setor responsável.
- Registro automático de cada análise válida como chamado em banco SQLite, com protocolo (seção 14). O `historico.csv` da versão anterior deixa de ser gravado e pode ser importado.
- Área de gestão local na tela: fila por setor, filtros, detalhes e acompanhamento de status (seção 14).
- Mensagens compreensíveis de carregamento, sucesso e falha.
- README com configuração, execução e roteiro de demonstração.
- Execução documentada em Windows, Linux e Docker Compose, com arquivos Docker entregues junto do código.

Ficam fora da entrega: login, chatbot com histórico de conversa, processamento em lote, envio de e-mail, WhatsApp, n8n, hospedagem, dashboards e frameworks de agentes. Banco de dados, protocolo, setores, fila e acompanhamento foram incluídos pela evolução (seção 14). O aplicativo trata uma mensagem por envio. Tela e bot podem funcionar ao mesmo tempo: o SQLite serializa as gravações.

## 3. Regras de classificação

### Categoria: exatamente uma destas opções

| Valor | Regra |
|---|---|
| Dúvida | Pedido de informação ou esclarecimento. |
| Reclamação | Relato de insatisfação, defeito, atraso ou problema com compra/serviço. |
| Solicitação | Pedido de ação sem reclamação predominante, como atualizar um endereço. |
| Outros | Conteúdo insuficiente, ambíguo ou fora das categorias anteriores. |

Quando houver problema acompanhado de pedido de solução, priorizar `Reclamação`. Exemplo: produto quebrado com pedido de troca.

### Prioridade: exatamente uma destas opções

| Valor | Regra |
|---|---|
| Alta | A mensagem relata urgência explícita ou impacto imediato grave. |
| Média | Existe problema que exige resolução, sem urgência explícita. |
| Baixa | Consulta informativa, pedido rotineiro ou mensagem sem evidência de urgência/problema. |

Usar somente o conteúdo informado. Não inventar prazo de entrega, política comercial, número do pedido ou fatos sobre o cliente. Resumo e justificativa devem ter uma frase curta cada. A justificativa explica a prioridade sugerida.

### Setor responsável: exatamente uma destas opções

| Valor | Regra (definida na implementação; ajustável no prompt) |
|---|---|
| Atendimento | Informações gerais sobre a loja, produtos ou serviços. Também recebe mensagens sem informação suficiente. |
| Financeiro | Pagamentos, formas de pagamento, cobranças, reembolsos, estornos e notas fiscais. |
| Logística | Entregas, atrasos, frete, rastreamento, endereço de entrega, trocas e devoluções. |
| Suporte Técnico | Defeito ou mau funcionamento, instalação, configuração ou uso de produto, e problemas técnicos no site ou aplicativo. |

Categoria e setor são campos separados. Setor ausente ou fora da lista é gravado como `Atendimento`.

## 4. Interface e comportamento

A tela tem duas abas: **Registrar mensagem** (itens abaixo) e **Fila de chamados** (área de gestão, seção 14).

1. Mostrar título “Triagem Fácil” e uma frase explicando a função.
2. Mostrar campo “Mensagem do cliente”, com limite de 3.000 caracteres.
3. Usar formulário do Streamlit para processar apenas quando o botão for acionado.
4. Recusar mensagem vazia ou composta apenas por espaços antes de chamar a API.
5. Durante o processamento, mostrar “Analisando mensagem...”.
6. Depois de validar e salvar, informar que a solicitação foi registrada, com protocolo e setor responsável, e mostrar protocolo, setor, categoria, prioridade, resumo e justificativa.
7. Manter o último resultado em `st.session_state`; uma atualização normal da interface não pode causar nova chamada ou novo registro.
8. Um novo envio explícito, mesmo com texto repetido, conta como uma nova análise.

Exibir os campos como texto, sem executar ou renderizar HTML retornado pelo modelo. Se um envio falhar, não apresentar o resultado anterior como se fosse o resultado desse envio.

## 5. Tecnologias e configuração

- Python 3.11 ou superior.
- Dependências: `streamlit`, `requests`, `python-dotenv` e `python-telegram-bot`.
- Bibliotecas padrão para JSON, CSV, caminhos e data/hora.
- Requisições HTTP com `requests`, aproveitando o formato de chat compatível dos dois provedores, sem adicionar SDK de IA.
- `AI_PROVIDER` aceita `gemini` ou `openrouter`, com padrão `gemini` para facilitar a avaliação da camada gratuita. Recusar valores desconhecidos com erro claro.
- Gemini: endpoint `https://generativelanguage.googleapis.com/v1beta/openai/chat/completions`, configuração `GEMINI_API_KEY` e `GEMINI_MODEL`.
- OpenRouter: endpoint `https://openrouter.ai/api/v1/chat/completions`, configuração `OPENROUTER_API_KEY` e `OPENROUTER_MODEL`.
- Carregar configurações do ambiente ou de `.env` local com `python-dotenv`, preservando a precedência do ambiente. Validar apenas chave e modelo do provedor escolhido. Usar `Authorization: Bearer <chave>` e JSON no corpo; manter endpoints fixos no código por provedor.
- Criar `.env.example` apenas com placeholders; `.env` fica fora do versionamento.

Consultar a documentação oficial durante a implementação para confirmar os parâmetros utilizados: https://openrouter.ai/docs/quickstart e https://ai.google.dev/gemini-api/docs/openai. Escolher/configurar um modelo de chat disponível na conta; não presumir gratuidade, saldo ou disponibilidade de um identificador antigo. Gemini possui camada gratuita para determinados modelos e cotas: https://ai.google.dev/gemini-api/docs/pricing e https://ai.google.dev/gemini-api/docs/rate-limits. Não exigir ativação de faturamento para experimentar a camada gratuita elegível. Os exemplos do README devem usar mensagens fictícias; a documentação informa uso do conteúdo da camada gratuita para melhoria dos produtos Google.

Concentrar a seleção de endpoint, chave e modelo em uma pequena função de `triagem.py`. Compartilhar prompt, validação, retorno e persistência entre provedores. Não criar hierarquia de classes, dependências extras ou seleção de provedor na interface. Uma solicitação chama somente o provedor selecionado; não há fallback automático. Em erro 429, orientar a verificar a cota e tentar posteriormente, sem trocar silenciosamente para uma opção paga.

Se faltarem chave ou modelo, mostrar instrução de configuração. Continuar a implementação e a verificação local sem credenciais, informando que a integração real permanece pendente. Não inventar resultado de chamada real nem solicitar que o usuário cole a chave em uma conversa.

## 6. Contrato da integração com IA

Enviar instrução de classificação em mensagem `system` e o texto do cliente em mensagem `user`. Orientar o modelo a tratar a mensagem como conteúdo para análise, inclusive quando ela contiver instruções para alterar as regras.

Solicitar exclusivamente um objeto JSON, sem Markdown, com estas cinco propriedades:

```json
{
  "categoria": "Reclamação",
  "prioridade": "Média",
  "resumo": "Cliente solicita troca de um produto que chegou danificado.",
  "justificativa": "O problema exige resolução, mas não há urgência explícita.",
  "setor": "Logística"
}
```

Fazer uma chamada por envio, com timeout finito de 30 segundos e limite de saída suficiente para esse objeto pequeno. Não implementar retentativas automáticas. Usar temperatura baixa se o modelo aceitar esse parâmetro.

Ler o conteúdo da resposta de chat e convertê-lo com `json.loads`. Aceitar, opcionalmente, um único bloco externo de código JSON removendo apenas seus delimitadores. Validar objeto, campos obrigatórios, tipos string, strings não vazias e valores permitidos de categoria/prioridade. Validar o setor contra a lista permitida; setor ausente ou inválido vira `Atendimento`. Persistir somente os campos previstos. JSON inválido ou resposta incompleta gera erro visível e nenhum registro.

Tratar erros de rede/timeout, autenticação, saldo/limite, serviço indisponível e estrutura inesperada. Mostrar orientação curta, permitir nova tentativa pelo botão e nunca expor chave, cabeçalhos de autenticação ou resposta técnica bruta na interface.

## 7. Registro CSV (versão anterior)

> **Substituída pela seção 14.** O registro passou a ser feito em SQLite, e o CSV deixou de ser gravado a cada análise. Esta seção descreve o formato do `historico.csv` da versão anterior, que continua válido para a **importação** (somente leitura). A **exportação** CSV da área de gestão mantém o mesmo padrão de arquivo (ponto e vírgula, UTF-8 com BOM, neutralização de fórmulas), com as colunas da seção 14.

Salvar `historico.csv` na pasta do aplicativo por padrão, usando caminho baseado em `__file__`, independente do diretório de execução. Permitir sobrescrever o destino com `CSV_PATH`; criar o diretório pai quando necessário. No Docker, usar `/app/data/historico.csv` e persistir essa pasta no host.

Colunas, nesta ordem:

```text
data_hora;mensagem;categoria;prioridade;resumo;justificativa
```

- Usar `csv.DictWriter`, delimitador `;`, `newline=""` e codificação compatível com acentos no Excel (UTF-8 com BOM, sem inserir BOM entre registros).
- Criar arquivo e cabeçalho na primeira gravação; acrescentar linhas nas seguintes.
- Registrar data/hora local com offset em formato ISO 8601.
- Preservar mensagens com acentos, aspas, ponto e vírgula e quebras de linha via escape do módulo CSV.
- Neutralizar células textuais iniciadas por `=`, `+`, `-` ou `@` com apóstrofo para abertura como texto em planilha.
- Salvar apenas depois da validação da resposta da IA.
- Se a gravação falhar, mostrar falha de registro, sem afirmar que o chamado foi salvo. Orientar a fechar o CSV no Excel se estiver bloqueado.

## 8. Arquivos a entregar

```text
triagem-facil/
├── app.py                 # Tela: abas Registrar mensagem e Fila de chamados.
├── bot.py
├── triagem.py             # Classificação e validação da resposta da IA.
├── chamados.py            # SQLite: registro compartilhado, protocolo, fila, acompanhamento, exportação e importação CSV.
├── .streamlit/config.toml # Tela local aceita conexões somente de localhost.
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── Dockerfile
├── compose.yaml
├── .dockerignore
├── triagem.db             # Gerado em execução; não entregar dados de teste como dados reais.
└── historico.csv          # Somente da versão anterior; lido pela importação e nunca alterado.
```

Manter funções pequenas em `triagem.py` para classificar pela API e validar o resultado, e em `chamados.py` para gravar e consultar os chamados. `app.py` constrói a tela e `bot.py` recebe e responde mensagens. Os dois canais devem chamar as mesmas funções, sem duplicar prompt, validação ou persistência. Usar proteção `if __name__ == "__main__"` nos pontos de entrada. Evitar arquitetura adicional para esse tamanho de aplicação.

No `.gitignore`, incluir `.env`, `.venv/`, `__pycache__/`, `historico.csv`, `*.db`, `*.db-journal` e `data/`. O README deve explicar dependências, chave/modelo, execução, localização do CSV e limitações: requer internet/API disponível e classificações podem variar. Usar como base o `README.md` entregue ao lado desta especificação, copiando e ajustando seu conteúdo para `triagem-facil/README.md` após implementar e conferir os comandos.

## 9. Sequência de implementação

1. Criar arquivos, dependências e configuração de ambiente. Conclusão: aplicação inicia e avisa claramente quando falta configuração.
2. Implementar seleção Gemini/OpenRouter, chamada HTTP e validação do contrato. Conclusão: cada configuração seleciona o endpoint e as credenciais corretas; uma resposta válida vira dados estruturados e falhas são reconhecidas.
3. Implementar gravação CSV. Conclusão: dois registros de teste geram um único cabeçalho e duas linhas de dados, preservando caracteres especiais.
4. Integrar formulário, carregamento, resultado e mensagens de erro. Conclusão: um envio explícito provoca uma classificação e um registro.
5. Executar as verificações da seção seguinte e corrigir falhas. Conclusão: evidências documentadas, distinguindo testes simulados de integração real.
6. Finalizar README com roteiro de demonstração. Conclusão: outra pessoa consegue configurar e executar usando somente as instruções.

Comandos esperados no PowerShell, dentro da pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Preencher .env localmente com chave e modelo válidos.
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## 10. Verificação e critérios de aceite

Executar verificações focadas; não criar infraestrutura extensa de testes. Usar arquivos temporários para verificar CSV e respostas simuladas para exercitar falhas sem consumir API.

- [ ] Mensagem vazia não chama a API e não grava arquivo.
- [ ] JSON válido é aceito; categoria/prioridade fora das opções e campos ausentes são rejeitados.
- [ ] Timeout e falha de autenticação são tratados sem sucesso falso ou gravação.
- [ ] Dois envios válidos geram dois registros e um cabeçalho.
- [ ] Acentos, aspas e separadores sobrevivem à gravação e leitura do CSV.
- [ ] Uma atualização da tela sem novo envio não duplica registros nem chamadas.
- [ ] Falha de gravação não exibe confirmação de registro.
- [ ] Segredos não aparecem no código, logs compartilhados ou arquivos entregues.
- [ ] A aplicação inicia e o fluxo é verificado pela interface.
- [ ] Com credenciais disponíveis, pelo menos uma classificação real completa o fluxo até o CSV.
- [ ] Os dois provedores têm seleção e contrato verificados com respostas simuladas; a ausência da chave do provedor não selecionado não impede o uso.
- [ ] Valores inválidos de `AI_PROVIDER` são rejeitados, e erro 429 não provoca fallback nem gravação.
- [ ] Executar chamada real para cada provedor que tiver credenciais disponíveis; informar separadamente os provedores cuja integração real ficou pendente.

Se não houver credenciais, concluir todos os itens independentes e declarar explicitamente a integração real como não verificada. Nunca usar classificações fixas para fingir a demonstração de IA.

## 11. Demonstração e avaliação

Preparar estes exemplos no README. Resultados abaixo são expectativas para orientar o ensaio, não valores fixos a serem programados:

| Mensagem | Categoria esperada | Prioridade esperada |
|---|---|---|
| “Vocês aceitam pagamento por cartão?” | Dúvida | Baixa |
| “Meu produto chegou quebrado e quero fazer a troca.” | Reclamação | Média |
| “Meu pedido está atrasado e preciso receber ainda hoje para um evento.” | Reclamação | Alta |

Roteiro de 10 a 15 minutos: explicar o problema e o processo manual; apresentar entrada, processamento e saída; executar três mensagens; abrir o CSV; explicar benefícios e limitações. Cronometrar a triagem manual e automática se quiser apresentar economia de tempo; usar medidas reais ou identificar claramente estimativas.

| Critério visível na rubrica | Evidência na apresentação |
|---|---|
| Interação da IA com o ambiente / entrada — 0,6 | Mensagem digitada ao vivo no formulário. |
| Processamento e uso adequado da IA — 0,6 | Interpretação de texto livre, categoria, prioridade e justificativa. |
| Resultado final da automação / saída — 0,6 | Resultado na tela e linha criada automaticamente no CSV. |
| Problema e benefícios — 0,6 | Explicação da tarefa manual e do trabalho automatizado. |
| Demonstração prática ao vivo — 0,6 | Fluxo executado com conexão real à API. |

A rubrica fornecida mostra somente os títulos dos critérios; seus descritores internos estavam recolhidos. A proposta atende aos requisitos visíveis, sem promessa de nota. O PDF orienta usar entrada, processamento, saída e IA justificada, permite Python sem n8n e prevê apresentação de 10 a 15 minutos.

## 12. Bot do Telegram — extensão solicitada pelo usuário

O bot é um segundo canal do mesmo classificador. Manter o escopo restrito a texto em conversa privada, sem memória de conversa ou ferramentas extras. Cada mensagem é analisada independentemente.

### Configuração e execução

- O usuário cria o bot pelo `@BotFather` oficial, usando `/newbot`, e guarda o token localmente em `.env`, na variável `TELEGRAM_BOT_TOKEN`.
- Acrescentar essa variável ao `.env.example`. O token é uma credencial secreta; não incluí-lo no código, URLs exibidas, logs compartilhados ou capturas de tela.
- Implementar com `python-telegram-bot` e long polling (`run_polling`). Confirmar a API da versão instalada na documentação oficial da biblioteca: https://docs.python-telegram-bot.org/.
- A recepção por polling dispensa webhook, domínio público e hospedagem. O computador precisa estar ligado, conectado e executando `bot.py` durante a demonstração.
- Documentação oficial do Telegram: https://core.telegram.org/bots/tutorial e https://core.telegram.org/bots/api#getupdates.
- Executar o bot com `.\.venv\Scripts\python.exe bot.py` após configurar o mesmo ambiente do aplicativo.
- A ausência do token do Telegram deve impedir somente a execução do bot; a tela continua utilizável com as configurações do provedor de IA selecionado.

### Comportamento

1. `/start` envia uma explicação curta: “Envie uma mensagem de cliente para registrar uma solicitação. Cada mensagem de texto válida vira um chamado: você recebe o protocolo, o setor responsável, a categoria, a prioridade, o resumo e a justificativa.” Esse comando não chama a IA nem grava chamado.
2. Processar apenas novas mensagens de texto em conversa privada, com o limite de 3.000 caracteres e as mesmas validações da tela. Ignorar edições de mensagens e mensagens de grupos.
3. Para áudio, foto, documento ou outro conteúdo não textual em conversa privada, pedir o envio de texto, sem chamar a IA. Comandos desconhecidos recebem orientação para usar `/start`.
4. Para texto válido, avisar “Analisando mensagem...”, classificar, validar, salvar e responder no mesmo chat com “Solicitação registrada.”, protocolo, setor responsável, os quatro campos da análise e a informação de que a solicitação está na fila do setor, sem prometer que o problema foi resolvido.
5. Enviar respostas como texto simples, sem `parse_mode`, evitando erros com caracteres gerados pela IA.
6. Tratar falha de API ou gravação com mensagem curta e orientação para enviar novamente; não registrar resposta inválida.
7. Se o chamado foi salvo, mas o envio da resposta ao Telegram falhar, não executar novamente a classificação ou gravação. Registrar apenas um diagnóstico sem segredos no terminal.
8. Se a mesma atualização do Telegram (mesmo chat e mesma mensagem) for recebida novamente, não chamar a IA nem gravar outro chamado: responder com o protocolo já registrado.

Para manter a implementação simples, processar atualizações sequencialmente. Como a integração compartilhada usa `requests`, executá-la fora do loop assíncrono com `asyncio.to_thread`. Configurar a inicialização para descartar atualizações antigas pendentes, documentando que mensagens enviadas enquanto o programa estava desligado não serão processadas nessa versão de demonstração. Executar uma única instância do bot por token.

### Inclusão no plano e nos critérios de aceite

Após concluir o núcleo compartilhado e a interface, implementar o bot e atualizar o README com criação pelo BotFather, configuração e comando de execução. A validação real depende de token do Telegram e acesso ao provedor de IA selecionado; avançar nas demais etapas se as credenciais ainda estiverem ausentes.

- [ ] `/start` explica o uso sem consumir IA ou criar registro.
- [ ] Texto enviado ao bot produz classificação real, uma linha no CSV e resposta na própria conversa.
- [ ] Conteúdo não textual, mensagens longas e erros de API têm resposta compreensível.
- [ ] O bot usa exatamente as regras e funções de classificação da tela.
- [ ] Reiniciar o bot não reprocessa mensagens antigas pendentes na demonstração.
- [ ] O README informa que o bot funciona enquanto o processo local estiver em execução.

Na apresentação, enviar as três mensagens de exemplo pelo celular ou Telegram Desktop, mostrar as respostas e abrir o CSV gerado no computador. Usar a tela Streamlit como alternativa caso o Telegram falhe; ambos continuam dependendo da API de IA. A mensagem no Telegram demonstra a entrada, a classificação demonstra o processamento e a resposta com registro em CSV demonstra a saída.

## 13. Windows, Linux e Docker — entrega obrigatória

Entregar o README com passos completos para as três opções: pré-requisitos, configuração das credenciais, início, teste, encerramento, troca de canal e localização dos dados. Os comandos de Windows devem usar diretamente o Python da `.venv`, dispensando alterações de política do PowerShell. No Linux, usar `.venv/bin/python` e explicar o pacote `python3-venv` em distribuições Debian/Ubuntu.

### Contrato Docker

- Criar `Dockerfile` com base `python:3.11-slim`, diretório `/app`, instalação do `requirements.txt` e cópia dos arquivos de código. Fixar dependências em versões compatíveis verificadas na implementação.
- Criar `.dockerignore` excluindo `.env`, `.env.*` (permitindo `.env.example`), `.venv`, `.git`, caches, CSVs e `data/`. As credenciais entram somente em execução.
- Criar `compose.yaml` com serviços `web` e `bot`, ambos usando a mesma definição de build e `env_file: .env`. O serviço `bot` usa profile `telegram`, não tem portas publicadas e executa `python bot.py`. O serviço `web` executa `python -m streamlit run app.py --server.address=0.0.0.0 --server.port=8501` e publica somente `127.0.0.1:8501:8501`.
- Nos dois serviços, configurar `DB_PATH=/app/data/triagem.db`, `CSV_PATH=/app/data/historico.csv` (origem da importação), `PYTHONUNBUFFERED=1` e bind mount `./data:/app/data`. O banco deve sobreviver à remoção/recriação dos contêineres. Datas no contêiner podem usar UTC, sempre com offset; explicar isso no README.
- Não definir dependência entre `web` e `bot`. Os dois podem rodar juntos (`docker compose --profile telegram up --build`), gravando no mesmo banco; executar uma única instância do bot por token.
- Validar que `docker compose up --build web` e `docker compose up --build bot` iniciam apenas o serviço escolhido em um ambiente inicialmente parado. `docker compose --profile telegram down` deve encerrar ambos sem remover os dados do bind mount.
- Documentar que a opção Docker dispensa instalar Python no host, mas exige Docker Engine/Desktop em funcionamento, Compose e internet.

### Verificação adicional

- [ ] README contém os passos de Windows PowerShell, Linux e Docker, com comandos separados por shell quando necessário.
- [ ] Configuração Compose validada com `docker compose config --quiet`, evitando imprimir credenciais interpoladas.
- [ ] Imagem construída e serviço web acessível em `http://localhost:8501`, quando Docker estiver disponível.
- [ ] O banco no bind mount permanece após parar/recriar o contêiner.
- [ ] Serviço bot possui comando independente, recebe token em execução e não publica portas.
- [ ] Declarar quais sistemas e modos foram efetivamente testados; não declarar portabilidade comprovada apenas por leitura dos comandos.

Referências: https://docs.docker.com/compose/how-tos/profiles/, https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/, https://docs.streamlit.io/deploy/tutorials/docker e https://docs.python.org/3/library/venv.html.

## 14. Evolução — banco, protocolo, setores, fila e acompanhamento

Solicitada depois da primeira entrega (`PROMPT_EVOLUCAO_TRIAGEM_FACIL.md`). Amplia o escopo anterior mantendo a integração com Gemini/OpenRouter, a tela Streamlit e o bot do Telegram. Login, WhatsApp, envio de e-mail e hospedagem continuam fora do escopo. A área de gestão é destinada ao uso local.

### Banco de dados SQLite

- `chamados.py` grava os chamados em SQLite (`triagem.db` na pasta do aplicativo, ou `DB_PATH`; no Docker, `/app/data/triagem.db`), usando apenas a biblioteca padrão (`sqlite3`).
- Tabela `chamados`: `protocolo` (UNIQUE), `criado_em`, `atualizado_em`, `mensagem`, `categoria`, `prioridade`, `resumo`, `justificativa`, `setor`, `status` e `origem` (UNIQUE, identifica a mensagem do Telegram ou a linha do CSV importado; vazia nos envios pela tela).
- Datas em ISO 8601 com offset. A ordenação converte para o instante real, mesmo com offsets diferentes.
- Cada operação abre e fecha a própria conexão, em uma transação (commit ao final, rollback em erro), com espera de até 15 segundos quando outro processo está gravando. Assim tela e bot podem funcionar ao mesmo tempo.
- Falhas do banco geram mensagem curta ao usuário e detalhe técnico apenas no terminal. Falha ao gravar uma análise mostra "Falha no registro" e nenhum protocolo.

### Protocolo

- Gerado pelo Python: `TF-AAAAMMDD-XXXXXX`, com a data de criação e seis caracteres sorteados com `secrets` (alfabeto sem `0`, `O`, `1` e `I`).
- A coluna UNIQUE impede repetição; um sorteio repetido é refeito (até 5 tentativas).
- Exibido na tela e na confirmação do Telegram. A área de gestão localiza um chamado pelo protocolo, aceitando minúsculas e espaços nas pontas.

### Setores e encaminhamento

- A IA sugere o setor na mesma chamada da classificação (quinta chave do JSON, seção 6). O Python valida contra Atendimento, Financeiro, Logística e Suporte Técnico; sem informação suficiente ou com valor fora da lista, o setor é Atendimento.
- Encaminhar significa gravar o chamado com status Aberto e o setor sugerido: ele passa a aparecer na fila desse setor.

### Fila e acompanhamento (aba Fila de chamados)

- Colunas: protocolo, resumo, setor, prioridade, status e data de criação.
- Filtros por setor, prioridade e status (vazio = todos). Padrão de status: Aberto e Em atendimento.
- Ordem: prioridade Alta, Média, Baixa; na mesma prioridade, o chamado mais antigo primeiro.
- Detalhes do chamado: protocolo, datas, status, setor, prioridade, categoria, mensagem original, resumo e justificativa.
- Status: Aberto, Em atendimento e Resolvido. A interface altera o status e corrige setor ou prioridade; toda alteração registra `atualizado_em`. Mensagem original, categoria, resumo e justificativa não são alterados.
- Botão "Atualizar fila" para exibir chamados recebidos pelo bot.
- Histórico: tabela `historico` (`protocolo`, `registrado_em`, `alteracoes`, `observacao`). Cada gravação do acompanhamento acrescenta uma linha com o que mudou (ex.: `Status: Aberto → Em atendimento`) e a observação/justificativa opcional (até 1.000 caracteres); só observação também é aceita. O painel do chamado mostra o histórico do mais recente para o mais antigo. As observações são internas: não aparecem na consulta por protocolo nem na exportação. Bancos anteriores recebem a tabela automaticamente.

### Canais

- Tela e bot chamam a mesma função `chamados.analisar_e_registrar(texto, origem)`.
- Após salvar, informam que a solicitação foi registrada, com protocolo e setor responsável, sem prometer resolução.
- Consulta por protocolo: antes de registrar, tela e bot chamam `chamados.consultar_status(texto)`. Se a mensagem citar protocolos (`TF-AAAAMMDD-XXXXXX`, sem diferenciar maiúsculas/minúsculas), o canal responde status, setor e última atualização de cada um (ou "não encontrado"), sem chamar a IA e sem criar chamado. A resposta não mostra o conteúdo da mensagem original.
- O bot envia `origem = "telegram:<chat_id>:<message_id>"`. Se essa origem já existir, a função devolve o chamado gravado, sem chamar a IA nem gravar. A restrição UNIQUE protege também contra gravações concorrentes.

### CSV

- Exportação: botão na área de gestão com todos os chamados (`protocolo;criado_em;atualizado_em;mensagem;categoria;prioridade;resumo;justificativa;setor;status`), ponto e vírgula, UTF-8 com BOM e neutralização de fórmulas.
- Importação explícita do `historico.csv` anterior (`CSV_PATH` ou pasta do aplicativo): arquivo aberto só para leitura; cada linha válida vira um chamado Aberto na fila de Atendimento, com protocolo novo e a data original como criação; o apóstrofo de neutralização é removido. A origem de cada linha é calculada do conteúdo (SHA-256 mais o número da ocorrência), então a importação pode ser repetida sem duplicar. Linhas inválidas são contadas e ignoradas; cabeçalho diferente ou arquivo ilegível não importam nada.

### Execução

- Windows, Linux e Docker continuam suportados, sem novas dependências.
- `.streamlit/config.toml` define `server.address = "localhost"` na execução local. No Docker, a porta continua publicada somente em `127.0.0.1`.

### Critérios de aceite da evolução

- [x] Chamados persistem após reiniciar (leitura por outro processo).
- [x] Protocolos únicos, com novo sorteio em caso de colisão.
- [x] Encaminhamento para o setor sugerido, com Atendimento como padrão, e fila ordenada por prioridade e antiguidade.
- [x] Filtros por setor, prioridade e status; alteração de status e correção de setor/prioridade com registro da última atualização.
- [x] Importação repetível sem duplicação, preservando o arquivo original.
- [x] Reentrega da mesma atualização do Telegram não duplica o chamado nem chama a IA de novo.
- [x] Canais existentes (tela e bot) funcionando com respostas simuladas após as mudanças.
- [x] Consulta por protocolo na tela e no bot, sem IA e sem chamado novo.
- [x] Observação/justificativa salva no histórico a cada alteração de status, setor ou prioridade.
- [x] Docker verificado com o banco no bind mount (Docker Desktop no Linux: serviços `web`, `bot` e profile `telegram`; banco preservado após `down`).
- [ ] Integração real com IA e Telegram (pendente de credenciais).
