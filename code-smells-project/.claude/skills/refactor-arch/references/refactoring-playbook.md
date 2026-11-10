# Playbook de refatoração — Fase 3

Cada transformação diz quais anti-patterns resolve, mostra código antes e depois e lista cuidados para não quebrar o contrato. Os exemplos estão em Python/Flask e Node.js/Express e usam nomes genéricos; adapte-os ao vocabulário do projeto. Em outra stack, aplique o mesmo princípio com os recursos equivalentes do framework, respeitando as regras de `mvc-guidelines.md`.

## Ordem de aplicação

1. Estrutura, configuração e composition root — PB02, PB08.
2. Models com SQL seguro, consultas eficientes e transações — PB01, PB10, PB12.
3. Services com as regras de negócio — PB07, PB03.
4. Controllers com validação de entrada — PB11.
5. Routes (View) com o mesmo contrato — PB05.
6. Erros, middlewares e segurança — PB09, PB06, PB16, PB04.
7. Ajustes finais — PB13, PB14, PB15, PB17; remoção de código morto e dos módulos antigos.

Faça a checagem estática e uma subida rápida da aplicação ao fim das etapas 1, 5, 6 e 7 (ver `validation.md`).

| PB | Transformação | Resolve |
|---|---|---|
| PB01 | Parametrizar SQL | AP01 |
| PB02 | Configuração e segredos fora do código | AP02, AP11, AP30 |
| PB03 | Hash de senha com biblioteca já disponível | AP03 |
| PB04 | Dados sensíveis fora de respostas e logs | AP04 |
| PB05 | Decompor God Class/Module por domínio e camada | AP05, AP14, AP24, AP28 |
| PB06 | Proteger endpoints administrativos | AP06, AP10 |
| PB07 | Extrair regras de negócio para services | AP07, AP14 |
| PB08 | App factory, injeção de dependência e conexão por requisição | AP08, AP09, AP19 |
| PB09 | Tratamento de erros centralizado | AP12, AP16, AP25 |
| PB10 | Eliminar N+1 e agregar no banco | AP13 |
| PB11 | Validação de entrada na fronteira | AP12, AP15 |
| PB12 | Transações e integridade de dados | AP17 |
| PB13 | Substituir APIs deprecated | AP21 |
| PB14 | Callbacks para async/await | AP12, AP23, AP28 |
| PB15 | Constantes nomeadas e logging | AP26, AP27 |
| PB16 | CORS e headers por configuração | AP18, AP31 |
| PB17 | Paginação compatível com o contrato | AP20 |

---

## PB01 — Parametrizar SQL

**Resolve:** AP01.

Python, antes:

```python
cursor.execute("SELECT * FROM users WHERE email = '" + email + "' AND password = '" + password + "'")
cursor.execute("UPDATE orders SET status = '" + status + "' WHERE id = " + str(order_id))
```

Python, depois:

```python
row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()  # senha conferida no service (PB03)
conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
```

Filtros dinâmicos — só cláusulas fixas entram no texto; os valores vão nos parâmetros:

```python
clauses, params = [], []
if term:
    clauses.append("(name LIKE ? OR description LIKE ?)")
    params += [f"%{term}%", f"%{term}%"]
if category:
    clauses.append("category = ?")
    params.append(category)
where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
rows = conn.execute(f"SELECT * FROM products {where}", params).fetchall()
```

Node, antes e depois:

```js
db.get(`SELECT * FROM users WHERE email = '${email}'`, cb);          // antes
const user = await db.get('SELECT * FROM users WHERE email = ?', [email]); // depois
```

**Cuidados:** a f-string do filtro dinâmico só junta cláusulas escritas no código; nunca interpole valores vindos da requisição. Nomes de coluna ou de ordenação vindos de fora precisam passar por uma lista branca.

## PB02 — Configuração e segredos fora do código

**Resolve:** AP02, AP11, AP30.

Python, antes:

```python
app.config["SECRET_KEY"] = "minha-chave-123"
app.run(host="0.0.0.0", port=5000, debug=True)
db_path = "app.db"
```

Python, depois:

