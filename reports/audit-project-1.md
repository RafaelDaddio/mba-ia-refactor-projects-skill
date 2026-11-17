```text
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3.11.4 + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
```

## Summary

CRITICAL: 7 | HIGH: 6 | MEDIUM: 12 | LOW: 8

## Findings

### F01 · [CRITICAL] Execução de SQL arbitrário sem autenticação em /admin/query
- **Anti-pattern:** AP06 — Endpoint administrativo ou destrutivo desprotegido
- **File:** `app.py:59-78`
- **Description:** `POST /admin/query` lê `dados.get("sql")` e passa o texto direto a `cursor.execute(query)` (`app.py:69`), com `commit` para tudo que não começa com `SELECT` (`app.py:75`). Nenhuma credencial é verificada.
- **Impact:** Qualquer cliente na rede lê, altera ou apaga qualquer tabela, inclusive as senhas de `usuarios`. Na prática, é acesso total ao banco.
- **Recommendation:** Exigir credencial de administrador (`X-Admin-Token` da configuração ou token de conta `admin`): 401 sem prova, 403 com prova insuficiente (PB06).

### F02 · [CRITICAL] SQL Injection no login, na busca e nas escritas
- **Anti-pattern:** AP01 — SQL Injection por concatenação
- **File:** `models.py:109-111`, `models.py:289-299`, `models.py:126-129`, `models.py:47-50`, `models.py:57-61`, `models.py:140`, `models.py:148-151`, `models.py:155-166`, `models.py:279-281` (e outras 8 concatenações com inteiro vindo da rota: `models.py:28`, `68`, `92`, `174`, `188`, `192`, `220`, `224`)
- **Description:** 19 das 27 chamadas `execute` de `models.py` montam o SQL com `+`.
  - O login concatena `email` e `senha` (`"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`).
  - A busca pública concatena `q` e `categoria` em `LIKE '%" + termo + "%'`.
  - Cadastro de usuário, criação e atualização de produto e criação de pedido concatenam campos do corpo JSON (`usuario_id`, `produto_id`, `quantidade`).
- **Impact:** Um e-mail como `admin@loja.com' --` autentica sem senha. `GET /produtos/busca?q=` aceita `UNION SELECT` e extrai `usuarios.senha`. As escritas permitem gravar valores arbitrários.
- **Recommendation:** Usar placeholders `?` com parâmetros separados em todas as queries e montar os filtros dinâmicos da busca só com cláusulas fixas (PB01).

### F03 · [CRITICAL] Reset do banco sem autenticação em /admin/reset-db
- **Anti-pattern:** AP06 — Endpoint administrativo ou destrutivo desprotegido
- **File:** `app.py:47-57`
- **Description:** `POST /admin/reset-db` executa `DELETE FROM` em `itens_pedido`, `pedidos`, `produtos` e `usuarios` e faz `commit`, sem verificar credencial.
- **Impact:** Uma única requisição anônima apaga todos os dados da loja. Como `loja.db` persiste entre execuções, a perda é permanente.
- **Recommendation:** Exigir credencial de administrador, como em F01 (PB06).

### F04 · [CRITICAL] Senhas gravadas e comparadas em texto puro
- **Anti-pattern:** AP03 — Armazenamento inseguro de senha
- **File:** `models.py:126-129`, `models.py:109-111`, `database.py:75-83`
- **Description:** `criar_usuario` grava a senha recebida na coluna `senha` sem hash. O login compara a senha dentro do SQL (`AND senha = '...'`). O seed insere `admin123`, `123456` e `senha123` em claro.
- **Impact:** Qualquer leitura do banco (F01, F02, F05) revela as senhas de todos os usuários.
- **Recommendation:** Gravar hash com salt usando `werkzeug.security` (já instalado), buscar o usuário por e-mail e conferir com `check_password_hash`, e gravar o seed já com hash (PB03).

