```text
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js v24.18.0) + Express 4.22.1
Files:   3 analyzed | ~180 lines of code
```

## Summary

CRITICAL: 5 | HIGH: 6 | MEDIUM: 11 | LOW: 7

## Findings

### F01 · [CRITICAL] Relatório financeiro administrativo exposto sem autenticação
- **Anti-pattern:** AP06 — Endpoint administrativo ou destrutivo desprotegido
- **File:** `src/AppManager.js:80-129`
- **Description:** `GET /api/admin/financial-report` tem `admin` no caminho. Para cada curso, devolve a receita e a lista de alunos com o valor pago (`src/AppManager.js:90`, `src/AppManager.js:112-115`). Não verifica nenhuma credencial, e `src/app.js:5-10` não registra middleware de administração.
- **Impact:** Qualquer cliente anônimo obtém o faturamento por curso e o nome de cada aluno com o valor que pagou.
- **Recommendation:** Exigir credencial administrativa (token lido do ambiente e enviado em header) antes do handler. Caminho e formato da resposta continuam os mesmos (PB06).

### F02 · [CRITICAL] Número do cartão e chave do gateway gravados em log
- **Anti-pattern:** AP04 — Exposição de dados sensíveis
- **File:** `src/AppManager.js:45`
- **Description:** Cada checkout executa ``console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`)``. A linha grava o número completo recebido em `card` e a chave `pk_live_...` de `src/utils.js:4`.
- **Impact:** Quem tem acesso aos logs obtém números de cartão completos e a chave de produção do gateway. Os dados de cartão passam a ficar armazenados fora de qualquer controle.
- **Recommendation:** Tirar o cartão e a chave do log. Se for preciso registrar algo, usar só os 4 últimos dígitos (PB04).

### F03 · [CRITICAL] Chave live de pagamento e credenciais de banco e SMTP fixas no código
- **Anti-pattern:** AP02 — Segredos e credenciais hardcoded
- **File:** `src/utils.js:1-7`
- **Description:** O objeto `config` traz `dbUser: "admin_master"`, `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"` e `smtpUser`. Pelo Grep, `dbUser`, `dbPass` e `smtpUser` não são lidos em nenhum ponto do projeto. `paymentGatewayKey` só é usada no log de `src/AppManager.js:45` (F02).
- **Impact:** Quem acessa o repositório obtém a senha de banco de produção e a chave live do gateway. Para trocar os segredos é preciso alterar o código, e eles continuam no histórico do git.
- **Recommendation:** Ler os segredos de variáveis de ambiente, sem valor padrão sensível, num módulo de configuração, e remover os que não são usados (PB02). A rotação das credenciais já expostas no histórico fica como pendência fora do código.

### F04 · [CRITICAL] Senha com hash caseiro reversível, senha padrão fixa e seed em texto puro
- **Anti-pattern:** AP03 — Armazenamento inseguro de senha
- **File:** `src/utils.js:17-23`, `src/AppManager.js:68`, `src/AppManager.js:18`
- **Description:** `badCrypto` repete 10.000 vezes os 2 primeiros caracteres do base64 da senha e corta em 10. O resultado depende só do primeiro caractere e de 4 bits do segundo: `"123"` e `"123456"` geram o mesmo valor `MTMTMTMTMT` (confirmado com `node -e`). O checkout chama `badCrypto(p || "123456")`, então uma conta criada sem `pwd` recebe a senha conhecida `123456`. O seed grava `'123'` em texto puro na coluna `pass`.
- **Impact:** Quem obtém a tabela `users` recupera as senhas, ou senhas equivalentes, na hora. Contas criadas sem `pwd` têm senha pública.
- **Recommendation:** Gravar com `crypto.scrypt` e salt aleatório (biblioteca padrão do Node), no checkout e no seed. Na falta de `pwd`, gerar um valor aleatório que ninguém conhece em vez de uma senha fixa (PB03). Tornar `pwd` obrigatório mudaria o contrato do checkout e fica como pendência.

