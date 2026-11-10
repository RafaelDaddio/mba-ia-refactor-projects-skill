# Refatoração Arquitetural Automatizada — skill `refactor-arch`

Entrega do desafio **Criação de Skills — Refatoração Arquitetural Automatizada**. O enunciado original está no repositório [devfullcycle/mba-ia-refactor-projects-skill](https://github.com/devfullcycle/mba-ia-refactor-projects-skill).

O objetivo é construir uma skill do Claude Code que analisa uma codebase backend, audita seus anti-patterns e a refatora para o padrão MVC, validando que a aplicação continua funcionando. A skill é exercitada em três projetos legados:

| Projeto | Stack | Domínio | Organização inicial |
|---|---|---|---|
| `code-smells-project/` | Python 3 + Flask 3.1.1 + sqlite3 | API de e-commerce (produtos, usuários, pedidos, relatório) | Monolito em 4 arquivos |
| `ecommerce-api-legacy/` | Node.js + Express 4 + sqlite3 (em memória) | LMS com fluxo de checkout | Uma classe (`AppManager`) concentra banco, rotas e regras |
| `task-manager-api/` | Python 3 + Flask 3.0.0 + Flask-SQLAlchemy | Gerenciador de tarefas | Parcialmente em camadas (`models/`, `routes/`, `services/`, `utils/`) |

### Escala de severidade

A classificação segue a escala definida no enunciado:

- **CRITICAL** — falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex.: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex.: God Class com banco de dados, lógica complexa e roteamento no mesmo arquivo).
- **HIGH** — fortes violações de MVC ou SOLID que dificultam muito a manutenção e os testes (ex.: lógica de negócio pesada em controllers, forte acoplamento sem injeção de dependência, estado global mutável).
- **MEDIUM** — problemas de padronização, duplicação de código ou gargalos de performance moderada (ex.: queries N+1, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW** — melhorias de legibilidade, nomes de variáveis ruins ou magic numbers soltos no código.

Problemas que a escala não cobre diretamente (dependências vulneráveis, headers de resposta, modelagem de dados) foram classificados pelo impacto observado em cada projeto.

---

## A) Análise Manual

### Metodologia

1. Leitura integral do código dos três projetos, registrando arquivo e linha de cada problema.
2. Execução de cada aplicação em ambiente isolado (um venv por projeto Python, `npm ci` no projeto Node) e reprodução, com `curl`, dos problemas observáveis por HTTP.
3. Auditoria das dependências com `pip-audit` e `npm audit`.

As tabelas abaixo documentam 21 problemas no projeto 1, 18 no projeto 2 e 20 no projeto 3, selecionados pelo impacto arquitetural e de segurança. Eles servem de gabarito para medir a auditoria da skill.

Os locais (`arquivo:linha`) referem-se ao código original, antes da refatoração — commit [`6d1ce62`](https://github.com/RafaelDaddio/mba-ia-refactor-projects-skill/tree/6d1ce62).

### Projeto 1 — `code-smells-project` (Python/Flask)

4 arquivos `.py`, 780 linhas, 19 rotas. Documentados: **21 problemas — CRITICAL 6 | HIGH 3 | MEDIUM 8 | LOW 4**.

| ID | Severidade | Problema | Local | Justificativa |
|---|---|---|---|---|
| P1-01 | CRITICAL | SQL Injection | `models.py` — todas as queries com parâmetro são concatenadas (ex.: `:110` login, `:291` busca, `:127` cadastro) | Permite entrar como qualquer usuário sem a senha e extrair a base inteira por um endpoint público de busca. |
| P1-02 | CRITICAL | Execução arbitrária de SQL por HTTP | `app.py:59-78` | `POST /admin/query` executa qualquer SQL recebido no corpo, sem autenticação: leitura, alteração ou remoção de qualquer tabela. |
| P1-03 | CRITICAL | Endpoint destrutivo sem autenticação | `app.py:47-57` | `POST /admin/reset-db` apaga as quatro tabelas com uma requisição anônima. |
| P1-04 | CRITICAL | Segredos e credenciais hardcoded | `app.py:7`, `database.py:76`, `controllers.py:289` | `SECRET_KEY` e a senha do admin padrão ficam versionadas no git; o `/health` ainda devolve a chave a qualquer cliente. |
| P1-05 | CRITICAL | Senhas em texto plano | `database.py:31, 76-78`; `models.py:110, 126-128` | Senhas gravadas e comparadas sem hash: qualquer leitura da base (P1-01, P1-02) entrega todas, reaproveitáveis em outros serviços. |
| P1-06 | CRITICAL | God module | `models.py:1-314` | Um único arquivo concentra SQL, regras de negócio (estoque, totais, descontos) e serialização dos quatro domínios; nenhum domínio pode ser testado ou alterado isoladamente. |
| P1-07 | HIGH | Conexão global mutável compartilhada entre threads | `database.py:4, 8-11` | Uma única conexão SQLite (`check_same_thread=False`) atende todos os requests: transações concorrentes se misturam (o `commit()` de uma requisição efetiva a escrita parcial de outra) e não há como injetar outro banco em teste. |
| P1-08 | HIGH | Regras de negócio espalhadas, sem camada de serviço | `controllers.py:43-54, 208-210, 247-250`; `models.py:139-146, 256-262` | Validações de domínio e notificações ficam no controller; estoque, totais e faixas de desconto, na camada de dados. As regras não se reaproveitam e já divergem entre criar e atualizar produto. |
| P1-09 | HIGH | Ausência de autenticação e autorização | `app.py:11-30`; `controllers.py:167-186` | Nenhuma rota exige identidade e o login não emite token nem sessão: qualquer cliente lista pedidos e usuários, muda status e lê o relatório de vendas. |
| P1-10 | MEDIUM | Queries N+1 | `models.py:171-201, 203-233` | Listar pedidos executa uma query, mais uma por pedido, mais uma por item; o custo cresce linearmente com o histórico. |
| P1-11 | MEDIUM | Duplicação de código | `models.py:171-201` ≈ `:203-233`; serialização de produto em `:12-21, 31-40, 304-313` | Funções e blocos copiados: uma correção numa cópia não chega às outras. |
| P1-12 | MEDIUM | Pedido aceita quantidade negativa ou zero | `controllers.py:195-201`; `models.py:144-146, 163-166` | Sem validação dos itens, quantidade `-5` gera total negativo e aumenta o estoque. |
| P1-13 | MEDIUM | Esquema sem restrições de integridade | `database.py:14-53`; `models.py:68, 196` | Sem `NOT NULL`, `UNIQUE` no e-mail ou chave estrangeira: e-mails duplicados, pedidos para usuários inexistentes e itens órfãos exibidos como "Desconhecido". |
| P1-14 | MEDIUM | `get_db()` mistura conexão, schema e seed | `database.py:7-86` | O primeiro acesso ao banco cria tabelas e insere dados de exemplo como efeito colateral, em qualquer ambiente. |
| P1-15 | MEDIUM | Faturamento inclui pedidos cancelados | `models.py:242` (consultas em `:239-254`) | `SUM(total)` sem filtro de status distorce faturamento e ticket médio; são cinco queries onde uma agregação bastaria. |
| P1-16 | MEDIUM | Listagens sem paginação | `models.py:7, 75, 206` | `SELECT *` sem limite: resposta e latência crescem sem controle. |
| P1-17 | MEDIUM | Formato de resposta sem padrão | `controllers.py:20` vs `:142`; `:276-292` | Alguns erros trazem `"sucesso": false`, outros não, e o `/health` usa outro formato: o cliente não consegue tratar respostas de forma uniforme. |
| P1-18 | LOW | Números e strings mágicos | `models.py:257-262`; `controllers.py:47-52, 242` | Faixas de desconto, limites e listas de categorias e status embutidos no código escondem regras de negócio. |
| P1-19 | LOW | Configuração fixa no código | `database.py:5`; `app.py:85, 88` | Caminho do banco relativo ao diretório de execução, host e porta fixos: rodar a aplicação de outra pasta cria outro banco silenciosamente. |
| P1-20 | LOW | Imports não usados | `database.py:2`; `models.py:2` | Ruído que esconde as dependências reais de cada módulo. |
| P1-21 | LOW | Dependências com vulnerabilidades conhecidas | `requirements.txt:1-2` | `pip-audit` aponta uma falha em `flask 3.1.1` (corrigida na 3.1.3) e três em `flask-cors 5.0.1` (corrigidas na 6.0.0). O impacto aqui é baixo: a falha do Flask envolve a sessão, que a aplicação não usa, e as do flask-cors afrouxam regras de CORS que já estão totalmente abertas (`app.py:9`). |

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express)

3 arquivos `.js`, 180 linhas, 3 rotas. Documentados: **18 problemas — CRITICAL 4 | HIGH 2 | MEDIUM 7 | LOW 5**.

| ID | Severidade | Problema | Local | Justificativa |
|---|---|---|---|---|
| P2-01 | CRITICAL | Segredos hardcoded | `src/utils.js:1-7` | Senha do banco e chave do gateway de pagamento (`pk_live_…`) versionadas e exportadas para a aplicação inteira. |
| P2-02 | CRITICAL | Número do cartão e chave do gateway no log | `src/AppManager.js:45` | Todo checkout grava o cartão completo e a chave do gateway na saída do servidor: violação de PCI-DSS e vazamento para qualquer coletor de logs. |
| P2-03 | CRITICAL | God Class | `src/AppManager.js:4-139` | Uma classe cria a conexão, o schema e o seed, registra as rotas e implementa checkout e relatório financeiro — exatamente a "God Class" da escala. |
| P2-04 | CRITICAL | Rotas administrativas e destrutivas sem autenticação | `src/AppManager.js:80-129, 131-137` | O relatório financeiro (nomes de alunos e valores pagos) é público, e qualquer cliente apaga qualquer usuário. |
| P2-05 | HIGH | Um único request derruba o servidor | `src/AppManager.js:33, 46` | Com `card` numérico, `cc.startsWith` lança `TypeError` dentro de um callback do sqlite3; a exceção não é capturada e o processo Node encerra para todos os clientes. |
| P2-06 | HIGH | Acoplamento sem injeção de dependência | `src/AppManager.js:7`; `src/app.js:8-10` | A classe instancia o próprio banco: não há como trocar a persistência nem testar a lógica isoladamente. |
| P2-07 | MEDIUM | Queries N+1 no relatório financeiro | `src/AppManager.js:83-128` | Uma query por curso e duas por matrícula; o custo cresce com o número de matrículas. |
| P2-08 | MEDIUM | Callbacks aninhados com contadores manuais | `src/AppManager.js:37-77, 89-127` | Cinco níveis de callback e controle de término por contadores: um erro no meio deixa o cliente sem resposta ou derruba o processo. |
| P2-09 | MEDIUM | Erros ignorados, sem tratamento centralizado | `src/AppManager.js:57, 92-93, 104, 106, 133-135` | `err` é descartado em vários callbacks e não há middleware de erro; o DELETE responde sucesso mesmo para um usuário inexistente. |
| P2-10 | MEDIUM | Validação de entrada ausente no checkout | `src/AppManager.js:29-35` | Só a presença dos campos é verificada: e-mail inválido é aceito e o cartão `"4abc"` é aprovado. |
| P2-11 | MEDIUM | Matrícula duplicada; senha ignorada para e-mail existente | `src/AppManager.js:40, 66-75` | O mesmo aluno compra o mesmo curso duas vezes (cobrança em dobro), e qualquer pessoa matricula outra conhecendo só o e-mail. |
| P2-12 | MEDIUM | Esquema sem restrições; exclusão deixa órfãos | `src/AppManager.js:12-16, 131-137` | Sem chaves estrangeiras, apagar um usuário mantém matrículas e pagamentos, e o relatório passa a exibir "Unknown". |
| P2-13 | MEDIUM | Dependências vulneráveis e deprecated | `package.json:10-11` | `npm audit` aponta 13 vulnerabilidades (2 críticas, 8 altas). Nas dependências do Express 4.22.1, falhas de negação de serviço (`body-parser`, `path-to-regexp`, `qs`) e de falsificação de IP (`proxy-addr`), corrigíveis sem trocar de versão major. Na cadeia de instalação do `sqlite3 5.1.7`, `tar` com escrita arbitrária de arquivos e pacotes deprecated (`prebuild-install`, `glob@7`); a correção exige `sqlite3` 6.x. |
| P2-14 | LOW | Números e strings mágicos | `src/utils.js:6, 19, 22`; `src/AppManager.js:46, 68` | Prefixo `"4"` como regra de aprovação, `"123456"` como senha padrão, iterações e cortes sem nome. |
| P2-15 | LOW | Código morto | `src/utils.js:2-3, 5, 10`; `src/AppManager.js:2` | `dbUser`, `dbPass`, `smtpUser` e `totalRevenue` nunca são usados — incluindo um segredo sem propósito. |
| P2-16 | LOW | `self = this` misturado com arrow functions | `src/AppManager.js:26, 50-57` | Três formas de referenciar o contexto no mesmo método tornam fácil errar o `this`. |
| P2-17 | LOW | Configuração fixa no código | `src/utils.js:6`; `src/AppManager.js:7` | Porta e banco `:memory:` sem variáveis de ambiente. |
| P2-18 | LOW | Header `X-Powered-By: Express` exposto | `src/app.js:5` | O header padrão revela a tecnologia do servidor e facilita o reconhecimento. |

### Projeto 3 — `task-manager-api` (Python/Flask)

15 arquivos `.py`, 1.158 linhas, 22 rotas. Documentados: **20 problemas — CRITICAL 2 | HIGH 2 | MEDIUM 10 | LOW 6**.

| ID | Severidade | Problema | Local | Justificativa |
|---|---|---|---|---|
| P3-01 | CRITICAL | Segredos hardcoded | `app.py:13`; `services/notification_service.py:7-10` | `SECRET_KEY` e usuário/senha de SMTP versionados no git. |
| P3-02 | CRITICAL | Hash da senha exposto pela API | `models/user.py:21` (via `to_dict`); `routes/user_routes.py:33, 85, 129, 209` | GET/POST/PUT de usuário e o login devolvem o hash; como é MD5 sem salt (`models/user.py:29`), ele é revertido por tabela pronta. |
| P3-03 | HIGH | Autenticação de fachada e escalada de privilégio | `routes/user_routes.py:52, 71-72, 119-122, 210` | O token `fake-jwt-token-<id>` nunca é verificado, e qualquer cliente se cadastra ou se promove a `admin`. |
| P3-04 | HIGH | Rotas concentram toda a lógica; camada de serviço vazia | `routes/*.py`; `services/` | As rotas fazem consulta, validação, regras (atraso, estatísticas) e serialização; `services/` só tem um serviço de notificação que ninguém usa. A separação em pastas não reflete separação de responsabilidades. |
| P3-05 | MEDIUM | Queries N+1 | `routes/task_routes.py:41-57`; `routes/user_routes.py:22`; `routes/report_routes.py:55-56, 161-163` | `GET /tasks` faz duas consultas extras por task; listagem de usuários e relatórios repetem o padrão. |
| P3-06 | MEDIUM | Agregações ineficientes | `routes/report_routes.py:15-28, 30-43`; `routes/task_routes.py:275-287` | Doze `COUNT` separados e carga de todas as tasks em memória só para contar atrasos. |
| P3-07 | MEDIUM | Lógica do model reescrita nas rotas | `routes/task_routes.py:17-39, 71-80, 110-114, 176-184, 283-287`; `routes/user_routes.py:162-180`; `routes/report_routes.py:34-36, 132-135` (vs. `models/task.py:23-60`) | `to_dict`, cálculo de atraso e validações existem no model e são reimplementados até seis vezes. |
| P3-08 | MEDIUM | `except:` genérico, sem tratamento centralizado | `routes/task_routes.py:62, 137, 204, 236`; `routes/user_routes.py:130, 149`; `routes/report_routes.py:186, 207, 221` | Qualquer exceção é capturada e respondida com mensagem genérica, sem registro: os erros ficam invisíveis. |
| P3-09 | MEDIUM | Validações ausentes resultam em 500 | `routes/task_routes.py:113, 167, 182, 261, 264`; `routes/report_routes.py:196-202` | `priority: "alta"`, `?priority=abc` e corpo `null` estouram exceções fora de qualquer `try`; como o app roda com `debug=True` (`app.py:34`), a resposta é a página do debugger com código-fonte. |
| P3-10 | MEDIUM | APIs deprecated | `Model.query.get()` em 16 pontos (ex.: `routes/task_routes.py:42`); `datetime.utcnow` em 22 pontos (ex.: `models/task.py:15`) | `Query.get()` é API legada no SQLAlchemy 2.x (substituto: `db.session.get(Model, id)`) e emite `LegacyAPIWarning` em runtime; `datetime.utcnow()` é deprecated desde o Python 3.12 (substituto: `datetime.now(timezone.utc)`). |
| P3-11 | MEDIUM | Listagens sem paginação | `routes/task_routes.py:14, 266`; `routes/user_routes.py:12`; `routes/report_routes.py:159` | Toda listagem usa `.all()`: a resposta cresce sem limite. |
| P3-12 | MEDIUM | CRUD de categorias no blueprint de relatórios | `routes/report_routes.py:157-223` | Responsabilidade no módulo errado: as rotas de categorias não estão onde se esperaria encontrá-las. |
| P3-13 | MEDIUM | Criação de tabelas no import, sem migrações | `app.py:30-31` | Importar `app` (o `seed.py` faz isso) cria tabelas como efeito colateral, e mudanças de schema não chegam a bancos existentes. |
| P3-14 | MEDIUM | Dependências vulneráveis, sem uso e sem versão fixa | `requirements.txt:1-6` | `pip-audit` aponta falhas em cinco dos seis pacotes; a do `flask-cors 4.0.0` está no caminho das requisições (envia `Access-Control-Allow-Private-Network: true` por padrão, expondo recursos da rede privada). `requests`, `marshmallow` e `python-dotenv` nem são importados, e SQLAlchemy e Werkzeug não têm versão fixa (a instalação trouxe o SQLAlchemy 2.1.8). |
| P3-15 | LOW | `print()` no lugar de logging | `routes/task_routes.py:149, 153, 219, 234`; `routes/user_routes.py:83, 89, 147` | Sem níveis nem destino configurável. |
| P3-16 | LOW | Imports não usados | `app.py:7`; `routes/task_routes.py:7`; `routes/user_routes.py:6`; `utils/helpers.py:3-7` | Ruído que esconde as dependências reais. |
| P3-17 | LOW | Código morto | `utils/helpers.py:9-116`; `models/task.py:38-60`; `services/notification_service.py` | Validações e constantes prontas nunca são usadas, dando a falsa impressão de que existem. |
| P3-18 | LOW | Números e strings mágicos | `routes/task_routes.py:96-100, 110, 113`; `routes/user_routes.py:64, 71` | Status, prioridades e limites repetidos no código, enquanto as constantes de `utils/helpers.py:110-116` ficam sem uso. |
| P3-19 | LOW | Configuração fixa no código | `app.py:11, 34` | URI do banco, host e porta embutidos. |
| P3-20 | LOW | Tags armazenadas como texto separado por vírgula | `models/task.py:18, 35` | Uma tag com vírgula quebra o dado, e não há como consultar por tag. |
