```text
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js v24.18.0) + Express 4.22.1
Files:   3 analyzed | ~180 lines of code
```

## Summary

CRITICAL: 5 | HIGH: 5 | MEDIUM: 12 | LOW: 7

## Findings

### F01 · [CRITICAL] Credenciais de produção e chave do gateway fixas no código
- **Anti-pattern:** AP02 — Segredos e credenciais hardcoded
- **File:** `src/utils.js:2-5`
- **Description:** O objeto `config` traz literais `dbUser: "admin_master"`, `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"` e `smtpUser`. Não há leitura de `process.env` em nenhum arquivo.
- **Impact:** Quem tem acesso ao repositório tem a senha do banco e a chave live do gateway; trocar um segredo exige novo commit e o valor antigo fica no histórico do git.
- **Recommendation:** Mover a configuração para um módulo que lê `process.env`, sem valor padrão para segredos, e documentar as variáveis em `.env.example` (PB02). Os segredos já versionados devem ser rotacionados.

### F02 · [CRITICAL] Número do cartão e chave do gateway gravados no log
- **Anti-pattern:** AP04 — Exposição de dados sensíveis
- **File:** `src/AppManager.js:45`
- **Description:** Cada checkout executa ``console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`)``, com o número completo do cartão recebido em `card` e a chave `pk_live_...`.
- **Impact:** O número completo do cartão e a chave do gateway ficam em texto puro no stdout e em qualquer coletor de logs.
- **Recommendation:** Remover os dois valores do log; se for preciso rastrear, registrar só os 4 últimos dígitos (PB04).

### F03 · [CRITICAL] Senhas com "hash" caseiro, senha padrão e seed em texto puro
- **Anti-pattern:** AP03 — Armazenamento inseguro de senha
- **File:** `src/utils.js:17-23`, `src/AppManager.js:68`, `src/AppManager.js:18`
- **Description:** `badCrypto` repete 10.000 vezes os 2 primeiros caracteres do base64 da senha e corta em 10 caracteres: o resultado depende só do início da senha, sem salt. Quando `pwd` não vem, o checkout grava o hash de `"123456"` (`p || "123456"`). O seed insere o usuário com `pass = '123'` em texto puro.
- **Impact:** Senhas que começam igual geram o mesmo valor e o valor guardado revela o início da senha. Contas criadas sem `pwd` têm senha conhecida. A senha gravada nunca é conferida em nenhum ponto do código.
- **Recommendation:** Usar `crypto.scrypt` com salt aleatório e comparação em tempo constante, aplicar o mesmo hash ao seed e eliminar a senha padrão (PB03). Exigir `pwd` no cadastro via checkout é correção de validação (PB11).

### F04 · [CRITICAL] Relatório financeiro administrativo sem credencial
- **Anti-pattern:** AP06 — Endpoint administrativo ou destrutivo desprotegido
- **File:** `src/AppManager.js:80-129`
- **Description:** `GET /api/admin/financial-report` é registrada sem nenhum middleware ou verificação; devolve faturamento por curso e o nome de cada aluno com o valor pago.
- **Impact:** Qualquer cliente anônimo lê o faturamento e a lista de alunos de todos os cursos.
- **Recommendation:** Exigir `X-Admin-Token` (valor vindo da configuração) com 401 sem prova e 403 com prova inválida (PB06).

### F05 · [CRITICAL] AppManager concentra conexão, schema, seed, rotas, regras e SQL
- **Anti-pattern:** AP05 — God Class / God Module
- **File:** `src/AppManager.js:4-139`
- **Description:** A classe abre o banco (linha 7), cria as 5 tabelas e o seed (10-23) e registra as 3 rotas (25-138), cujos handlers contêm o SQL e as regras de usuários, cursos, matrículas, pagamentos e auditoria.
- **Impact:** Nenhuma parte é testável isoladamente; qualquer mudança em um domínio toca o mesmo arquivo e os mesmos closures dos outros.
- **Recommendation:** Separar em config, database, models (um por tabela), services, controllers, routes e middlewares, com composition root no entry point (PB05).

### F06 · [HIGH] Identidade das contas desprotegida no checkout e na exclusão
- **Anti-pattern:** AP10 — Autenticação ausente ou de fachada
- **File:** `src/AppManager.js:131-137`, `src/AppManager.js:40`, `src/AppManager.js:73-75`
- **Description:** `DELETE /api/users/:id` apaga qualquer conta sem identificar quem pede. No checkout, quando o e-mail já existe, o fluxo segue direto para `processPaymentAndEnroll(user.id)`: a `pwd` recebida é ignorada e nunca comparada com a senha gravada.
- **Impact:** Qualquer cliente exclui a conta de outra pessoa ou cria matrícula e pagamento em nome de uma conta existente sabendo apenas o e-mail.
- **Recommendation:** No checkout com e-mail existente, conferir `pwd` contra o hash da conta ou aceitar `X-Admin-Token`; na exclusão, exigir `X-Admin-Token`, já que a rota não recebe senha e o projeto não tem login (PB06). Não criar rota de login nem papéis.

### F07 · [HIGH] Entrada não string derruba o processo dentro de callbacks do sqlite
- **Anti-pattern:** AP12 — Exceção não tratada derruba o processo
- **File:** `src/AppManager.js:46`, `src/AppManager.js:68` (com `src/utils.js:20`), `src/AppManager.js:92-93`
- **Description:** `cc.startsWith("4")` roda dentro de callback do sqlite e a validação da linha 35 só checa presença: `card` numérico lança `TypeError`. `badCrypto(p)` chama `Buffer.from(pwd)`, que lança para `pwd` numérico, também dentro de callback. No relatório, `enrollments.length` é lido sem checar `err`.
- **Impact:** No Express 4, exceção em callback assíncrono não chega a nenhum middleware: uma única requisição com `"card": 4111` encerra o servidor para todos os clientes.
- **Recommendation:** Validar tipos antes de qualquer acesso ao banco, trocar callbacks por async/await com erros encaminhados a um middleware central (PB11, PB14, PB09).

### F08 · [HIGH] Regras de negócio dentro dos handlers de rota
- **Anti-pattern:** AP07 — Regra de negócio fora da camada de serviço
- **File:** `src/AppManager.js:43-75`, `src/AppManager.js:89-127`
- **Description:** O handler do checkout decide a aprovação do pagamento, cria o usuário, a matrícula, o pagamento e o log de auditoria; o handler do relatório soma a receita só de pagamentos `PAID` e monta a lista de alunos.
- **Impact:** As regras só podem ser exercitadas por HTTP e ficam misturadas a status codes e SQL.
- **Recommendation:** Extrair `checkoutService`, `reportService` e `userService`; os controllers ficam com a tradução HTTP (PB07).

### F09 · [HIGH] Infraestrutura instanciada dentro da classe, sem injeção
- **Anti-pattern:** AP09 — Acoplamento forte sem injeção de dependência
- **File:** `src/AppManager.js:7`, `src/AppManager.js:2`, `src/app.js:8-12`
- **Description:** O construtor faz `new sqlite3.Database(':memory:')`, a classe importa `config` e os helpers direto de `./utils`, e `app.js` cria o app, o manager e já chama `listen` no mesmo módulo.
- **Impact:** Não dá para trocar o banco ou a configuração num teste, nem importar o app sem abrir a porta.
- **Recommendation:** Criar a conexão num módulo de banco, injetá-la em models e services e montar tudo numa app factory separada do `listen` (PB08).

### F10 · [HIGH] Cache global mutável que só cresce
- **Anti-pattern:** AP08 — Estado global mutável / conexão compartilhada
- **File:** `src/utils.js:9-15`, `src/AppManager.js:59`
- **Description:** `globalCache` é um objeto de módulo que recebe uma chave `last_checkout_<userId>` a cada checkout. Nenhum arquivo lê esse objeto e nada remove entradas.
- **Impact:** Estado compartilhado por todas as requisições, sem limite de tamanho e sem utilidade observável.
- **Recommendation:** Remover o cache, já que nada o consome, mantendo apenas o registro em log (PB08).

### F11 · [MEDIUM] Exclusão de usuário deixa órfãos e sempre responde sucesso
- **Anti-pattern:** AP17 — Integridade de dados e regras de estado
- **File:** `src/AppManager.js:131-137`
- **Description:** O handler executa só `DELETE FROM users`, ignora `err`, não verifica se alguma linha foi afetada e responde 200 com "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco." O relatório passa a mostrar o aluno como `'Unknown'` (linha 113).
- **Impact:** Matrículas e pagamentos apontam para usuário inexistente; id inexistente ou erro de banco recebe 200.
- **Recommendation:** Remover pagamentos, matrículas e usuário na mesma transação e devolver 404 para id inexistente; a própria mensagem do código declara que os dados ficam sujos (PB12).

### F12 · [MEDIUM] A mesma matrícula pode ser comprada e cobrada mais de uma vez
- **Anti-pattern:** AP17 — Integridade de dados e regras de estado
- **File:** `src/AppManager.js:50-54`
- **Description:** O checkout insere em `enrollments` e `payments` sem consultar se o usuário já está matriculado no curso; não há `UNIQUE(user_id, course_id)`.
- **Impact:** Repetir a requisição gera duas matrículas e dois pagamentos `PAID` para o mesmo aluno e curso, e o relatório soma a receita em dobro.
- **Recommendation:** Verificar a matrícula existente antes de cobrar e responder 409 (PB12).

### F13 · [MEDIUM] Checkout grava em até quatro passos sem transação
- **Anti-pattern:** AP17 — Integridade de dados e regras de estado
- **File:** `src/AppManager.js:50-57`, `src/AppManager.js:69`
- **Description:** Usuário, matrícula, pagamento e log de auditoria são `INSERT`s independentes, encadeados por callbacks. O usuário é criado antes da decisão do pagamento, e o erro do `INSERT` de auditoria é ignorado.
- **Impact:** Falha no pagamento deixa matrícula sem pagamento; pagamento recusado deixa a conta criada.
- **Recommendation:** Envolver matrícula, pagamento e auditoria em uma transação (PB12). Se a conta criada num checkout recusado deve ou não persistir é regra que o código não declara: fica como pendência.

### F14 · [MEDIUM] Schema sem NOT NULL, UNIQUE nem FOREIGN KEY
- **Anti-pattern:** AP17 — Integridade de dados e regras de estado
- **File:** `src/AppManager.js:12-16`
- **Description:** As 5 tabelas declaram só a chave primária. `users.email` é a chave de busca do checkout (linha 40) e não é `UNIQUE`; `enrollments.user_id`, `enrollments.course_id` e `payments.enrollment_id` não têm `FOREIGN KEY`; não há `PRAGMA foreign_keys = ON`.
- **Impact:** O banco aceita e-mails duplicados, referências a registros inexistentes e campos nulos.
- **Recommendation:** Adicionar `NOT NULL`, `UNIQUE(email)`, chaves estrangeiras e o `PRAGMA`; como o banco é em memória e recriado a cada boot, não há dados existentes a migrar (PB12).

### F15 · [MEDIUM] Relatório financeiro com N+1 e sem limite
- **Anti-pattern:** AP13 — Queries N+1 e agregações ineficientes
- **File:** `src/AppManager.js:83-106`
- **Description:** Uma query lista os cursos, uma por curso lista as matrículas e duas por matrícula buscam usuário e pagamento. Tudo é carregado em memória e a receita é somada em JavaScript.
- **Impact:** Com C cursos e M matrículas são 1 + C + 2M queries por requisição, e a resposta cresce sem limite.
- **Recommendation:** Uma única consulta com `LEFT JOIN` entre cursos, matrículas, usuários e pagamentos, agrupada no service (PB10).

### F16 · [MEDIUM] Callbacks em 5 níveis e contadores manuais
- **Anti-pattern:** AP23 — Callbacks aninhados e controle assíncrono manual
- **File:** `src/AppManager.js:37-62`, `src/AppManager.js:86-122`, `src/AppManager.js:26`
- **Description:** O checkout aninha 5 callbacks. O relatório usa `coursesPending--` e `enrPending--` para decidir quando responder, com o bloco de finalização duplicado (95-99 e 118-122). `const self = this` convive com arrow functions.
- **Impact:** A ordem do array do relatório depende da ordem de conclusão dos callbacks, e um caminho de erro que não decremente o contador deixa a requisição sem resposta.
- **Recommendation:** Envolver o sqlite3 em Promises e reescrever com async/await (PB14).

### F17 · [MEDIUM] Erros tratados callback a callback, sem middleware central
- **Anti-pattern:** AP16 — Tratamento de erros não centralizado
- **File:** `src/AppManager.js:38`, `src/AppManager.js:41`, `src/AppManager.js:51`, `src/AppManager.js:55`, `src/AppManager.js:57`, `src/AppManager.js:70`, `src/AppManager.js:84`, `src/AppManager.js:92`, `src/AppManager.js:104-106`, `src/AppManager.js:133`, `src/app.js:5-10`
- **Description:** Cada callback repete `if (err) return res.status(500).send(...)`; em 5 pontos o `err` é ignorado; `err || !course` transforma erro de banco em 404. `app.js` não registra middleware de erro nem de 404, então JSON inválido e rota inexistente caem na resposta HTML padrão do Express.
- **Impact:** Erros somem sem registro, o status não reflete a causa e o cliente recebe HTML numa API JSON.
- **Recommendation:** Classes de erro da aplicação, um middleware de erro e um de 404 (PB09).

### F18 · [MEDIUM] Validação do checkout checa só presença
- **Anti-pattern:** AP15 — Validação de entrada ausente ou inconsistente
- **File:** `src/AppManager.js:29-35`, `src/AppManager.js:132`
- **Description:** A única validação é `!u || !e || !cid || !cc`. Tipos não são checados, `pwd` é opcional e `:id` da exclusão vai direto para a query.
- **Impact:** Valores de tipo errado chegam ao banco ou derrubam o processo (F07); contas são criadas sem senha informada (F03).
- **Recommendation:** Validar tipo de `usr`, `eml`, `pwd`, `c_id`, `card` e `id` com 400 (PB11). Formato de e-mail e de cartão são regras que o código não declara: ficam como pendência.

### F19 · [MEDIUM] Erros em texto puro, sucesso em JSON
- **Anti-pattern:** AP25 — Formato de resposta sem padrão
- **File:** `src/AppManager.js:35`, `src/AppManager.js:38`, `src/AppManager.js:48`, `src/AppManager.js:60`, `src/AppManager.js:135` (e outros 5 `send` de erro)
- **Description:** Os erros usam `res.status(...).send("texto")`, em inglês ("Bad Request") e português; os sucessos do checkout e do relatório são JSON; o sucesso da exclusão é texto puro.
- **Impact:** O cliente precisa tratar dois formatos e não tem um campo estável para ler o erro.
- **Recommendation:** Padronizar os erros em um único formato JSON (PB09). A resposta de sucesso da exclusão continua como está, por ser contrato.

### F20 · [MEDIUM] Schema, seed e listen disparados na carga do entry point
- **Anti-pattern:** AP19 — Efeitos colaterais na inicialização
- **File:** `src/AppManager.js:10-23`, `src/app.js:8-14`
- **Description:** `initDb` mistura DDL e seed e roda em todo boot, em qualquer ambiente; `app.js` chama `listen` sem esperar o banco e sem separar criação do app e subida do servidor.
- **Impact:** Não há como subir sem seed nem como importar o app sem abrir a porta 3000.
- **Recommendation:** Separar schema e seed em módulos próprios, aguardá-los e só então chamar `listen` (PB08). O seed continua carregando no boot, como o README descreve.

### F21 · [MEDIUM] utils.js mistura configuração, cache e hash de senha
- **Anti-pattern:** AP24 — Responsabilidade no módulo errado
- **File:** `src/utils.js:1-25`
- **Description:** O mesmo arquivo exporta `config` com segredos, o cache global com log, o contador `totalRevenue` e `badCrypto`.
- **Impact:** Qualquer módulo que precise de um helper importa também os segredos, e a regra de senha fica escondida num arquivo genérico.
- **Recommendation:** Distribuir em `config/`, `utils/password.js` e `utils/logger.js` (PB05).

### F22 · [MEDIUM] 13 vulnerabilidades e 9 pacotes deprecated na árvore de dependências
- **Anti-pattern:** AP22 — Dependências vulneráveis, sem uso ou sem versão fixa
- **File:** `package.json:10-11`, `package-lock.json`
- **Description:** `npm audit` reporta 13 vulnerabilidades (2 critical, 8 high, 1 moderate, 2 low). No caminho das requisições, via express 4.22.1: `body-parser` (DoS por bytes após corpo comprimido), `qs`, `path-to-regexp` (ReDoS com múltiplos parâmetros de rota) e `proxy-addr` (IP spoofing com trust subnet). Via sqlite3 5.1.7, em tempo de instalação: `tar`, `node-gyp`, `cacache`, `make-fetch-happen`. O lockfile marca 9 pacotes como deprecated (`tar 6.2.1`, `glob 7.2.3`, `inflight`, `rimraf 3.0.2`, `npmlog`, `gauge`, `are-we-there-yet`, `prebuild-install`, `@npmcli/move-file`). As duas dependências diretas usam faixa `^`.
- **Impact:** A falha do `body-parser` é alcançável porque toda rota passa por `express.json()`. As de `path-to-regexp` e `proxy-addr` dependem de recursos que o projeto não usa (rota com vários parâmetros, `trust proxy`).
- **Recommendation:** `npm audit fix` resolve a cadeia do express; a do sqlite3 exige a major 6.0.1. Nenhuma atualização é feita sem autorização: fica como pendência.

### F23 · [LOW] Literais de negócio espalhados
- **Anti-pattern:** AP26 — Números e strings mágicos
- **File:** `src/AppManager.js:46`, `src/AppManager.js:48`, `src/AppManager.js:108`, `src/AppManager.js:68`, `src/utils.js:19-22`
- **Description:** O prefixo `"4"` que aprova o cartão, os status `"PAID"` e `"DENIED"`, a senha padrão `"123456"` e os números `10000`, `2` e `10` do hash aparecem como literais.
- **Impact:** A regra de aprovação e os status ficam implícitos e repetidos.
- **Recommendation:** Constantes nomeadas num módulo próprio (PB15).

### F24 · [LOW] console.log como logging
- **Anti-pattern:** AP27 — `print`/`console.log` como logging
- **File:** `src/utils.js:13`, `src/app.js:13`, `src/AppManager.js:45`
- **Description:** Os três registros do projeto usam `console.log` direto, sem nível; o da linha 45 é o caso sensível tratado em F02.
- **Impact:** Não há como filtrar por severidade nem silenciar em testes.
- **Recommendation:** Um logger único com níveis, sobre a biblioteca padrão (PB15).

### F25 · [LOW] Identificadores de uma ou duas letras
- **Anti-pattern:** AP28 — Nomes ruins e contexto ambíguo
- **File:** `src/AppManager.js:29-33`, `src/AppManager.js:26`, `src/AppManager.js:89`, `src/utils.js:17`
- **Description:** `u`, `e`, `p`, `cid`, `cc`, `c` e `enr` nomeiam os dados do checkout e do relatório; `err` é redeclarado em cada nível de callback; `self = this` convive com arrow functions; a função de hash se chama `badCrypto`.
- **Impact:** É preciso reler o corpo da requisição para entender cada variável.
- **Recommendation:** Renomear durante a extração das camadas, mantendo os nomes dos campos do contrato (PB05, PB14).

### F26 · [LOW] Exports e configurações nunca usados
- **Anti-pattern:** AP29 — Código morto e imports não usados
- **File:** `src/AppManager.js:2`, `src/utils.js:10`, `src/utils.js:25`, `src/utils.js:2-3`, `src/utils.js:5`
- **Description:** `totalRevenue` é importado em `AppManager.js` e nunca referenciado; `globalCache` é exportado e nenhum arquivo o importa; `dbUser`, `dbPass` e `smtpUser` não são lidos em nenhum ponto (confirmado por Grep em `src/`).
- **Impact:** Sugere um contador de receita e integrações que não existem.
- **Recommendation:** Remover durante a refatoração.

### F27 · [LOW] Porta e banco fixos no código
- **Anti-pattern:** AP30 — Configuração não secreta fixa no código
- **File:** `src/utils.js:6`, `src/AppManager.js:7`
- **Description:** `port: 3000` e `':memory:'` são literais.
- **Impact:** Mudar a porta ou usar um banco em arquivo exige editar o código.
- **Recommendation:** Ler `PORT` e o caminho do banco do ambiente, com os valores atuais como padrão (PB02).

### F28 · [LOW] Header X-Powered-By ativo
- **Anti-pattern:** AP31 — Header que revela a stack
- **File:** `src/app.js:5-6`
- **Description:** O app é criado sem `app.disable('x-powered-by')`.
- **Impact:** Toda resposta anuncia o framework.
- **Recommendation:** Desabilitar o header na criação do app (PB16).

### F29 · [LOW] Valores monetários em REAL e status em texto livre
- **Anti-pattern:** AP32 — Modelagem de dados frágil
- **File:** `src/AppManager.js:13`, `src/AppManager.js:15`
- **Description:** `courses.price` e `payments.amount` são `REAL`, somados em ponto flutuante no relatório (linha 109); `payments.status` é `TEXT` sem `CHECK`.
- **Impact:** Somas sujeitas a erro de arredondamento e status fora de `PAID`/`DENIED` aceitos pelo banco.
- **Recommendation:** `CHECK` no status cabe junto com F14; trocar o tipo monetário para centavos inteiros mudaria os valores do contrato e fica como pendência.

## Deprecated APIs

Nenhuma API deprecated encontrada no código-fonte.

Há 9 pacotes deprecated na árvore de dependências: ver F22 (AP22).

```text
================================
Total: 29 findings
================================
```
