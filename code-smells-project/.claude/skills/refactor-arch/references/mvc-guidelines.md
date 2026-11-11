# Diretrizes da arquitetura MVC alvo — Fase 3

Estas diretrizes valem para qualquer linguagem e framework. Elas definem **o que** a estrutura final precisa cumprir; **como** fazer isso em cada stack está nos exemplos do playbook.

Em uma API, o MVC fica assim: **Model** guarda o acesso aos dados, **View** é a fronteira HTTP (rotas e formato da resposta) e **Controller** coordena cada requisição. Regras de negócio ficam numa camada de **Service** entre o controller e o model, para que nenhum dos três acumule lógica que não é sua.

## 1. Camadas e responsabilidades

| Camada | Faz | Não faz |
|---|---|---|
| **Model** | Acesso a dados de um domínio: queries parametrizadas ou ORM, mapeamento de registro para estrutura de dados, transações de escrita. | Regras de negócio, validação de entrada, uso de objetos HTTP. |
| **Service** | Regras de negócio: cálculos, transições de estado, invariantes, orquestração de vários models, efeitos colaterais (notificações, auditoria). Lança erros de domínio. | Acesso direto ao banco, uso de objetos HTTP, formatação de resposta. |
| **Controller** | Lê a requisição, valida a entrada, chama o service, escolhe o status e monta a resposta. | Acesso ao banco, regras de negócio. |
| **View (routes)** | Mapeia URL e método para o controller e aplica middlewares por rota (ex.: autenticação administrativa). | Lógica de qualquer tipo. |
| **Config** | Lê variáveis de ambiente e expõe as configurações tipadas. | Ser lida diretamente pelas camadas internas (a configuração é injetada). |
| **Middlewares** | Tratamento de erros centralizado, autenticação administrativa, CORS, logging de requisição. | Regras de negócio. |
| **Composition root** | Cria a aplicação, lê a configuração, abre o banco, instancia models, services e controllers com suas dependências, registra rotas e middlewares. | Regras de negócio ou acesso ao banco fora da inicialização. |
| **Utils** | Funções genéricas sem regra de domínio (validadores, logger, erros de aplicação). | Regra de domínio. |

"Objetos HTTP" são a requisição, a resposta e os utilitários de serialização do framework.

## 2. Regra de dependência

```text
routes → controllers → services → models → banco de dados
               ↘ utils (validadores, erros)        config → injetada pela composition root
```

- Cada camada depende só das camadas à sua direita. Nenhuma camada depende de `routes`.
- Acesso ao banco (SQL ou ORM) só aparece nos models e no módulo de banco.
- Objetos HTTP só aparecem em controllers, routes e middlewares.
- Services e models recebem suas dependências (conexão, outros models, configuração) por parâmetro ou construtor; não buscam a infraestrutura por conta própria nem a instanciam.

## 3. Layout alvo

```text
<raiz do projeto>/
├── <entry point original>    # mantido: delega à composition root e continua sendo o comando documentado
├── <manifesto de dependências>
├── .env.example              # variáveis de ambiente documentadas, sem valores reais
└── <diretório de código>/
    ├── <composition root>    # cria a aplicação e injeta as dependências
    ├── config/
    ├── database/             # conexão, schema e seed explícitos (pode ser um único módulo)
    ├── models/
    ├── services/
    ├── controllers/
    ├── routes/               # camada View
    ├── middlewares/          # tratamento de erros, autenticação administrativa
    └── utils/                # erros de aplicação, validadores, logger
```

Regras do layout:

1. **Diretório de código.** Em projeto tipo A, crie um diretório de código-fonte (`src/` ou o equivalente convencional da linguagem). Em projeto tipo B, mantenha as camadas onde o projeto já as organiza (raiz ou diretório existente). Se o framework impõe uma estrutura própria de diretórios, mapeie as camadas para ela em vez de criar uma estrutura paralela.
2. **Um módulo por domínio em cada camada,** com nomes no vocabulário do projeto e na convenção de nomes da linguagem (ex.: `pedido_model` num projeto com nomes em português e arquivos em snake_case; `courseModel` num projeto em inglês com camelCase).
3. **Módulos importáveis:** inclua o que a linguagem exige para que os diretórios sejam pacotes ou módulos (ex.: arquivo de inicialização do pacote).
4. **Entry point original preservado:** o arquivo e o comando documentados continuam sendo o ponto de partida e expõem os mesmos nomes que scripts e ferramentas importam dele.
5. **Nada além do layout:** não crie diretórios ou arquivos que nenhuma camada usa.

