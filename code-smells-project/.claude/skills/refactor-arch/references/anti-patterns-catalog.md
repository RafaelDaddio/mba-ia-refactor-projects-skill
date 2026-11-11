# Catálogo de anti-patterns — Fase 2

Cada entrada traz: o que é, sinais de detecção (o que procurar no código), o que **não** confundir e a transformação do playbook que corrige (PBxx). Use os sinais para localizar candidatos e confirme sempre lendo o trecho.

## Como classificar

### Escala de severidade

- **CRITICAL** — falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (God Class com banco, regras e roteamento juntos).
- **HIGH** — fortes violações de MVC ou SOLID que dificultam muito a manutenção e os testes: regra de negócio pesada em controllers, forte acoplamento sem injeção de dependência, estado global mutável.
- **MEDIUM** — padronização, duplicação de código ou performance moderada: queries N+1, middlewares inadequados, validações ausentes.
- **LOW** — legibilidade: nomes ruins, magic numbers, código morto.

### Regras de classificação

1. Use a severidade da entrada do catálogo. As entradas que admitem ajuste dizem quando subir ou descer.
2. Problemas que a escala não cobre diretamente (dependências, headers, modelagem) são classificados pelo impacto observado **neste** projeto.
3. **Um finding por causa.** Ocorrências da mesma causa com a mesma correção formam um finding com vários locais (ex.: todas as queries concatenadas). Problemas diferentes que caem no mesmo anti-pattern formam findings separados (ex.: execução arbitrária de SQL e reset do banco sem autenticação são dois findings AP06).
4. Cite primeiro os locais de maior impacto (ex.: a concatenação explorável pelo endpoint público antes da que recebe um inteiro já convertido).

### Índice

| ID | Anti-pattern | Severidade |
|---|---|---|
| AP01 | SQL Injection por concatenação | CRITICAL |
| AP02 | Segredos e credenciais hardcoded | CRITICAL |
| AP03 | Armazenamento inseguro de senha | CRITICAL |
| AP04 | Exposição de dados sensíveis | CRITICAL |
| AP05 | God Class / God Module | CRITICAL |
| AP06 | Endpoint administrativo ou destrutivo desprotegido | CRITICAL |
| AP07 | Regra de negócio fora da camada de serviço | HIGH |
| AP08 | Estado global mutável / conexão compartilhada | HIGH |
| AP09 | Acoplamento forte sem injeção de dependência | HIGH |
| AP10 | Autenticação ausente ou de fachada | HIGH |
| AP11 | Debug ligado e servidor exposto no entry point | HIGH |
| AP12 | Exceção não tratada derruba o processo | HIGH |
| AP13 | Queries N+1 e agregações ineficientes | MEDIUM |
| AP14 | Duplicação de código | MEDIUM |
| AP15 | Validação de entrada ausente ou inconsistente | MEDIUM |
| AP16 | Tratamento de erros não centralizado | MEDIUM |
| AP17 | Integridade de dados e regras de estado | MEDIUM |
| AP18 | CORS e middlewares inadequados | MEDIUM |
| AP19 | Efeitos colaterais na inicialização | MEDIUM |
| AP20 | Listagens sem paginação | MEDIUM |
| AP21 | API deprecated | MEDIUM |
| AP22 | Dependências vulneráveis, sem uso ou sem versão fixa | MEDIUM / LOW |
| AP23 | Callbacks aninhados e controle assíncrono manual | MEDIUM |
| AP24 | Responsabilidade no módulo errado | MEDIUM |
| AP25 | Formato de resposta sem padrão | MEDIUM |
| AP26 | Números e strings mágicos | LOW |
| AP27 | `print`/`console.log` como logging | LOW |
| AP28 | Nomes ruins e contexto ambíguo | LOW |
| AP29 | Código morto e imports não usados | LOW |
| AP30 | Configuração não secreta fixa no código | LOW |
| AP31 | Header que revela a stack | LOW |
| AP32 | Modelagem de dados frágil | LOW |

---

## CRITICAL

### AP01 — SQL Injection por concatenação

SQL montado juntando strings com valores vindos de fora.

