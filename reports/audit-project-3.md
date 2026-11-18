```text
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.11.4 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.1.8)
Files:   15 analyzed | ~1158 lines of code
```

## Summary

CRITICAL: 3 | HIGH: 5 | MEDIUM: 10 | LOW: 7

## Findings

### F01 · [CRITICAL] Hash da senha devolvido nas respostas da API
- **Anti-pattern:** AP04 — Exposição de dados sensíveis
- **File:** `models/user.py:21`, `routes/user_routes.py:33`, `routes/user_routes.py:85-86`, `routes/user_routes.py:129`, `routes/user_routes.py:209`
- **Description:** `User.to_dict()` inclui `'password': self.password`. O dicionário é devolvido por `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e dentro de `user` no `POST /login`. Nenhuma dessas rotas exige credencial.
- **Impact:** Qualquer cliente lê o hash de qualquer conta percorrendo `GET /users/1`, `/users/2`, …; combinado com o MD5 sem salt (F02), as senhas são recuperáveis.
- **Recommendation:** Remover `password` da serialização do usuário; as demais chaves permanecem (PB04).

### F02 · [CRITICAL] Senhas guardadas com MD5 sem salt
- **Anti-pattern:** AP03 — Armazenamento inseguro de senha
- **File:** `models/user.py:27-32`
- **Description:** `set_password` grava `hashlib.md5(pwd.encode()).hexdigest()` e `check_password` compara com o mesmo cálculo. Não há salt nem função de derivação lenta.
- **Impact:** Senhas iguais geram hashes iguais e o MD5 é quebrado por tabela ou força bruta em segundos; com o F01, o hash já está exposto.
- **Recommendation:** Usar `werkzeug.security` (`generate_password_hash`/`check_password_hash`), já instalado com o Flask; como o `seed.py` recria as contas via `set_password`, não há hash legado a migrar (PB03).

### F03 · [CRITICAL] Segredos e credenciais fixos no código
- **Anti-pattern:** AP02 — Segredos e credenciais hardcoded
- **File:** `app.py:13`, `services/notification_service.py:9-10`, `seed.py:19-20`
- **Description:** `SECRET_KEY = 'super-secret-key-123'` em `app.py`; usuário e senha de SMTP (`taskmanager@gmail.com` / `senha123`) no construtor de `NotificationService`; o seed cria a conta `joao@email.com` com papel `admin` e senha fixa `1234`.
- **Impact:** Quem lê o repositório conhece a chave que passará a assinar os tokens, a credencial de e-mail e a senha da conta administrativa.
- **Recommendation:** Ler `SECRET_KEY` e as credenciais de SMTP do ambiente; a senha do admin do seed vem de `SEED_ADMIN_PASSWORD` (sem ela, senha aleatória com aviso). As contas comuns do seed mantêm as senhas (PB02).

### F04 · [HIGH] Identidade das contas desprotegida: token de fachada e papel definido pelo cliente
- **Anti-pattern:** AP10 — Autenticação ausente ou de fachada
- **File:** `routes/user_routes.py:210`, `routes/user_routes.py:52`, `routes/user_routes.py:71-78`, `routes/user_routes.py:119-122`, `routes/user_routes.py:27-40`, `routes/user_routes.py:92-151`, `routes/user_routes.py:10-25`, `routes/report_routes.py:103-155`
- **Description:** O login devolve `'fake-jwt-token-' + str(user.id)`, que nenhuma rota confere. `POST /users` aceita `role` do corpo (inclusive `admin`) e `PUT /users/<id>` troca `role`, `password`, `email` e `active` de qualquer conta. `GET /users`, `GET /users/<id>`, `DELETE /users/<id>` e `GET /reports/user/<id>` não identificam quem pede.
- **Impact:** Qualquer cliente se cadastra como administrador, troca a senha de outra conta, desativa ou exclui usuários (a exclusão apaga também as tasks deles) e lê nome e e-mail de todos.
- **Recommendation:** O login passa a emitir token assinado no campo `token` já existente; rotas de conta exigem dono ou administrador, `GET /users` e a definição de `role` exigem administrador (PB06). Restringir o que o papel `manager` pode fazer não está no código e fica como pendência.

### F05 · [HIGH] Escritas e relatório geral sem autenticação
- **Anti-pattern:** AP10 — Autenticação ausente ou de fachada
- **File:** `routes/task_routes.py:85-238`, `routes/report_routes.py:167-223`, `routes/task_routes.py:11-63`, `routes/report_routes.py:12-101`
- **Description:** `POST/PUT/DELETE /tasks` e `POST/PUT/DELETE /categories` gravam sem nenhuma credencial. `GET /tasks` devolve `user_name` de cada responsável e `GET /reports/summary` devolve `user_productivity` com nome e totais de todos os usuários, também sem credencial.
- **Impact:** Um cliente anônimo cria, altera e apaga todas as tasks e categorias e obtém o relatório de produtividade de todas as contas.
- **Recommendation:** Exigir conta autenticada nas escritas e em `GET /tasks`, e administrador em `GET /reports/summary`; as leituras sem dados pessoais continuam públicas (PB06).

### F06 · [HIGH] Debug ligado e servidor exposto em todas as interfaces
- **Anti-pattern:** AP11 — Debug ligado e servidor exposto no entry point
- **File:** `app.py:34`
- **Description:** `app.run(debug=True, host='0.0.0.0', port=5000)` está fixo no código.
- **Impact:** Com debug ligado, qualquer exceção não tratada (F09 lista várias) devolve o traceback ao cliente e o depurador do Werkzeug fica acessível pela rede.
- **Recommendation:** Debug desligado por padrão, com host, porta e debug lidos da configuração/ambiente; `python app.py` continua subindo na porta 5000 (PB02).

### F07 · [HIGH] Regras de negócio e acesso a dados dentro das rotas
- **Anti-pattern:** AP07 — Regra de negócio fora da camada de serviço
- **File:** `routes/task_routes.py:85-154`, `routes/task_routes.py:156-223`, `routes/task_routes.py:273-299`, `routes/user_routes.py:42-90`, `routes/user_routes.py:185-211`, `routes/report_routes.py:12-101`, `routes/report_routes.py:103-155`, `services/notification_service.py:4`
- **Description:** Os handlers validam campos, aplicam as regras de domínio (status, prioridade, atraso, taxa de conclusão), consultam o ORM e montam as respostas. `services/` só contém `NotificationService`, que nenhum módulo importa.
- **Impact:** Nenhuma regra pode ser testada sem subir o Flask e o banco; cada mudança de regra exige editar handlers de 60–90 linhas.
- **Recommendation:** Mover validação e regras para serviços por domínio (tasks, usuários, categorias, relatórios, autenticação) e deixar os controllers só com HTTP (PB07).

### F08 · [HIGH] Aplicação global sem factory nem configuração injetável
- **Anti-pattern:** AP09 — Acoplamento forte sem injeção de dependência
- **File:** `app.py:9-20`, `app.py:11`, `services/notification_service.py:5-10`, `services/notification_service.py:15`
- **Description:** `app` é criado e configurado no nível do módulo, com a URI do banco como literal; importar `app` já devolve a aplicação presa a `sqlite:///tasks.db`. `NotificationService` cria a própria conexão SMTP com host e credenciais internos.
- **Impact:** Não dá para subir a aplicação com outro banco (teste, validação) sem editar o código; o seed e qualquer teste herdam a configuração de produção.
- **Recommendation:** App factory (`create_app(config)`) com objeto de configuração, mantendo `app` exportado em `app.py` para o `seed.py` (PB08).

