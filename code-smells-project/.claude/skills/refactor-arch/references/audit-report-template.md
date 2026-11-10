# Template do relatório de auditoria — Fase 2

O relatório é impresso no terminal e, se a skill recebeu um caminho como argumento, gravado nesse arquivo depois da resposta do usuário. Use exatamente a estrutura abaixo, em Markdown. Rótulos em inglês, conteúdo em português.

## Estrutura

````markdown
```text
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório do projeto>
Stack:   <linguagem> + <framework e versão>
Files:   <n> analyzed | ~<linhas> lines of code
```

## Summary

CRITICAL: <a> | HIGH: <b> | MEDIUM: <c> | LOW: <d>

## Findings

### F01 · [CRITICAL] <Título curto>
- **Anti-pattern:** AP<xx> — <nome no catálogo>
- **File:** `<arquivo>:<linha>`, `<arquivo>:<início>-<fim>`
- **Description:** <o que está errado, com a evidência que foi lida>
- **Impact:** <consequência concreta para segurança, manutenção, testes ou dados>
- **Recommendation:** <o que fazer> (PB<xx>)

### F02 · [HIGH] <Título curto>
...

## Deprecated APIs

| Uso legado | Local | Situação | Equivalente moderno |
|---|---|---|---|
| <API> | `<arquivo>:<linha>` (+ <n> ocorrências) | <deprecated/removido desde a versão X> | <substituto> |

```text
================================
Total: <N> findings
================================
```
````

## Regras

1. **Ordem:** CRITICAL → HIGH → MEDIUM → LOW. Dentro da mesma severidade, o de maior impacto primeiro. A numeração (F01, F02, …) segue essa ordem.
2. **Locais exatos:** caminho relativo à raiz do projeto, mais a linha (`models.py:110`) ou o intervalo (`models.py:171-201`). Com muitas ocorrências, liste as mais relevantes e informe o total (ex.: "`routes/tasks.py:42` e outras 15 ocorrências").
3. **Summary e Total** batem com a quantidade de findings listados.
4. **Deprecated APIs** é sempre impressa. Sem ocorrências, escreva no lugar da tabela: "Nenhuma API deprecated encontrada no código-fonte." Se houver pacotes deprecated na árvore de dependências, acrescente uma linha apontando o finding AP22 correspondente.
5. **Fora do catálogo:** use `AP-- (fora do catálogo)` no campo Anti-pattern.
6. **Sem conteúdo inventado:** cada Description cita o que foi lido; nada de "provavelmente" sem evidência.
7. O relatório **não** inclui a pergunta de confirmação; ela vem depois, fora do relatório.

## Exemplo de finding preenchido

```markdown
### F01 · [CRITICAL] SQL Injection no login e na busca
- **Anti-pattern:** AP01 — SQL Injection por concatenação
- **File:** `src/repository.py:48`, `src/repository.py:112-118` (e outras 9 queries no mesmo arquivo)
- **Description:** O login monta `"... WHERE email = '" + email + "'"` e a busca concatena o termo da query string em `LIKE '%" + termo + "%'`. Nenhuma query do arquivo usa placeholders.
- **Impact:** Um e-mail como `admin@x.com' --` autentica sem senha; a busca pública permite `UNION SELECT` e extração de qualquer tabela.
- **Recommendation:** Usar placeholders com parâmetros separados em todas as queries e montar filtros dinâmicos só com cláusulas fixas (PB01).
```