```python
# src/config/settings.py
import logging
import os
import secrets
from pathlib import Path

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parents[2]  # raiz do projeto


def _as_bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    def __init__(self, env=None):
        env = os.environ if env is None else env
        self.debug = _as_bool(env.get("APP_DEBUG"))
        self.host = env.get("APP_HOST", "127.0.0.1")
        self.port = int(env.get("APP_PORT", "5000"))
        self.database_path = env.get("DATABASE_PATH", str(BASE_DIR / "app.db"))
        self.seed_on_start = _as_bool(env.get("SEED_ON_START"), default=True)
        self.secret_key = env.get("SECRET_KEY") or self._ephemeral_secret()
        self.admin_token = env.get("ADMIN_TOKEN")
        self.cors_origins = [
            origin.strip()
            for origin in env.get("CORS_ORIGINS", "http://localhost:3000").split(",")
            if origin.strip()
        ]

    @staticmethod
    def _ephemeral_secret():
        logger.warning("SECRET_KEY não definida: usando chave aleatória temporária.")
        return secrets.token_hex(32)
```

```python
# app.py (raiz) — o comando `python app.py` continua igual
from src.app import create_app
from src.config.settings import Settings

settings = Settings()
app = create_app(settings)

if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
```

Node, antes e depois:

```js
// antes — src/utils.js
const config = { dbPass: 'senha_prod_123', paymentGatewayKey: 'pk_live_abc123', port: 3000 };

// depois — src/config/index.js
const crypto = require('crypto');

function loadConfig(env = process.env) {
  return {
    port: Number(env.PORT || 3000),
    databasePath: env.DATABASE_PATH || ':memory:',
    paymentGatewayKey: env.PAYMENT_GATEWAY_KEY || null, // sem chave, a integração fica desabilitada
    adminToken: env.ADMIN_TOKEN || null,
    sessionSecret: env.SESSION_SECRET || crypto.randomBytes(32).toString('hex'),
  };
}

module.exports = { loadConfig };
```

**Cuidados:** mantenha a porta original como padrão; o padrão de seed deve preservar o comportamento documentado do projeto; credenciais sem uso no código são removidas, não migradas; documente as variáveis em `.env.example`. Trocar o host padrão para `127.0.0.1` é mudança intencional.

## PB03 — Hash de senha com biblioteca já disponível

**Resolve:** AP03.

Python (o Werkzeug já vem com o Flask), antes:

```python
cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
user = cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password)).fetchone()
self.password = hashlib.md5(pwd.encode()).hexdigest()
```

Python, depois:

```python
from werkzeug.security import check_password_hash, generate_password_hash

conn.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, generate_password_hash(password)))

def authenticate(conn, email, password):
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if row is None or not check_password_hash(row["password"], password):
        return None
    return row
```

Sem Werkzeug, use `hashlib.scrypt` com salt de `os.urandom(16)` e compare com `hmac.compare_digest`.

Node, antes e depois:

```js
// antes
const hash = Buffer.from(pwd || '123456').toString('base64').substring(0, 10);

// depois
const crypto = require('crypto');

function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(password, salt, 64).toString('hex');
  return `${salt}:${hash}`;
}

function verifyPassword(password, stored) {
  const [salt, hash] = stored.split(':');
  const expected = Buffer.from(hash, 'hex');
  const candidate = crypto.scryptSync(password, salt, expected.length);
  return crypto.timingSafeEqual(candidate, expected);
}
```

**Cuidados:** o seed passa a gravar hashes, para que as credenciais de exemplo continuem funcionando no login; remova qualquer senha padrão (`|| "123456"`) e exija o campo; bancos já existentes com senhas em texto puro deixam de autenticar — avise no resumo final. Se a coluna tiver limite de tamanho, confira se o hash cabe.

## PB04 — Dados sensíveis fora de respostas e logs

**Resolve:** AP04.

Python, antes e depois:

```python
# antes
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password, "role": self.role}

@app.route("/health")
def health():
    return jsonify({"status": "ok", "secret_key": app.config["SECRET_KEY"], "debug": True})

# depois
def to_dict(self):
    return {"id": self.id, "email": self.email, "role": self.role}

def health():
    return jsonify({"status": "ok", "database": "connected"}), 200
```