- **Sinais:**
  - Python: `execute(`/`executemany(` cujo SQL usa `+`, f-string, `%` ou `.format(`; variáveis `query +=` montadas com entrada. Grep: `execute\(\s*f?["'].*["']\s*\+|execute\(\s*f["']|query\s*\+=`.
  - Node: `db.run|get|all|exec|query(` com template literal `${...}` ou `+` no SQL.
  - Qualquer stack: literal `"SELECT|INSERT|UPDATE|DELETE ..."` seguido de `+`.
- **Não confundir:** placeholders (`?`, `%s`, `:nome`, `$1`) com os valores passados à parte; ORM e query builders; concatenação apenas de constantes ou de cláusulas fixas. Um valor já convertido para inteiro pela rota (`<int:id>`) reduz a exploração, mas a função continua vulnerável: entra no mesmo finding, depois dos pontos exploráveis.
- **Correção:** PB01.

### AP02 — Segredos e credenciais hardcoded

- **Sinais:** literais atribuídos a `SECRET_KEY`, `*_KEY`, `*_SECRET`, `*_TOKEN`, `password`, `pass`, `pwd`, `api_key`; prefixos `pk_live_`, `sk_live_`; usuário e senha de SMTP ou banco; seed que cria administrador com senha fixa e roda em qualquer ambiente; o mesmo segredo repetido em respostas ou logs. Grep: `(SECRET|KEY|TOKEN|PASS|PWD|password)\w*["']?\s*[:=]\s*["'][^"']{3,}`.
- **Não confundir:** leitura de `os.environ`/`process.env` sem valor padrão sensível; valores de exemplo em `.env.example`; dados de teste em fixtures que não rodam fora dos testes.
- **Correção:** PB02.

### AP03 — Armazenamento inseguro de senha

- **Sinais:** coluna `senha`/`password` gravada com o valor recebido; comparação de senha dentro do SQL (`WHERE email = ... AND senha = ...`); `md5`/`sha1`/`sha256` sem salt para senha; "criptografia" caseira (base64, laços, `substring`); senha padrão quando o campo vem vazio (`p || "123456"`).
- **Não confundir:** `werkzeug.security`, `bcrypt`, `argon2`, `hashlib.scrypt`, `crypto.scrypt`/`pbkdf2` com salt aleatório.
- **Correção:** PB03.

### AP04 — Exposição de dados sensíveis

- **Sinais:** serialização (`to_dict`, dict de resposta, `res.json`) com `password`/`senha`/hash; endpoints de health, debug ou info que devolvem segredos, caminhos ou flags internas; `print`/`console.log` com número de cartão, senha, token ou chave.
- **Não confundir:** campos sensíveis lidos apenas internamente e nunca devolvidos ou logados; contagens, versões e outros dados de negócio em endpoints de health ou info (não são sensíveis e continuam na resposta).
- **Correção:** PB04.

### AP05 — God Class / God Module

- **Sinais:** um arquivo ou classe que combina duas ou mais destas responsabilidades para vários domínios: acesso a dados (SQL/ORM), regras de negócio, roteamento ou registro de rotas, serialização, criação de schema e seed. Arquivos com mais de ~300 linhas atendendo três ou mais entidades; classes "Manager"/"Utils" com conexão de banco e rotas.
- **Severidade:** CRITICAL quando mistura dados e regras (com ou sem rotas) de vários domínios; HIGH quando restrito a um domínio.
- **Correção:** PB05.

### AP06 — Endpoint administrativo ou destrutivo desprotegido

- **Sinais:** rota administrativa pela definição da regra 3 do `SKILL.md` sem verificação de credencial: `admin` no caminho ou no nome do handler; reset, purge, drop ou exclusão em massa; execução de SQL ou código vindo da requisição (`execute(request...)`, `eval`, `exec`, `child_process` com entrada externa).
- **Não confundir:** CRUD de recurso individual e leituras comuns sem autenticação, mesmo de dados de outros usuários (ex.: `DELETE /items/:id`, listagem geral, relatório fora de `/admin`). São AP10.
- **Separar em findings:** execução arbitrária (pior caso), destruição de dados e exposição de relatório administrativo são findings distintos.
- **Correção:** PB06.

## HIGH

### AP07 — Regra de negócio fora da camada de serviço