### F05 · [CRITICAL] Senhas e SECRET_KEY devolvidas nas respostas
- **Anti-pattern:** AP04 — Exposição de dados sensíveis
- **File:** `models.py:83`, `models.py:99`, `controllers.py:286-289`
- **Description:** `get_todos_usuarios` e `get_usuario_por_id` incluem `"senha"` no dicionário devolvido por `GET /usuarios` e `GET /usuarios/<id>`. `GET /health` devolve `secret_key`, `db_path`, `debug` e `ambiente`.
- **Impact:** Um cliente anônimo obtém as senhas de todas as contas e a chave de assinatura da aplicação.
- **Recommendation:** Remover `senha` da serialização de usuário e manter no health só `status`, `database`, `counts` e `versao` (PB04). É uma mudança intencional de contrato, permitida pela regra 3.

### F06 · [CRITICAL] SECRET_KEY e credenciais de administrador fixas no código
- **Anti-pattern:** AP02 — Segredos e credenciais hardcoded
- **File:** `app.py:7`, `controllers.py:289`, `database.py:75-79`
- **Description:** `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` está no código e o mesmo literal se repete na resposta do health. O seed cria `admin@loja.com` com a senha `admin123` sempre que a tabela `produtos` está vazia (`database.py:56-57`), em qualquer ambiente.
- **Impact:** Quem lê o repositório conhece a chave de assinatura e a conta de administrador de qualquer instalação.
- **Recommendation:** Ler `SECRET_KEY` e a senha inicial do administrador do ambiente, num módulo de configuração, sem valor padrão sensível (PB02).

### F07 · [CRITICAL] Módulos que misturam SQL, regras, validação e rotas de todos os domínios
- **Anti-pattern:** AP05 — God Class / God Module
- **File:** `models.py:1-314`, `controllers.py:1-292`, `app.py:47-78`
- **Description:**
  - `models.py` (314 linhas) atende produtos, usuários, pedidos e relatório, e junta SQL, serialização e regras: checagem de estoque e total (`models.py:139-146`) e faixas de desconto (`models.py:256-262`).
  - `controllers.py` (292 linhas) reúne os handlers de todos os domínios, com validação, notificações e SQL direto no health (`controllers.py:266-274`).
  - `app.py` mistura configuração, registro de rotas e dois handlers administrativos com SQL.
- **Impact:** Qualquer mudança num domínio mexe em arquivos compartilhados por todos, e não há como testar regras sem banco e sem HTTP.
- **Recommendation:** Separar por domínio em `models/` (acesso a dados), `services/` (regras), `controllers/` e `routes/`, com configuração e inicialização próprias (PB05).

### F08 · [HIGH] Login sem token e contas acessíveis por qualquer cliente
- **Anti-pattern:** AP10 — Autenticação ausente ou de fachada
- **File:** `controllers.py:167-186`, `models.py:113-119`, `controllers.py:136-144`, `controllers.py:188-203`, `controllers.py:222-227`, `controllers.py:237-252`
- **Description:** `POST /login` devolve só `id`, `nome`, `email` e `tipo`, sem token nem sessão, e nenhuma rota verifica identidade. Com isso:
  - `GET /usuarios/<id>` lê qualquer conta;
  - `POST /pedidos` cria pedido para qualquer `usuario_id` informado no corpo;
  - `GET /pedidos/usuario/<id>` lê os pedidos de qualquer conta;
  - `PUT /pedidos/<id>/status` altera o pedido de qualquer conta.
- **Impact:** Qualquer cliente lê dados pessoais, compra em nome de terceiros e cancela pedidos alheios.
- **Recommendation:** Emitir no login um token assinado numa chave nova da resposta e exigir `Authorization: Bearer` do dono da conta ou de um administrador nessas rotas, com 401 sem prova e 403 para outra conta (PB06).

