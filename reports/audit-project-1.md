```text
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3.11.4 + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
```

## Summary

CRITICAL: 8 | HIGH: 6 | MEDIUM: 12 | LOW: 8

## Findings

### F01 · [CRITICAL] Execução de SQL arbitrário sem autenticação
- **Anti-pattern:** AP06 — Endpoint administrativo ou destrutivo desprotegido
- **File:** `app.py:59-78`
- **Description:** `POST /admin/query` lê `dados.get("sql")` e passa o texto direto para `cursor.execute(query)` (`app.py:69`), com `commit` para tudo que não começa com `SELECT`. Nenhuma credencial é verificada.
- **Impact:** Qualquer cliente lê todas as tabelas (inclusive senhas), altera ou apaga dados e muda o schema com uma única requisição.
- **Recommendation:** Exigir prova de administrador (`X-Admin-Token` da configuração ou token de conta `admin`) antes de executar, mantendo caminho e chaves da resposta (PB06).

### F02 · [CRITICAL] SQL Injection em todas as queries com parâmetros
- **Anti-pattern:** AP01 — SQL Injection por concatenação
- **File:** `models.py:109-111`, `models.py:289-297`, `models.py:126-129`, `models.py:47-50`, `models.py:57-61`, `models.py:140`, `models.py:148-151`, `models.py:155-166` (e outras 9 queries: `models.py:28`, `68`, `92`, `174`, `188`, `192`, `220`, `224`, `279-281`)
- **Description:** O login monta `"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`; a busca concatena `q` e `categoria` da query string em `LIKE '%" + termo + "%'`; cadastro de usuário, criação e atualização de produto e criação de pedido (`usuario_id`, `produto_id`, `quantidade` vindos do corpo) seguem o mesmo padrão. Nenhuma query do arquivo usa placeholders. As que recebem inteiros já convertidos pela rota (`<int:id>`) são menos exploráveis, mas têm a mesma construção.
- **Impact:** Um e-mail como `admin@loja.com' --` autentica sem senha; a busca pública permite `UNION SELECT` sobre `usuarios`; os campos de texto permitem alterar ou corromper registros.
- **Recommendation:** Placeholders `?` com parâmetros separados em todas as queries; filtros dinâmicos montados só com cláusulas fixas (PB01).

### F03 · [CRITICAL] Reset do banco sem autenticação
- **Anti-pattern:** AP06 — Endpoint administrativo ou destrutivo desprotegido
- **File:** `app.py:47-57`
- **Description:** `POST /admin/reset-db` executa `DELETE FROM` em `itens_pedido`, `pedidos`, `produtos` e `usuarios` e faz commit, sem verificar credencial.
- **Impact:** Uma requisição anônima apaga todos os dados da loja; como o seed só roda quando `produtos` está vazia no momento da conexão (`database.py:56-57`), o estado só volta ao reiniciar o processo.
- **Recommendation:** Exigir prova de administrador, mantendo caminho e resposta (PB06).

### F04 · [CRITICAL] Senhas gravadas e comparadas em texto puro
- **Anti-pattern:** AP03 — Armazenamento inseguro de senha
- **File:** `models.py:126-129`, `models.py:109-111`, `database.py:75-83`, `database.py:31`
- **Description:** `criar_usuario` grava a senha recebida na coluna `senha`; o login compara a senha dentro do SQL (`AND senha = '...'`); o seed insere as três contas com senha em texto puro.
- **Impact:** Qualquer leitura do banco (F01, F02, F05 ou cópia do `loja.db`) entrega as senhas de todos os usuários.
- **Recommendation:** Hash com salt via `werkzeug.security` (já instalado) no cadastro e no seed; login busca por e-mail e confere o hash em Python; migrar no boot as senhas em texto puro já gravadas (PB03).

