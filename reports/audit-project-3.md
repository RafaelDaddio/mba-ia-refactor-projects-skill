```text
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.11.4 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.1.8)
Files:   15 analyzed | ~1158 lines of code
```

## Summary

CRITICAL: 4 | HIGH: 5 | MEDIUM: 10 | LOW: 7

## Findings

### F01 · [CRITICAL] Hash da senha devolvido nas respostas de usuário e login
- **Anti-pattern:** AP04 — Exposição de dados sensíveis
- **File:** `models/user.py:21`, `routes/user_routes.py:33`, `routes/user_routes.py:85`, `routes/user_routes.py:129`, `routes/user_routes.py:209`
- **Description:** `User.to_dict()` inclui `'password': self.password`, o hash MD5. Esse dicionário é devolvido por `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login` (dentro de `user`). O próprio código já sabe que o campo não deve sair: `GET /users` monta o dicionário à mão sem `password` (`routes/user_routes.py:15-23`).
- **Impact:** Qualquer cliente anônimo obtém o hash de qualquer usuário com `GET /users/1`. Como é MD5 sem salt (F02) e as senhas do seed têm 4 caracteres, a quebra é imediata.
- **Recommendation:** Tirar `password` da serialização de `User` em todas as respostas (PB04).

### F02 · [CRITICAL] Senhas armazenadas com MD5 sem salt
- **Anti-pattern:** AP03 — Armazenamento inseguro de senha
- **File:** `models/user.py:27-32`, `routes/user_routes.py:64`, `routes/user_routes.py:115`
- **Description:** `set_password` grava `hashlib.md5(pwd.encode()).hexdigest()`, e `check_password` compara com o mesmo MD5. Não há salt nem custo computacional. O mínimo aceito é 4 caracteres.
- **Impact:** Hashes vazados (F01) são revertidos por tabela pré-computada ou força bruta em segundos. Senhas iguais geram hashes iguais.
- **Recommendation:** Usar `werkzeug.security.generate_password_hash`/`check_password_hash`, já instalado com o Flask, e aceitar hashes MD5 legados no login, regravando-os no formato novo (PB03). Aumentar o tamanho mínimo da senha seria uma regra nova e fica como recomendação.

### F03 · [CRITICAL] SECRET_KEY, credenciais SMTP e senha do administrador fixas no código
- **Anti-pattern:** AP02 — Segredos e credenciais hardcoded
- **File:** `app.py:13`, `services/notification_service.py:9-10`, `seed.py:16-20`
- **Description:** `app.config['SECRET_KEY'] = 'super-secret-key-123'`. O `NotificationService` tem `email_user = 'taskmanager@gmail.com'` e `email_password = 'senha123'`. O seed cria o administrador `joao@email.com` com senha `'1234'` em qualquer ambiente.
- **Impact:** Quem lê o repositório pode assinar sessões e cookies, usar a conta SMTP e entrar como administrador em qualquer instância populada pelo seed.
- **Recommendation:** Ler `SECRET_KEY` e as credenciais SMTP de variáveis de ambiente, sem valor padrão sensível. Sem `SECRET_KEY` definida, gerar uma aleatória por processo (PB02). As senhas do seed fazem parte do comando documentado (`python seed.py`) e das credenciais de demonstração; restringi-las a desenvolvimento fica como pendência.

### F04 · [CRITICAL] Blueprints acumulam roteamento, acesso a dados, regras e serialização de vários domínios
- **Anti-pattern:** AP05 — God Class / God Module
- **File:** `routes/report_routes.py:12-223`, `routes/task_routes.py:11-299`, `routes/user_routes.py:10-211`
- **Description:** Cada handler lê a requisição, consulta o ORM diretamente (`Task.query`, `User.query`, `Category.query`), aplica regras e monta o JSON à mão. `report_routes.py` atende Task, User e Category (relatórios e CRUD de categorias). `task_routes.py` (299 linhas) consulta as três entidades. Não há camada entre rotas e models: `services/` contém só um serviço nunca usado (F21).
- **Impact:** Nenhuma regra pode ser testada sem HTTP e banco. Qualquer mudança de modelo ou regra exige mexer em vários handlers, e o mesmo arquivo cresce com responsabilidades de domínios diferentes.
- **Recommendation:** Separar por recurso em controllers finos (HTTP), services (regras) e models com as consultas (PB05).