### F09 · [HIGH] Escritas no catálogo e listagens gerais sem autenticação
- **Anti-pattern:** AP10 — Autenticação ausente ou de fachada
- **File:** `controllers.py:24`, `controllers.py:64`, `controllers.py:98`, `controllers.py:128-134`, `controllers.py:229-235`, `controllers.py:257-262` (rotas em `app.py:14-16`, `18`, `24`, `28`)
- **Description:** `POST`, `PUT` e `DELETE /produtos` alteram o catálogo sem identificar quem pede. `GET /usuarios`, `GET /pedidos` e `GET /relatorios/vendas` devolvem dados de todas as contas a qualquer cliente.
- **Impact:** Um anônimo altera preços, apaga produtos e lê a base de clientes e o faturamento.
- **Recommendation:** Exigir conta autenticada nas escritas de produto e administrador nas três listagens (PB06). Restringir a escrita de produtos ao papel `admin` é regra que o código não define e fica como pendência.

### F10 · [HIGH] Regras de negócio na camada de dados e nos controllers
- **Anti-pattern:** AP07 — Regra de negócio fora da camada de serviço
- **File:** `models.py:137-169`, `models.py:256-262`, `controllers.py:208-210`, `controllers.py:247-250`, `controllers.py:43-54`
- **Description:** `models.criar_pedido` valida estoque, calcula o total e baixa o estoque entre as queries. `models.relatorio_vendas` aplica as faixas de desconto. Os controllers disparam as "notificações" (e-mail, SMS, push) e validam regras de domínio (categoria, limites de nome).
- **Impact:** As regras não podem ser testadas sem banco e sem HTTP, e ficam espalhadas em duas camadas que não são donas delas.
- **Recommendation:** Mover as regras para serviços por domínio, deixando os models só com acesso a dados e os controllers só com HTTP (PB07).

### F11 · [HIGH] Conexão SQLite global compartilhada entre requisições
- **Anti-pattern:** AP08 — Estado global mutável / conexão compartilhada
- **File:** `database.py:4`, `database.py:8-10`
- **Description:** `db_connection` é uma variável de módulo alterada com `global` e criada com `check_same_thread=False`. Todas as requisições usam a mesma conexão e a mesma transação implícita.
- **Impact:** Requisições concorrentes compartilham a transação. O `commit` de uma grava escritas pendentes de outra, e um erro no meio de uma escrita deixa alterações pendentes para a próxima requisição.
- **Recommendation:** Abrir uma conexão por requisição (no `g` do Flask) e fechá-la no teardown (PB08).

### F12 · [HIGH] get_db() chamado de todas as camadas, sem app factory
- **Anti-pattern:** AP09 — Acoplamento forte sem injeção de dependência
- **File:** `models.py:5` (e as outras 14 funções do arquivo), `controllers.py:266`, `app.py:49`, `app.py:66`, `app.py:82`, `app.py:6`, `database.py:5`
- **Description:** As 15 funções de `models.py`, o health e os dois handlers administrativos buscam a conexão diretamente em `database.get_db()`. O caminho do banco é um literal de módulo e `app` é criado no import, sem factory.
- **Impact:** Não há como subir a aplicação com outro banco (por exemplo, num teste) sem alterar o código.
- **Recommendation:** Criar `create_app()` como composition root, com o caminho do banco vindo da configuração e a conexão obtida num único ponto (PB08).

### F13 · [HIGH] Debug ligado e servidor exposto em todas as interfaces
- **Anti-pattern:** AP11 — Debug ligado e servidor exposto no entry point
- **File:** `app.py:8`, `app.py:88`, `app.py:61-62`
- **Description:** `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)` estão fixos. Em `/admin/query`, `dados.get` roda fora do `try`, então um corpo JSON `null` gera exceção não tratada, que em modo debug devolve a página do depurador com traceback.
- **Impact:** O depurador interativo do Werkzeug fica acessível pela rede e os tracebacks revelam código e caminhos internos.
- **Recommendation:** Ler debug e host do ambiente, com padrão desligado e `127.0.0.1` (PB02).

### F14 · [MEDIUM] Cancelamento não devolve estoque e faturamento soma pedidos cancelados
- **Anti-pattern:** AP17 — Integridade de dados e regras de estado
- **File:** `controllers.py:249-250`, `models.py:275-283`, `models.py:242`, `models.py:272`, `controllers.py:245-252`
- **Description:**
  - Ao cancelar, o controller imprime "cancelado. Devolver estoque.", mas `atualizar_status_pedido` só faz o `UPDATE` do status.
  - O relatório conta os cancelados à parte (`models.py:253`), mas `SUM(total)` e o ticket médio incluem esses pedidos.
  - `PUT /pedidos/<id>/status` responde 200 "Status atualizado" para um pedido que não existe.
  - Qualquer transição de status é aceita.
