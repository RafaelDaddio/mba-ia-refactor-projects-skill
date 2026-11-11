```text
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3.11.4 + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
```

## Summary

CRITICAL: 8 | HIGH: 5 | MEDIUM: 13 | LOW: 6

## Findings

### F01 · [CRITICAL] SQL Injection no login, na busca e nos cadastros
- **Anti-pattern:** AP01 — SQL Injection por concatenação
- **File:** `models.py:109-111`, `models.py:289-299`, `models.py:126-129`, `models.py:47-50`, `models.py:57-61`, `models.py:140`, `models.py:148-166` (e outras 9 queries com ids já convertidos pela rota: `models.py:28`, `models.py:68`, `models.py:92`, `models.py:174`, `models.py:188`, `models.py:192`, `models.py:220`, `models.py:224`, `models.py:279-281`)
- **Description:** O login monta `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"`. A busca pública concatena `q` e `categoria` da query string em `LIKE '%" + termo + "%'` e `categoria = '" + categoria + "'`. Os cadastros de usuário e de produto concatenam nome, e-mail, senha, descrição e categoria. `criar_pedido` concatena `usuario_id`, `produto_id` e `quantidade` vindos do JSON sem conversão de tipo. Nenhuma query de `models.py` usa placeholders. Só o seed (`database.py:70-83`) usa `?`.
- **Impact:** `email = "admin@loja.com' --"` autentica como administrador sem senha. `GET /produtos/busca?q=' UNION SELECT ...` lê qualquer tabela, inclusive as senhas. Um nome com apóstrofo (`O'Brien`) quebra o cadastro com 500.
- **Recommendation:** Usar placeholders `?` com parâmetros separados em todas as queries e montar os filtros dinâmicos só com cláusulas fixas (PB01).

### F02 · [CRITICAL] Execução de SQL arbitrário em /admin/query sem autenticação
- **Anti-pattern:** AP06 — Endpoint administrativo ou destrutivo desprotegido
- **File:** `app.py:59-78`
- **Description:** `POST /admin/query` lê `sql` do corpo e executa `cursor.execute(query)` (`app.py:69`) sem verificar nenhuma credencial. Quando a query não começa com SELECT, faz `db.commit()` (`app.py:75`). Os erros do banco voltam ao cliente em `str(e)` (`app.py:77-78`).
- **Impact:** Qualquer cliente lê, altera ou apaga qualquer tabela (`SELECT senha FROM usuarios`, `DROP TABLE pedidos`, `UPDATE usuarios SET tipo='admin'`).
- **Recommendation:** Exigir credencial administrativa antes de executar (PB06). A rota continua existindo para preservar o contrato. Recomenda-se removê-la em produção.

### F03 · [CRITICAL] Reset do banco em /admin/reset-db sem autenticação
- **Anti-pattern:** AP06 — Endpoint administrativo ou destrutivo desprotegido
- **File:** `app.py:47-57`
- **Description:** `POST /admin/reset-db` executa `DELETE FROM` em `itens_pedido`, `pedidos`, `produtos` e `usuarios` (`app.py:51-54`) e faz commit sem verificar quem chama.
- **Impact:** Uma requisição anônima apaga todos os dados da loja.
- **Recommendation:** Exigir credencial administrativa e levar a operação para um service (PB06).

### F04 · [CRITICAL] Senhas devolvidas pela API de usuários
- **Anti-pattern:** AP04 — Exposição de dados sensíveis
- **File:** `models.py:79-86`, `models.py:95-102`, `controllers.py:128-144`
- **Description:** `get_todos_usuarios` e `get_usuario_por_id` serializam a coluna `senha` (`models.py:83`, `models.py:99`). `GET /usuarios` e `GET /usuarios/<id>` devolvem esse dict sem filtro e sem autenticação.
- **Impact:** Qualquer cliente obtém o e-mail e a senha em texto puro de todos os usuários, inclusive de `admin@loja.com`.
- **Recommendation:** Serializar o usuário sem `senha`, num único ponto (PB04).

### F05 · [CRITICAL] Senhas armazenadas e comparadas em texto puro
- **Anti-pattern:** AP03 — Armazenamento inseguro de senha
- **File:** `models.py:126-129`, `models.py:109-111`, `database.py:75-83`
- **Description:** `criar_usuario` grava `senha` como recebida. O login compara a senha dentro do SQL (`AND senha = '...'`). O seed insere `admin123`, `123456` e `senha123` em texto puro.
- **Impact:** Qualquer vazamento do banco, inclusive pelos findings F01, F02 e F04, entrega as senhas reais. A comparação no SQL faz parte do vetor de bypass do login.
- **Recommendation:** Gravar a senha com hash e salt (`werkzeug.security`, já instalado) no cadastro e no seed, e verificá-la fora do SQL no login (PB03).