### F05 · [CRITICAL] Senha devolvida nas respostas de usuários
- **Anti-pattern:** AP04 — Exposição de dados sensíveis
- **File:** `models.py:83`, `models.py:99`, `controllers.py:132`, `controllers.py:140`
- **Description:** `get_todos_usuarios` e `get_usuario_por_id` incluem `"senha": row["senha"]` no dicionário que `GET /usuarios` e `GET /usuarios/<id>` devolvem.
- **Impact:** Uma requisição anônima lista e-mail e senha de todas as contas, inclusive a de administrador.
- **Recommendation:** Remover `senha` da serialização de usuário; as demais chaves permanecem (PB04).

### F06 · [CRITICAL] Health check expõe a chave secreta e a configuração interna
- **Anti-pattern:** AP04 — Exposição de dados sensíveis
- **File:** `controllers.py:286-289`
- **Description:** `GET /health` devolve `"secret_key": "minha-chave-super-secreta-123"`, `"db_path": "loja.db"`, `"debug": True` e `"ambiente": "producao"` junto com as contagens.
- **Impact:** A chave de assinatura da aplicação e detalhes internos ficam públicos; com a chave, tokens e sessões assinados podem ser forjados.
- **Recommendation:** Remover `secret_key`, `db_path`, `debug` e `ambiente` da resposta; manter `status`, `database`, `counts` e `versao` (PB04).

### F07 · [CRITICAL] Chave secreta e senha do administrador fixas no código
- **Anti-pattern:** AP02 — Segredos e credenciais hardcoded
- **File:** `app.py:7`, `controllers.py:289`, `database.py:76`
- **Description:** `SECRET_KEY` é o literal `"minha-chave-super-secreta-123"`, repetido no health check; o seed de boot cria a conta `admin@loja.com` com papel `admin` e senha fixa `admin123`.
- **Impact:** Quem lê o repositório conhece a chave de assinatura e a credencial de administrador de qualquer instalação.
- **Recommendation:** `SECRET_KEY` e token administrativo lidos do ambiente (com `.env.example`); senha do admin do seed vinda de `SEED_ADMIN_PASSWORD`, ou aleatória com aviso quando ausente; contas comuns de exemplo mantêm as senhas (PB02).

### F08 · [CRITICAL] Módulos-deus: dados, regras, serialização e rotas de todos os domínios juntos
- **Anti-pattern:** AP05 — God Class / God Module
- **File:** `models.py:1-314`, `controllers.py:1-292`, `app.py:6-78`
- **Description:** `models.py` reúne SQL, serialização e regras (estoque e total do pedido em `133-169`, faixas de desconto em `256-262`) de produtos, usuários, pedidos e relatório. `controllers.py` reúne handlers, validação, notificações e SQL do health para os mesmos domínios. `app.py` mistura configuração, registro de rotas e handlers administrativos com SQL.
- **Impact:** Qualquer mudança toca arquivos compartilhados por todos os domínios; nada pode ser testado isoladamente.
- **Recommendation:** Separar por camada e por domínio (config, database, models, services, controllers, routes, middlewares) (PB05).

### F09 · [HIGH] Identidade das contas desprotegida
- **Anti-pattern:** AP10 — Autenticação ausente ou de fachada
- **File:** `controllers.py:167-186`, `models.py:113-119`, `controllers.py:136-144`, `controllers.py:188-203`, `controllers.py:222-227`, `controllers.py:237-252`
- **Description:** O login devolve apenas `id`, `nome`, `email` e `tipo`, sem token nem sessão, e nenhuma rota verifica identidade. `GET /usuarios/<id>` e `GET /pedidos/usuario/<id>` devolvem dados de qualquer conta; `POST /pedidos` cria pedido para o `usuario_id` informado no corpo; `PUT /pedidos/<id>/status` altera o pedido de qualquer conta.
- **Impact:** Qualquer cliente lê o perfil e os pedidos de terceiros, compra em nome de outra conta e cancela ou aprova pedidos alheios.
- **Recommendation:** Login passa a emitir token assinado numa chave nova da resposta; essas rotas exigem o dono da conta ou um administrador (401 sem prova, 403 para outra conta) (PB06).

