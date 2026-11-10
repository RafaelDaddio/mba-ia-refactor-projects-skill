# Validação — Fase 3

A validação compara a aplicação refatorada com a original. A pergunta não é "responde 200?", e sim "responde como antes, exceto pelas mudanças que decidimos fazer?". Por isso o baseline vem antes de qualquer alteração.

## 1. Preparação

- **Interpretador:** Python → `.venv/Scripts/python` (Windows) ou `.venv/bin/python` (Unix); sem venv, `python3`/`python`. Node → `node`/`npm`, com `node_modules/` já instalado. Se as dependências não estiverem instaladas, pare e peça ao usuário para instalá-las (regra 6).
- **Comando e porta:** os levantados na Fase 1.
- **Arquivos de dados:** anote quais já existem (`*.db`, `*.sqlite*`, `instance/`). Você só pode apagar os que a validação criar.
- **Logs:** grave a saída do servidor fora do projeto, em `${TMPDIR:-/tmp}/refactor-arch-<projeto>-<etapa>.log`.

### Comandos de apoio (Bash)

```bash
BASE="http://127.0.0.1:<porta>"

# espera o servidor aceitar conexões (até ~30 s)
curl -s -o /dev/null --retry 30 --retry-connrefused --retry-delay 1 "$BASE<caminho GET simples>"

# requisição: imprime status e content-type; corpo salvo para inspeção
curl -s -o "${TMPDIR:-/tmp}/ra-body.json" -w "%{http_code} %{content_type}\n" -X POST \
  -H "Content-Type: application/json" --data-binary @- "$BASE/caminho" <<'EOF'
{"campo": "valor"}
EOF

# libera a porta (o modo debug do Flask cria um processo filho que sobrevive ao kill do pai)
free_port() {
  local port=$1
  if command -v lsof >/dev/null 2>&1; then
    lsof -ti tcp:"$port" | xargs -r kill -9
  else
    for pid in $(netstat -ano | grep -E "[:.]$port[[:space:]].*LISTEN" | awk '{print $NF}' | sort -u); do
      taskkill //PID "$pid" //F >/dev/null 2>&1   # Git Bash no Windows: flags com //
    done
  fi
}
```

Suba o servidor em segundo plano (na ferramenta Bash, use a execução em background), redirecionando a saída para o log. Use `--data-binary @-` com heredoc para corpos JSON: evita problemas de aspas em qualquer shell.

## 2. Plano de requisições

Monte uma lista ordenada com pelo menos uma requisição por endpoint do inventário da Fase 1. O **mesmo plano** roda no baseline e na versão refatorada.

1. **Payloads**, nesta ordem de preferência: exemplos do projeto (`*.http`, `*.rest`, README); campos obrigatórios lidos no código; IDs existentes no seed.
2. **Ordem:** leituras → criações → atualizações → exclusões de recursos criados pelo próprio plano → endpoints destrutivos globais (ex.: reset do banco) por último.
3. **Entradas válidas apenas.** O plano verifica funcionamento, não explora falhas. Para cada correção de validação, acrescente no fim **um** caso inválido que antes gerava 500, para mostrar o 4xx.
4. **Rotas administrativas:** na versão refatorada, chame sem credencial (espera-se 401/403) e com o token configurado na subida (espera-se o comportamento original). Endpoints desligados por padrão devem responder 403.
5. **Pré-requisitos:** rode antes de subir o que o README exige (ex.: `python seed.py`).

Registre por requisição: método, caminho, status, content-type e as chaves de primeiro nível do JSON (ou o tipo do corpo).

## 3. Baseline (antes de alterar qualquer arquivo)

1. Rode os pré-requisitos e suba a aplicação original com o comando original.
2. Espere a porta responder; se não subir, registre o erro do log — o baseline também documenta falhas preexistentes.
3. Execute o plano e registre os resultados.
4. Pare o processo e rode `free_port`.
5. Apague os arquivos de dados que o baseline criou (só os que não existiam antes), para a versão refatorada começar do zero.

## 4. Durante a refatoração

Ao fim de cada etapa estrutural do playbook:

- **Checagem estática:** Python → `<python> -m py_compile <arquivos alterados>`; Node → `node --check <arquivo>` em cada arquivo alterado.
- **Subida rápida:** suba, espere a porta, chame um endpoint simples, pare e libere a porta.

Corrija antes de seguir para a próxima etapa.

## 5. Validação final

1. Checagem estática de **todos** os arquivos-fonte.
2. Pré-requisitos (ex.: seed) com o comando original — ele precisa funcionar sem alterações de uso.
3. Suba com o comando original, definindo apenas as variáveis de ambiente necessárias aos testes (ex.: `ADMIN_TOKEN=validation-token`). Python: acrescente `-W default` para revelar avisos de API deprecated.
4. Leia o log: nenhum `Traceback`, `Error` ou aviso de deprecação que a refatoração deveria ter eliminado.
5. Execute o plano de requisições.
6. Compare com o baseline, requisição por requisição:

| Situação | Resultado |
|---|---|
| Mesmo status e mesmas chaves de primeiro nível | ✓ |
| Diferença listada como mudança intencional (dado sensível removido, rota administrativa protegida, 500 → 4xx para entrada inválida, formato de erro padronizado, cálculo corrigido) | ✓ com nota |
| Qualquer outra diferença | ✗ — corrigir e validar de novo |

7. Pare tudo, rode `free_port` e apague os arquivos de dados criados pela validação.

Se uma falha persistir depois de 3 tentativas de correção, pare e reporte o que falhou, a causa provável e o que falta. Não reverta arquivos com git (regra 5).

## 6. Checklist do resumo final

Cada item vira uma linha ✓/✗ na seção "Validation" do resumo da Fase 3, sempre com base no que foi executado:

- Application boots without errors (comando original, log sem erros)
- All endpoints respond correctly (n/n, incluindo as mudanças intencionais)
- MVC directory structure (`mvc-guidelines.md`, seção 3)
- Configuration extracted to a config module (nenhum segredo no código)
- Models abstract data access (nenhum SQL fora de `models/` e do módulo de banco)
- Routes only route; controllers own the request flow
- Centralized error handling
- Clear entry point (composition root) and original run command unchanged
- Auxiliary scripts still work (ex.: seed)
- No deprecation warnings at startup (quando AP21 foi encontrado)