- **Impact:** O estoque fica menor que o real a cada cancelamento, o faturamento fica inflado e o cliente recebe sucesso por uma operação que não aconteceu.
- **Recommendation:** Devolver o estoque ao cancelar (uma única vez), excluir os cancelados do faturamento e do ticket médio e responder 404 para pedido inexistente (PB12). Restringir quais transições são permitidas é regra que o código não declara e fica como pendência.

### F15 · [MEDIUM] Pedido gravado em vários passos sem transação e com estoque negativo possível
- **Anti-pattern:** AP17 — Integridade de dados e regras de estado
- **File:** `models.py:139-146`, `models.py:148-168`
- **Description:** O estoque é conferido item a item, sem somar itens repetidos do mesmo produto. O `INSERT` do pedido, os `INSERT` dos itens e os `UPDATE` de estoque rodam em sequência, sem `rollback` em caso de erro e sem condição `estoque >= quantidade` no `UPDATE`.
- **Impact:** Dois itens com o mesmo `produto_id` passam na checagem e deixam o estoque negativo. Uma falha no meio deixa escritas parciais pendentes na conexão compartilhada (F11).
- **Recommendation:** Agregar as quantidades por produto antes de checar e gravar tudo numa transação com `rollback` (PB12).

### F16 · [MEDIUM] Schema sem constraints, e-mail duplicado e pedido para usuário inexistente
- **Anti-pattern:** AP17 — Integridade de dados e regras de estado
- **File:** `database.py:14-53`, `models.py:122-131`, `models.py:148-151`, `models.py:65-70`
- **Description:**
  - Nenhuma tabela tem `NOT NULL`, `UNIQUE` ou `FOREIGN KEY`.
  - `criar_usuario` aceita e-mail já cadastrado, embora o login busque por e-mail.
  - `criar_pedido` não confere se `usuario_id` existe.
  - `deletar_produto` apaga produtos referenciados por `itens_pedido`; a leitura contorna com `"Desconhecido"` (`models.py:196`).
- **Impact:** Contas duplicadas tornam o login ambíguo, e pedidos ficam apontando para usuários e produtos inexistentes.
- **Recommendation:** Rejeitar e-mail duplicado (409) e pedido para usuário inexistente, e tratar a exclusão de produto com pedidos conforme o playbook (PB12). Alterar o schema de bancos já existentes fica como recomendação.

### F17 · [MEDIUM] Validação de entrada ausente ou diferente entre criar e atualizar
- **Anti-pattern:** AP15 — Validação de entrada ausente ou inconsistente
- **File:** `controllers.py:196-203`, `models.py:144-146`, `controllers.py:43-54`, `controllers.py:87-90`, `controllers.py:118-121`, `controllers.py:170`, `controllers.py:240`, `controllers.py:154-158`
- **Description:**
  - Os itens do pedido não são validados: sem `produto_id` ou `quantidade` ocorre `KeyError` (500), e quantidade negativa ou zero é aceita, gerando total negativo e aumento de estoque (`models.py:164`).
  - `preco < 0` e `len(nome)` falham com 500 quando o tipo é errado.
  - `atualizar_produto` não valida tamanho do nome nem categoria, que `criar_produto` valida.
  - `float(preco_min)` não tem tratamento.
  - `dados.get` quebra quando o corpo JSON não é um objeto.
  - O e-mail não tem verificação de formato.
- **Impact:** Entradas inválidas viram 500 ou corrompem estoque e totais, e um produto pode ser atualizado para um estado que a criação rejeita.
- **Recommendation:** Centralizar validadores de tipo e faixa, compartilhados entre criar e atualizar, exigindo quantidade inteira maior que zero e respondendo 400 (PB11). O formato do e-mail é restrição que o código não expressa e fica como pendência.