### F05 · [HIGH] Autenticação de fachada: token previsível que nenhuma rota verifica
- **Anti-pattern:** AP10 — Autenticação ausente ou de fachada
- **File:** `routes/user_routes.py:207-211`, `routes/user_routes.py:92-151`, `routes/task_routes.py:225-238`
- **Description:** O login devolve `'token': 'fake-jwt-token-' + str(user.id)`, que nenhuma rota lê. As 22 rotas são públicas: qualquer cliente altera e-mail e senha de outro usuário (`PUT /users/<id>`), exclui usuários com todas as tasks deles (`DELETE /users/<id>`) e lê os relatórios.
- **Impact:** Tomada de conta de qualquer usuário: basta trocar a senha dele por `PUT`. Também é possível apagar e alterar dados de terceiros sem identificação.
- **Recommendation:** Emitir um token real e exigi-lo nas rotas. Isso muda o contrato de todas as rotas comuns e nenhuma é administrativa pela regra 3, então fica como pendência.

### F06 · [HIGH] Debug ligado e servidor escutando em todas as interfaces
- **Anti-pattern:** AP11 — Debug ligado e servidor exposto no entry point
- **File:** `app.py:34`
- **Description:** `app.run(debug=True, host='0.0.0.0', port=5000)` é fixo. Com debug, toda exceção não tratada, como as entradas inválidas de F10, devolve ao cliente a página do debugger do Werkzeug com traceback e trechos do código, e o console interativo do debugger fica acessível pela rede.
- **Impact:** Vazamento de código e caminhos internos para qualquer cliente da rede, além de superfície para execução de código pelo console do debugger.
- **Recommendation:** Ler debug, host e porta da configuração por variável de ambiente, com debug desligado e host local como padrão, mantendo `python app.py` e a porta 5000 (PB02).

### F07 · [HIGH] Cliente define o próprio papel, inclusive `admin`, no cadastro e na atualização
- **Anti-pattern:** AP10 — Autenticação ausente ou de fachada
- **File:** `routes/user_routes.py:52`, `routes/user_routes.py:71-72`, `routes/user_routes.py:119-122`
- **Description:** `POST /users` aceita `role` do corpo entre `['user', 'admin', 'manager']`, e `PUT /users/<id>` permite trocá-lo. Nenhuma credencial é exigida. `User.is_admin()` existe (`models/user.py:34-38`), mas nunca é chamado.
- **Impact:** Qualquer pessoa cria uma conta `admin` ou se promove. O papel gravado não tem valor como dado de identidade, e qualquer autorização futura baseada nele já nasce contornável.
- **Recommendation:** Impedir que o cliente atribua a si um papel privilegiado: o campo `role` continua aceito, mas um valor diferente de `user` exige credencial administrativa (PB06).

### F08 · [HIGH] Regras de negócio nos handlers; camada de serviço sem uso
- **Anti-pattern:** AP07 — Regra de negócio fora da camada de serviço
- **File:** `routes/task_routes.py:273-299`, `routes/report_routes.py:12-155`, `routes/task_routes.py:92-144`, `routes/user_routes.py:54-72`, `routes/user_routes.py:140-142`, `services/notification_service.py:4-48`
- **Description:** Os handlers calculam estatísticas, taxa de conclusão e atraso, validam regras de domínio (status, prioridade, papel, unicidade de e-mail, existência de usuário e categoria) e aplicam a exclusão em cascata das tasks ao remover um usuário. O único serviço, `NotificationService`, nunca é instanciado.
- **Impact:** Regras não testáveis isoladamente e que divergem entre endpoints (F14). Não há ponto único para mudar uma regra.
- **Recommendation:** Extrair services por domínio (tasks, users, categories, reports) que recebem dados já validados e devolvem resultados ou lançam erros de domínio (PB07).

### F09 · [HIGH] Sem app factory: app global com configuração fixa e efeitos no import
- **Anti-pattern:** AP09 — Acoplamento forte sem injeção de dependência
- **File:** `app.py:9-31`, `seed.py:2`, `services/notification_service.py:5-15`
- **Description:** A aplicação é criada no import do módulo, com URI, chave e CORS fixos, e `db.create_all()` também roda no import. `seed.py` depende desse global (`from app import app, db`). O `NotificationService` monta o próprio `smtplib.SMTP` com configuração interna.
- **Impact:** Não dá para apontar a aplicação para um banco de teste sem editar código, e importar `app` já cria `instance/tasks.db`.
- **Recommendation:** Criar `create_app(config)` como composition root, mantendo `app = create_app()` em `app.py` para que `python app.py` e `from app import app, db` continuem funcionando (PB08).