### F09 · [MEDIUM] Validação de entrada ausente ou divergente entre criar e atualizar
- **Anti-pattern:** AP15 — Validação de entrada ausente ou inconsistente
- **File:** `routes/task_routes.py:113`, `routes/task_routes.py:182`, `routes/task_routes.py:96`, `routes/task_routes.py:167`, `routes/task_routes.py:261-264`, `routes/task_routes.py:140-144`, `routes/user_routes.py:61-64`, `routes/user_routes.py:102-103`, `routes/user_routes.py:124-125`, `routes/report_routes.py:196-202`
- **Description:** `priority < 1` é comparado sem checar o tipo (string lança `TypeError` fora de qualquer `try`); `len(title)` e `len(password)`/`re.match(email)` recebem o valor cru; `int(priority)` e `int(user_id)` na busca não tratam `ValueError`; `','.join(tags)` assume lista de strings. Na atualização, `name` do usuário e da categoria aceita vazio (a criação exige), `active` aceita qualquer valor e `update_category` usa `data` sem verificar se é nulo.
- **Impact:** Entradas inválidas comuns (`"priority": "alta"`, `?priority=abc`, `"title": 123`) viram erro 500 em vez de 400; registros ficam com nome vazio ou prioridade fracionária.
- **Recommendation:** Validar tipo, faixa e obrigatoriedade num único ponto por entidade, com as mesmas regras em criar e atualizar, devolvendo 400 (PB11). Validar o formato de `color` não é aplicado em nenhum ponto do código e fica como pendência.