### F06 · [CRITICAL] /health expõe a secret key e a configuração interna
- **Anti-pattern:** AP04 — Exposição de dados sensíveis
- **File:** `controllers.py:276-290`
- **Description:** A resposta do health, numa rota pública, inclui `"secret_key": "minha-chave-super-secreta-123"`, `"db_path": "loja.db"`, `"debug": True` e `"ambiente": "producao"` (`controllers.py:286-289`).
- **Impact:** A chave que o Flask usa para assinar sessões fica pública, junto com o caminho do banco e o estado do debug.
- **Recommendation:** Remover `secret_key`, `db_path`, `debug` e `ambiente` da resposta e manter `status`, `database`, `counts` e `versao` (PB04).

### F07 · [CRITICAL] Secret key e senhas de usuários fixas no código
- **Anti-pattern:** AP02 — Segredos e credenciais hardcoded
- **File:** `app.py:7`, `controllers.py:289`, `database.py:75-83`
- **Description:** `SECRET_KEY = "minha-chave-super-secreta-123"` está escrita literalmente em `app.py:7` e repetida em `controllers.py:289`. Em qualquer ambiente, o seed cria o usuário `Admin` (`tipo` `admin`) com a senha `admin123` e dois clientes com senhas fixas.
- **Impact:** Quem lê o repositório conhece a chave de assinatura e a senha do administrador de qualquer instalação.
- **Recommendation:** Ler `SECRET_KEY` de variável de ambiente, com valor aleatório quando ela não existir. Ler as senhas do seed de variáveis de ambiente, deixando os valores atuais só como padrão de desenvolvimento, e gravá-las com hash (PB02, PB03).

### F08 · [CRITICAL] models.py concentra dados, regras e serialização de quatro domínios
- **Anti-pattern:** AP05 — God Class / God Module
- **File:** `models.py:1-314`, `app.py:47-78`
- **Description:** `models.py` (314 linhas) mistura SQL, serialização manual de dicts e regras de negócio de produtos, usuários, pedidos e relatório. Lá ficam a checagem de estoque, o cálculo do total e a baixa de estoque do pedido (`models.py:139-166`) e as faixas de desconto do relatório (`models.py:256-262`). `app.py` mistura configuração, registro de rotas e handlers administrativos com SQL direto.
- **Impact:** Qualquer mudança num domínio exige mexer no mesmo arquivo. As regras não podem ser testadas sem banco, e não há fronteira entre persistência e negócio.
- **Recommendation:** Separar em models por entidade, services com as regras, controllers finos e rotas em blueprints (PB05).

### F09 · [HIGH] Debug ligado e servidor exposto em todas as interfaces
- **Anti-pattern:** AP11 — Debug ligado e servidor exposto no entry point
- **File:** `app.py:8`, `app.py:88`
- **Description:** `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)` estão fixos no código.
- **Impact:** O debugger interativo do Werkzeug e o reloader ficam ativos numa porta acessível pela rede. Tracebacks e o console de execução de código ficam protegidos apenas pelo PIN.
- **Recommendation:** Ler debug, host e porta de configuração por ambiente, com debug desligado por padrão (PB02).

### F10 · [HIGH] Uma conexão SQLite global compartilhada por todas as requisições
- **Anti-pattern:** AP08 — Estado global mutável / conexão compartilhada
- **File:** `database.py:4-11`
- **Description:** `get_db()` usa `global db_connection` e abre uma única conexão com `check_same_thread=False`, reaproveitada por todas as threads do servidor. Nenhum ponto do código faz rollback.
- **Impact:** Requisições concorrentes compartilham a mesma transação. Um erro no meio de uma escrita deixa alterações pendentes que o `commit()` da próxima requisição grava.
- **Recommendation:** Abrir uma conexão por requisição (`flask.g`), fechá-la no teardown e fazer commit e rollback explícitos (PB08).