### F10 · [MEDIUM] Validação de entrada ausente ou inconsistente gera 500 e referências inválidas
- **Anti-pattern:** AP15 — Validação de entrada ausente ou inconsistente
- **File:** `routes/task_routes.py:113`, `routes/task_routes.py:96`, `routes/task_routes.py:167`, `routes/task_routes.py:261`, `routes/task_routes.py:264`, `routes/task_routes.py:116-124`, `routes/task_routes.py:186-198`, `routes/report_routes.py:196-197`, `routes/user_routes.py:61`, `routes/user_routes.py:102-103`, `routes/user_routes.py:124-125`
- **Description:**
  - `priority < 1` com `priority` string ou `null` lança `TypeError`.
  - `len(title)` com título numérico (create) ou `null` (update) lança `TypeError`.
  - `int(priority)` e `int(user_id)` na busca lançam `ValueError`.
  - Um corpo JSON que não é objeto (lista, número) quebra em `data.get`.
  - `PUT /categories/<id>` não verifica corpo nulo (`'name' in data`), ao contrário dos outros handlers.
  - `re.match` sobre e-mail não-string lança `TypeError`.
  - `if user_id:` e `if category_id:` pulam a verificação para `0`, e a task é gravada com `user_id = 0`, uma referência a usuário inexistente (o SQLite roda sem `PRAGMA foreign_keys`).
  - `PUT /users/<id>` aceita `name` vazio, que o cadastro rejeita, e `active` de qualquer tipo.
  - `PUT /categories/<id>` aceita `name` vazio, que o cadastro rejeita.
- **Impact:** Erros do cliente viram 500, com traceback por causa de F06. Dados ficam com referências quebradas e regras divergem entre criar e atualizar.
- **Recommendation:** Validar tipo e faixa de cada campo num ponto único usado por criação e atualização, devolvendo 400; verificar existência de IDs com `is not None`; aplicar na atualização as mesmas regras do cadastro (PB11). Formato de `color` e regras não declaradas no código ficam como recomendação.

### F11 · [MEDIUM] Tratamento de erros espalhado, com `except:` genérico e respostas HTML
- **Anti-pattern:** AP16 — Tratamento de erros não centralizado
- **File:** `routes/task_routes.py:62`, `routes/task_routes.py:137`, `routes/task_routes.py:151-154`, `routes/task_routes.py:221-223`, `routes/user_routes.py:87-90` (e outras 7 ocorrências de `except:` em `routes/`), `app.py:9-31`
- **Description:** São 9 `except:` sem tipo e 3 `except Exception as e` copiados entre handlers. `GET /tasks` envolve o handler inteiro e devolve `'Erro interno'`, escondendo qualquer bug. Não há `errorhandler`: 404 de rota inexistente, 405, 415 (corpo sem `Content-Type: application/json`) e 500 saem em HTML, enquanto os handlers respondem `{"error": ...}`.
- **Impact:** O cliente precisa tratar dois formatos de erro, bugs ficam mascarados e erros de entrada viram 500.
- **Recommendation:** Registrar handlers de erro centrais que devolvem JSON `{"error": ...}`, mapear erros de domínio para 4xx e remover os `try/except` repetidos (PB09).

### F12 · [MEDIUM] CORS liberado para qualquer origem
- **Anti-pattern:** AP18 — CORS e middlewares inadequados
- **File:** `app.py:15`
- **Description:** `CORS(app)` sem `origins` responde `Access-Control-Allow-Origin: *` em todas as rotas, inclusive login e alteração de usuários.
- **Impact:** Qualquer site pode chamar a API a partir do navegador da vítima e ler as respostas, incluindo os hashes de F01.
- **Recommendation:** Definir as origens permitidas na configuração, lidas de variável de ambiente (PB16).