Node, antes e depois:

```js
// antes
console.log(`Processando cartão ${card} na chave ${config.paymentGatewayKey}`);

// depois
const maskCard = (card) => `**** ${String(card).slice(-4)}`;
logger.info('Processando pagamento', { card: maskCard(card) });
```

**Cuidados:** remover campos sensíveis das respostas é mudança intencional — liste quais campos saíram. Mantenha as demais chaves.

## PB05 — Decompor God Class/Module por domínio e camada

**Resolve:** AP05, AP14, AP24, AP28.

Antes — um arquivo com acesso a dados, regra e serialização de vários domínios:

```python
# models.py
def get_product(id):
    row = get_db().cursor().execute("SELECT * FROM products WHERE id = " + str(id)).fetchone()
    return {"id": row["id"], "name": row["name"], "price": row["price"]} if row else None

def create_order(user_id, items): ...   # regra de estoque e total misturada com SQL
def sales_report(): ...                 # faixas de desconto misturadas com SQL
```

Depois — um arquivo por domínio em cada camada:

```python
# src/models/product_model.py
class ProductModel:
    def __init__(self, conn):
        self.conn = conn

    def find_by_id(self, product_id):
        row = self.conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        return dict(row) if row else None


# src/services/product_service.py
from src.utils.errors import AppError


class ProductService:
    def __init__(self, products):
        self.products = products

    def get(self, product_id):
        product = self.products.find_by_id(product_id)
        if product is None:
            raise AppError("Produto não encontrado", status=404)
        return product


# src/controllers/product_controller.py
from flask import jsonify

from src.database import get_db
from src.models.product_model import ProductModel
from src.services.product_service import ProductService


def _service():
    return ProductService(ProductModel(get_db()))  # dependências montadas por requisição


def get_product(product_id):
    return jsonify({"data": _service().get(product_id)}), 200


# src/routes/product_routes.py
from flask import Blueprint

from src.controllers import product_controller

bp = Blueprint("products", __name__)
bp.add_url_rule("/products/<int:product_id>", view_func=product_controller.get_product, methods=["GET"])
```

Node — mesma divisão:

```js
// src/models/productModel.js
class ProductModel {
  constructor(db) { this.db = db; }
  findById(id) { return this.db.get('SELECT * FROM products WHERE id = ?', [id]); }
}

// src/controllers/productController.js
function buildProductController({ productService }) {
  return {
    async getById(req, res) {
      const product = await productService.get(Number(req.params.id));
      res.status(200).json({ data: product });
    },
  };
}

// src/routes/productRoutes.js
function buildProductRoutes({ productController }) {
  const router = express.Router();
  router.get('/products/:id', asyncHandler(productController.getById));
  return router;
}
```

**Cuidados:** os caminhos, métodos e chaves das respostas continuam idênticos (o JSON acima é ilustrativo). Serialização repetida vira uma única função por entidade. Rotas que estavam no módulo de outro recurso vão para o módulo do próprio recurso, com o mesmo caminho. Ao terminar, apague os módulos antigos.

## PB06 — Proteger endpoints administrativos

**Resolve:** AP06, AP10.

Python:

```python
# src/middlewares/auth.py
import hmac
from functools import wraps

from flask import current_app, request

from src.utils.errors import AppError


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = (current_app.config.get("ADMIN_TOKEN") or "").encode()
        provided = request.headers.get("X-Admin-Token", "").encode()
        if not expected or not hmac.compare_digest(provided, expected):
            raise AppError("Acesso administrativo negado", status=401)
        return view(*args, **kwargs)
    return wrapper


# src/routes/admin_routes.py — mesmo caminho, agora protegido
bp.add_url_rule("/admin/reset-db", view_func=require_admin(admin_controller.reset_db), methods=["POST"])


# endpoints que executam SQL ou código recebido ficam desligados por padrão
@require_admin
def run_query():
    if not current_app.config.get("ALLOW_ADMIN_SQL"):
        raise AppError("Endpoint desabilitado", status=403)
    ...
```