### F10 · [MEDIUM] Tratamento de erros repetido por handler e erros do framework em HTML
- **Anti-pattern:** AP16 — Tratamento de erros não centralizado
- **File:** `routes/task_routes.py:62`, `routes/task_routes.py:236`, `routes/user_routes.py:130`, `routes/user_routes.py:149`, `routes/report_routes.py:186`, `routes/report_routes.py:207`, `routes/report_routes.py:221` (12 `except:` sem tipo no total), `app.py:9-34`
- **Description:** Cada handler tem o próprio `try/except` em volta do commit, a maioria com `except:` sem tipo que engole qualquer erro e responde 500 genérico. `app.py` não registra nenhum `errorhandler`: 404 de rota inexistente, 405, JSON malformado e exceções fora dos `try` saem no formato HTML padrão do Flask, enquanto os handlers respondem `{"error": ...}`.
- **Impact:** O cliente recebe dois formatos de erro; falhas reais ficam sem registro porque o `except:` descarta a exceção.
- **Recommendation:** Exceções de domínio + `errorhandler` central que devolve sempre `{"error": ...}`, com rollback e log num lugar só (PB09).

### F11 · [MEDIUM] Chaves estrangeiras não aplicadas e referências inválidas aceitas
- **Anti-pattern:** AP17 — Integridade de dados e regras de estado
- **File:** `models/task.py:13-14`, `database.py:3`, `routes/task_routes.py:116-124`, `routes/task_routes.py:131-132`, `routes/task_routes.py:186-198`
- **Description:** O modelo declara `ForeignKey('users.id')` e `ForeignKey('categories.id')`, mas nenhum ponto do projeto ativa `PRAGMA foreign_keys` no SQLite. A existência do usuário/categoria só é conferida quando o valor é "verdadeiro" (`if user_id:`), e em seguida o valor é gravado como veio: `0`, `""` ou `false` são salvos em `user_id`/`category_id` sem apontar para nenhum registro.
- **Impact:** Tasks podem referenciar usuários e categorias inexistentes, e o banco não impede.
- **Recommendation:** Ativar `PRAGMA foreign_keys=ON` por conexão e aceitar apenas `null` (sem vínculo) ou um id existente (PB12). Definir quais transições de status são permitidas não está no código e fica como pendência.

### F12 · [MEDIUM] Queries N+1 e contagens em memória
- **Anti-pattern:** AP13 — Queries N+1 e agregações ineficientes
- **File:** `routes/task_routes.py:41-57`, `routes/user_routes.py:22`, `routes/report_routes.py:55-56`, `routes/report_routes.py:163`, `routes/report_routes.py:19-28`, `routes/task_routes.py:275-287`, `routes/report_routes.py:30-43`
- **Description:** `GET /tasks` faz `User.query.get` e `Category.query.get` para cada task; `GET /users` acessa `len(u.tasks)` (lazy) por usuário; o relatório consulta as tasks de cada usuário num laço e `GET /categories` faz um `count` por categoria. O resumo dispara 9 `COUNT` separados por status e prioridade, e os atrasos são contados carregando todas as tasks.
- **Impact:** O número de queries cresce com a quantidade de registros (2N+1 em `GET /tasks`); o relatório fica mais lento a cada usuário cadastrado.
- **Recommendation:** Carregar relacionamentos com join/eager loading e trocar as contagens por `GROUP BY` e filtros no banco (PB10).