### F18 · [MEDIUM] try/except repetido em cada handler devolvendo str(e) com 500
- **Anti-pattern:** AP16 — Tratamento de erros não centralizado
- **File:** `controllers.py:10-12` (e os outros 15 handlers do arquivo), `app.py:77-78`
- **Description:** Os 16 handlers de `controllers.py` e `/admin/query` repetem `except Exception as e: return jsonify({"erro": str(e)}), 500`. Não há `errorhandler`. O `except` também captura erros HTTP do Flask levantados dentro do `try` (JSON malformado, `Content-Type` ausente), que viram 500.
- **Impact:** Erros do cliente aparecem como falha do servidor, mensagens internas (como erros de SQL) vazam na resposta, e 404/405 de rota saem em HTML numa API JSON.
- **Recommendation:** Criar exceções de domínio e `errorhandler` centralizados, com mensagem genérica no 500 e log do erro real (PB09).

### F19 · [MEDIUM] Queries N+1 nas listagens de pedidos e contagens separadas no relatório
- **Anti-pattern:** AP13 — Queries N+1 e agregações ineficientes
- **File:** `models.py:171-201`, `models.py:203-233`, `models.py:155-156`, `models.py:239-254`
- **Description:** As duas listagens de pedidos fazem uma query de itens por pedido e uma query de produto por item. `criar_pedido` consulta o mesmo produto de novo no segundo laço. O relatório faz cinco queries (`COUNT`/`SUM`) onde uma agregação por status basta.
- **Impact:** `GET /pedidos` executa 1 + N + N×M queries, e o custo cresce com o volume de pedidos.
- **Recommendation:** Carregar itens e nomes de produto com `JOIN`/`IN`, reutilizar o produto já lido e agregar o relatório com `GROUP BY status` (PB10).

### F20 · [MEDIUM] Serialização, validação e listagem de pedidos duplicadas
- **Anti-pattern:** AP14 — Duplicação de código
- **File:** `models.py:12-21`, `models.py:31-40`, `models.py:304-313`, `models.py:79-86`, `models.py:95-102`, `models.py:171-233`, `controllers.py:28-46`, `controllers.py:72-90`
- **Description:** O dicionário de produto é montado três vezes e o de usuário duas. `get_pedidos_usuario` e `get_todos_pedidos` são idênticas exceto pelo `WHERE`. A validação de produto está copiada em criar e atualizar.
- **Impact:** Correções precisam ser feitas em vários pontos; a validação divergente de F17 nasceu dessa cópia.
- **Recommendation:** Usar um serializador por entidade, uma única função de montagem de pedidos e um validador de produto compartilhado (PB05, PB07, PB15).

### F21 · [MEDIUM] get_db() cria schema e insere seed ao conectar
- **Anti-pattern:** AP19 — Efeitos colaterais na inicialização
- **File:** `database.py:7-86`
- **Description:** A função que devolve a conexão também executa os quatro `CREATE TABLE IF NOT EXISTS` e, quando `produtos` está vazia, insere os produtos e usuários de exemplo, incluindo o administrador. Isso acontece em qualquer ambiente e não há migrações.
- **Impact:** Conectar ao banco tem efeito de escrita. Depois de um reset (F03), o próximo boot recria o administrador padrão.
- **Recommendation:** Separar conexão, criação de schema e seed em funções distintas, chamadas explicitamente na inicialização da aplicação (PB08).

### F22 · [MEDIUM] Formato de erro diferente entre endpoints
- **Anti-pattern:** AP25 — Formato de resposta sem padrão
- **File:** `controllers.py:20`, `controllers.py:142`, `controllers.py:183`, `controllers.py:206`, `controllers.py:29`, `controllers.py:292`
- **Description:** Alguns erros trazem `{"erro", "sucesso": False}` (404 de produto, 401 do login, 400 do pedido) e os demais só `{"erro"}` (404 de usuário, validações). O health usa `{"status": "erro", "detalhes"}`.
- **Impact:** O cliente não consegue tratar erros de forma uniforme.
- **Recommendation:** Emitir todos os erros pelo handler central num formato único, `{"erro", "sucesso": false}` (PB09).