### F10 · [HIGH] Escritas no catálogo e listagens gerais sem autenticação
- **Anti-pattern:** AP10 — Autenticação ausente ou de fachada
- **File:** `app.py:14-16`, `app.py:18`, `app.py:24`, `app.py:28` (handlers em `controllers.py:24`, `64`, `98`, `128`, `229`, `257`)
- **Description:** `POST/PUT/DELETE /produtos` alteram o catálogo sem identificar quem pede; `GET /usuarios`, `GET /pedidos` e `GET /relatorios/vendas` devolvem dados de todas as contas a qualquer cliente.
- **Impact:** Um anônimo altera preços, apaga produtos e obtém a base de clientes, todos os pedidos e o faturamento.
- **Recommendation:** Escritas de produto exigem conta autenticada; as três listagens/relatório exigem administrador (PB06). Restringir a escrita de produtos ao papel `admin` é regra que o código não define e fica como pendência.

### F11 · [HIGH] Debug ligado e servidor exposto em todas as interfaces
- **Anti-pattern:** AP11 — Debug ligado e servidor exposto no entry point
- **File:** `app.py:8`, `app.py:88`
- **Description:** `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)` estão fixos no código.
- **Impact:** O debugger interativo do Werkzeug e o reloader ficam ativos e acessíveis pela rede; erros não tratados devolvem traceback com código-fonte.
- **Recommendation:** Debug, host e porta lidos do ambiente, com debug desligado e `127.0.0.1` por padrão; `python app.py` continua subindo na porta 5000 (PB02).

### F12 · [HIGH] Regras de negócio na camada de dados e nos controllers
- **Anti-pattern:** AP07 — Regra de negócio fora da camada de serviço
- **File:** `models.py:133-169`, `models.py:256-262`, `controllers.py:43-54`, `controllers.py:208-210`, `controllers.py:247-250`
- **Description:** `models.criar_pedido` verifica estoque, calcula o total e baixa o estoque no meio do SQL; `models.relatorio_vendas` aplica as faixas de desconto; os controllers validam regras de produto (faixas, categorias) e disparam as "notificações" de pedido. Não existe camada de serviço.
- **Impact:** As regras só podem ser exercitadas via HTTP com banco real e se misturam com SQL e respostas.
- **Recommendation:** Extrair serviços por domínio (produto, usuário, pedido, relatório, notificação); models só com acesso a dados e controllers só com HTTP (PB07).

### F13 · [HIGH] Conexão única global compartilhada entre requisições
- **Anti-pattern:** AP08 — Estado global mutável / conexão compartilhada
- **File:** `database.py:4`, `database.py:7-11`
- **Description:** `db_connection` é uma variável de módulo alterada via `global` e criada com `check_same_thread=False`; todas as requisições usam a mesma conexão e, portanto, a mesma transação.
- **Impact:** Com o servidor em threads, requisições concorrentes intercalam escritas na mesma transação: o `commit` de uma grava o trabalho parcial de outra.
- **Recommendation:** Conexão por requisição em `flask.g`, fechada no teardown (PB08).

### F14 · [HIGH] Camadas acopladas a `get_db()` e aplicação criada no import
- **Anti-pattern:** AP09 — Acoplamento forte sem injeção de dependência
- **File:** `app.py:6`, `app.py:49`, `app.py:66`, `controllers.py:266`, `models.py:5` (e as outras 16 funções de `models.py`), `database.py:5`
- **Description:** A aplicação é instanciada no import de `app.py`; entry point, controller e todas as funções de model chamam `get_db()` diretamente, que abre o caminho fixo `loja.db`.
- **Impact:** Não é possível criar a aplicação com outra configuração ou outro banco (testes, ambientes) sem editar o código.
- **Recommendation:** App factory (`create_app`) como composition root, com o caminho do banco vindo da configuração (PB08).