### F13 · [MEDIUM] Queries N+1 e contagens separadas onde um agrupamento basta
- **Anti-pattern:** AP13 — Queries N+1 e agregações ineficientes
- **File:** `routes/task_routes.py:41-57`, `routes/user_routes.py:22`, `routes/report_routes.py:53-56`, `routes/report_routes.py:15-30`, `routes/report_routes.py:163`, `routes/task_routes.py:275-281`
- **Description:**
  - `GET /tasks` faz `User.query.get` e `Category.query.get` dentro do laço: uma consulta por usuário e por categoria distintos (o identity map evita repetir o mesmo id).
  - `GET /users` carrega `u.tasks` (lazy) por usuário.
  - O resumo executa 12 `COUNT` separados, carrega todas as tasks para filtrar as atrasadas em memória e faz uma query de tasks por usuário.
  - `GET /categories` faz um `COUNT` por categoria.
  - `/tasks/stats` repete o padrão com 5 `COUNT` e a carga de todas as tasks.
- **Impact:** O número de queries cresce com o volume de usuários, categorias e tasks, e os relatórios degradam linearmente.
- **Recommendation:** Usar `GROUP BY` para contagens por status, prioridade, usuário e categoria, carregar os relacionamentos em lote e filtrar atrasadas no SQL (PB10).

### F14 · [MEDIUM] Regra de atraso e serialização de task reimplementadas em vários handlers
- **Anti-pattern:** AP14 — Duplicação de código
- **File:** `routes/task_routes.py:30-39`, `routes/task_routes.py:71-80`, `routes/task_routes.py:283-287`, `routes/user_routes.py:171-180`, `routes/report_routes.py:33-37`, `routes/report_routes.py:132-135`, `routes/task_routes.py:17-28`, `routes/user_routes.py:162-169`
- **Description:**
  - A regra "atrasada = `due_date` no passado e status diferente de `done`/`cancelled`" aparece 6 vezes, enquanto `Task.is_overdue()` (`models/task.py:50-60`) faz o mesmo e não é usado.
  - `GET /tasks` replica `Task.to_dict()` campo a campo.
  - A taxa de conclusão é recalculada em 3 lugares (`task_routes.py:296`, `report_routes.py:67`, `report_routes.py:151`), embora `calculate_percentage` seja importado (`report_routes.py:7`) e nunca chamado.
  - As validações de criação e atualização são duplicadas, e `utils/helpers.py:57-108` traz uma terceira cópia, sem uso.
- **Impact:** Corrigir uma regra exige achar todas as cópias. As cópias já divergem no formato da task entre endpoints.
- **Recommendation:** Centralizar atraso e serialização no model, cálculos e validações nos services, e reaproveitar os helpers (PB07, PB15). Os formatos atuais de cada endpoint fazem parte do contrato e são preservados.

### F15 · [MEDIUM] `create_all` no import e seed destrutivo sem proteção de ambiente
- **Anti-pattern:** AP19 — Efeitos colaterais na inicialização
- **File:** `app.py:30-31`, `seed.py:11-14`
- **Description:** `db.create_all()` roda no import de `app.py`, inclusive quando o seed importa o módulo, e não há migrações. O seed apaga todas as tasks, usuários e categorias (`Query.delete()`) e recria o administrador com senha fixa, sem checar o ambiente.
- **Impact:** Importar a aplicação já mexe no banco, mudanças de schema não são aplicadas em bancos existentes e um `python seed.py` acidental apaga os dados de produção.
- **Recommendation:** Mover a criação do schema para a inicialização da app factory (PB08). O comportamento destrutivo do seed é o documentado no README: proteção por ambiente e migrações ficam como recomendação.

### F16 · [MEDIUM] CRUD de categorias no blueprint de relatórios e validação de domínio em utils
- **Anti-pattern:** AP24 — Responsabilidade no módulo errado
- **File:** `routes/report_routes.py:157-223`, `utils/helpers.py:57-108`
- **Description:** As quatro rotas de `/categories` estão em `report_bp`. `utils/helpers.py` contém `process_task_data`, com regras de domínio de task (status, prioridade e título).
- **Impact:** Categorias não têm módulo próprio, e regras de domínio ficam num módulo genérico, sem dono.
- **Recommendation:** Criar o controller e o service de categorias e mover as validações de task para o domínio de tasks (PB05).

### F17 · [MEDIUM] Listagens devolvem todos os registros
- **Anti-pattern:** AP20 — Listagens sem paginação
- **File:** `routes/task_routes.py:14`, `routes/task_routes.py:266`, `routes/user_routes.py:12`, `routes/user_routes.py:159`, `routes/report_routes.py:159`
- **Description:** `GET /tasks`, `/tasks/search`, `/users`, `/users/<id>/tasks` e `/categories` fazem `.all()` sem limite e devolvem um array JSON com tudo.
- **Impact:** Resposta e consumo de memória crescem sem limite com o volume de dados.
- **Recommendation:** Paginação (PB17) sem mudar o formato de array das respostas atuais. O que exigir mudar o formato fica como pendência.

