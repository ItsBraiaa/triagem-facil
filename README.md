# Triagem Fácil

> **Aviso:** projeto desenvolvido com auxílio de inteligência artificial, apenas como prova de conceito (PoC) para um trabalho da faculdade. Não é uma solução homologada nem 100% segura: não deve ser usado em produção.

> **Como instalar e executar:** siga o guia **[COMO_EXECUTAR.md](COMO_EXECUTAR.md)**. Ele traz o passo a passo para Windows, Linux e Docker, a configuração do arquivo `.env`, o uso do sistema e os problemas comuns.

## 1. O que o sistema faz

O Triagem Fácil classifica mensagens de clientes de uma pequena loja com Python e IA (**Gemini ou OpenRouter**, um provedor por execução) e registra cada mensagem como um **chamado** em um banco **SQLite**. Cada chamado recebe um **protocolo**, vai para a **fila do setor responsável** (Atendimento, Financeiro, Logística ou Suporte Técnico) e é acompanhado na **área de gestão** da tela, com os status Aberto, Em atendimento e Resolvido.

As mensagens chegam por dois canais, que usam a mesma lógica de registro e podem funcionar ao mesmo tempo:

- **Tela web** (Streamlit), com as abas **Registrar mensagem** e **Fila de chamados**.
- **Bot do Telegram** (long polling), em conversa privada.

**Fluxo:** mensagem digitada na tela ou enviada ao bot → chamada à IA → validação da resposta → chamado gravado no banco com protocolo, status Aberto e setor sugerido → protocolo, setor e tempo da triagem informados no mesmo canal → acompanhamento na fila de chamados → aviso ao cliente no Telegram quando o status muda.

A IA interpreta o texto e sugere categoria, prioridade, setor, resumo e justificativa. O Python valida a resposta, gera o protocolo, controla data/hora, grava o banco e envia os avisos. Uma mensagem que cita um protocolo (ex.: “status do pedido TF-20260929-7STU8D”) é uma **consulta**: o canal responde a situação do chamado, sem chamar a IA e sem abrir chamado novo.

## 2. Funcionalidades

- **Registro com protocolo e setor:** cada mensagem válida vira um chamado com protocolo no formato `TF-AAAAMMDD-XXXXXX`, status Aberto e o setor sugerido pela IA. A confirmação mostra protocolo, setor, categoria, prioridade, resumo e justificativa. O protocolo usa a data de criação e seis caracteres sorteados pelo Python, sem `0`, `O`, `1` e `I`, para evitar confusão ao ditar. O banco não aceita protocolos repetidos: se um sorteio coincidir, o Python sorteia outro.
- **Tempo da triagem automática:** a confirmação informa quanto durou a triagem (chamada à IA, validação e gravação), com uma casa decimal. Na tela, a mensagem de sucesso termina com “Triagem automática concluída em 3,2 s.”; no bot, aparece a linha “Tempo da triagem automática: 3,2 s” logo depois da justificativa. O tempo não aparece na consulta por protocolo, nem quando o Telegram reentrega uma mensagem já registrada, e não é gravado no banco.
- **Fila com painel “Visão geral” e atualização automática a cada 30 s:** no topo da aba **Fila de chamados**, o painel mostra a quantidade de chamados em cada status (Aberto, Em atendimento, Resolvido) e o total, e os pendentes de cada setor (“Pendentes · Logística”, por exemplo), contando os status Aberto ou Em atendimento. O painel conta todos os chamados, sem considerar os filtros da fila. O painel e a fila se atualizam sozinhos a cada 30 segundos, trazendo os chamados novos recebidos pelo bot sem ninguém clicar. Só essa parte da tela é recarregada: quem estiver digitando uma observação não perde o texto. O botão **Atualizar fila** recarrega a tela inteira na hora.
- **Acompanhamento com histórico e observação:** nos detalhes de um chamado, a gestão altera o status e corrige o setor ou a prioridade, com uma observação opcional de até 1.000 caracteres, e clica em **Salvar alterações**. Cada gravação entra no **Histórico** com a data, o que mudou (ex.: `Status: Aberto → Em atendimento; Setor: Logística → Financeiro`) e a observação. Também é possível salvar só uma observação. A mensagem original e a análise da IA não mudam, e as observações são internas.
- **Aviso ao cliente no Telegram quando o status muda:** se o chamado foi aberto pelo bot e o status mudou, a própria tela envia ao cliente, na mesma conversa do Telegram, uma mensagem com o protocolo e o novo status:

  ```text
  Atualização da sua solicitação TF-20260929-7STU8D:
  Novo status: Em atendimento.
  Informe o protocolo se precisar falar sobre ela.
  ```

  O status é salvo antes do envio. Com sucesso, a tela mostra “Chamado atualizado e registrado no histórico. Cliente avisado no Telegram.”. Se o envio falhar, ou se a tela não tiver o `TELEGRAM_BOT_TOKEN` no `.env`, aparece um alerta “Cliente não avisado no Telegram: …”, o novo status continua salvo e a gestão deve avisar o cliente por outro canal. Mudanças só de setor, prioridade ou observação não geram aviso, e a observação nunca vai para o cliente. O envio é feito pela tela, direto à API do Telegram: não depende de o `bot.py` estar em execução. Chamados registrados pela tela ou importados do CSV não têm conversa no Telegram e não geram aviso.