### F13 · [MEDIUM] Cálculo de atraso, serialização e validações duplicados
- **Anti-pattern:** AP14 — Duplicação de código
- **File:** `routes/task_routes.py:30-39`, `routes/task_routes.py:71-80`, `routes/task_routes.py:284-287`, `routes/user_routes.py:171-180`, `routes/report_routes.py:34-36`, `routes/report_routes.py:132-135`, `models/task.py:50-60`, `routes/task_routes.py:17-28`, `routes/user_routes.py:61`, `routes/user_routes.py:106`, `utils/helpers.py:21`
- **Description:** O teste "vencida e não concluída/cancelada" aparece 6 vezes nas rotas, embora `Task.is_overdue()` já exista e nunca seja chamado. `get_tasks` remonta campo a campo o que `Task.to_dict()` devolve. A regex de e-mail está em 3 lugares, a validação de título/status/prioridade está em `create_task`, `update_task` e `process_task_data`, e a lista de status em 5 lugares.
- **Impact:** Mudar uma regra exige editar vários pontos; as cópias já divergem (mensagens de erro diferentes entre criar e atualizar).
- **Recommendation:** Uma única implementação por regra (model/serviço) e um serializador por entidade (PB05, PB07, PB15).

### F14 · [MEDIUM] CORS aberto para qualquer origem
- **Anti-pattern:** AP18 — CORS e middlewares inadequados
- **File:** `app.py:15`
- **Description:** `CORS(app)` é chamado sem lista de origens, o que libera todas as rotas para qualquer origem.
- **Impact:** Qualquer site pode chamar a API pelo navegador de um usuário, inclusive as rotas de escrita.
- **Recommendation:** Origens permitidas vindas da configuração (PB16).

### F15 · [MEDIUM] Schema criado no import do módulo
- **Anti-pattern:** AP19 — Efeitos colaterais na inicialização
- **File:** `app.py:30-31`
- **Description:** `db.create_all()` roda no nível do módulo, dentro de `with app.app_context()`: qualquer `import app` (como o do `seed.py:2`) cria o arquivo do banco e as tabelas.
- **Impact:** Importar a aplicação para testar ou inspecionar já grava no banco configurado; não há como importar sem efeito colateral.
- **Recommendation:** Levar a criação do schema para a inicialização explícita da app factory (PB08).

### F16 · [MEDIUM] Listagens devolvem todos os registros
- **Anti-pattern:** AP20 — Listagens sem paginação
- **File:** `routes/task_routes.py:14`, `routes/task_routes.py:266`, `routes/user_routes.py:12`, `routes/user_routes.py:35`, `routes/user_routes.py:159`, `routes/report_routes.py:159`
- **Description:** `GET /tasks`, `/tasks/search`, `/users`, `/users/<id>/tasks` e `/categories` devolvem o resultado de `.all()` inteiro; `GET /users/<id>` embute todas as tasks do usuário.
- **Impact:** O tamanho da resposta e o uso de memória crescem sem limite com o volume de dados.
- **Recommendation:** Paginação opcional por query string, mantendo o formato atual da resposta quando os parâmetros não são enviados (PB17).