### F15 · [MEDIUM] Regras de estado do pedido anunciadas e não aplicadas
- **Anti-pattern:** AP17 — Integridade de dados e regras de estado
- **File:** `controllers.py:249-250`, `models.py:242`, `models.py:253-254`, `models.py:275-283`, `controllers.py:245-252`
- **Description:** Ao cancelar, o código imprime `"cancelado. Devolver estoque."` e não devolve o estoque. O relatório conta cancelados à parte (`models.py:253`), mas `SUM(total)` soma todos os pedidos no faturamento. `atualizar_status_pedido` faz `UPDATE` sem checar se o pedido existe e responde 200 "Status atualizado" para um id inexistente.
- **Impact:** O estoque fica menor que o real a cada cancelamento; faturamento, desconto e ticket médio saem inflados; o cliente recebe sucesso para uma operação que não aconteceu.
- **Recommendation:** Devolver o estoque na transição para `cancelado` (uma única vez), excluir cancelados do faturamento e devolver 404 para pedido inexistente (PB12). Quais transições de status são permitidas o código não declara: fica como pendência.

### F16 · [MEDIUM] Schema sem restrições e referências não verificadas
- **Anti-pattern:** AP17 — Integridade de dados e regras de estado
- **File:** `database.py:14-53`, `models.py:122-131`, `models.py:148-151`, `models.py:65-70`
- **Description:** Nenhuma tabela tem `NOT NULL`, `UNIQUE` ou `FOREIGN KEY`, e não há `PRAGMA foreign_keys`. `criar_usuario` aceita e-mail já cadastrado, embora o login busque por e-mail. `criar_pedido` grava o `usuario_id` recebido sem verificar se o usuário existe. `deletar_produto` apaga o produto e deixa `itens_pedido` apontando para ele (a listagem mostra `"Desconhecido"`, `models.py:196`).
- **Impact:** Contas duplicadas tornam o login ambíguo; pedidos órfãos e itens sem produto corrompem histórico e relatórios.
- **Recommendation:** Recusar e-mail duplicado (409) e pedido para usuário inexistente; índice único em `usuarios.email` quando os dados existentes permitirem (PB12). Impedir a exclusão de produto com pedidos é regra que o código não declara: fica como pendência.

### F17 · [MEDIUM] Pedido gravado em vários passos sem transação
- **Anti-pattern:** AP17 — Integridade de dados e regras de estado
- **File:** `models.py:139-168`
- **Description:** `criar_pedido` confere o estoque num laço, insere o pedido, insere cada item e baixa cada estoque em comandos separados, com um único `commit` no fim e nenhum `rollback`. Uma exceção no meio (ex.: item sem `quantidade`) deixa escritas pendentes na conexão global (F13), que o próximo `commit` de qualquer requisição persiste.
- **Impact:** Pedidos sem itens ou com estoque parcialmente baixado; a checagem e a baixa de estoque separadas permitem estoque negativo sob concorrência.
- **Recommendation:** Transação explícita com rollback em erro e baixa condicional (`UPDATE ... WHERE estoque >= ?`) (PB12).

### F18 · [MEDIUM] Validação de entrada ausente ou inconsistente
- **Anti-pattern:** AP15 — Validação de entrada ausente ou inconsistente
- **File:** `models.py:139-146`, `controllers.py:43-50`, `controllers.py:87-90`, `controllers.py:118-121`, `controllers.py:169-171`, `controllers.py:239-240`, `controllers.py:153-158`, `app.py:61-62`
- **Description:** Itens do pedido são usados sem checagem: `quantidade` negativa passa em `estoque < quantidade`, gera total negativo e aumenta o estoque; zero é aceito; chave ausente lança `KeyError`. `preco < 0` e `len(nome)` falham com tipo errado (`TypeError` → 500). A atualização de produto não aplica os limites de nome nem a lista de categorias exigidos na criação. `float(preco_min)` sem tratamento. Login, status do pedido e `/admin/query` chamam `dados.get` sem verificar se há corpo. E-mail não tem verificação de formato.
- **Impact:** Entradas inválidas viram 500 ou corrompem estoque e totais; um mesmo produto pode ser válido na atualização e inválido na criação.
- **Recommendation:** Validadores por recurso (tipo, faixa, obrigatórios), reutilizados em criar e atualizar, devolvendo 400 (PB11). Formato de e-mail é regra que o código não declara: fica como pendência.