Node:

```js
// src/middlewares/adminAuth.js
const crypto = require('crypto');
const { AppError } = require('../utils/errors');

function adminAuth(adminToken) {
  return (req, res, next) => {
    const provided = Buffer.from(req.get('X-Admin-Token') || '');
    const expected = Buffer.from(adminToken || '');
    const ok = Boolean(adminToken)
      && provided.length === expected.length
      && crypto.timingSafeEqual(provided, expected);
    return ok ? next() : next(new AppError('Acesso administrativo negado', 401));
  };
}

// uso: router.delete('/users/:id', adminAuth(config.adminToken), asyncHandler(userController.remove));
```

**Cuidados:** o caminho e o método continuam os mesmos; sem o header, a resposta passa a ser 401 (ou 403 para recurso desabilitado) — mudança intencional. Não adicione autenticação obrigatória às rotas públicas: registre essa ausência como pendência. Impeça que o cliente defina o próprio papel administrativo (campo `role`/`tipo` ignorado ou restrito a administradores) e liste a mudança.

## PB07 — Extrair regras de negócio para services

**Resolve:** AP07, AP14.

Antes — controller com efeitos colaterais e camada de dados com a regra:

```python
def create_order():
    data = request.get_json()
    result = models.create_order(data["user_id"], data["items"])  # valida estoque e calcula total com SQL
    print("ENVIANDO EMAIL: pedido criado")
    return jsonify(result), 201
```

Depois:

```python
# src/services/order_service.py
from src.utils.errors import AppError


class OrderService:
    def __init__(self, conn, orders, products, notifier):
        self.conn = conn
        self.orders = orders
        self.products = products
        self.notifier = notifier

    def create_order(self, user_id, items):
        lines, total = [], 0
        for item in items:
            product = self.products.find_by_id(item["product_id"])
            if product is None:
                raise AppError(f"Produto {item['product_id']} não encontrado", status=400)
            if product["stock"] < item["quantity"]:
                raise AppError(f"Estoque insuficiente para {product['name']}", status=400)
            lines.append((product, item["quantity"]))
            total += product["price"] * item["quantity"]

        with self.conn:  # transação: tudo ou nada (PB12)
            order_id = self.orders.insert(user_id, total)
            for product, quantity in lines:
                self.orders.insert_item(order_id, product["id"], quantity, product["price"])
                self.products.decrement_stock(product["id"], quantity)

        self.notifier.order_created(order_id, user_id)  # serviço de notificação com logging
        return {"order_id": order_id, "total": total}
```

**Cuidados:** preserve as mensagens e os status que o projeto já devolvia nos casos de erro existentes. Efeitos colaterais simulados (e-mail, SMS) viram um serviço de notificação com logging, chamado pelo service. Regras que existiam no model (ex.: `is_overdue`) passam a ser a única implementação usada.

## PB08 — App factory, injeção de dependência e conexão por requisição

**Resolve:** AP08, AP09, AP19.

Python com `sqlite3`, antes:

```python
db_connection = None

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("app.db", check_same_thread=False)
        # ... CREATE TABLE e seed aqui dentro
    return db_connection
```

Depois:

```python
# src/database.py
import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL
);
"""


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DATABASE_PATH"])
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(_error=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db(app, seed=True):
    app.teardown_appcontext(close_db)
    with app.app_context():
        conn = get_db()
        conn.executescript(SCHEMA)
        if seed:
            seed_if_empty(conn)


# src/app.py — composition root
from flask import Flask
from flask_cors import CORS

from src import database
from src.middlewares.error_handler import register_error_handlers
from src.routes import order_routes, product_routes


def create_app(settings):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.secret_key,
        DATABASE_PATH=settings.database_path,
        ADMIN_TOKEN=settings.admin_token,
    )
    CORS(app, origins=settings.cors_origins)
    database.init_db(app, seed=settings.seed_on_start)
    register_error_handlers(app)
    for routes in (product_routes, order_routes):
        app.register_blueprint(routes.bp)
    return app
```