## 4. Estratégia por tipo

| Tipo | Estratégia |
|---|---|
| **A — Monolito** | Crie a estrutura alvo e migre domínio por domínio: model (acesso a dados seguro) → service (regras) → controller (entrada e resposta) → route (mesmo caminho e método). Ao final, apague os módulos antigos e transforme o entry point original num ponto de entrada fino. |
| **B — Camadas parciais** | Preserve os pacotes que já cumprem um papel MVC. Afine as rotas, extraia controllers e services, mova código que está no módulo errado (ex.: rotas de um recurso no módulo de outro), centralize configuração e erros, use a lógica que já existe nos models em vez de duplicá-la e remova o código morto. Não mova pastas só por estética. |
| **C — Em camadas** | Corrija os findings no lugar, sem reestruturar. |

## 5. Contrato e pontos de entrada

- Mesmos métodos, caminhos, nomes de campos de entrada e chaves das respostas de sucesso.
- Mantenha as chaves de erro que o projeto já usa (ex.: `erro` ou `error`) e aplique o mesmo formato a todos os erros.
- O comando de execução documentado continua funcionando sem argumentos extras.
- Scripts auxiliares (seed, migração) continuam funcionando com o mesmo comando; atualize os imports deles.
- O comportamento documentado da inicialização se mantém (ex.: "o banco é criado com dados de exemplo no primeiro boot"), agora de forma explícita e configurável.

## 6. Configuração

- Tudo que varia por ambiente sai do código: segredos, porta, host, caminho ou URI do banco, modo debug, origens de CORS, token administrativo.
- **Valores não secretos** têm padrão seguro para desenvolvimento: porta original, debug desligado, host `127.0.0.1`.
- **Segredos** não têm valor padrão no código. Se faltarem em desenvolvimento, gere um valor aleatório na inicialização e registre um aviso; recursos que dependem de um segredo externo (ex.: chave de gateway de pagamento) ficam desabilitados até ele ser configurado.
- Caminhos de arquivo são resolvidos a partir do diretório do projeto, não do diretório de execução.
- Variável definida mas vazia vale como ausente (usa o padrão).
- Documente cada variável em `.env.example`, sem valores reais, informando que são lidas do ambiente do processo. Só sugira um arquivo `.env` se o projeto já o carrega.

## 7. Tratamento de erros

- Uma classe de erro de aplicação (mensagem + status HTTP) lançada por services e controllers.
- Um handler central, registrado no mecanismo de erros do framework, que converte esse erro, os erros HTTP do próprio framework e as exceções inesperadas no formato padrão do projeto.
- Exceções inesperadas: log com stack trace no servidor e resposta 500 genérica, sem detalhes internos.
- Entrada inválida responde 400; recurso inexistente, 404; sem credencial administrativa, 401; recurso desabilitado, 403.
- Em código assíncrono, todo erro (rejeição de promessa, erro de callback) precisa chegar ao handler central. Nenhum erro pode escapar do ciclo da requisição e derrubar o processo.

## 8. Checklist de conformidade

Antes de encerrar a Fase 3, confirme cada item. Eles reaparecem na seção "Validation" do resumo final.

- [ ] Estrutura de diretórios segue o layout desta referência.
- [ ] Configuração extraída para módulo de config; nenhum segredo no código.
- [ ] Models abstraem os dados; não há acesso ao banco fora dos models e do módulo de banco.
- [ ] Views/Routes só fazem roteamento.
- [ ] Controllers concentram o fluxo da requisição; regras ficam em services.
- [ ] Tratamento de erros centralizado.
- [ ] Entry point claro (composition root) e o comando original continua funcionando.
- [ ] A aplicação inicia sem erros.
- [ ] Os endpoints originais respondem como no baseline, salvo as mudanças intencionais listadas.