### F19 · [MEDIUM] `try/except Exception` em cada handler devolvendo `str(e)`
- **Anti-pattern:** AP16 — Tratamento de erros não centralizado
- **File:** `controllers.py:10-12`, `controllers.py:60-62`, `controllers.py:185-186`, `controllers.py:218-220` (e outros 14 blocos em `controllers.py`), `app.py:77-78`
- **Description:** Os 18 handlers de `controllers.py` repetem `except Exception as e: return jsonify({"erro": str(e)}), 500`; `/admin/query` faz o mesmo. Não há `errorhandler`. Erros do cliente (corpo sem JSON, tipo errado) saem como 500, e a mensagem interna da exceção (inclusive erros de SQL) vai para o cliente.
- **Impact:** Status incorretos, vazamento de detalhes internos e tratamento duplicado 19 vezes.
- **Recommendation:** Exceções de domínio e `errorhandler` centralizados; 4xx para entrada inválida e mensagem genérica no 500 (PB09).

### F20 · [MEDIUM] Queries N+1 nas listagens de pedidos e agregações separadas
- **Anti-pattern:** AP13 — Queries N+1 e agregações ineficientes
- **File:** `models.py:187-199`, `models.py:219-231`, `models.py:140`, `models.py:155`, `models.py:239-254`, `controllers.py:269-274`
- **Description:** Para cada pedido há uma query de itens e, para cada item, uma query do nome do produto. `criar_pedido` consulta o mesmo produto duas vezes por item. O relatório faz cinco queries (`COUNT`, `SUM` e três `COUNT` por status) e o health faz três `COUNT`.
- **Impact:** O número de queries cresce com pedidos × itens; listagens ficam lentas à medida que a base cresce.
- **Recommendation:** `JOIN` de itens com produtos para os pedidos listados, reaproveitar o produto já lido e agregar com `GROUP BY status` (PB10).

### F21 · [MEDIUM] Serialização, listagem de pedidos e validação duplicadas
- **Anti-pattern:** AP14 — Duplicação de código
- **File:** `models.py:171-201`, `models.py:203-233`, `models.py:12-21`, `models.py:31-40`, `models.py:304-313`, `models.py:79-86`, `models.py:95-102`, `controllers.py:28-46`, `controllers.py:72-90`
- **Description:** `get_pedidos_usuario` e `get_todos_pedidos` diferem só no `WHERE`. O dicionário de produto aparece três vezes e o de usuário duas. A validação de produto está copiada entre criar e atualizar (e já divergiu, ver F18).
- **Impact:** Cada correção precisa ser repetida em vários pontos; as cópias já se comportam de forma diferente.
- **Recommendation:** Um serializador por entidade, uma função de listagem de pedidos com filtro opcional e um validador de produto compartilhado (PB05, PB07, PB15).

### F22 · [MEDIUM] `get_db()` conecta, cria o schema e insere o seed
- **Anti-pattern:** AP19 — Efeitos colaterais na inicialização
- **File:** `database.py:7-86`
- **Description:** A primeira chamada de `get_db()` abre a conexão, executa quatro `CREATE TABLE IF NOT EXISTS` e, se `produtos` estiver vazia, insere 10 produtos e 3 usuários (incluindo o admin), em qualquer ambiente.
- **Impact:** Não é possível abrir uma conexão sem risco de DDL e seed; o seed reaparece em qualquer base cuja tabela de produtos esteja vazia.
- **Recommendation:** Separar conexão, schema e seed em módulos próprios, executados na inicialização da aplicação; o primeiro boot continua criando `loja.db` com os dados de exemplo (PB08).

### F23 · [MEDIUM] Handlers com SQL no entry point e no controller
- **Anti-pattern:** AP24 — Responsabilidade no módulo errado
- **File:** `app.py:47-78`, `controllers.py:264-274`, `app.py:32-45`
- **Description:** As rotas `/admin/reset-db` e `/admin/query` são definidas e implementadas com SQL dentro de `app.py`; `health_check` abre cursor e executa quatro queries dentro do controller; a rota `/` também vive no entry point.
- **Impact:** Acesso a dados fora dos models e rotas espalhadas entre `add_url_rule` e decorators dificultam localizar e proteger os endpoints.
- **Recommendation:** Mover para controllers, services e models próprios (admin e sistema), deixando `app.py` só como entry point (PB05).