Python com Flask-SQLAlchemy — o `create_all()` sai do import do módulo e vai para a factory:

```python
# antes — app.py, executado em todo import
db.init_app(app)
with app.app_context():
    db.create_all()

# depois
def create_app(settings):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.database_uri
    db.init_app(app)
    with app.app_context():
        db.create_all()
    register_error_handlers(app)
    ...
    return app
```

Node — dependências criadas uma vez e injetadas:

```js
// src/app.js
const express = require('express');
const { loadConfig } = require('./config');
const { Database } = require('./database/connection');
const { initSchema } = require('./database/schema');

function createApp({ db, config }) {
  const app = express();
  app.disable('x-powered-by');
  app.use(express.json());

  const products = new ProductModel(db);
  const productService = new ProductService({ products });
  const productController = buildProductController({ productService });

  app.use('/api', buildProductRoutes({ productController, adminAuth: adminAuth(config.adminToken) }));
  app.use(errorHandler);
  return app;
}

async function main() {
  const config = loadConfig();
  const db = await Database.open(config.databasePath);
  await initSchema(db);
  createApp({ db, config }).listen(config.port, () => logger.info(`Servidor na porta ${config.port}`));
}

if (require.main === module) {
  main().catch((err) => {
    logger.error('Falha ao iniciar', { error: err.stack });
    process.exit(1);
  });
}

module.exports = { createApp };
```

**Cuidados:** scripts que importam a aplicação (ex.: `from app import app, db`) continuam encontrando os mesmos nomes no mesmo módulo. Caches de módulo que nunca são lidos são removidos; se forem usados, viram uma classe injetada com limite de tamanho.

## PB09 — Tratamento de erros centralizado

**Resolve:** AP12, AP16, AP25.

Python, antes:

```python
def list_products():
    try:
        ...
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

Python, depois:

```python
# src/utils/errors.py
class AppError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


# src/middlewares/error_handler.py
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.utils.errors import AppError

logger = logging.getLogger(__name__)
ERROR_KEY = "error"  # use a chave que o projeto já usa (ex.: "erro") e mantenha campos fixos existentes


def _error(message, status):
    return jsonify({ERROR_KEY: message}), status


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return _error(err.message, err.status)

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return _error(err.description, err.code)

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("Erro inesperado")
        return _error("Erro interno do servidor", 500)
```

Node:

```js
// src/utils/errors.js
class AppError extends Error {
  constructor(message, status = 400) {
    super(message);
    this.status = status;
  }
}

// src/middlewares/asyncHandler.js — encaminha rejeições ao middleware de erro
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

// src/middlewares/errorHandler.js — registrado por último
function errorHandler(err, req, res, next) { // eslint-disable-line no-unused-vars
  if (err instanceof AppError) return res.status(err.status).json({ error: err.message });
  if (err.type === 'entity.parse.failed') return res.status(400).json({ error: 'JSON inválido' });
  logger.error('Erro inesperado', { error: err.stack });
  return res.status(500).json({ error: 'Erro interno do servidor' });
}
```

**Cuidados:** remova os `try/except` repetidos dos handlers; mantenha só os que tratam um caso específico. Mensagens internas nunca chegam ao cliente. Em Node, nenhum código pode lançar dentro de callback cru: use a API em Promises (PB14).

## PB10 — Eliminar N+1 e agregar no banco

**Resolve:** AP13.

Python, antes:

```python
for order in orders:
    items = conn.execute("SELECT * FROM order_items WHERE order_id = " + str(order["id"])).fetchall()
    for item in items:
        product = conn.execute("SELECT name FROM products WHERE id = " + str(item["product_id"])).fetchone()
```

Python, depois — uma query e agrupamento em memória:

```python
rows = conn.execute(
    """
    SELECT o.id, o.user_id, o.status, o.total, o.created_at,
           i.product_id, i.quantity, i.unit_price, p.name AS product_name
    FROM orders o
    LEFT JOIN order_items i ON i.order_id = o.id
    LEFT JOIN products p ON p.id = i.product_id
    WHERE (? IS NULL OR o.user_id = ?)
    ORDER BY o.id, i.id
    """,
    (user_id, user_id),
).fetchall()