### F11 · [HIGH] Regras de negócio espalhadas entre controllers e models
- **Anti-pattern:** AP07 — Regra de negócio fora da camada de serviço
- **File:** `controllers.py:43-54`, `controllers.py:208-210`, `controllers.py:242-250`, `models.py:139-166`, `models.py:256-262`
- **Description:** Os controllers validam regras de domínio (categorias válidas, status permitidos) e disparam notificações (e-mail, SMS, push, aprovação, cancelamento) via `print`. Os models checam estoque, calculam o total, dão baixa no estoque do pedido e aplicam as faixas de desconto. Não existe camada de serviço.
- **Impact:** As regras não podem ser reutilizadas nem testadas sem HTTP e banco. A mesma regra aparece em lugares diferentes, como a validação de produto, que já divergiu (F19).
- **Recommendation:** Criar um service por domínio (produtos, usuários, pedidos, relatório) com as regras e as notificações (PB07).

### F12 · [HIGH] Infraestrutura acessada de todas as camadas, sem app factory
- **Anti-pattern:** AP09 — Acoplamento forte sem injeção de dependência
- **File:** `app.py:6-30`, `app.py:49`, `app.py:66`, `controllers.py:266-274`, `models.py:5` (e as outras 14 funções de `models.py`)
- **Description:** A aplicação é criada no import de `app.py`. `get_db()` é chamado diretamente pelos handlers administrativos de `app.py`, pelo `health_check` do controller (que executa SQL próprio) e por cada uma das 15 funções de `models.py`. Não há composition root nem forma de injetar outro banco.
- **Impact:** Não é possível subir a app com um banco de teste nem trocar a configuração sem editar módulos. Controllers e rotas dependem de detalhes do SQLite.
- **Recommendation:** Criar uma app factory `create_app(config)` que registra os blueprints e o ciclo de vida do banco, e acessar dados só pelos models (PB08).

### F13 · [HIGH] Login sem credencial e nenhuma rota exige identidade
- **Anti-pattern:** AP10 — Autenticação ausente ou de fachada
- **File:** `controllers.py:167-186`, `app.py:11-30`
- **Description:** `POST /login` devolve os dados do usuário sem emitir token nem sessão, e nenhuma rota verifica identidade. `GET /usuarios`, `GET /pedidos`, `GET /pedidos/usuario/<id>`, `GET /relatorios/vendas`, `POST/PUT/DELETE /produtos` e `PUT /pedidos/<id>/status` aceitam qualquer cliente.
- **Impact:** Qualquer pessoa lista os pedidos de todos os clientes, altera preços e estoque, apaga produtos e muda o status de pedidos.
- **Recommendation:** As rotas administrativas (F02, F03) passam a exigir credencial pelo PB06. Nas demais, autenticação mudaria o contrato e fica como pendência e recomendação.

### F14 · [MEDIUM] Criação de pedido aceita itens que deixam estoque negativo e total inválido
- **Anti-pattern:** AP17 — Integridade de dados e regras de estado
- **File:** `models.py:139-146`, `models.py:148-168`, `controllers.py:195-203`
- **Description:** A checagem de estoque compara cada linha isoladamente (`produto["estoque"] < item["quantidade"]`, `models.py:144`). Dois itens do mesmo produto com 8 unidades cada passam contra um estoque de 10, e a baixa deixa o estoque em −6. `quantidade` não é validada: um valor negativo ou zero passa na checagem, gera total negativo ou zero e aumenta o estoque (`estoque - -5`). `usuario_id` não é verificado contra `usuarios`. As escritas (pedido, itens e baixa) não têm rollback em caso de erro.
- **Impact:** Estoque negativo, pedidos com total negativo, pedidos de usuário inexistente e, com a conexão compartilhada (F10), escritas parciais gravadas por outra requisição.
- **Recommendation:** No service de pedidos, validar `quantidade` como inteiro maior que zero, somar as quantidades por produto antes de checar o estoque, devolver 4xx para usuário inexistente e gravar tudo numa transação com rollback (PB11, PB12).

### F15 · [MEDIUM] Cancelamento anuncia devolução de estoque que não acontece
- **Anti-pattern:** AP17 — Integridade de dados e regras de estado
- **File:** `controllers.py:249-250`, `models.py:275-283`
- **Description:** Quando o status muda para `cancelado`, o controller imprime "Pedido X cancelado. Devolver estoque.", mas `atualizar_status_pedido` só atualiza a coluna `status`. Os itens do pedido continuam baixados do estoque.
- **Impact:** Cada cancelamento retira unidades do estoque de forma permanente.
- **Recommendation:** Devolver ao estoque as quantidades dos itens na transição para `cancelado`, uma única vez (não em cancelamentos repetidos) e dentro da mesma transação (PB12). Restringir as demais transições de status fica como recomendação, porque o código não expressa essa regra.