- **Consulta por protocolo (tela e bot):** se a mensagem citar um ou mais protocolos, em qualquer parte do texto e em maiúsculas ou minúsculas, o canal responde o status, o setor e a data da última atualização de cada um, por exemplo `TF-20260929-7STU8D: Em atendimento, setor Logística (atualizado em 29/09/2026 13:21)`. Protocolo inexistente recebe “não encontrado”. A consulta não chama a IA, não cria chamado e não mostra o conteúdo da mensagem original.
- **Exportação e importação CSV:** **Exportar chamados em CSV** baixa todos os chamados (colunas `protocolo;criado_em;atualizado_em;mensagem;categoria;prioridade;resumo;justificativa;setor;status`), com ponto e vírgula, UTF-8 com BOM para o Excel e neutralização de fórmulas. **Importar histórico CSV** copia para o banco o `historico.csv` da versão anterior: os registros entram como Aberto na fila de Atendimento, o arquivo não é alterado e a importação pode ser repetida sem duplicar chamados.
- **Tema visual:** o arquivo `.streamlit/config.toml` define as cores da tela em duas versões, clara (destaque `#0E7490`, texto `#0F172A` sobre fundo branco) e escura (destaque `#0891B2`, texto `#E2E8F0` sobre `#0F172A`), que quem usa a tela escolhe no menu ⋮ > Settings; a fonte `sans-serif` que já vem com o Streamlit (não depende de internet); e `toolbarMode = "viewer"`, que esconde o botão “Deploy” e as opções de desenvolvedor, mas mantém o menu ⋮ com a troca de tema. O `Dockerfile` copia a pasta `.streamlit` para a imagem, para o tema valer também no Docker (isso ainda não foi testado dentro de um contêiner; veja a seção 7).
- **Área de gestão só local:** a aba **Fila de chamados** não tem login e é destinada ao uso neste computador. Na execução local, o `address = "localhost"` do `config.toml` faz a tela aceitar conexões somente deste computador. No Docker, esse item do arquivo não vale (o comando usa `--server.address=0.0.0.0` dentro do contêiner), e a proteção vem da porta publicada só em `127.0.0.1`.

**Setores:** a IA sugere o setor seguindo as regras do `PROMPT_SISTEMA` em `triagem.py`: Atendimento (informações gerais), Financeiro (pagamentos, cobranças, reembolsos, notas fiscais), Logística (entregas, atrasos, frete, trocas e devoluções) e Suporte Técnico (defeitos, instalação, uso de produto, problemas no site ou aplicativo). Essas regras foram definidas nesta implementação e podem ser ajustadas no prompt. Sem informação suficiente, ou com setor fora da lista, o chamado vai para **Atendimento**. Categoria e setor são campos separados.

### Área de gestão em resumo