orders = {}
for row in rows:
    order = orders.setdefault(row["id"], {
        "id": row["id"], "user_id": row["user_id"], "status": row["status"],
        "total": row["total"], "created_at": row["created_at"], "items": [],
    })
    if row["quantity"] is not None:
        order["items"].append({
            "product_id": row["product_id"],
            "product_name": row["product_name"] or "Desconhecido",
            "quantity": row["quantity"],
            "unit_price": row["unit_price"],
        })
result = list(orders.values())
```

Agregações num único `SELECT`:

```sql
SELECT COUNT(*) AS total_orders,
       SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending,
       COALESCE(SUM(CASE WHEN status <> 'cancelled' THEN total END), 0) AS revenue
FROM orders;
```

SQLAlchemy:

```python
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

tasks = db.session.execute(
    select(Task).options(selectinload(Task.user), selectinload(Task.category))
).scalars().all()

counts = dict(db.session.execute(select(Task.status, func.count(Task.id)).group_by(Task.status)).all())
```

Node — a mesma ideia com `await db.all(...)` e um `JOIN` em vez de queries dentro de `forEach`.

**Cuidados:** a resposta mantém ordem, formato e valores de fallback. Mantenha a mesma semântica dos números, a menos que o finding seja justamente um cálculo errado (ex.: somar pedidos cancelados) — nesse caso, a correção é mudança intencional.

## PB11 — Validação de entrada na fronteira

**Resolve:** AP12, AP15.

Python:

```python
# src/utils/validators.py
from src.utils.errors import AppError


def json_body(request):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise AppError("Corpo da requisição deve ser um objeto JSON", status=400)
    return data


def require_str(data, field, min_len=1, max_len=None):
    value = data.get(field)
    if not isinstance(value, str) or len(value.strip()) < min_len:
        raise AppError(f"'{field}' é obrigatório", status=400)
    if max_len is not None and len(value.strip()) > max_len:
        raise AppError(f"'{field}' deve ter no máximo {max_len} caracteres", status=400)
    return value.strip()


def require_number(data, field, minimum=None, integer=False):
    value = data.get(field)
    allowed = (int,) if integer else (int, float)
    if isinstance(value, bool) or not isinstance(value, allowed):
        raise AppError(f"'{field}' deve ser numérico", status=400)
    if minimum is not None and value < minimum:
        raise AppError(f"'{field}' deve ser maior ou igual a {minimum}", status=400)
    return value


def query_int(args, field, default=None):
    raw = args.get(field)
    if raw in (None, ""):
        return default
    try:
        return int(raw)
    except ValueError:
        raise AppError(f"'{field}' deve ser um número inteiro", status=400) from None


# uso no controller
def create_order():
    data = json_body(request)
    user_id = require_number(data, "user_id", minimum=1, integer=True)
    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise AppError("Pedido deve ter pelo menos 1 item", status=400)
    for item in items:
        if not isinstance(item, dict):
            raise AppError("Item inválido", status=400)
        require_number(item, "product_id", minimum=1, integer=True)
        require_number(item, "quantity", minimum=1, integer=True)
    return jsonify(_service().create_order(user_id, items)), 201
```

Node:

```js
function validateCheckout(body) {
  if (!body || typeof body !== 'object') throw new AppError('Corpo inválido', 400);
  const { name, email, courseId, card } = body;
  if (typeof name !== 'string' || !name.trim()) throw new AppError('Nome obrigatório', 400);
  if (typeof email !== 'string' || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) throw new AppError('E-mail inválido', 400);
  if (!Number.isInteger(Number(courseId))) throw new AppError('Curso inválido', 400);
  if (typeof card !== 'string' || !/^\d{13,19}$/.test(card)) throw new AppError('Cartão inválido', 400);
  return { name: name.trim(), email, courseId: Number(courseId), card };
}
```

**Cuidados:** os nomes dos campos de entrada são os do contrato original (os nomes acima são ilustrativos). Se o projeto já declara uma biblioteca de validação (marshmallow, pydantic, joi, zod), use-a. Mantenha as mensagens e status existentes; o alvo são os casos que hoje viram 500 ou passam sem validação. Recusar entrada que antes era aceita indevidamente é mudança intencional.

## PB12 — Transações e integridade de dados

**Resolve:** AP17.

Python (`sqlite3`):

```python
with conn:  # BEGIN … COMMIT, ou ROLLBACK se houver exceção
    order_id = conn.execute("INSERT INTO orders (user_id, total) VALUES (?, ?)", (user_id, total)).lastrowid
    cur = conn.execute(
        "UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?",
        (quantity, product_id, quantity),
    )
    if cur.rowcount == 0:
        raise AppError("Estoque insuficiente", status=400)
