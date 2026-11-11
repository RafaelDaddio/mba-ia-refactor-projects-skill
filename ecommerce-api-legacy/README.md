# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

A configuração vem de variáveis de ambiente, documentadas em `.env.example`. O relatório em `/api/admin/financial-report` exige o header `X-Admin-Token` com o valor de `ADMIN_TOKEN`, por exemplo: `ADMIN_TOKEN=troque-me npm start`.

Exemplos de requisições estão em `api.http`.