- **Fila:** protocolo, resumo, setor, prioridade, status e data de criação, na ordem **Alta → Média → Baixa** e, na mesma prioridade, do mais antigo para o mais novo. Filtros por setor, prioridade e status; por padrão, aparecem os chamados Aberto e Em atendimento.
- **Detalhes:** escolha um chamado em **Abrir detalhes de um chamado da fila** ou digite o protocolo em **Localizar chamado pelo protocolo** (vale também para chamados fora dos filtros).
- **Acompanhamento, histórico, exportação e importação:** como descrito na lista acima.

O passo a passo de uso da tela e do bot está na seção “Usando o sistema” do [COMO_EXECUTAR.md](COMO_EXECUTAR.md).

## 3. Arquivos

| Arquivo | Função |
|---|---|
| `triagem.py` | Classificação: prompt, chamada à IA e validação da resposta (categoria, prioridade, setor, resumo e justificativa). |
| `chamados.py` | Chamados em SQLite: registro compartilhado (`analisar_e_registrar`), protocolo, consulta por protocolo (`consultar_status`), fila, números do painel (`contar_chamados`), acompanhamento e histórico, aviso ao cliente no Telegram (`avisar_cliente_telegram`), tempo formatado (`formatar_duracao`), exportação CSV e importação do histórico CSV anterior. |
| `app.py` | Tela Streamlit com as abas **Registrar mensagem** e **Fila de chamados** (painel, fila com atualização automática, detalhes e acompanhamento). |
| `bot.py` | Bot do Telegram (long polling), usando a mesma função de registro de `chamados.py`. |
| `.streamlit/config.toml` | Tema da tela (versões clara e escura, e fonte), barra de ferramentas sem o botão “Deploy” e, na execução local, acesso somente deste computador. |
| `requirements.txt` | Dependências com versões fixadas: `streamlit`, `requests`, `python-dotenv` e `python-telegram-bot`. |
| `.env.example` | Modelo de configuração, somente com placeholders. |
| `Dockerfile`, `compose.yaml`, `.dockerignore` | Execução com Docker Compose (serviços `web` e `bot`). |
| `COMO_EXECUTAR.md` | Guia de instalação e execução: Windows, Linux e Docker, arquivo `.env`, uso do sistema e problemas comuns. |
| `TRIAGEM_FACIL_SPEC_IMPLEMENTACAO.md` | Especificação e plano de implementação, com a evolução e os critérios de aceite. |

## 4. Onde ficam os dados

| Execução | Banco de dados (chamados) | Histórico CSV anterior (só para importação) |
|---|---|---|
| Windows ou Linux com Python | `triagem.db` na pasta do projeto, ou o caminho de `DB_PATH` | `historico.csv` na pasta do projeto, ou o caminho de `CSV_PATH` |
| Docker | `data/triagem.db` na pasta do projeto | `data/historico.csv` na pasta do projeto |

O banco é criado no primeiro acesso e guarda os chamados (protocolo, datas de criação e de última atualização, mensagem original, análise da IA, setor e status) e o histórico de alterações e observações. O tempo da triagem e o resultado dos avisos no Telegram não são gravados. O CSV deixou de ser gravado a cada análise: para uma planilha atualizada, use **Exportar chamados em CSV**. As execuções local e Docker usam bancos separados. Horários ficam em ISO 8601 com offset (no Docker, em UTC).

**Cópia de segurança:** com a tela e o bot encerrados, copie o arquivo `triagem.db` (ou a pasta `data`).

## 5. Demonstração

### Exemplos

Use estas mensagens fictícias. Os resultados são **expectativas** para orientar o ensaio, não valores fixos no programa: a IA decide e pode variar. Se o setor sugerido não for o esperado, corrija-o na área de gestão durante a demonstração.

| Mensagem | Categoria esperada | Prioridade esperada | Setor esperado |
|---|---|---|---|
| “Vocês aceitam pagamento por cartão?” | Dúvida | Baixa | Financeiro |
| “Meu produto chegou quebrado e quero fazer a troca.” | Reclamação | Média | Logística |
| “Meu pedido está atrasado e preciso receber ainda hoje para um evento.” | Reclamação | Alta | Logística |