```

Existência antes de alterar ou excluir, e regras de estado explícitas:

```python
if self.orders.find_by_id(order_id) is None:
    raise AppError("Pedido não encontrado", status=404)

ALLOWED_TRANSITIONS = {"pending": {"approved", "cancelled"}, "approved": {"shipped", "cancelled"}}
```

Schema para bancos novos:

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    total REAL NOT NULL
);
```

Node — a transação usa a fila da conexão (PB14) para que requisições concorrentes não entrem na mesma transação:

```js
const enrollment = await db.transaction(async () => {
  const already = await enrollments.findByUserAndCourse(user.id, course.id);
  if (already) throw new AppError('Aluno já matriculado neste curso', 409);
  const { lastID } = await enrollments.create(user.id, course.id);
  await payments.create(lastID, course.price, 'PAID');
  return lastID;
});
```

**Cuidados:** `CREATE TABLE IF NOT EXISTS` não altera tabelas existentes; bancos antigos continuam com o schema antigo — avise no resumo. Ao ligar chaves estrangeiras, escolha a ação de exclusão compatível com o comportamento atual, para que exclusões que hoje funcionam continuem funcionando. Regras de transição só entram quando estão evidentes no domínio; caso contrário, ficam como recomendação.

## PB13 — Substituir APIs deprecated

**Resolve:** AP21.

SQLAlchemy:

```python
task = Task.query.get(task_id)          # antes — LegacyAPIWarning no SQLAlchemy 2.x
task = db.session.get(Task, task_id)    # depois
```

Datas em UTC — o banco guarda datas sem fuso; comparar valor com fuso e valor sem fuso lança `TypeError`. Use um helper que mantém o mesmo tipo dos dados existentes:

```python
# antes
created_at = db.Column(db.DateTime, default=datetime.utcnow)
if task.due_date < datetime.utcnow(): ...

# depois — utils/time.py
from datetime import datetime, timezone


def utc_now():
    """UTC atual sem fuso, compatível com os valores já gravados."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

created_at = db.Column(db.DateTime, default=utc_now)
if task.due_date < utc_now(): ...
```

Node:

```js
const buf = new Buffer(text);      // antes — DEP0005
const buf = Buffer.from(text);     // depois
```

**Cuidados:** troque todas as ocorrências, inclusive em scripts auxiliares (seed). Depois da troca, suba a aplicação com avisos ligados (`python -W default`) e confirme que o aviso sumiu.

## PB14 — Callbacks para async/await

**Resolve:** AP12, AP23, AP28.

```js
// src/database/connection.js — API em Promises, com fila de transações por conexão
const sqlite3 = require('sqlite3');

class Database {
  constructor(raw) {
    this.raw = raw;
    this.queue = Promise.resolve();
  }

  static open(path) {
    return new Promise((resolve, reject) => {
      const raw = new sqlite3.Database(path, (err) => (err ? reject(err) : resolve(new Database(raw))));
    });
  }

  run(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.raw.run(sql, params, function onRun(err) {
        if (err) return reject(err);
        return resolve({ lastID: this.lastID, changes: this.changes });
      });
    });
  }

  get(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
  }

  all(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });
  }

  exec(sql) {
    return new Promise((resolve, reject) => {
      this.raw.exec(sql, (err) => (err ? reject(err) : resolve()));
    });
  }

  transaction(work) {
    const result = this.queue.then(async () => {
      await this.exec('BEGIN');
      try {
        const value = await work();
        await this.exec('COMMIT');
        return value;
      } catch (err) {
        await this.exec('ROLLBACK');
        throw err;
      }
    });
    this.queue = result.catch(() => undefined);
    return result;
  }
}

module.exports = { Database };
```

