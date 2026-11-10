# Análise de projeto — heurísticas da Fase 1

Objetivo: descrever o projeto com fatos verificáveis (stack, versões, banco, domínio, arquitetura, execução e endpoints) usando só leitura. Tudo o que for impresso na Fase 1 precisa ter vindo de um arquivo lido ou de um comando que não altera nada.

## 1. Inventário de arquivos

1. Liste os arquivos de código com Glob, por extensão: `**/*.py`, `**/*.js`, `**/*.mjs`, `**/*.cjs`, `**/*.ts`, `**/*.java`, `**/*.kt`, `**/*.go`, `**/*.rb`, `**/*.php`, `**/*.cs`.
2. Descarte tudo que estiver em diretórios ignorados (regra 4 do `SKILL.md`). O Glob pode devolver arquivos de `.venv/` e `node_modules/`: filtre explicitamente.
3. **Source files** = arquivos de código do próprio projeto, incluindo scripts auxiliares (`seed.py`, `migrate.js`) e `__init__.py`. Não entram manifestos, lockfiles, `.http`, README nem arquivos de dados.
4. **Linhas** = soma das linhas dos arquivos-fonte (`wc -l` ou a contagem do Read).
5. Registre à parte, sem contar como fonte: manifestos, lockfiles, `.env*`, `*.http`/`*.rest`, coleções Postman, README e arquivos de dados existentes (`*.db`, `*.sqlite*`, `instance/`).

## 2. Linguagem e versão