### F23 · [MEDIUM] Handlers administrativos no entry point e SQL direto no controller
- **Anti-pattern:** AP24 — Responsabilidade no módulo errado
- **File:** `app.py:47-78`, `controllers.py:266-274`
- **Description:** `reset_database` e `executar_query` são definidos em `app.py`, com SQL próprio, enquanto todos os outros handlers estão em `controllers.py`. `health_check` executa `SELECT COUNT(*)` direto no controller, sem passar por `models`.
- **Impact:** O acesso a dados fica espalhado por três módulos, e o entry point não pode ser importado sem carregar handlers destrutivos.
- **Recommendation:** Mover para controller, service e model de administração e de sistema (PB05).

### F24 · [MEDIUM] CORS liberado para qualquer origem
- **Anti-pattern:** AP18 — CORS e middlewares inadequados
- **File:** `app.py:9`
- **Description:** `CORS(app)` é chamado sem lista de origens, o que libera todas as rotas, inclusive `/admin/*`, para qualquer site.
- **Impact:** Uma página de terceiros aberta no navegador de alguém da rede pode chamar a API, inclusive os endpoints destrutivos.
- **Recommendation:** Ler as origens permitidas da configuração (PB16).

### F25 · [MEDIUM] Listagens sem paginação
- **Anti-pattern:** AP20 — Listagens sem paginação
- **File:** `models.py:7`, `models.py:75`, `models.py:206`, `models.py:174`, `models.py:299`
- **Description:** `GET /produtos`, `/usuarios`, `/pedidos`, `/pedidos/usuario/<id>` e `/produtos/busca` fazem `SELECT *` sem `LIMIT` e devolvem tudo.
- **Impact:** Tempo de resposta e memória crescem com a base; em `/pedidos` o efeito se soma ao N+1 de F19.
- **Recommendation:** Adicionar paginação opcional por query string, com padrão que preserve o contrato atual (PB17).

### F26 · [LOW] Faixas de desconto, categorias e status como literais
- **Anti-pattern:** AP26 — Números e strings mágicos
- **File:** `models.py:257-262`, `controllers.py:52`, `controllers.py:242`, `controllers.py:47-50`, `models.py:150`, `models.py:247-253`, `app.py:36`, `controllers.py:285`
- **Description:** Estão soltos no código: as faixas `10000/0.1`, `5000/0.05` e `1000/0.02`; a lista de categorias; a lista de status; os limites 2 e 200 do nome; o status `'pendente'`; e a versão `"1.0.0"`, repetida em dois arquivos.
- **Impact:** Mudar uma regra exige procurar literais em vários arquivos.
- **Recommendation:** Reunir em constantes nomeadas (PB15).

### F27 · [LOW] print usado como logging, com e-mails de usuários
- **Anti-pattern:** AP27 — `print`/`console.log` como logging
- **File:** `controllers.py:161`, `controllers.py:179`, `controllers.py:182`, `controllers.py:208-210`, `app.py:56` (e outras 12 ocorrências; 19 no total)
- **Description:** Handlers e entry point usam `print` para eventos e erros. Três mensagens incluem o e-mail do usuário (cadastro, login com sucesso e login falho).
- **Impact:** Não há nível nem destino configurável, e dados pessoais vão para o stdout.
- **Recommendation:** Usar o módulo `logging` com níveis e sem dados pessoais (PB15).

### F28 · [LOW] Nomes que sombreiam builtins e cursores numerados
- **Anti-pattern:** AP28 — Nomes ruins e contexto ambíguo
- **File:** `controllers.py:14`, `controllers.py:56`, `controllers.py:64`, `controllers.py:98`, `controllers.py:136`, `models.py:24`, `models.py:54`, `models.py:65`, `models.py:89`, `models.py:187`, `models.py:191`, `models.py:219`, `models.py:223`
- **Description:** `id` é usado como parâmetro e variável local, sombreando o builtin. As listagens de pedidos usam `cursor2` e `cursor3`.
- **Impact:** Leitura mais difícil e risco de usar o builtin errado.
- **Recommendation:** Renomear para `produto_id`, `usuario_id` e nomes descritivos durante a separação em camadas (PB05). Os parâmetros de caminho das rotas não mudam.