### F16 · [MEDIUM] Faturamento do relatório soma pedidos cancelados
- **Anti-pattern:** AP17 — Integridade de dados e regras de estado
- **File:** `models.py:242-245`, `models.py:253-254`, `models.py:256-272`
- **Description:** `SELECT SUM(total) FROM pedidos` inclui os pedidos cancelados, embora o próprio relatório os conte à parte em `pedidos_cancelados`. Desconto, faturamento líquido e ticket médio derivam desse valor.
- **Impact:** Faturamento, desconto aplicável e ticket médio ficam inflados por vendas que não aconteceram.
- **Recommendation:** Excluir os pedidos cancelados do faturamento e da base do ticket médio (PB12).

### F17 · [MEDIUM] E-mail duplicado aceito e schema sem restrições
- **Anti-pattern:** AP17 — Integridade de dados e regras de estado
- **File:** `models.py:122-131`, `controllers.py:146-165`, `database.py:14-53`
- **Description:** `criar_usuario` insere sem verificar se o e-mail já existe, e a tabela `usuarios` não tem `UNIQUE(email)`. O login busca pelo e-mail (`models.py:109-112`) e usa o primeiro registro encontrado. Nenhuma tabela declara `NOT NULL`, `UNIQUE` ou `FOREIGN KEY`, e não há `PRAGMA foreign_keys = ON`.
- **Impact:** Dois cadastros com o mesmo e-mail tornam o login ambíguo. O banco aceita itens e pedidos que apontam para registros inexistentes.
- **Recommendation:** Rejeitar no service, com 4xx, um e-mail já cadastrado (PB12). Restrições no schema exigem migrar os bancos existentes e ficam como recomendação.

### F18 · [MEDIUM] Atualização de status responde sucesso para pedido inexistente
- **Anti-pattern:** AP17 — Integridade de dados e regras de estado
- **File:** `controllers.py:237-252`, `models.py:275-283`
- **Description:** `PUT /pedidos/<id>/status` executa o `UPDATE` e responde 200 "Status atualizado" sem verificar se o pedido existe. `atualizar_produto` e `deletar_produto`, ao contrário, devolvem 404 (`controllers.py:68-70`, `controllers.py:101-103`).
- **Impact:** O cliente recebe confirmação de uma operação que não aconteceu.
- **Recommendation:** Devolver 404 quando o pedido não existe (PB12).

### F19 · [MEDIUM] Validação de entrada ausente e divergente entre criar e atualizar
- **Anti-pattern:** AP15 — Validação de entrada ausente ou inconsistente
- **File:** `controllers.py:43-54`, `controllers.py:87-90`, `controllers.py:118-121`, `controllers.py:169-170`, `controllers.py:239-240`, `app.py:61-62`
- **Description:** `criar_produto` valida o tamanho do nome e a categoria. `atualizar_produto` não valida nenhum dos dois e aceita nome vazio e categoria fora da lista. Nenhum dos dois checa tipos: com `preco: "abc"`, a comparação `preco < 0` lança `TypeError` (500). `float(preco_min)` sem tratamento devolve 500 para `preco_min=abc`. `login`, `atualizar_status_pedido` e `/admin/query` chamam `dados.get(...)` sem checar se o corpo é um objeto JSON.
- **Impact:** Ficam gravados produtos que o cadastro rejeitaria, e erros do cliente aparecem como 500.
- **Recommendation:** Criar uma validação única por recurso, aplicada em criar e em atualizar, com checagem de tipo e 400 para entrada inválida (PB11).

### F20 · [MEDIUM] try/except genérico em cada handler devolvendo str(e)
- **Anti-pattern:** AP16 — Tratamento de erros não centralizado
- **File:** `controllers.py:10-12` (e outros 15 handlers em `controllers.py`), `app.py:77-78`
- **Description:** Todos os handlers envolvem o corpo em `try/except Exception` e devolvem `{"erro": str(e)}` com 500, e não há `errorhandler`. `request.get_json()` fica dentro do `try`: um corpo sem `Content-Type: application/json` (415) ou com JSON malformado (400) levanta uma `HTTPException` que o `except` captura e devolve como 500.
- **Impact:** Mensagens internas do SQLite e do Python chegam ao cliente, e erros do cliente aparecem como falha do servidor. São 17 cópias do mesmo bloco.
- **Recommendation:** Centralizar os handlers de erro na app: exceções de domínio viram 4xx, `HTTPException` mantém o próprio status e as demais viram 500 com mensagem genérica (PB09).