- **Sinais:** handlers de rota ou controllers que calculam valores, aplicam regras de estado, validam regras de domínio ou disparam notificações; camada de dados com regras (descontos, estoque, totais); diretório `services/` vazio ou sem uso enquanto as rotas concentram a lógica.
- **Correção:** PB07.

### AP08 — Estado global mutável / conexão compartilhada

- **Sinais:** `global` dentro de funções; variáveis de módulo mutáveis alteradas em runtime (`cache = {}`, contadores); uma única conexão de banco no módulo compartilhada por todas as requisições, especialmente com `check_same_thread=False`.
- **Não confundir:** constantes; extensões com escopo por aplicação e sessão por requisição (`db = SQLAlchemy()`).
- **Correção:** PB08.

### AP09 — Acoplamento forte sem injeção de dependência

- **Sinais:** classes ou módulos que instanciam a própria infraestrutura (`new sqlite3.Database(...)` dentro do construtor, `get_db()` chamado de qualquer camada); ausência de composition root ou app factory; impossibilidade de trocar o banco num teste.
- **Correção:** PB08.

### AP10 — Autenticação ausente ou de fachada

- **Sinais:** login que não emite token nem sessão, ou que emite token previsível (`'token-' + id`) que nenhuma rota verifica; nenhuma rota exige identidade; rotas comuns que expõem ou alteram dados de outros usuários sem identificar quem pede (listagem geral, relatório fora de `/admin`, exclusão de recurso de terceiros); o cliente define o próprio `role`/`tipo`/`is_admin` no cadastro ou na atualização.
- **Correção:** PB06 só para as rotas administrativas da regra 3 do `SKILL.md` e para impedir que o cliente defina o próprio papel. Nas demais rotas, autenticação fica como recomendação e o finding fica pendente, porque mudaria o contrato.

### AP11 — Debug ligado e servidor exposto no entry point

- **Sinais:** `debug=True`, `app.config["DEBUG"] = True` ou `host="0.0.0.0"` fixos no código; tracebacks devolvidos ao cliente.
- **Correção:** PB02.

### AP12 — Exceção não tratada derruba o processo

- **Sinais (Node.js):** código que pode lançar exceção dentro de callbacks assíncronos (sqlite3, fs, timers) sem `try/catch`: métodos chamados sobre entrada não validada (`x.startsWith` quando `x` pode não ser string), uso do resultado ignorando `err` (`rows.length` com `rows` indefinido). No Express 4, uma exceção dentro de callback não chega ao middleware de erro e encerra o processo.
- **Severidade:** HIGH porque uma única requisição derruba o serviço para todos os clientes.
- **Correção:** PB09, PB11 e PB14.

## MEDIUM

### AP13 — Queries N+1 e agregações ineficientes

- **Sinais:** query dentro de `for`/`forEach`/`map` (`cursor.execute`, `Model.query.get`, `db.get` no laço); relacionamento lazy acessado no laço (`len(user.tasks)`); a mesma linha consultada duas vezes; vários `COUNT`/`SUM` separados onde um `GROUP BY` basta; todos os registros carregados para contar ou filtrar em memória.
- **Correção:** PB10.

### AP14 — Duplicação de código

- **Sinais:** funções quase idênticas (diferem num `WHERE`); blocos de serialização ou validação repetidos; lógica que já existe no model ou num helper reimplementada nas rotas; listas de valores válidos repetidas.
- **Correção:** PB05, PB07 e PB15.

### AP15 — Validação de entrada ausente ou inconsistente

- **Sinais:** uso direto de `request.get_json()[...]` ou `req.body.x` sem checar tipo, faixa e formato; comparações com valores que podem ser string (`priority < 1`); `int()`/`float()` sem tratamento; quantidade negativa ou zero aceita; regras diferentes entre criar e atualizar; e-mail sem verificação de formato.
- **Severidade:** se a falta de validação derruba o processo, registre como AP12 (HIGH).
- **Correção:** PB11.

### AP16 — Tratamento de erros não centralizado

- **Sinais:** `try/except Exception` repetido em cada handler devolvendo `str(e)`; `except:` sem tipo; `err` ignorado em callbacks; erros do cliente (JSON inválido, tipo errado) virando 500; ausência de `errorhandler` ou middleware de erro.
- **Correção:** PB09.