| Indício | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`, `*.py` | Python |
| `package.json`, `*.js`, `*.ts` | JavaScript/TypeScript (Node.js) |
| `pom.xml`, `build.gradle` | Java/Kotlin |
| `go.mod` | Go |
| `Gemfile` | Ruby |
| `composer.json` | PHP |
| `*.csproj` | C# |

Versão do runtime, nesta ordem: declaração no projeto (`requires-python`, `python_requires`, `.python-version`, `engines.node`, `.nvmrc`); versão do ambiente do projeto (`.venv/pyvenv.cfg`, linha `version`); versão do interpretador disponível (`python --version`, `node --version`).

## 3. Framework, versão e dependências

| Framework | Manifesto | Sinal no código |
|---|---|---|
| Flask | `flask` | `from flask import Flask`, `@app.route`, `Blueprint`, `add_url_rule` |
| Django | `django` | `settings.py`, `urls.py`, `INSTALLED_APPS` |
| FastAPI | `fastapi` | `FastAPI()`, `@app.get`, `APIRouter` |
| Express | `express` | `require('express')`, `app.get(`, `express.Router()` |
| Fastify / Koa / NestJS | `fastify` / `koa` / `@nestjs/core` | `fastify()`, `new Koa()`, `@Controller()` |

Versão, nesta ordem de preferência:

1. Versão fixada no manifesto (`flask==3.1.1`).
2. Versão resolvida no lockfile (`package-lock.json` → `"node_modules/express": { "version": ... }`).
3. Versão instalada: `.venv/Lib/site-packages/<pacote>-<versão>.dist-info` (Windows) ou `.venv/lib/python3.X/site-packages/...` (Unix); `node_modules/<pacote>/package.json`.

Quando a versão declarada e a instalada diferirem (ex.: `^4.18.2` → `4.22.1`), informe as duas. Liste as dependências diretas com versão e anote as que não têm versão fixa ou que nunca são importadas no código: elas alimentam o AP22 na Fase 2.

## 4. Banco de dados

| Sinal | Banco |
|---|---|
| `sqlite3.connect(...)`, URI `sqlite:///...` | SQLite em arquivo |
| `new sqlite3.Database(':memory:')`, `sqlite:///:memory:` | SQLite em memória |
| `SQLAlchemy(`, `db.Model`, `DeclarativeBase` | SQLAlchemy (o banco vem da URI) |
| `psycopg`, `postgresql://`, pacote `pg` | PostgreSQL |
| `pymysql`, `mysqlclient`, `mysql2` | MySQL |
| `pymongo`, `mongoose` | MongoDB |
| `sequelize`, `typeorm`, `prisma` | ORM Node (o banco vem da configuração) |

Tabelas: `CREATE TABLE <nome>`, `__tablename__ = '<nome>'`, classes de modelo (`db.Model`, `Base`), schemas Mongoose. Anote onde o arquivo de banco é criado: caminho relativo ao diretório de execução, ou pasta `instance/` (o Flask-SQLAlchemy 3 resolve `sqlite:///arquivo.db` para `instance/arquivo.db`).

## 5. Domínio

Deduza o domínio pelos nomes de tabelas e modelos, pelos prefixos de rota e pelos dados de seed. Escreva uma linha com o vocabulário do próprio projeto, por exemplo: "E-commerce (produtos, usuários, pedidos, relatório de vendas)".

## 6. Arquitetura (tipo A, B ou C)

Mapeie onde vive cada responsabilidade: roteamento, validação de entrada, regras de negócio, acesso a dados, serialização, configuração, tratamento de erros e inicialização (schema/seed). Depois classifique:

| Tipo | Critério | Sinais típicos |
|---|---|---|
| **A — Monolito/plano** | Roteamento, regras e acesso a dados nos mesmos arquivos ou em poucos módulos planos; não há diretórios de camada. | `app.py` + `models.py` + `controllers.py` com SQL; uma classe única com conexão de banco e registro de rotas. |
| **B — Camadas parciais** | Há diretórios de camada, mas as responsabilidades vazam: rotas com queries e regras, `services/` vazio ou sem uso, sem configuração nem tratamento de erros centralizados. | `routes/` chamando `Model.query` e calculando regras; helpers e serviços não usados. |
| **C — Em camadas** | Cada responsabilidade está na sua camada; os problemas são pontuais. | Rotas finas, serviços com as regras, modelos com o acesso a dados. |

No resumo, escreva o tipo e uma descrição curta, por exemplo: "A — monolítica: rotas, regras e SQL em 4 arquivos, sem camadas".

## 7. Execução

- **Entry point:** bloco `if __name__ == "__main__":` com `app.run`, campo `main` e `scripts.start` do `package.json`, `Procfile`, `CMD` do `Dockerfile`.
- **Comando de execução:** o que o README indica; na falta dele, o `scripts.start` ou o entry point.
- **Host e porta:** `app.run(host=..., port=...)`, `app.listen(...)`, objeto de configuração.
- **Interpretador:** Python → `.venv/Scripts/python` (Windows) ou `.venv/bin/python` (Unix); sem venv, `python3`/`python`, avisando que dependências podem faltar. Node → verifique se `node_modules/` existe.
- **Pré-requisitos:** scripts de seed ou migração citados no README (ex.: `python seed.py`), variáveis de ambiente, `.env.example`.
- **Scripts auxiliares que importam a aplicação** (ex.: `seed.py` com `from app import app, db`): anote, porque a Fase 3 precisa mantê-los funcionando.
- **Arquivos de dados já existentes:** anote. A Fase 3 nunca pode apagá-los.

## 8. Inventário de endpoints

| Framework | Onde procurar | Prefixos |
|---|---|---|
| Flask | `@app.route(path, methods=[...])` (sem `methods` = GET), `@<bp>.route`, `app.add_url_rule(path, endpoint, view, methods=[...])` | `Blueprint(..., url_prefix=)`, `register_blueprint(bp, url_prefix=)` |
| Express | `app.<verbo>(path, ...)`, `router.<verbo>(path, ...)` | `app.use('/prefixo', router)` |
| FastAPI | `@app.<verbo>(path)`, `@router.<verbo>(path)` | `APIRouter(prefix=)`, `include_router(prefix=)` |
| Django | `urls.py` (`path`, `re_path`) + views | `include()` |

Para cada endpoint, registre:

- método e caminho completo (com prefixos);
- handler (`arquivo:linha`);
- campos de entrada: chaves lidas do corpo (`request.get_json()`, `dados["x"]`, `data.get("x")`, `req.body.x`), da query string (`request.args.get`, `req.query`) e parâmetros de caminho;
- se é administrativo ou destrutivo (apaga dados, executa SQL ou comandos, expõe relatórios internos).

Procure também exemplos de requisição: `*.http`, `*.rest`, coleções Postman e comandos `curl` no README. Eles são a melhor fonte de payloads válidos para a Fase 3.

Formato da tabela impressa:

| Method | Path | Handler | Inputs | Admin/destrutivo |
|---|---|---|---|---|
| POST | /login | `routes/auth.py:12` | body: email, password | não |
| DELETE | /admin/items/:id | `routes/admin.py:40` | path: id | sim (destrutivo) |