### F21 · [MEDIUM] Queries N+1 na listagem de pedidos e agregações separadas no relatório
- **Anti-pattern:** AP13 — Queries N+1 e agregações ineficientes
- **File:** `models.py:171-201`, `models.py:203-233`, `models.py:239-254`, `models.py:140`, `models.py:155`
- **Description:** Para cada pedido há uma query de itens, e para cada item uma query do nome do produto (`models.py:187-193`, `models.py:219-225`). O relatório faz cinco consultas (`COUNT`, `SUM` e três `COUNT ... WHERE status`) onde uma agregação bastaria. `criar_pedido` consulta o mesmo produto duas vezes (`models.py:140` e `models.py:155`).
- **Impact:** `GET /pedidos` com N pedidos e M itens por pedido executa 1 + N + N·M queries.
- **Recommendation:** Buscar itens e nomes de produto com JOIN e montar o resultado em memória, calcular o relatório numa única agregação condicional e reaproveitar o produto já lido (PB10).

### F22 · [MEDIUM] Funções, serialização e validação duplicadas
- **Anti-pattern:** AP14 — Duplicação de código
- **File:** `models.py:171-201` e `models.py:203-233`; `models.py:12-21`, `models.py:31-40` e `models.py:304-313`; `models.py:79-86` e `models.py:95-102`; `controllers.py:26-50` e `controllers.py:66-90`
- **Description:** `get_pedidos_usuario` e `get_todos_pedidos` são idênticas, exceto pelo `WHERE`. O dict de produto é montado três vezes, e o de usuário, duas. A validação de produto está copiada entre criar e atualizar.
- **Impact:** Cada correção precisa ser repetida, e as cópias tendem a divergir, como já aconteceu com a validação de produto (F19).
- **Recommendation:** Criar um serializador por entidade, uma consulta de pedidos parametrizada e um validador de produto compartilhado (PB05, PB15).

### F23 · [MEDIUM] Abrir a conexão cria o schema e insere o seed
- **Anti-pattern:** AP19 — Efeitos colaterais na inicialização
- **File:** `database.py:7-86`, `app.py:82`
- **Description:** A primeira chamada de `get_db()` em cada processo cria as quatro tabelas e, se `produtos` estiver vazia, insere produtos e usuários, inclusive o administrador. Isso acontece em qualquer ambiente, disparado pela camada que chamar `get_db()` primeiro.
- **Impact:** Conectar ao banco tem efeito colateral. Um banco de produção vazio recebe o usuário `admin@loja.com`/`admin123`, e não há como criar o schema sem o seed.
- **Recommendation:** Separar conexão, criação do schema e seed em funções explícitas chamadas pela app factory (PB08).

### F24 · [MEDIUM] Formato das respostas de erro sem padrão
- **Anti-pattern:** AP25 — Formato de resposta sem padrão
- **File:** `controllers.py:20`, `controllers.py:142`, `controllers.py:183`, `controllers.py:206`, `controllers.py:292`
- **Description:** O 404 vem como `{"erro", "sucesso": false}` em `buscar_produto` e só como `{"erro"}` em `buscar_usuario`. O 401 e o 400 do pedido trazem `sucesso: false`, e os demais 400 não. O health devolve `{"status": "erro", "detalhes"}`.
- **Impact:** Os clientes não conseguem tratar os erros de forma uniforme.
- **Recommendation:** Adotar um formato único de erro, gerado pelos handlers centrais (PB09).

### F25 · [MEDIUM] CORS liberado para qualquer origem
- **Anti-pattern:** AP18 — CORS e middlewares inadequados
- **File:** `app.py:9`
- **Description:** `CORS(app)` sem `origins` aplica `Access-Control-Allow-Origin: *` a todas as rotas, inclusive `/admin/*`.
- **Impact:** Qualquer site pode chamar a API a partir do navegador do usuário, inclusive as rotas administrativas.
- **Recommendation:** Ler as origens permitidas da configuração (PB16).

### F26 · [MEDIUM] Listagens sem paginação
- **Anti-pattern:** AP20 — Listagens sem paginação
- **File:** `models.py:7`, `models.py:75`, `models.py:206`, `models.py:174`, `models.py:289-299`
- **Description:** `GET /produtos`, `GET /usuarios`, `GET /pedidos`, `GET /pedidos/usuario/<id>` e a busca executam `SELECT *` sem `LIMIT` e devolvem todos os registros.
- **Impact:** Tempo de resposta e memória crescem com a base. Somado ao N+1 (F21), `GET /pedidos` degrada rapidamente.
- **Recommendation:** Paginação opcional por query string, preservando o formato atual da resposta (PB17).