### F24 · [MEDIUM] Respostas de erro em formatos diferentes
- **Anti-pattern:** AP25 — Formato de resposta sem padrão
- **File:** `controllers.py:20`, `controllers.py:183`, `controllers.py:206`, `controllers.py:29`, `controllers.py:70`, `controllers.py:142`, `controllers.py:292`
- **Description:** Alguns erros devolvem `{"erro", "sucesso": False}` (404 de produto, 401 do login, 400 do pedido), outros só `{"erro"}` (404 de usuário, 400 de validação, todos os 500), e o health usa `{"status": "erro", "detalhes"}`.
- **Impact:** O cliente não consegue tratar erros de forma uniforme.
- **Recommendation:** Formato único `{"erro": ..., "sucesso": false}` produzido pelo tratamento central de erros (PB09).

### F25 · [MEDIUM] CORS aberto para qualquer origem
- **Anti-pattern:** AP18 — CORS e middlewares inadequados
- **File:** `app.py:9`
- **Description:** `CORS(app)` é aplicado sem lista de origens, liberando todas as rotas (inclusive `/admin/*`) para qualquer site.
- **Impact:** Qualquer página pode chamar a API a partir do navegador de um usuário.
- **Recommendation:** Origens permitidas lidas da configuração (PB16).

### F26 · [MEDIUM] Listagens sem paginação
- **Anti-pattern:** AP20 — Listagens sem paginação
- **File:** `models.py:7`, `models.py:75`, `models.py:206`, `models.py:174`, `models.py:299`
- **Description:** Produtos, usuários, pedidos (todos e por usuário) e a busca fazem `SELECT *` sem `LIMIT` e devolvem o resultado inteiro.
- **Impact:** Tempo e tamanho de resposta crescem sem limite, agravados pelo N+1 dos pedidos (F20).
- **Recommendation:** Paginação por parâmetros opcionais de query string, mantendo a resposta atual quando ausentes (PB17).

### F27 · [LOW] `print` como logging, com e-mails de usuários
- **Anti-pattern:** AP27 — `print`/`console.log` como logging
- **File:** `controllers.py:161`, `controllers.py:179`, `controllers.py:182`, `controllers.py:208-210`, `app.py:56` (e outras 12 ocorrências em `controllers.py` e `app.py:83-86`)
- **Description:** Há 19 chamadas a `print`: 14 em `controllers.py` e 5 em `app.py`. Três delas gravam o e-mail do usuário (cadastro, login bem-sucedido e falho).
- **Impact:** Sem níveis nem formato, e com dado pessoal na saída padrão.
- **Recommendation:** Módulo `logging` com níveis, sem dados pessoais (PB15).

### F28 · [LOW] Faixas de desconto, categorias, status e limites como literais
- **Anti-pattern:** AP26 — Números e strings mágicos
- **File:** `models.py:257-262`, `controllers.py:52`, `controllers.py:242`, `controllers.py:47-50`, `app.py:36`, `controllers.py:285`
- **Description:** Faixas `10000/5000/1000` e percentuais `0.1/0.05/0.02` do desconto, lista de categorias, lista de status, limites `2` e `200` do nome e a versão `"1.0.0"` (repetida em dois arquivos) estão soltos no código.
- **Impact:** Regras de negócio difíceis de localizar e fáceis de divergir.
- **Recommendation:** Constantes nomeadas num único lugar (PB15).