Antes e depois de um fluxo:

```js
// antes — cinco níveis de callback, err ignorado, self = this
db.get('SELECT * FROM courses WHERE id = ?', [cid], (err, course) => {
  db.get('SELECT id FROM users WHERE email = ?', [email], (err, user) => {
    db.run('INSERT INTO enrollments ...', [user.id, cid], function (err) {
      self.db.run('INSERT INTO payments ...', [this.lastID], (err) => { /* ... */ });
    });
  });
});

// depois — service
async checkout({ courseId, email, name, password, card }) {
  const course = await this.courses.findActiveById(courseId);
  if (!course) throw new AppError('Curso não encontrado', 404);
  const user = (await this.users.findByEmail(email)) || (await this.users.create({ name, email, password }));
  return this.db.transaction(() => this.enroll(user, course, card));
}
```

**Cuidados:** o `function` com `this.lastID` fica só dentro do wrapper; o código de negócio não usa mais `self = this`. Todo handler assíncrono passa pelo `asyncHandler` (PB09).

## PB15 — Constantes nomeadas e logging

**Resolve:** AP26, AP27.

```python
# antes
if revenue > 10000:
    discount = revenue * 0.1
elif revenue > 5000:
    discount = revenue * 0.05
print("Pedido criado para " + email)

# depois
DISCOUNT_TIERS = ((10_000, 0.10), (5_000, 0.05), (1_000, 0.02))  # (faturamento mínimo, desconto)


def discount_for(revenue):
    for threshold, rate in DISCOUNT_TIERS:
        if revenue > threshold:
            return revenue * rate
    return 0

logger = logging.getLogger(__name__)
logger.info("Pedido %s criado", order_id)  # sem e-mail, senha ou cartão
```

```python
# src/utils/logger.py — configurado uma vez na composition root
import logging


def configure_logging(debug=False):
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
```

```js
// src/utils/logger.js
const logger = {
  info: (msg, meta = {}) => console.log(JSON.stringify({ level: 'info', msg, ...meta })),
  error: (msg, meta = {}) => console.error(JSON.stringify({ level: 'error', msg, ...meta })),
};
module.exports = { logger };
```

**Cuidados:** constantes que já existem no projeto e não eram usadas passam a ser a fonte única. Listas de valores válidos ficam junto do domínio que as usa (model ou service).

## PB16 — CORS e headers por configuração

**Resolve:** AP18, AP31.

```python
CORS(app)                                    # antes — qualquer origem
CORS(app, origins=settings.cors_origins)     # depois — origens vindas de CORS_ORIGINS
```

```js
const app = express();
app.disable('x-powered-by');                 // remove o header que revela a stack
```

**Cuidados:** restringir origens é mudança intencional (clientes de navegador de outras origens precisam ser configurados). Requisições sem navegador, como `curl`, não são afetadas.

## PB17 — Paginação compatível com o contrato

**Resolve:** AP20.

```python
DEFAULT_LIMIT, MAX_LIMIT = 100, 500


def pagination(args):
    limit = query_int(args, "limit", DEFAULT_LIMIT)
    offset = query_int(args, "offset", 0)
    if limit < 1 or offset < 0:
        raise AppError("Parâmetros de paginação inválidos", status=400)
    return min(limit, MAX_LIMIT), offset

rows = conn.execute("SELECT * FROM products ORDER BY id LIMIT ? OFFSET ?", (limit, offset)).fetchall()
```

```python
# SQLAlchemy
tasks = db.session.execute(select(Task).order_by(Task.id).limit(limit).offset(offset)).scalars().all()
```

**Cuidados:** a resposta mantém o formato (uma lista continua lista; metadados de paginação só entram se a resposta já for um objeto). O limite padrão precisa ser alto o bastante para não alterar as respostas atuais; ainda assim, liste a paginação como mudança intencional.