### F05 · [CRITICAL] AppManager concentra conexão, schema, seed, rotas, SQL e regras
- **Anti-pattern:** AP05 — God Class / God Module
- **File:** `src/AppManager.js:4-139`
- **Description:** A mesma classe faz quatro coisas:
  - cria a conexão (`:7`);
  - cria as 5 tabelas e insere o seed a cada boot (`:10-23`);
  - registra as 3 rotas num único método de ~110 linhas (`:25-138`);
  - executa o SQL inline e as regras de checkout, faturamento e exclusão para usuários, cursos, matrículas, pagamentos e auditoria.

  Não há camadas de model, service ou controller.
- **Impact:** Nenhuma regra pode ser testada sem subir o Express e o banco. Qualquer mudança em um domínio mexe no mesmo método.
- **Recommendation:** Separar em configuração, banco (conexão e schema/seed), models/repositórios, services, controllers e rotas, com composition root em `src/app.js` (PB05).

### F06 · [HIGH] `card` ou `pwd` não textuais derrubam o processo
- **Anti-pattern:** AP12 — Exceção não tratada derruba o processo
- **File:** `src/AppManager.js:46`, `src/AppManager.js:68` → `src/utils.js:20`, `src/AppManager.js:92-93`
- **Description:** A validação de `:35` só confere presença. As falhas abaixo foram confirmadas com `node -e`:
  - Com `"card": 4111222233334444` (número), `cc.startsWith("4")` lança `TypeError: ... startsWith is not a function` dentro do callback do sqlite3.
  - Com `"pwd": 123` e um e-mail novo, `Buffer.from(123)` lança `ERR_INVALID_ARG_TYPE`.

  No relatório, `enrollments.length` é lido sem checar `err` (`:92-93`). No Express 4, uma exceção dentro de callback do sqlite3 não chega ao Express e encerra o processo.
- **Impact:** Uma única requisição anônima derruba a API para todos os clientes.
- **Recommendation:** Validar os tipos antes de usar e devolver 400 (PB11). Converter o fluxo para async/await com propagação de erro (PB14) e um middleware de erro central (PB09).

### F07 · [HIGH] Qualquer cliente exclui qualquer usuário
- **Anti-pattern:** AP10 — Autenticação ausente ou de fachada
- **File:** `src/AppManager.js:131-137`
- **Description:** `DELETE /api/users/:id` apaga o usuário do id informado sem identificar quem faz a requisição. Nenhuma rota tem login, token ou sessão.
- **Impact:** Um cliente anônimo apaga contas de outros usuários, e os registros dessas contas ficam órfãos (F13).
- **Recommendation:** Exigir autenticação e verificar que quem pede é o dono da conta ou um administrador. Pela regra 3, essa rota é CRUD de recurso individual: a mudança alteraria o contrato e fica como pendência.

### F08 · [HIGH] Checkout pede senha, mas não a confere quando o e-mail já existe
- **Anti-pattern:** AP10 — Autenticação ausente ou de fachada
- **File:** `src/AppManager.js:40`, `src/AppManager.js:73-75`
- **Description:** Quando `eml` já existe, o handler segue com `user.id` sem comparar `pwd` com a senha gravada. `pwd` só é usado ao criar uma conta (`:68`).
- **Impact:** Quem conhece o e-mail de alguém cria matrículas e pagamentos na conta dessa pessoa. O campo `pwd` dá a falsa impressão de que existe verificação.
- **Recommendation:** Verificar a senha da conta existente ou exigir autenticação prévia. O código não declara essa regra e a mudança alteraria as respostas do checkout, então fica como pendência (regra 4).

### F09 · [HIGH] Regras de negócio dentro dos handlers de rota
- **Anti-pattern:** AP07 — Regra de negócio fora da camada de serviço
- **File:** `src/AppManager.js:46-48`, `src/AppManager.js:66-72`, `src/AppManager.js:108-115`
- **Description:** O handler do checkout decide a aprovação do pagamento (`cc.startsWith("4") ? "PAID" : "DENIED"`), cria a conta quando o e-mail não existe e encadeia matrícula, pagamento e auditoria. O handler do relatório soma a receita e monta a lista de alunos.
- **Impact:** As regras de pagamento e faturamento não podem ser testadas nem reutilizadas sem HTTP. Mudar a regra de aprovação exige editar o handler.
- **Recommendation:** Mover as regras para services de checkout, relatório e usuário e deixar os controllers só com entrada e saída HTTP (PB07).