### F17 · [MEDIUM] Uso de APIs legadas do SQLAlchemy e do `datetime`
- **Anti-pattern:** AP21 — API deprecated
- **File:** `routes/task_routes.py:42` (e outras 15 ocorrências de `.query.get(`), `models/task.py:15-16` (e outras 20 linhas com `datetime.utcnow`)
- **Description:** `Model.query.get(id)` é usado 16 vezes; no SQLAlchemy 2.1.8 instalado o método está marcado `became_legacy_20`. `datetime.utcnow` aparece em 22 linhas, inclusive como `default=` das colunas; é deprecated a partir do Python 3.12 (o ambiente usa 3.11.4).
- **Impact:** Avisos de API legada hoje e quebra futura ao atualizar SQLAlchemy ou Python.
- **Recommendation:** `db.session.get(Model, id)` e `datetime.now(timezone.utc)`, preservando o formato das datas nas respostas (PB13).

### F18 · [MEDIUM] CRUD de categorias dentro do blueprint de relatórios
- **Anti-pattern:** AP24 — Responsabilidade no módulo errado
- **File:** `routes/report_routes.py:157-223`, `routes/user_routes.py:185-211`, `utils/helpers.py:57-108`
- **Description:** As quatro rotas de `/categories` estão registradas em `report_bp`; o login fica no blueprint de usuários; `utils/helpers.py` guarda `process_task_data`, que é validação de domínio de tasks.
- **Impact:** Quem procura o código de categorias não o encontra pelo nome do arquivo; relatórios e categorias mudam juntos sem relação.
- **Recommendation:** Blueprint, controller e serviço próprios para categorias e para autenticação (PB05).

### F19 · [LOW] Dependências sem uso e transitivas sem versão fixa
- **Anti-pattern:** AP22 — Dependências vulneráveis, sem uso ou sem versão fixa
- **File:** `requirements.txt:4-6`, `requirements.txt:1-2`
- **Description:** `marshmallow`, `requests` e `python-dotenv` estão declarados e nenhum arquivo os importa. SQLAlchemy e Werkzeug não têm versão fixa: vêm por transitividade e o ambiente resolveu 2.1.8 e 3.1.9. Não há `pip-audit` no `.venv`, então vulnerabilidades conhecidas não foram verificadas.
- **Impact:** Instalações em datas diferentes produzem ambientes diferentes; pacotes sem uso aumentam a superfície sem benefício.
- **Recommendation:** Remover as três dependências sem uso, fixar SQLAlchemy e Werkzeug e rodar `pip-audit` (prioridade para `flask-cors`, que está no caminho das requisições). Fica como pendência: a skill não altera pacotes sem perguntar.

### F20 · [LOW] Código morto e imports sem uso
- **Anti-pattern:** AP29 — Código morto e imports não usados
- **File:** `services/notification_service.py:4-48`, `utils/helpers.py:9-116`, `models/task.py:38-60`, `models/user.py:34-38`, `app.py:7`, `routes/task_routes.py:7`, `routes/user_routes.py:6`, `routes/report_routes.py:7-8`, `models/task.py:3`, `utils/helpers.py:3-7`
- **Description:** `NotificationService` não é importado em lugar nenhum. Todas as funções e constantes de `utils/helpers.py` ficam sem chamada (`format_date` e `calculate_percentage` são importadas em `report_routes.py:7` e não usadas). `Task.validate_status`, `validate_priority`, `is_overdue` e `User.is_admin` nunca são chamados. Imports sem uso: `os, sys, json` (`app.py`), `json, os, sys, time` (`task_routes.py`), `hashlib, json` (`user_routes.py`), `json` (`report_routes.py`, `models/task.py`), `os, json, sys, math, hashlib` (`helpers.py`).
- **Impact:** Cerca de 170 linhas que parecem regra vigente mas não rodam, confundindo quem mantém o código.
- **Recommendation:** Passar a usar o que expressa regra real (`is_overdue`, `is_admin`, constantes) e remover o restante durante a refatoração.