### AP17 — Integridade de dados e regras de estado

- **Sinais:** schema sem `NOT NULL`, `UNIQUE` ou `FOREIGN KEY` (no SQLite, também sem `PRAGMA foreign_keys = ON`); escrita em vários passos sem transação; exclusão que deixa registros órfãos ou responde sucesso sem verificar se o recurso existe; duplicidades aceitas (pedido ou matrícula repetidos); transições de estado livres; cálculos que ignoram o estado (somar cancelados no faturamento).
- **Correção:** PB12. Restrições que o código não declara (ex.: quais transições de status são permitidas) entram no relatório só como recomendação (regra 4 do `SKILL.md`).

### AP18 — CORS e middlewares inadequados

- **Sinais:** `CORS(app)` ou `cors()` sem lista de origens permitidas; middlewares globais desnecessários ou na ordem errada.
- **Correção:** PB16.

### AP19 — Efeitos colaterais na inicialização

- **Sinais:** função de conexão que também cria o schema e insere seed; `db.create_all()` ou DDL executados no import do módulo; seed que roda em qualquer ambiente; ausência de migrações.
- **Correção:** PB08.

### AP20 — Listagens sem paginação

- **Sinais:** `SELECT *` sem `LIMIT` em endpoints de listagem; `.all()` devolvido inteiro; `db.all` sem limite.
- **Correção:** PB17.

### AP21 — API deprecated

**Como detectar:**

1. Use as versões levantadas na Fase 1.
2. Procure no código os usos da tabela abaixo (e outros que você conheça com certeza).
3. Confirme que a deprecação vale para a versão em uso ou para versões posteriores da mesma dependência, e diga a partir de qual versão.
4. Se a aplicação emite aviso em runtime (`DeprecationWarning`, `LegacyAPIWarning`), cite-o.

| Stack / versão | Uso legado | Situação | Equivalente moderno |
|---|---|---|---|
| SQLAlchemy ≥ 2.0 | `Model.query.get(id)`, `session.query(M).get(id)` | legado; emite `LegacyAPIWarning` | `db.session.get(Model, id)` |
| SQLAlchemy ≥ 2.0 | `engine.execute(...)`, SQL em string pura no `execute` | removido | `connection.execute(text("..."))` |
| SQLAlchemy ≥ 2.0 | `sqlalchemy.ext.declarative.declarative_base` | deprecated | `sqlalchemy.orm.DeclarativeBase` |
| Python ≥ 3.12 | `datetime.utcnow()`, `datetime.utcfromtimestamp()`, inclusive `default=datetime.utcnow` | deprecated | `datetime.now(timezone.utc)` (ver PB13 sobre datas sem fuso) |
| Python ≥ 3.12 | `import distutils`, `import imp` | removidos | `setuptools`/`packaging`, `importlib` |
| Python ≥ 3.12 | adaptadores padrão de `datetime` no `sqlite3` | deprecated | adaptadores explícitos ou ISO 8601 em texto |
| Flask ≥ 2.3 | `@app.before_first_request` | removido | inicialização na app factory |
| Flask ≥ 2.3 | `flask.json.JSONEncoder`, `app.json_encoder` | removido | `app.json` (`DefaultJSONProvider`) |
| Flask ≥ 2.3 | `FLASK_ENV`, `app.config["ENV"]` | removido | `--debug` / `FLASK_DEBUG` |
| Flask ≥ 3.0 | `flask.Markup`, `flask.escape` | removido | `markupsafe.Markup`, `markupsafe.escape` |
| Werkzeug ≥ 3.0 | `werkzeug.urls.url_quote`, `url_parse`, `url_encode` | removido | `urllib.parse` |
| Node.js | `new Buffer(...)` | deprecated (DEP0005) | `Buffer.from()` / `Buffer.alloc()` |
| Node.js | `url.parse()` | deprecated (DEP0169) | `new URL()` |
| Node.js | `fs.exists()` | deprecated (DEP0034) | `fs.existsSync()` / `fs.promises.access()` |
| Node.js ≥ 22 | `crypto.createCipher()` | removido (DEP0106) | `crypto.createCipheriv()` |
| Express 4 | `req.param(name)` | deprecated | `req.params` / `req.body` / `req.query` |
| Express 4 | `res.send(status, body)`, `res.json(status, obj)`, `res.sendfile()` | deprecated | `res.status(s).send(b)`, `res.sendFile()` |
| Express 4 | `app.del()` | deprecated | `app.delete()` |
| Express 4 | `bodyParser()` genérico do pacote body-parser | deprecated | `express.json()` / `express.urlencoded()` |