### F10 · [HIGH] Conexão de banco criada dentro da classe, sem injeção
- **Anti-pattern:** AP09 — Acoplamento forte sem injeção de dependência
- **File:** `src/AppManager.js:7`, `src/app.js:8-10`
- **Description:** O construtor faz `new sqlite3.Database(':memory:')` e todas as rotas usam `this.db` diretamente. `app.js` não tem como fornecer outro banco.
- **Impact:** Não é possível trocar o banco num teste nem reutilizar as regras com outra conexão.
- **Recommendation:** Criar a conexão no composition root e injetá-la nos repositórios e services (PB08).

### F11 · [HIGH] Cache global mutável que cresce e nunca é lido
- **Anti-pattern:** AP08 — Estado global mutável / conexão compartilhada
- **File:** `src/utils.js:9`, `src/utils.js:12-15`, `src/AppManager.js:59`
- **Description:** `globalCache` é um objeto de módulo que ganha a chave `last_checkout_<userId>` a cada checkout. É exportado, mas o Grep não encontra nenhum módulo que o leia.
- **Impact:** Estado compartilhado entre requisições que ganha uma chave por usuário comprador, sem limite, sem expiração e sem uso.
- **Recommendation:** Remover o cache e o `logAndCache` (PB08).

### F12 · [MEDIUM] A mesma compra pode ser cobrada duas vezes, e o e-mail pode se repetir
- **Anti-pattern:** AP17 — Integridade de dados e regras de estado
- **File:** `src/AppManager.js:50-55`, `src/AppManager.js:40`, `src/AppManager.js:66-72`, `src/AppManager.js:12-14`
- **Description:** O checkout não verifica se o usuário já está matriculado no curso: repetir a requisição cria outra matrícula e outro pagamento `PAID`. O e-mail é a chave de busca do usuário (`:40`), mas `users.email` não é `UNIQUE`, e a busca e o insert (`:69`) são passos separados. Assim, dois checkouts simultâneos com o mesmo e-mail novo criam dois usuários. `enrollments` também não tem `UNIQUE (user_id, course_id)`.
- **Impact:** O mesmo curso é cobrado em dobro. Usuários duplicados tornam ambígua a busca por e-mail.
- **Recommendation:** Rejeitar a matrícula repetida com 409 antes de cobrar (mudança intencional). Declarar `UNIQUE` em `users.email` e em `(user_id, course_id)` e tratar o conflito na criação do usuário. O banco é recriado a cada boot, então o schema pode mudar sem migração (PB12).

### F13 · [MEDIUM] Excluir um usuário deixa matrículas e pagamentos órfãos e confirma ids inexistentes
- **Anti-pattern:** AP17 — Integridade de dados e regras de estado
- **File:** `src/AppManager.js:131-137`, `src/AppManager.js:12-16`
- **Description:** O handler executa só `DELETE FROM users`, e a própria resposta admite: "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco." O schema não declara `FOREIGN KEY` nem ativa `PRAGMA foreign_keys`. O handler ignora o `err` e o número de linhas afetadas, então um id inexistente recebe a mesma mensagem de sucesso.
- **Impact:** Matrículas e pagamentos sem dono continuam no relatório financeiro como aluno `Unknown` (`:113`). O cliente recebe confirmação de exclusões que não aconteceram.
- **Recommendation:** Excluir pagamentos, matrículas e usuário numa transação, declarar as chaves estrangeiras e devolver 404 quando o usuário não existe. A mensagem de sucesso, que hoje anuncia a sujeira, deve ser corrigida (PB12).

### F14 · [MEDIUM] Checkout grava matrícula, pagamento e auditoria sem transação
- **Anti-pattern:** AP17 — Integridade de dados e regras de estado
- **File:** `src/AppManager.js:50-61`
- **Description:** São três `INSERT` encadeados em callbacks, sem `BEGIN/COMMIT`. Se o insert do pagamento falha (`:55`), a matrícula já gravada fica sem pagamento. O erro do insert de auditoria é ignorado (`:57`).
- **Impact:** Uma matrícula sem pagamento aparece no relatório com `paid: 0` e dá acesso ao curso sem cobrança registrada.
- **Recommendation:** Executar os três inserts numa transação serializada na conexão (PB12).