### F21 · [LOW] Listas de status, papéis e limites como literais
- **Anti-pattern:** AP26 — Números e strings mágicos
- **File:** `routes/task_routes.py:96-114`, `routes/task_routes.py:177-182`, `routes/user_routes.py:64`, `routes/user_routes.py:71`, `routes/user_routes.py:120`, `routes/report_routes.py:45`, `routes/report_routes.py:129`, `routes/report_routes.py:180`, `utils/helpers.py:110-116`
- **Description:** Status válidos, papéis, faixa de prioridade 1–5, título 3–200, senha mínima 4, "alta prioridade ≤ 2", janela de 7 dias e cor `#000000` aparecem como literais nas rotas, enquanto as constantes de `utils/helpers.py:110-116` existem e não são usadas.
- **Impact:** Alterar um limite exige localizar todas as cópias.
- **Recommendation:** Módulo único de constantes usado por serviços e models (PB15).

### F22 · [LOW] `print` usado como log
- **Anti-pattern:** AP27 — `print`/`console.log` como logging
- **File:** `routes/task_routes.py:149`, `routes/task_routes.py:153`, `routes/task_routes.py:219`, `routes/task_routes.py:234`, `routes/user_routes.py:83`, `routes/user_routes.py:89`, `routes/user_routes.py:147`, `services/notification_service.py:21-24`, `utils/helpers.py:39-41`
- **Description:** 11 chamadas a `print` em handlers, serviço e helper; `user_routes.py:83` imprime o nome do usuário e `notification_service.py:21` o e-mail do destinatário.
- **Impact:** Sem nível, sem destino configurável e com dado pessoal na saída padrão.
- **Recommendation:** `logging` com logger por módulo, sem dados pessoais (PB15).

### F23 · [LOW] Banco, host, porta e SMTP fixos no código
- **Anti-pattern:** AP30 — Configuração não secreta fixa no código
- **File:** `app.py:11-12`, `app.py:34`, `services/notification_service.py:7-8`
- **Description:** A URI `sqlite:///tasks.db`, o host `0.0.0.0`, a porta `5000` e o servidor SMTP (`smtp.gmail.com:587`) são literais.
- **Impact:** Mudar de ambiente exige editar o código-fonte.
- **Recommendation:** Módulo de configuração lendo o ambiente, com os valores atuais como padrão (PB02).

### F24 · [LOW] Identificadores de uma letra e nomes numerados
- **Anti-pattern:** AP28 — Nomes ruins e contexto ambíguo
- **File:** `routes/report_routes.py:24-28`, `routes/task_routes.py:14-59`, `routes/user_routes.py:14`, `models/category.py:14`, `models/task.py:45`, `utils/helpers.py:25`, `utils/helpers.py:83`
- **Description:** `p1`…`p5` para contagens por prioridade; `t`, `u`, `c` em laços de até 45 linhas; `d`, `p`, `s` como variável ou parâmetro.
- **Impact:** Leitura mais lenta e erros fáceis nos laços longos.
- **Recommendation:** Renomear ao mover o código para serviços e controllers (PB05).

### F25 · [LOW] Tags em texto separado por vírgula e status/papel sem enumeração
- **Anti-pattern:** AP32 — Modelagem de dados frágil
- **File:** `models/task.py:18`, `models/task.py:35`, `models/task.py:11`, `models/user.py:12`
- **Description:** `tags` é uma `String(500)` unida por vírgula e separada no `to_dict`; `status` e `role` são strings livres, validadas só nas rotas.
- **Impact:** Uma tag com vírgula se divide em duas; qualquer escrita fora das rotas grava status ou papel inválido.
- **Recommendation:** Tabela de tags e enumeração no modelo. Fica como pendência: mudar o schema pode quebrar dados existentes.

## Deprecated APIs

| Uso legado | Local | Situação | Equivalente moderno |
|---|---|---|---|
| `Model.query.get(id)` | `routes/task_routes.py:42` (+ 15 ocorrências) | legado desde SQLAlchemy 2.0 (instalado: 2.1.8, marcado `became_legacy_20`) | `db.session.get(Model, id)` |
| `datetime.utcnow()` / `default=datetime.utcnow` | `models/task.py:15` (+ 21 linhas) | deprecated desde Python 3.12 (ambiente atual: 3.11.4, ainda sem aviso em runtime) | `datetime.now(timezone.utc)` |

```text
================================
Total: 25 findings
================================
```
