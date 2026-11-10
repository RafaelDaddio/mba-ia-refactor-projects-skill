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

Problemas que a escala não cobre diretamente (dependências vulneráveis, modo debug, headers de resposta, modelagem de dados) foram classificados pelo impacto observado em cada projeto.

---

## A) Análise Manual

### Metodologia

1. Leitura integral do código dos três projetos, registrando arquivo e linha de cada problema.
2. Execução de cada aplicação em ambiente isolado (um venv por projeto Python, `npm ci` no projeto Node) e reprodução, com `curl`, dos problemas observáveis por HTTP.
3. Auditoria das dependências com `pip-audit` e `npm audit`.

As tabelas abaixo documentam 23 problemas no projeto 1, 18 no projeto 2 e 22 no projeto 3, selecionados pelo impacto arquitetural e de segurança. Eles servem de gabarito para medir a auditoria da skill.

Os locais (`arquivo:linha`) referem-se ao código original, antes da refatoração — commit [`6d1ce62`](https://github.com/RafaelDaddio/mba-ia-refactor-projects-skill/tree/6d1ce62).

### Projeto 1 — `code-smells-project` (Python/Flask)

4 arquivos `.py`, 780 linhas, 19 rotas. Documentados: **23 problemas — CRITICAL 6 | HIGH 4 | MEDIUM 9 | LOW 4**.

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
| P1-10 | HIGH | Debug ligado com o servidor exposto na rede | `app.py:8, 88` | `debug=True` com `host="0.0.0.0"` deixa o debugger do Werkzeug acessível a qualquer máquina da rede: uma exceção não tratada devolve o traceback com código-fonte, e o console interativo, protegido só por um PIN, executa código no servidor. |
| P1-11 | MEDIUM | Queries N+1 | `models.py:171-201, 203-233` | Listar pedidos executa uma query, mais uma por pedido, mais uma por item; o custo cresce linearmente com o histórico. |
| P1-12 | MEDIUM | Duplicação de código | `models.py:171-201` ≈ `:203-233`; serialização de produto em `:12-21, 31-40, 304-313` | Funções e blocos copiados: uma correção numa cópia não chega às outras. |
| P1-13 | MEDIUM | Pedido aceita quantidade negativa ou zero | `controllers.py:195-201`; `models.py:144-146, 163-166` | Sem validação dos itens, quantidade `-5` gera total negativo e aumenta o estoque. |
| P1-14 | MEDIUM | Esquema sem restrições de integridade | `database.py:14-53`; `models.py:68, 196` | Sem `NOT NULL`, `UNIQUE` no e-mail ou chave estrangeira: e-mails duplicados, pedidos para usuários inexistentes e itens órfãos exibidos como "Desconhecido". |
| P1-15 | MEDIUM | `get_db()` mistura conexão, schema e seed | `database.py:7-86` | O primeiro acesso ao banco cria tabelas e insere dados de exemplo como efeito colateral, em qualquer ambiente. |
| P1-16 | MEDIUM | Faturamento inclui pedidos cancelados | `models.py:242` (consultas em `:239-254`) | `SUM(total)` sem filtro de status distorce faturamento e ticket médio; são cinco queries onde uma agregação bastaria. |
| P1-17 | MEDIUM | Listagens sem paginação | `models.py:7, 75, 206` | `SELECT *` sem limite: resposta e latência crescem sem controle. |
| P1-18 | MEDIUM | Formato de resposta sem padrão | `controllers.py:20` vs `:142`; `:276-292` | Alguns erros trazem `"sucesso": false`, outros não, e o `/health` usa outro formato: o cliente não consegue tratar respostas de forma uniforme. |
| P1-19 | MEDIUM | CORS liberado para qualquer origem | `app.py:9` | `CORS(app)` sem lista de origens aceita qualquer site e qualquer método: o navegador deixa uma página maliciosa chamar as rotas sem autenticação, inclusive `/admin/query`, e ler as respostas. |
| P1-20 | LOW | Números e strings mágicos | `models.py:257-262`; `controllers.py:47-52, 242` | Faixas de desconto, limites e listas de categorias e status embutidos no código escondem regras de negócio. |
| P1-21 | LOW | Configuração fixa no código | `database.py:5`; `app.py:85, 88` | Caminho do banco relativo ao diretório de execução e porta fixa: rodar a aplicação de outra pasta cria outro banco silenciosamente. |
| P1-22 | LOW | Imports não usados | `database.py:2`; `models.py:2` | Ruído que esconde as dependências reais de cada módulo. |
| P1-23 | LOW | Dependências com vulnerabilidades conhecidas | `requirements.txt:1-2` | `pip-audit` aponta uma falha em `flask 3.1.1` (corrigida na 3.1.3) e três em `flask-cors 5.0.1` (corrigidas na 6.0.0). O impacto aqui é baixo: a falha do Flask envolve a sessão, que a aplicação não usa, e as do flask-cors afrouxam regras de CORS que já estão totalmente abertas (P1-19). |

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

15 arquivos `.py`, 1.158 linhas, 22 rotas. Documentados: **22 problemas — CRITICAL 2 | HIGH 3 | MEDIUM 11 | LOW 6**.

| ID | Severidade | Problema | Local | Justificativa |
|---|---|---|---|---|
| P3-01 | CRITICAL | Segredos hardcoded | `app.py:13`; `services/notification_service.py:7-10` | `SECRET_KEY` e usuário/senha de SMTP versionados no git. |
| P3-02 | CRITICAL | Hash da senha exposto pela API | `models/user.py:21` (via `to_dict`); `routes/user_routes.py:33, 85, 129, 209` | GET/POST/PUT de usuário e o login devolvem o hash; como é MD5 sem salt (`models/user.py:29`), ele é revertido por tabela pronta. |
| P3-03 | HIGH | Autenticação de fachada e escalada de privilégio | `routes/user_routes.py:52, 71-72, 119-122, 210` | O token `fake-jwt-token-<id>` nunca é verificado, e qualquer cliente se cadastra ou se promove a `admin`. |
| P3-04 | HIGH | Rotas concentram toda a lógica; camada de serviço vazia | `routes/*.py`; `services/` | As rotas fazem consulta, validação, regras (atraso, estatísticas) e serialização; `services/` só tem um serviço de notificação que ninguém usa. A separação em pastas não reflete separação de responsabilidades. |
| P3-05 | HIGH | Debug ligado com o servidor exposto na rede | `app.py:34` | `debug=True` com `host='0.0.0.0'` deixa o debugger do Werkzeug acessível a qualquer máquina da rede: as entradas inválidas de P3-10 devolvem a página do debugger com código-fonte, e o console interativo, protegido só por um PIN, executa código no servidor. |
| P3-06 | MEDIUM | Queries N+1 | `routes/task_routes.py:41-57`; `routes/user_routes.py:22`; `routes/report_routes.py:55-56, 161-163` | `GET /tasks` faz duas consultas extras por task; listagem de usuários e relatórios repetem o padrão. |
| P3-07 | MEDIUM | Agregações ineficientes | `routes/report_routes.py:15-28, 30-43`; `routes/task_routes.py:275-287` | Doze `COUNT` separados e carga de todas as tasks em memória só para contar atrasos. |
| P3-08 | MEDIUM | Lógica do model reescrita nas rotas | `routes/task_routes.py:17-39, 71-80, 110-114, 176-184, 283-287`; `routes/user_routes.py:162-180`; `routes/report_routes.py:34-36, 132-135` (vs. `models/task.py:23-60`) | `to_dict`, cálculo de atraso e validações existem no model e são reimplementados até seis vezes. |
| P3-09 | MEDIUM | `except:` genérico, sem tratamento centralizado | `routes/task_routes.py:62, 137, 204, 236`; `routes/user_routes.py:130, 149`; `routes/report_routes.py:186, 207, 221` | Qualquer exceção é capturada e respondida com mensagem genérica, sem registro: os erros ficam invisíveis. |
| P3-10 | MEDIUM | Validações ausentes resultam em 500 | `routes/task_routes.py:113, 167, 182, 261, 264`; `routes/report_routes.py:196-202` | `priority: "alta"`, `?priority=abc` e corpo `null` estouram exceções fora de qualquer `try`; com o debug ligado (P3-05), a resposta é a página do debugger com código-fonte. |
| P3-11 | MEDIUM | APIs deprecated | `Model.query.get()` em 16 pontos (ex.: `routes/task_routes.py:42`); `datetime.utcnow` em 22 pontos (ex.: `models/task.py:15`) | `Query.get()` é API legada no SQLAlchemy 2.x (substituto: `db.session.get(Model, id)`) e emite `LegacyAPIWarning` em runtime; `datetime.utcnow()` é deprecated desde o Python 3.12 (substituto: `datetime.now(timezone.utc)`). |
| P3-12 | MEDIUM | Listagens sem paginação | `routes/task_routes.py:14, 266`; `routes/user_routes.py:12`; `routes/report_routes.py:159` | Toda listagem usa `.all()`: a resposta cresce sem limite. |
| P3-13 | MEDIUM | CRUD de categorias no blueprint de relatórios | `routes/report_routes.py:157-223` | Responsabilidade no módulo errado: as rotas de categorias não estão onde se esperaria encontrá-las. |
| P3-14 | MEDIUM | Criação de tabelas no import, sem migrações | `app.py:30-31` | Importar `app` (o `seed.py` faz isso) cria tabelas como efeito colateral, e mudanças de schema não chegam a bancos existentes. |
| P3-15 | MEDIUM | Dependências vulneráveis, sem uso e sem versão fixa | `requirements.txt:1-6` | `pip-audit` aponta falhas em cinco dos seis pacotes; a do `flask-cors 4.0.0` está no caminho das requisições (envia `Access-Control-Allow-Private-Network: true` por padrão, expondo recursos da rede privada). `requests`, `marshmallow` e `python-dotenv` nem são importados, e SQLAlchemy e Werkzeug não têm versão fixa (a instalação trouxe o SQLAlchemy 2.1.8). |
| P3-16 | MEDIUM | CORS liberado para qualquer origem | `app.py:15` | `CORS(app)` sem lista de origens aceita qualquer site e qualquer método: o navegador deixa uma página maliciosa chamar a API e ler as respostas, incluindo os hashes de senha de P3-02; o `flask-cors 4.0.0` ainda estende esse acesso a APIs na rede privada (P3-15). |
| P3-17 | LOW | `print()` no lugar de logging | `routes/task_routes.py:149, 153, 219, 234`; `routes/user_routes.py:83, 89, 147` | Sem níveis nem destino configurável. |
| P3-18 | LOW | Imports não usados | `app.py:7`; `routes/task_routes.py:7`; `routes/user_routes.py:6`; `utils/helpers.py:3-7` | Ruído que esconde as dependências reais. |
| P3-19 | LOW | Código morto | `utils/helpers.py:9-116`; `models/task.py:38-60`; `services/notification_service.py` | Validações e constantes prontas nunca são usadas, dando a falsa impressão de que existem. |
| P3-20 | LOW | Números e strings mágicos | `routes/task_routes.py:96-100, 110, 113`; `routes/user_routes.py:64, 71` | Status, prioridades e limites repetidos no código, enquanto as constantes de `utils/helpers.py:110-116` ficam sem uso. |
| P3-21 | LOW | Configuração fixa no código | `app.py:11, 34` | URI do banco e porta embutidos. |
| P3-22 | LOW | Tags armazenadas como texto separado por vírgula | `models/task.py:18, 35` | Uma tag com vírgula quebra o dado, e não há como consultar por tag. |

---

## B) Construção da Skill

### Decisões de design

#### Arquivos

```text
.claude/skills/refactor-arch/
├── SKILL.md
└── references/
    ├── project-analysis.md
    ├── anti-patterns-catalog.md
    ├── audit-report-template.md
    ├── mvc-guidelines.md
    ├── refactoring-playbook.md
    └── validation.md
```

O **`SKILL.md`** é o orquestrador. Ele traz as regras que valem durante toda a execução, o passo a passo das três fases e o formato exato do que cada fase imprime. O conhecimento técnico fica nos arquivos de referência, e cada fase lê só os de que precisa; assim o playbook, o maior deles, só entra no contexto depois da confirmação.

O **`project-analysis.md`** ensina a reconhecer o projeto: identificar linguagem, framework e versão a partir de manifestos e lockfiles, encontrar o banco e suas tabelas, classificar a arquitetura em três tipos e levantar os endpoints de cada framework.

O **`anti-patterns-catalog.md`** é a base da auditoria. Descreve 32 anti-patterns com severidade, sinais de detecção, falsos positivos a evitar e a transformação que corrige cada um, e traz uma tabela de APIs deprecated com seus substitutos.

O **`audit-report-template.md`** fixa o formato do relatório (cabeçalho, contagem por severidade, findings com local exato, APIs deprecated) e inclui um finding preenchido como exemplo.

O **`mvc-guidelines.md`** descreve a arquitetura de chegada sem citar framework: o papel de cada camada, quem pode depender de quem, o layout de diretórios e o checklist que a refatoração precisa cumprir.

O **`refactoring-playbook.md`** contém 17 transformações com código antes e depois em Python e Node.js, na ordem em que devem ser aplicadas.

O **`validation.md`** detalha procedimentos como subir a aplicação, montar o plano de requisições, registrar o baseline e comparar os resultados.

#### Fluxo de execução

1. **Chamada.** Dentro do projeto, o usuário roda, por exemplo, `/refactor-arch $ARGUMENTS`, com argumento sendo o caminho do relatório de auditoria, por exemplo `../reports/audit-project-1.md`. O Claude Code carrega o `SKILL.md` e repassa o caminho para a skill, que só grava o relatório no passo 4; sem argumento, o relatório só é impresso.
2. **Fase 1.** A skill lê `project-analysis.md`, inspeciona o projeto só com ferramentas de leitura e imprime o resumo da análise e o inventário de endpoints.
3. **Fase 2.** Lê `anti-patterns-catalog.md` e `audit-report-template.md`, confronta o código com o catálogo e imprime o relatório. Termina com `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` e encerra o turno.
4. **Resposta.** Qualquer que seja a resposta, o relatório é gravado no caminho recebido. Se não for "y", a skill para sem ter alterado o projeto.
5. **Fase 3.** Lê `mvc-guidelines.md`, `refactoring-playbook.md` e `validation.md`. Antes de mexer no código, sobe a aplicação original e registra a resposta de cada endpoint. Depois escolhe a estratégia pelo tipo de arquitetura, imprime o plano e aplica as transformações em etapas, com checagem de sintaxe e subida rápida ao fim de cada uma.
6. **Validação.** Sobe a versão refatorada com o comando original, repete as requisições e compara com o baseline. Encerra os processos, apaga os dados de teste e imprime o resumo final: nova estrutura, checklist de validação, endpoints antes e depois e findings resolvidos ou pendentes.

#### Outras decisões

**Só roda quando chamada.** O frontmatter usa `disable-model-invocation: true` para evitar que a skill seja invocada acidentalmente, e ela só roda com o comando `/refactor-arch`.

**Regras no topo.** O `SKILL.md` começa pelas regras que valem em todas as fases, como não alterar nada antes da confirmação e preservar o contrato dos endpoints, para que sejam lidas antes de qualquer instrução específica.

**Comparar em vez de checar "200".** Saber que um endpoint responde não diz se ele responde como antes. Com o baseline gravado, toda diferença depois da refatoração precisa ser uma mudança intencional: dado sensível removido, rota administrativa protegida, 4xx no lugar de 500 para entrada inválida, formato de erro padronizado.

**Segurança sem quebrar clientes.** Rotas administrativas passam a exigir um token definido em variável de ambiente, e endpoints que executam SQL recebido ficam desligados por padrão. As rotas públicas não ganham autenticação, porque isso quebraria quem já as usa; a ausência fica registrada como pendência. Nenhuma dependência nova é instalada.

### Anti-patterns do catálogo

| Severidade | Anti-patterns |
|---|---|
| CRITICAL | AP01 SQL Injection · AP02 segredos hardcoded · AP03 senha armazenada de forma insegura · AP04 exposição de dados sensíveis · AP05 God Class · AP06 endpoint administrativo desprotegido |
| HIGH | AP07 regra de negócio fora de services · AP08 estado global e conexão compartilhada · AP09 acoplamento sem injeção de dependência · AP10 autenticação ausente ou de fachada · AP11 debug ligado com servidor exposto · AP12 exceção que derruba o processo |
| MEDIUM | AP13 N+1 e agregações ineficientes · AP14 duplicação · AP15 validação de entrada · AP16 erros não centralizados · AP17 integridade de dados · AP18 CORS sem restrição · AP19 efeitos colaterais na inicialização · AP20 listagem sem paginação · AP21 API deprecated · AP22 dependência vulnerável ou sem versão · AP23 callbacks aninhados · AP24 código no módulo errado · AP25 formato de resposta sem padrão |
| LOW | AP26 valores mágicos · AP27 `print`/`console.log` como log · AP28 nomes ambíguos · AP29 código morto · AP30 configuração fixa no código · AP31 header que revela a stack · AP32 modelagem de dados frágil |

O catálogo foi construído a partir da análise manual, para que a auditoria encontre cada um dos 63 problemas documentados na seção A. O AP21 traz ainda uma tabela de APIs deprecated de Flask, SQLAlchemy, Python, Node e Express, para que a skill funcione em outros projetos.

Cada entrada descreve sinais de detecção (como "query dentro de `for`"), falsos positivos a evitar (como placeholders, que não são SQL Injection) e a transformação do playbook que corrige o problema.

### Como a skill se mantém agnóstica de tecnologia

**Detecção pelos arquivos do projeto.** A Fase 1 identifica linguagem, framework, versão, banco e comando de execução a partir de manifestos, lockfiles e pacotes instalados. Nenhum arquivo da skill menciona os projetos deste repositório.

**Arquitetura alvo sem framework.** O `mvc-guidelines.md` define as camadas e o layout de diretórios sem citar framework. O playbook mostra cada transformação em Python/Flask e Node/Express, e o princípio por trás dela vale para outras stacks. O catálogo segue a mesma ideia, com sinais por stack e um sinal genérico.

**Estratégia por tipo de projeto.** A Fase 1 classifica o projeto como monolito (A), camadas parciais (B) ou em camadas (C), e a Fase 3 usa essa classificação para decidir entre criar a estrutura do zero, completar as camadas que faltam ou corrigir os problemas no lugar.

**Validação por HTTP.** A Fase 3 testa a aplicação com `curl`, usando o comando de execução descoberto na Fase 1, para não depender de um framework de testes. Para liberar a porta, usa `lsof` ou `netstat`/`taskkill`, conforme o sistema operacional.

### Desafios encontrados

**Pausa no meio da skill.** O Claude Code não tem um mecanismo para pausar uma skill. A solução foi instruir a skill a imprimir a pergunta `[y/n]` e encerrar o turno, para que a resposta do usuário chegue como uma nova mensagem.

**Relatório antes da confirmação.** O relatório precisa ficar salvo em `reports/`, mas a skill não pode criar nem alterar arquivos antes da confirmação do usuário. Por isso, na Fase 2, ela só imprime o relatório no terminal e grava o arquivo depois da resposta, seja ela "y" ou "n".

**Achados inventados.** Os projetos 1 e 2 não usam APIs deprecated no código, só nas dependências. Para evitar que a skill invente achados, o catálogo separa os dois casos (AP21 e AP22), e o relatório informa quando não encontra nenhuma API deprecated.

**Escala de severidade incompleta.** Dependências vulneráveis, headers de resposta e modelagem de dados não se encaixam na escala do enunciado. Esses casos são classificados pelo impacto observado em cada projeto.