### F15 · [MEDIUM] Erros ignorados, mascarados ou devolvidos com stack trace
- **Anti-pattern:** AP16 — Tratamento de erros não centralizado
- **File:** `src/AppManager.js:38`, `src/AppManager.js:57`, `src/AppManager.js:92`, `src/AppManager.js:104-106`, `src/AppManager.js:133`, `src/app.js:5-14`
- **Description:** Cada callback trata `err` de um jeito. Um erro de banco na busca do curso vira 404 (`:38`). O `err` é ignorado no insert de auditoria, nas consultas do relatório e no `DELETE`. Não há middleware de erro: um JSON malformado cai no handler padrão do Express, que fora de `NODE_ENV=production` devolve HTML com `err.stack` (`node_modules/finalhandler/index.js:176-178`).
- **Impact:** Falhas de banco chegam ao cliente como "curso não encontrado" ou como sucesso. O stack trace expõe caminhos internos do servidor.
- **Recommendation:** Criar um middleware de erro central que responda em JSON, usar erros de domínio com status e propagar `err` (PB09).

### F16 · [MEDIUM] Dependências com vulnerabilidades conhecidas e pacotes deprecated
- **Anti-pattern:** AP22 — Dependências vulneráveis, sem uso ou sem versão fixa
- **File:** `package.json:10-11`, `package-lock.json`
- **Description:** `npm audit --omit=dev` reporta 13 vulnerabilidades (2 critical, 8 high, 1 moderate, 2 low). Elas se dividem em duas cadeias, e as versões são declaradas com `^`.
  - **Cadeia do Express 4.22.1**, no caminho das requisições:
    - `body-parser@1.20.4`: DoS com corpo comprimido. O `express.json()` de `src/app.js:6` descomprime por padrão.
    - `qs@6.14.2`.
    - `path-to-regexp@0.1.12`.
    - `proxy-addr@2.0.7`: só explorável com `trust proxy`, que não está configurado.
  - **Cadeia de instalação do sqlite3 5.1.7:**
    - Vulneráveis: `node-gyp@8.4.1`, `tar@6.2.1`, `@tootallnate/once`, `ip-address@10.1.0` e `brace-expansion@1.1.12`.
    - Marcados como deprecated no lockfile: `tar@6.2.1`, `prebuild-install@7.1.3` e os opcionais `glob@7.2.3`, `inflight@1.0.6`, `rimraf@3.0.2`, `npmlog@6.0.2`, `gauge@4.0.4`, `are-we-there-yet@3.0.1` e `@npmcli/move-file@1.1.2`.
- **Impact:** A API fica exposta a DoS pelo corpo da requisição. A instalação das dependências nativas também tem risco.
- **Recommendation:** `npm audit fix` resolve a cadeia do Express sem quebra. Para o sqlite3, avaliar a versão 6, que o npm marca como mudança com quebra. Atualizar pacotes depende de aprovação e fica como pendência.

### F17 · [MEDIUM] Entrada do checkout validada só por presença
- **Anti-pattern:** AP15 — Validação de entrada ausente ou inconsistente
- **File:** `src/AppManager.js:29-35`, `src/AppManager.js:132`
- **Description:** A única validação é `if (!u || !e || !cid || !cc)`.
  - Tipo e formato de `usr`, `eml`, `c_id` e `card` não são conferidos, e `pwd` não é validado.
  - Um `usr` objeto é gravado como o texto `[object Object]` (comportamento do driver confirmado com `node -e` num banco em memória). `eml` aceita qualquer texto.
  - O `id` de `DELETE /api/users/:id` vai direto ao SQL.
- **Impact:** O banco recebe dados inconsistentes. Os casos que derrubam o processo estão no F06.
- **Recommendation:** Validar os tipos num único ponto e devolver 400 (PB11), aceitando `c_id` numérico em texto para não quebrar os clientes atuais. Regras de formato que o código não declara, como e-mail e número de cartão, ficam como recomendação (regra 4).

### F18 · [MEDIUM] Consultas N+1 no relatório financeiro
- **Anti-pattern:** AP13 — Queries N+1 e agregações ineficientes
- **File:** `src/AppManager.js:83-106`
- **Description:** O relatório faz 1 consulta de cursos, 1 de matrículas por curso e, para cada matrícula, 1 de usuário e 1 de pagamento: 1 + C + 2E consultas.
- **Impact:** O tempo do relatório cresce linearmente com o número de matrículas. Com 10 mil matrículas, são mais de 20 mil consultas por requisição.
- **Recommendation:** Uma consulta com `LEFT JOIN` de cursos, matrículas, usuários e pagamentos, agregada no service (PB10).