- **Se nada for encontrado:** o relatório diz explicitamente "Nenhuma API deprecated encontrada no código-fonte". Pacotes deprecated na árvore de dependências não são AP21: registre-os como AP22.
- **Correção:** PB13.

### AP22 — Dependências vulneráveis, sem uso ou sem versão fixa

- **Sinais:** versões com falhas conhecidas; dependências declaradas e nunca importadas; dependências críticas sem versão fixa (ex.: SQLAlchemy puxado pelo Flask-SQLAlchemy); pacotes deprecated na árvore de instalação.
- **Ferramentas:** use apenas o que já existe, sem instalar nada: `npm audit` (lê o lockfile) ou `pip-audit`, se disponível. Sem ferramenta, reporte só o que dá para verificar (sem uso, sem versão fixa) e recomende a auditoria.
- **Severidade:** MEDIUM quando alguma falha está no caminho das requisições da aplicação; LOW quando nenhuma é alcançável (ex.: falha num recurso que a aplicação não usa, ou só na instalação).
- **Correção:** recomendação no resumo final; não atualize pacotes sem perguntar.

### AP23 — Callbacks aninhados e controle assíncrono manual

- **Sinais:** três ou mais níveis de callback; contadores manuais (`pending--`) para decidir quando responder; `self = this` para atravessar callbacks.
- **Correção:** PB14.

### AP24 — Responsabilidade no módulo errado

- **Sinais:** rotas de um recurso dentro do módulo de outro (CRUD de categorias no blueprint de relatórios); helpers com regra de domínio; models que conhecem HTTP.
- **Correção:** PB05.

### AP25 — Formato de resposta sem padrão

- **Sinais:** erros do mesmo tipo com formatos diferentes (`{"erro": ...}` em uns e `{"erro": ..., "sucesso": false}` em outros); texto puro em alguns erros e JSON em outros; status de sucesso para operações que não aconteceram; datas em formatos diferentes.
- **Correção:** PB09.

## LOW

### AP26 — Números e strings mágicos

- **Sinais:** literais com significado de negócio no meio do código (faixas, limites, percentuais, prefixos, listas de status, categorias e papéis); constantes definidas e não usadas enquanto os literais se repetem.
- **Correção:** PB15.

### AP27 — `print`/`console.log` como logging

- **Sinais:** `print(` ou `console.log(` em handlers e serviços; mensagens com dados pessoais (e-mail, nome).
- **Severidade:** se o log contém segredo, senha, token ou cartão, registre como AP04 (CRITICAL).
- **Correção:** PB15.

### AP28 — Nomes ruins e contexto ambíguo

- **Sinais:** identificadores de uma ou duas letras fora de laços curtos (`u`, `e`, `cc`); nomes que sombreiam builtins (`id`, `type`, `list`); `cursor2`, `data2`; `self = this` misturado com arrow functions.
- **Correção:** aplicada durante PB05 e PB14.

### AP29 — Código morto e imports não usados

- **Sinais:** imports sem uso; funções, métodos, constantes, serviços ou exports nunca referenciados.
- **Como confirmar:** Grep pelo nome em todo o projeto antes de registrar.
- **Correção:** remover durante a refatoração.

### AP30 — Configuração não secreta fixa no código

- **Sinais:** porta, host, caminho de banco, URI e flags como literais espalhados; caminho de banco relativo ao diretório de execução.
- **Correção:** PB02.

### AP31 — Header que revela a stack

- **Sinais:** Express sem `app.disable('x-powered-by')`; header `Server` com nome e versão.
- **Correção:** PB16.

### AP32 — Modelagem de dados frágil

- **Sinais:** listas guardadas em coluna de texto separada por vírgula; datas como texto livre; status sem enumeração nem validação no modelo.
- **Correção:** recomendação. Mudar o schema pode quebrar dados existentes e o contrato; aplique só se não alterar nenhum dos dois.