### F27 · [LOW] Regras de negócio em literais espalhados
- **Anti-pattern:** AP26 — Números e strings mágicos
- **File:** `models.py:256-262`, `controllers.py:52`, `controllers.py:242`, `controllers.py:47-50`, `app.py:36`, `controllers.py:285`
- **Description:** Faixas de desconto (10.000, 5.000 e 1.000; 10%, 5% e 2%), lista de categorias, lista de status, limites do nome (2 e 200) e a versão `"1.0.0"` aparecem como literais no meio do código. A versão está repetida em dois arquivos.
- **Impact:** Mudar uma regra exige caçar literais pelo código.
- **Recommendation:** Constantes nomeadas num módulo de domínio ou de configuração (PB15).

### F28 · [LOW] print como logging, com e-mails de usuários
- **Anti-pattern:** AP27 — `print`/`console.log` como logging
- **File:** `controllers.py:161`, `controllers.py:179`, `controllers.py:182`, `controllers.py:208-210` (e outras 13 ocorrências em `controllers.py` e `app.py`)
- **Description:** Eventos, erros e "notificações" são feitos com `print`. Cadastro e login imprimem o e-mail do usuário.
- **Impact:** Não há nível nem destino configurável, e dados pessoais vão para o stdout.
- **Recommendation:** Usar o módulo `logging` com um logger por módulo, sem e-mail nas mensagens (PB15).

### F29 · [LOW] Nomes que sombreiam builtins e cursores numerados
- **Anti-pattern:** AP28 — Nomes ruins e contexto ambíguo
- **File:** `controllers.py:14`, `controllers.py:56`, `models.py:24`, `models.py:187-193`, `models.py:219-225`
- **Description:** Parâmetros e variáveis chamados `id` sombreiam o builtin em handlers e funções de produto e usuário, e os laços de pedidos usam `cursor2` e `cursor3`.
- **Impact:** A leitura fica mais difícil, e há risco de usar o builtin por engano.
- **Recommendation:** Renomear durante a reorganização, sem alterar os caminhos públicos (PB05).

### F30 · [LOW] Imports não usados e consulta redundante
- **Anti-pattern:** AP29 — Código morto e imports não usados
- **File:** `models.py:2`, `database.py:2`, `controllers.py:268`
- **Description:** `import sqlite3` em `models.py` e `import os` em `database.py` nunca são usados (confirmado por busca). `SELECT 1` no health é seguido de três consultas que já exercitam a conexão.
- **Impact:** Ruído na leitura e dependências aparentes que não existem.
- **Recommendation:** Remover durante a refatoração.

### F31 · [LOW] Caminho do banco, host e porta fixos no código
- **Anti-pattern:** AP30 — Configuração não secreta fixa no código
- **File:** `database.py:5`, `app.py:88`, `controllers.py:286-287`
- **Description:** `db_path = "loja.db"` é relativo ao diretório de execução, e host e porta são literais em `app.run`. O health declara `"ambiente": "producao"` fixo, contradizendo `debug=True`.
- **Impact:** Rodar a aplicação a partir de outro diretório cria outro banco vazio, e não dá para mudar porta ou banco sem editar o código.
- **Recommendation:** Centralizar a configuração, mantendo os valores atuais como padrão com override por variável de ambiente, e resolver o caminho do banco a partir do projeto (PB02).

### F32 · [LOW] Dinheiro em REAL e status como texto livre
- **Anti-pattern:** AP32 — Modelagem de dados frágil
- **File:** `database.py:19`, `database.py:40-41`, `database.py:51`, `models.py:146`
- **Description:** `preco`, `total` e `preco_unitario` são `REAL`, e o total é somado em ponto flutuante. `status` é `TEXT` sem `CHECK`, e a lista de valores válidos só existe no controller.
- **Impact:** Valores monetários ficam sujeitos a erros de arredondamento, e o banco aceita status fora da lista (por exemplo, via `/admin/query`).
- **Recommendation:** Fica apenas como recomendação: centavos inteiros ou `Decimal` e um `CHECK` de status exigem migração e mudariam o formato numérico das respostas.

## Deprecated APIs

Nenhuma API deprecated encontrada no código-fonte.

```text
================================
Total: 32 findings
================================
```