### F19 · [MEDIUM] Callbacks aninhados e contadores manuais
- **Anti-pattern:** AP23 — Callbacks aninhados e controle assíncrono manual
- **File:** `src/AppManager.js:37-77`, `src/AppManager.js:86-122`, `src/AppManager.js:26`
- **Description:**
  - O checkout aninha cinco callbacks de banco.
  - O relatório decide quando responder com `coursesPending--` e `enrPending--`, e o bloco "adiciona ao array, decrementa e responde" está duplicado (`:95-99` e `:118-122`).
  - `const self = this` convive com arrow functions e `function`, usada para ler `this.lastID`.
  - O curso entra em `report` quando suas consultas terminam: um curso sem matrículas entra antes de um curso cujas consultas de alunos ainda estão pendentes.
- **Impact:** O fluxo é difícil de seguir. Um caminho que esqueça de decrementar deixa a requisição sem resposta, e a ordem dos cursos no relatório depende da ordem de conclusão das consultas.
- **Recommendation:** Promisificar o acesso ao banco e reescrever com async/await (PB14).

### F20 · [MEDIUM] Respostas em texto puro e JSON misturados
- **Anti-pattern:** AP25 — Formato de resposta sem padrão
- **File:** `src/AppManager.js:35`, `src/AppManager.js:38`, `src/AppManager.js:41`, `src/AppManager.js:48`, `src/AppManager.js:51`, `src/AppManager.js:55`, `src/AppManager.js:70`, `src/AppManager.js:84`, `src/AppManager.js:135`
- **Description:** O checkout e o relatório respondem sucesso em JSON. Todos os erros saem em texto puro ("Bad Request", "Curso não encontrado", "Erro DB", "Pagamento recusado", …), misturando inglês e português, e a exclusão responde com texto.
- **Impact:** Os clientes precisam tratar dois formatos e não têm um campo estável para identificar o erro.
- **Recommendation:** Responder os erros em JSON, num formato único, pelo middleware de erro (PB09). As respostas de sucesso mantêm o formato atual (contrato).

### F21 · [MEDIUM] `utils.js` mistura configuração, cache e hash de senha
- **Anti-pattern:** AP24 — Responsabilidade no módulo errado
- **File:** `src/utils.js:1-25`
- **Description:** O módulo genérico "utils" guarda a configuração com segredos, o cache global, o log de cache e a função de hash de senha. `AppManager` importa tudo junto (`src/AppManager.js:2`).
- **Impact:** Responsabilidades de segurança e de configuração ficam escondidas num módulo genérico, e qualquer import dele carrega os segredos.
- **Recommendation:** Separar a configuração e o hash de senha em módulos próprios. O cache sai com o F11 (PB05).

### F22 · [MEDIUM] Campo `paid` do relatório ignora o status do pagamento
- **Anti-pattern:** AP17 — Integridade de dados e regras de estado
- **File:** `src/AppManager.js:108-115`
- **Description:** A receita soma só os pagamentos `PAID` (`:108-110`), mas cada aluno recebe `paid: payment.amount` qualquer que seja o status (`:114`).
- **Impact:** Hoje não há diferença visível, porque só pagamentos `PAID` são gravados: o `DENIED` retorna antes do insert (`:48`). Um pagamento com outro status apareceria como pago para o aluno sem entrar na receita.
- **Recommendation:** Aplicar a mesma condição de status nos dois cálculos, no service (PB07).

### F23 · [LOW] Regras e status como literais
- **Anti-pattern:** AP26 — Números e strings mágicos
- **File:** `src/AppManager.js:46`, `src/AppManager.js:48`, `src/AppManager.js:108`, `src/AppManager.js:21`, `src/AppManager.js:68`, `src/AppManager.js:37`, `src/utils.js:19`
- **Description:** O prefixo de aprovação `"4"`, os status `'PAID'` e `'DENIED'` repetidos em quatro pontos, a senha padrão `"123456"`, o filtro `active = 1` e o laço de `10000` aparecem como literais.
- **Impact:** A regra de aprovação e os status ficam espalhados, e mudar um deles exige caçar cada ocorrência.
- **Recommendation:** Substituir por constantes nomeadas (PB15).