### F29 · [LOW] `id` sombreando builtin e cursores numerados
- **Anti-pattern:** AP28 — Nomes ruins e contexto ambíguo
- **File:** `controllers.py:14`, `controllers.py:56`, `controllers.py:64`, `controllers.py:98`, `controllers.py:136`, `controllers.py:160`, `models.py:24`, `models.py:54`, `models.py:65`, `models.py:89`, `models.py:187`, `models.py:191`, `models.py:219`, `models.py:223`
- **Description:** Parâmetros e variáveis chamados `id` sombreiam o builtin; as listagens de pedidos usam `cursor2` e `cursor3`.
- **Impact:** Legibilidade.
- **Recommendation:** Nomes descritivos (`produto_id`, `usuario_id`) no código interno, mantendo os nomes dos parâmetros de rota onde o contrato depende deles (aplicado durante PB05).

### F30 · [LOW] Imports e parâmetros sem uso
- **Anti-pattern:** AP29 — Código morto e imports não usados
- **File:** `database.py:2`, `models.py:2`, `models.py:122`
- **Description:** `import os` em `database.py` e `import sqlite3` em `models.py` não são usados. O parâmetro `tipo` de `criar_usuario` nunca é passado pelo único chamador (`controllers.py:160`).
- **Impact:** Ruído.
- **Recommendation:** Remover durante a refatoração.

### F31 · [LOW] Caminho do banco, host, porta e ambiente fixos no código
- **Anti-pattern:** AP30 — Configuração não secreta fixa no código
- **File:** `database.py:5`, `app.py:88`, `controllers.py:286-287`
- **Description:** `db_path = "loja.db"` é relativo ao diretório de execução; host `0.0.0.0` e porta `5000` são literais; o health devolve `"ambiente": "producao"` e `"db_path": "loja.db"` como constantes, sem relação com a configuração real.
- **Impact:** Mudar de ambiente exige editar código; o banco muda de lugar conforme o diretório de onde o comando é executado.
- **Recommendation:** Módulo de configuração lido do ambiente, com os valores atuais como padrão (PB02).

### F32 · [LOW] Header `Server` revela Werkzeug e Python
- **Anti-pattern:** AP31 — Header que revela a stack
- **File:** `app.py:88`
- **Description:** A aplicação é servida por `app.run`, o servidor de desenvolvimento do Werkzeug, que define a versão do servidor como `Werkzeug/<versão>` (`werkzeug/serving.py:816`) e a envia no header `Server` junto com a versão do Python. Nenhum código do projeto sobrescreve o header.
- **Impact:** Facilita o reconhecimento da stack e das versões por um atacante.
- **Recommendation:** Sobrescrever o header `Server` num `after_request` (PB16).

### F33 · [LOW] Status e tipo como texto livre, coluna `ativo` sem uso e valores em `REAL`
- **Anti-pattern:** AP32 — Modelagem de dados frágil
- **File:** `database.py:40`, `database.py:32`, `database.py:22`, `database.py:19`, `database.py:41`, `database.py:51`
- **Description:** `pedidos.status` e `usuarios.tipo` são `TEXT` sem `CHECK`; `produtos.ativo` existe e é devolvida, mas nenhuma query a consulta (a exclusão é física, `models.py:68`); preços e totais usam `REAL`.
- **Impact:** Valores inválidos podem ser gravados fora da aplicação; erros de arredondamento em valores monetários.
- **Recommendation:** Fica como pendência: alterar o schema pode quebrar dados existentes e o contrato.

### F34 · [LOW] Dependências transitivas sem lockfile e sem auditoria
- **Anti-pattern:** AP22 — Dependências vulneráveis, sem uso ou sem versão fixa
- **File:** `requirements.txt:1-2`
- **Description:** `flask` e `flask-cors` estão fixadas e são usadas, mas não há lockfile: Werkzeug (3.1.9 instalado), Jinja2, Click, ItsDangerous, Blinker e MarkupSafe são resolvidos na instalação. `pip-audit` não está disponível no ambiente, então vulnerabilidades conhecidas não foram verificadas.
- **Impact:** Instalações em datas diferentes podem trazer versões diferentes do servidor HTTP e do motor de templates.
- **Recommendation:** Fica como pendência: gerar um lockfile e rodar `pip-audit`; nenhum pacote é instalado ou atualizado pela refatoração.

## Deprecated APIs

Nenhuma API deprecated encontrada no código-fonte.

```text
================================
Total: 34 findings
================================
```