### Teste antes da apresentação

Siga o “Teste rápido antes da apresentação” do [COMO_EXECUTAR.md](COMO_EXECUTAR.md#teste). Ele usa as três mensagens acima e confere o registro, o painel, a atualização automática, o acompanhamento com o aviso no Telegram, a consulta por protocolo, a persistência e a importação.

A tela não mostra por onde o chamado chegou. Para mostrar o aviso no Telegram, localize o chamado pelo protocolo que o bot respondeu.

O bot é um classificador: cada mensagem é independente. Mensagens enviadas enquanto o bot estava desligado são descartadas na inicialização; envie uma mensagem nova após iniciar o processo. Se o Telegram entregar a mesma mensagem de novo, o bot responde com o protocolo já registrado, sem nova análise.

### Roteiro de 10 a 15 minutos

| Tempo | O que fazer |
|---|---|
| 0–2 min | **Problema:** a loja lê, classifica, anota e encaminha cada mensagem manualmente. Mostre como seria a triagem manual de uma mensagem e, se possível, cronometre. |
| 2–4 min | **Solução:** entrada (tela ou Telegram) → processamento (`triagem.py` chama a IA e valida o JSON) → saída (chamado no banco, protocolo e setor no canal, fila por setor, aviso ao cliente). Explique que a IA interpreta o texto e o Python controla validação, protocolo, data/hora, gravação e avisos. |
| 4–9 min | **Ao vivo:** envie as três mensagens pelo Telegram (celular ou Telegram Desktop) ou pela tela. Mostre o protocolo, o setor, a análise e o tempo da triagem automática, e comente se bateram com a expectativa. |
| 9–12 min | **Gestão:** mostre o painel **Visão geral** e a fila ordenada por prioridade, que recebe sozinha o chamado enviado pelo bot. Filtre por setor, localize pelo protocolo um chamado que o bot registrou, mude o status com uma observação e mostre o aviso chegando no celular. Consulte o protocolo pelo bot e exporte o CSV. |
| 12–15 min | **Benefícios e limitações** (seção 6) e perguntas. |

**Plano B:** se o Telegram falhar (na rede usada nos testes, a conexão com o Telegram falhou de forma intermitente), use a aba de registro da tela; se o aviso não for entregue, a tela mostra um alerta e o status continua salvo. Os dois canais dependem da API de IA. Para falar de economia de tempo, compare a triagem manual cronometrada com o tempo que o próprio sistema mostra na confirmação; se usar valores que não foram medidos, identifique-os como estimativa.

| Critério da rubrica | Evidência na apresentação |
|---|---|
| Interação da IA com o ambiente / entrada | Mensagem digitada ao vivo na tela ou enviada ao bot pelo celular. |
| Processamento e uso adequado da IA | Interpretação de texto livre: categoria, prioridade, setor, resumo e justificativa, validados pelo Python. |
| Resultado final da automação / saída | Protocolo, setor e tempo da triagem no canal; chamado na fila do setor e no painel, que se atualizam sozinhos; aviso ao cliente no Telegram quando o status muda; CSV exportado. |
| Problema e benefícios | Tarefa manual comparada ao trabalho automatizado, com o tempo da triagem automática exibido pelo sistema. |
| Demonstração prática ao vivo | Fluxo executado com conexão real à API de IA e ao Telegram. |

## 6. Limitações

- Exige internet e a API do provedor de IA disponível, com cota ou saldo; não há retentativa nem troca automática de provedor. Um modelo pode deixar de estar disponível: nos testes, o `gemini-2.5-flash-lite` respondeu HTTP 404 para chaves novas.
- As classificações e o setor são produzidos pela IA e podem variar entre envios. A prioridade e o setor são **sugestões** de triagem, corrigíveis na área de gestão.
- A área de gestão não tem login: é destinada ao uso local, neste computador. Login, WhatsApp, envio de e-mail e hospedagem ficam fora desta versão.
- **Atualização automática:** acontece na página aberta no navegador e recarrega só o painel e a fila, a cada 30 segundos; um chamado novo pode levar até esse tempo para aparecer. Os detalhes do chamado aberto e o arquivo da exportação não entram nesse ciclo: clique em **Atualizar fila** para recarregar a tela inteira antes de exportar.
- **Aviso no Telegram:**
  - Só para chamados criados pelo bot e só quando o status muda.
  - A tela precisa do `TELEGRAM_BOT_TOKEN` no `.env`, lido quando o programa inicia: depois de preencher, reinicie a tela.
  - Não há retentativa. Se o envio falhar, a tela mostra um alerta, o status continua salvo e a gestão avisa o cliente por outro canal. O resultado do envio não fica registrado no histórico.
  - O envio usa um tempo limite de 10 segundos; enquanto isso, a tela mostra “Avisando o cliente no Telegram...”.
  - O cliente recebe só o protocolo e o novo status; as observações são internas.
- A consulta por protocolo não identifica quem pergunta: quem souber o protocolo vê status, setor e data (nunca o conteúdo da mensagem). Mensagens que citam um protocolo são sempre tratadas como consulta, não como chamado novo.
- O tempo da triagem mede uma execução neste computador (IA, validação e gravação) e varia com a rede e o modelo; não é gravado no banco.
- O bot só funciona enquanto o processo (`bot.py` ou o contêiner) estiver em execução. Mensagens enviadas com o bot desligado são descartadas ao iniciar. Use uma única instância por token.
- Apenas texto, até 3.000 caracteres por mensagem; o bot atende só conversas privadas e ignora grupos e mensagens editadas.
- SQLite grava um chamado por vez: tela e bot podem funcionar juntos, e uma gravação espera a outra por até 15 segundos. Mantenha o banco em disco local (não em pasta de rede).
- No Docker, o horário fica em UTC (`+00:00`).

## 7. Verificação realizada

### Nesta rodada: tema, tempo da triagem, aviso no Telegram, painel e atualização automática

**Com respostas simuladas** (Linux, Python 3.14.4 e 3.11.16, com as versões do `requirements.txt`: streamlit 1.64.0, requests 2.34.2, python-dotenv 1.2.3 e python-telegram-bot 22.8). Nenhuma chamada real à IA ou ao Telegram; credenciais falsas. Os scripts de verificação ficam numa pasta temporária, fora do projeto.

| Verificação | Checagens | O que confere |
|---|---|---|
| Regressão do núcleo e do bot | 144 | Validação, setor, registro, protocolo único, fila, acompanhamento, histórico, consulta por protocolo, importação e exportação CSV, reentrega do Telegram e respostas do bot. |
| Regressão da tela (Streamlit AppTest) | 52 | Abas, registro, resultado, fila, filtros, detalhes, acompanhamento, localização por protocolo, importação e exportação. |
| Painel e fila | 70 | Contagem por status e total, pendentes por setor (Aberto e Em atendimento), zeros com banco vazio, painel que não muda com os filtros, um único trecho da tela com atualização automática contendo só painel e fila, detalhes/localizar/exportação fora dele, seletor que abre os detalhes, **Atualizar fila** e erro compreensível com banco inacessível. |
| Tempo da triagem | 58 | Formato com vírgula, tempo no fim da confirmação da tela e logo depois da justificativa no bot; sem tempo em falha, consulta, mensagem vazia e reentrega do Telegram; atualização da tela sem nova chamada à IA; confirmação do bot abaixo de 4.096 caracteres. |
| Tema | 58 | Valores de `[theme]`, `[theme.light]`, `[theme.dark]` e `[client]` (`toolbarMode = "viewer"`) lidos pelo Streamlit instalado; sem `base` fixa, para permitir a troca entre claro e escuro; fonte sem download; `--server.address=0.0.0.0` vence o `address` do arquivo e o tema continua valendo; `Dockerfile` copia `.streamlit` e o `.dockerignore` não a exclui; nenhuma requisição feita. |
| Aviso no Telegram | 91 | Aviso só para chamado do bot e só com mudança de status; texto só com protocolo e novo status, sem a observação e sem `parse_mode`; tempo limite de 10 s; sem token ou com falha de envio, alerta com o status salvo; clique na tela durante o envio; token e URL do Telegram fora dos logs; nenhum envio com o banco aberto. |

**Total: 473 checagens por versão do Python, todas passando no branch integrado.**

**No navegador** (servidor de teste local, com respostas simuladas): a fila e o painel se atualizaram sozinhos com um chamado gravado por outro processo, em ciclos de 30 segundos; o texto não salvo da observação foi preservado durante a atualização; o seletor abriu os detalhes do chamado; o tema foi aplicado e o botão “Deploy” ficou escondido. Também foi provado localmente que o `--server.address=0.0.0.0` da linha de comando tem precedência sobre o `address = "localhost"` do `config.toml`.

### Integração real (29/09/2026)

- **Gemini:** o modelo `gemini-3.1-flash-lite` classificou corretamente os três exemplos, com 2 a 12 segundos por mensagem. O modelo `gemini-2.5-flash-lite` respondeu HTTP 404 (“no longer available to new users”) para chaves novas.
- **Telegram:** o bot real conectou ao Telegram (“Application started”). Na rede usada, a conexão com `api.telegram.org` falhou de forma intermitente (3 de 6 tentativas pelo próprio computador).

### Docker

Verificado na rodada anterior (evolução do banco), com Docker Desktop 29.6.1 no Linux: `docker compose config`, construção da imagem, serviço `web` publicado só em `127.0.0.1:8501`, serviço `bot` sozinho e sem portas, profile `telegram` com os dois serviços e banco preservado em `./data` depois de encerrar os contêineres. **Nesta rodada**, nada foi testado dentro de um contêiner, inclusive as mudanças em `app.py`, `bot.py` e `chamados.py`. A cópia da pasta `.streamlit` no `Dockerfile` foi revisada e conferida pelo script do tema, e a precedência do `--server.address` foi provada fora do Docker.

### Não verificado nesta rodada

- Aviso no Telegram entregue a um cliente real.
- Tempo da triagem exibido numa triagem real, pela tela e pelo bot (a integração real registrou de 2 a 12 s por mensagem, mas a exibição do tempo com a IA real não foi conferida).
- Tela integrada no Windows.
- Tema e aviso no Telegram dentro do contêiner Docker.
- Integração real com o OpenRouter.

### Rodadas anteriores

- **Evolução do banco** (protocolo, setores, fila, acompanhamento, histórico e consulta por protocolo): as mesmas 144 checagens do núcleo e do bot e 52 da tela, incluindo três processos gravando no mesmo banco ao mesmo tempo (180 chamados sem erro), importação repetida sem duplicar, servidor real escutando só em `127.0.0.1` e os serviços Docker descritos acima.
- **Versão anterior (CSV):** 138 checagens simuladas mais 16 checagens de correções em Windows 11 Pro com Python 3.12.14.

## 8. Referências

- [OpenRouter: integração](https://openrouter.ai/docs/quickstart).
- [Gemini: chaves da API](https://ai.google.dev/gemini-api/docs/api-key), [modelos](https://ai.google.dev/gemini-api/docs/models), [preços](https://ai.google.dev/gemini-api/docs/pricing) e [compatibilidade de chat](https://ai.google.dev/gemini-api/docs/openai).
- [Telegram: criação do bot](https://core.telegram.org/bots/tutorial) e [Bot API (`sendMessage`)](https://core.telegram.org/bots/api#sendmessage).
- [python-telegram-bot](https://docs.python-telegram-bot.org/).
- [Python: sqlite3](https://docs.python.org/3/library/sqlite3.html).
- [Streamlit: `st.fragment` e `run_every`](https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment) e [configuração `config.toml` (tema e `toolbarMode`)](https://docs.streamlit.io/develop/api-reference/configuration/config.toml).
- [Streamlit em Docker](https://docs.streamlit.io/deploy/tutorials/docker).
- [Docker Compose: serviços e perfis](https://docs.docker.com/compose/how-tos/profiles/).