### F29 · [LOW] Imports não usados
- **Anti-pattern:** AP29 — Código morto e imports não usados
- **File:** `models.py:2`, `database.py:2`
- **Description:** `import sqlite3` em `models.py` e `import os` em `database.py` não são referenciados (confirmado por busca de `sqlite3.` e `os.` no projeto).
- **Impact:** Ruído e falsa indicação de dependência.
- **Recommendation:** Remover durante a refatoração.

### F30 · [LOW] Caminho do banco, porta e dados do health fixos no código
- **Anti-pattern:** AP30 — Configuração não secreta fixa no código
- **File:** `database.py:5`, `app.py:88`, `app.py:85`, `controllers.py:285-288`
- **Description:** `db_path = "loja.db"` é relativo ao diretório de execução. A porta 5000 está fixa no `app.run` e na mensagem de boot. O health devolve os literais `"ambiente": "producao"` e `"debug": True`, que não refletem a configuração real.
- **Impact:** O banco muda de lugar conforme o diretório de onde se executa, e trocar a porta exige editar o código.
- **Recommendation:** Centralizar em configuração lida do ambiente, com os valores atuais como padrão (PB02).

### F31 · [LOW] Header Server revela Werkzeug e Python
- **Anti-pattern:** AP31 — Header que revela a stack
- **File:** `app.py:88`
- **Description:** A aplicação é servida por `app.run`, o servidor de desenvolvimento do Werkzeug, que envia `Server: Werkzeug/<versão> Python/<versão>` em toda resposta. Nada no código sobrescreve o header.
- **Impact:** Facilita o reconhecimento da stack e de versões vulneráveis.
- **Recommendation:** Tratar o header conforme o playbook (PB16). Trocar o servidor de desenvolvimento por um WSGI de produção exige dependência nova e fica como pendência.

### F32 · [LOW] Status e tipo sem enumeração, flag ativo sem uso e dinheiro em REAL
- **Anti-pattern:** AP32 — Modelagem de dados frágil
- **File:** `database.py:40`, `database.py:32`, `database.py:22`, `database.py:19`, `database.py:41`, `database.py:51`
- **Description:** `pedidos.status` e `usuarios.tipo` são `TEXT` livres, validados só no controller. `produtos.ativo` existe e é serializado, mas nenhuma query filtra por ele (a exclusão é física). `preco`, `total` e `preco_unitario` são `REAL`.
- **Impact:** O banco aceita estados inválidos gravados por outros caminhos (F01) e os valores monetários ficam sujeitos a arredondamento de ponto flutuante.
- **Recommendation:** Considerar `CHECK` para status e tipo e valores em centavos. Mudar o schema pode quebrar bancos existentes e o contrato, então fica como pendência.

### F33 · [LOW] Dependências transitivas sem versão fixa e sem auditoria
- **Anti-pattern:** AP22 — Dependências vulneráveis, sem uso ou sem versão fixa
- **File:** `requirements.txt:1-2`
- **Description:** O manifesto fixa só `flask` e `flask-cors`. Werkzeug, Jinja2, click, itsdangerous, blinker e MarkupSafe são resolvidos na instalação (Werkzeug 3.1.9 no `.venv` atual) e não há lockfile. `pip-audit` não está disponível no ambiente, então nenhuma vulnerabilidade pôde ser verificada.
- **Impact:** Duas instalações podem trazer versões diferentes da camada HTTP, e falhas conhecidas passam sem ser notadas.
- **Recommendation:** Fixar as transitivas num lockfile e rodar `pip-audit`. Fica como pendência, porque a regra 7 não permite instalar nem atualizar pacotes sem perguntar.

## Deprecated APIs

Nenhuma API deprecated encontrada no código-fonte.

```text
================================
Total: 33 findings
================================
```