### F18 · [MEDIUM] `Query.get()` legado no SQLAlchemy 2.x
- **Anti-pattern:** AP21 — API deprecated
- **File:** `routes/task_routes.py:42`, `routes/task_routes.py:67`, `routes/user_routes.py:29`, `routes/report_routes.py:105` (16 ocorrências no total)
- **Description:** `Model.query.get(id)` é usado em todos os blueprints. Na versão instalada (SQLAlchemy 2.1.8) o método tem `@util.became_legacy_20(":meth:`_orm.Query.get`", alternative="... Session.get")` (`.venv/Lib/site-packages/sqlalchemy/orm/query.py:1059-1062`), que emite `LegacyAPIWarning`.
- **Impact:** Avisos em runtime e dependência de uma API marcada para remoção, já que o SQLAlchemy está sem versão fixa (F20).
- **Recommendation:** Substituir por `db.session.get(Model, id)` (PB13).

### F19 · [MEDIUM] `datetime.utcnow()` deprecated a partir do Python 3.12
- **Anti-pattern:** AP21 — API deprecated
- **File:** `models/task.py:15-16`, `models/task.py:52`, `models/user.py:14`, `models/category.py:11`, `routes/report_routes.py:35` (22 linhas no total, 5 delas em `seed.py`)
- **Description:** Defaults de coluna (`default=datetime.utcnow`, `onupdate=datetime.utcnow`) e comparações de atraso usam `datetime.utcnow()`. O projeto roda em Python 3.11.4, e a função é deprecated desde o 3.12.
- **Impact:** `DeprecationWarning` ao atualizar o runtime e remoção futura.
- **Recommendation:** Usar um helper único baseado em `datetime.now(timezone.utc)` que devolva datetime sem fuso, preservando o formato gravado e o `str()` das respostas (PB13).

### F20 · [LOW] Dependências sem uso e dependências críticas sem versão fixa
- **Anti-pattern:** AP22 — Dependências vulneráveis, sem uso ou sem versão fixa
- **File:** `requirements.txt:4-6`, `requirements.txt:2`
- **Description:** `marshmallow==3.20.1`, `requests==2.31.0` e `python-dotenv==1.0.0` nunca são importados. SQLAlchemy (2.1.8) e Werkzeug (3.1.9) chegam como dependências transitivas sem versão fixa. Não há `pip-audit` no ambiente, por isso vulnerabilidades conhecidas não foram verificadas.
- **Impact:** Superfície de instalação desnecessária, e um reinstall pode trazer versões incompatíveis do ORM ou do servidor.
- **Recommendation:** Remover as dependências sem uso, fixar SQLAlchemy e Werkzeug e rodar `pip-audit`. Fica como pendência: a regra 7 proíbe alterar pacotes sem perguntar.

### F21 · [LOW] Código morto e imports não usados
- **Anti-pattern:** AP29 — Código morto e imports não usados
- **File:** `services/notification_service.py:4-48`, `utils/helpers.py:3-116`, `models/task.py:38-60`, `models/user.py:34-38`, `app.py:7`, `routes/task_routes.py:7`, `routes/user_routes.py:6`, `routes/report_routes.py:7-8`, `models/task.py:3`
- **Description:**
  - `NotificationService` nunca é instanciado.
  - Nenhuma função ou constante de `utils/helpers.py` é chamada; `format_date` e `calculate_percentage` são importados sem uso.
  - `Task.validate_status`, `validate_priority` e `is_overdue`, e `User.is_admin`, não têm chamadas.
  - Imports sem uso: `os, sys, json` (`app.py`); `json, os, sys, time` (`task_routes.py`); `hashlib, json` (`user_routes.py`); `json` (`report_routes.py`, `models/task.py`); `os, json, sys, math, hashlib` (`helpers.py`).
- **Impact:** Ruído que esconde a lógica real e sugere funcionalidades, como notificações, que não existem.
- **Recommendation:** Reaproveitar o que resolve duplicação (`is_overdue`, `calculate_percentage`, as constantes) e remover o restante.

