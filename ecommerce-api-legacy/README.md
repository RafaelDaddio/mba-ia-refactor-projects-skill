# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Configuração e credenciais

A configuração vem de variáveis de ambiente, descritas em `.env.example` (o projeto não carrega arquivos `.env`).

- `GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem o header `X-Admin-Token` com o valor de `ADMIN_TOKEN`. Sem a variável definida, as duas rotas respondem 401.
- `POST /api/checkout` com um e-mail novo cria a conta e exige `pwd`. Com um e-mail já cadastrado, exige a senha da conta em `pwd` ou o `X-Admin-Token`.

```bash
ADMIN_TOKEN=um-token-secreto npm start
```