### F24 · [LOW] Código e configuração sem uso
- **Anti-pattern:** AP29 — Código morto e imports não usados
- **File:** `src/AppManager.js:2`, `src/utils.js:10`, `src/utils.js:25`, `src/utils.js:2-3`, `src/utils.js:5`
- **Description:** Confirmado com Grep:
  - `totalRevenue` é importado e nunca usado, e `utils.js` nunca o altera.
  - `globalCache` é exportado e não é importado.
  - `dbUser`, `dbPass` e `smtpUser` não são lidos.
- **Impact:** O código sugere um faturamento acumulado e integrações que não existem.
- **Recommendation:** Remover.

### F25 · [LOW] Header X-Powered-By revela a stack
- **Anti-pattern:** AP31 — Header que revela a stack
- **File:** `src/app.js:5-6`
- **Description:** O app não chama `app.disable('x-powered-by')`, e o Express 4 envia `X-Powered-By: Express` por padrão.
- **Impact:** Facilita o fingerprinting da stack e a busca por vulnerabilidades específicas, como as do F16.
- **Recommendation:** Desabilitar o header (PB16).

### F26 · [LOW] Porta e caminho do banco fixos no código
- **Anti-pattern:** AP30 — Configuração não secreta fixa no código
- **File:** `src/utils.js:6`, `src/AppManager.js:7`
- **Description:** `port: 3000` fica dentro do objeto de segredos, e `':memory:'` é um literal no construtor.
- **Impact:** Trocar a porta ou o banco por ambiente exige alterar o código.
- **Recommendation:** Ler de variáveis de ambiente, com esses valores como padrão (PB02).

### F27 · [LOW] `console.log` como logging
- **Anti-pattern:** AP27 — `print`/`console.log` como logging
- **File:** `src/utils.js:13`, `src/app.js:13`
- **Description:** Cada checkout loga `[LOG] Salvando no cache: last_checkout_<id>`, e a mensagem de boot também usa `console.log`. O log com cartão e chave está no F02.
- **Impact:** Não há níveis nem um ponto único para controlar o que vai para o log.
- **Recommendation:** Centralizar num logger simples (PB15).

### F28 · [LOW] Nomes de uma letra e contexto ambíguo
- **Anti-pattern:** AP28 — Nomes ruins e contexto ambíguo
- **File:** `src/AppManager.js:29-33`, `src/AppManager.js:26`, `src/utils.js:17`, `src/app.js:13`
- **Description:** As variáveis internas se chamam `u`, `e`, `p`, `cid`, `cc` e `self`. Os nomes `badCrypto` e `AppManager` não dizem o que fazem, e o log de boot diz "Frankenstein LMS". Os nomes dos campos de entrada (`usr`, `eml`, `pwd`, `c_id`, `card`) são contrato e ficam como estão.
- **Impact:** A leitura do fluxo de checkout depende de deduzir o que cada letra representa.
- **Recommendation:** Dar nomes descritivos às variáveis internas (PB05, PB14).

### F29 · [LOW] Valores monetários em REAL e status em texto livre
- **Anti-pattern:** AP32 — Modelagem de dados frágil
- **File:** `src/AppManager.js:13`, `src/AppManager.js:15`, `src/AppManager.js:109`
- **Description:** `courses.price` e `payments.amount` são `REAL` (ponto flutuante) e se acumulam em `courseData.revenue += payment.amount`. `payments.status` é texto sem `CHECK`, e `active` é um inteiro usado como booleano.
- **Impact:** Somas de dinheiro acumulam erro de arredondamento, e o banco aceita qualquer status.
- **Recommendation:** Guardar centavos em `INTEGER` e restringir os status. Isso mudaria o schema e o formato dos valores da resposta, então fica como recomendação.

## Deprecated APIs

Nenhuma API deprecated encontrada no código-fonte.

Na árvore de dependências há pacotes deprecated, todos da cadeia de instalação do sqlite3: `tar@6.2.1`, `prebuild-install@7.1.3`, `glob@7.2.3`, `inflight@1.0.6`, `rimraf@3.0.2`, `npmlog@6.0.2` e outros. Ver F16.

```text
================================
Total: 29 findings
================================
```