### F22 · [LOW] Literais de negócio repetidos enquanto as constantes existem sem uso
- **Anti-pattern:** AP26 — Números e strings mágicos
- **File:** `routes/task_routes.py:110`, `routes/task_routes.py:177`, `routes/user_routes.py:71`, `routes/user_routes.py:120`, `routes/task_routes.py:96-100`, `routes/task_routes.py:113`, `routes/user_routes.py:64`, `utils/helpers.py:110-116`
- **Description:**
  - A lista de status aparece em 4 lugares, incluindo `models/task.py:39`, e a de papéis em 2.
  - Os limites de título (3/200), de prioridade (1–5) e de senha (4) e o regex de e-mail (`user_routes.py:61`, `:106`) são literais.
  - `helpers.py:110-116` define `VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH` e outras constantes que ninguém usa.
- **Impact:** Mudar um limite exige editar várias cópias, com risco de divergência.
- **Recommendation:** Um módulo de constantes usado por models e services (PB15).

### F23 · [LOW] `print` como logging, com dados pessoais
- **Anti-pattern:** AP27 — `print`/`console.log` como logging
- **File:** `routes/task_routes.py:149`, `routes/task_routes.py:153`, `routes/task_routes.py:219`, `routes/task_routes.py:234`, `routes/user_routes.py:83`, `routes/user_routes.py:89`, `routes/user_routes.py:147`, `services/notification_service.py:21`, `utils/helpers.py:39-41`
- **Description:** Os eventos são registrados com `print`, incluindo o nome do usuário criado (`user_routes.py:83`) e o e-mail do destinatário (`notification_service.py:21`).
- **Impact:** Não há nível, formato nem destino configuráveis, e dados pessoais vão para o stdout.
- **Recommendation:** Usar o módulo `logging` com logger por módulo e sem dados pessoais (PB15).

### F24 · [LOW] URI do banco, host, porta e SMTP fixos no código
- **Anti-pattern:** AP30 — Configuração não secreta fixa no código
- **File:** `app.py:11`, `app.py:34`, `services/notification_service.py:7-8`
- **Description:** A URI `sqlite:///tasks.db`, `host='0.0.0.0'`, `port=5000` e o host e a porta SMTP são literais.
- **Impact:** Trocar de ambiente exige editar código.
- **Recommendation:** Centralizar em um módulo de configuração com leitura de ambiente e os valores atuais como padrão (PB02).

### F25 · [LOW] Tags em texto separado por vírgula e status sem restrição no schema
- **Anti-pattern:** AP32 — Modelagem de dados frágil
- **File:** `models/task.py:18`, `models/task.py:35`, `routes/task_routes.py:140-144`, `routes/task_routes.py:209-213`, `models/task.py:11`
- **Description:** `tags` é `String(500)` montada com `','.join(tags)` e lida com `split(',')`: uma tag que contém vírgula vira duas na leitura, e uma string enviada como `tags` é gravada crua. `status` é `String(50)` sem enumeração no schema.
- **Impact:** Dados de tags corrompidos silenciosamente, e status inválidos só são barrados nas rotas.
- **Recommendation:** Tabela de tags ou JSON, e enum ou `CHECK` de status. Fica como recomendação, porque muda o schema e os dados existentes.

### F26 · [LOW] Nomes pouco descritivos
- **Anti-pattern:** AP28 — Nomes ruins e contexto ambíguo
- **File:** `routes/report_routes.py:24-28`, `routes/task_routes.py:247-266`, `models/category.py:14`
- **Description:** As contagens por prioridade se chamam `p1`…`p5`. Em `search_tasks`, `tasks` guarda um query builder e não uma lista. Em `Category.to_dict`, o dicionário de resposta é `d`.
- **Impact:** A leitura depende do contexto ao redor.
- **Recommendation:** Renomear durante a extração dos services e controllers (PB05).

## Deprecated APIs

| Uso legado | Local | Situação | Equivalente moderno |
|---|---|---|---|
| `Model.query.get(id)` (`Query.get`) | `routes/task_routes.py:42` (+ 15 ocorrências) | legado desde SQLAlchemy 2.0 (instalado 2.1.8); emite `LegacyAPIWarning` | `db.session.get(Model, id)` |
| `datetime.utcnow()` / `default=datetime.utcnow` | `models/task.py:15` (+ 21 linhas, 5 em `seed.py`) | deprecated desde Python 3.12 (projeto em 3.11.4) | `datetime.now(timezone.utc)`, convertido para naive UTC para preservar o formato |

```text
================================
Total: 26 findings
================================
```
