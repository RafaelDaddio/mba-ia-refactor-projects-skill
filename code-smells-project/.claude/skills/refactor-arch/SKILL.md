---
name: refactor-arch
description: Audita uma codebase backend de qualquer stack contra um catálogo de anti-patterns de arquitetura, segurança e qualidade, gera um relatório ordenado por severidade e, somente após confirmação explícita do usuário, refatora o projeto para o padrão MVC e valida que a aplicação sobe e que os endpoints originais continuam respondendo.
disable-model-invocation: true
argument-hint: "[caminho-do-relatorio.md]"
---

# refactor-arch

Execute três fases, nesta ordem, sobre o projeto do diretório atual:

1. **Análise** — detectar stack e arquitetura e imprimir um resumo.
2. **Auditoria** — cruzar o código com o catálogo de anti-patterns, imprimir o relatório e **pausar** para confirmação.
3. **Refatoração** — reestruturar para MVC e validar que a aplicação continua funcionando.

O conhecimento de cada fase está em `${CLAUDE_SKILL_DIR}/references/`. Leia cada arquivo somente na fase indicada.

Caminho do relatório (argumento da skill): `$ARGUMENTS`
Se estiver vazio, o relatório da Fase 2 é apenas impresso.

## Regras invioláveis

Valem durante toda a execução, inclusive depois da confirmação.

1. **Nada muda antes do "y".** Nas Fases 1 e 2, use apenas leitura: Read, Glob, Grep e comandos de shell que não alteram nada (`ls`, `wc`, `cat`, `npm audit`). Não crie, edite, mova nem apague arquivos, não instale nada e não execute a aplicação até o usuário confirmar ao fim da Fase 2.
2. **Todo finding tem evidência.** Cite `arquivo:linha` (ou intervalo) de trechos que você leu. Não reporte o que não verificou. Não force achados para preencher o catálogo — em especial APIs deprecated: só reporte quando o uso está no código e a deprecação vale para a versão em uso ou para versões posteriores da mesma dependência.
3. **O contrato externo não muda.** Preserve métodos e caminhos dos endpoints, nomes dos campos de entrada, chaves das respostas de sucesso, comandos de execução (ex.: `python app.py`, `npm start`) e scripts auxiliares (ex.: `seed.py`). Exceções permitidas, sempre listadas no resumo final como mudanças intencionais:
   - **Remover dados sensíveis das respostas:** segredos, senhas e hashes, dados de cartão e configuração interna (chaves, caminhos, flags de debug). Contagens, versões e outros dados de negócio continuam na resposta.
   - **Exigir credencial nas rotas administrativas**, que são somente: (a) as que o próprio projeto marca como administrativas — `admin` no caminho ou no nome do handler, ou um middleware de administração já existente; (b) operações destrutivas globais — reset ou purge do banco, exclusão em massa, execução de SQL ou comandos recebidos na requisição. CRUD de um recurso individual (ex.: `DELETE /items/:id`) e leituras comuns, mesmo de dados de outros usuários, não são administrativos: a falta de autenticação nelas é finding AP10 e fica como pendência.
   - Devolver 4xx em vez de 500 para entrada inválida.
   - Padronizar o formato dos erros.
   - Corrigir comportamento errado dentro dos limites da regra 4.
4. **Sem regras de negócio novas.** Corrija um comportamento só quando houver evidência de que ele está errado:
   - **O próprio código já expressa a regra:** um log ou comentário que anuncia uma ação que não é executada; uma validação aplicada num ponto e esquecida em outro; um estado que o código distingue, mas que um cálculo ignora.
   - **O comportamento corrompe dados ou identidade:** valor negativo ou zerado onde não faz sentido no domínio (estoque, total, quantidade de um item); referência a registro inexistente; duplicata de um campo usado como chave de busca (ex.: login por e-mail); associação repetida que gera efeito em dobro (ex.: a mesma compra cobrada duas vezes).

   Restrições que o código não expressa — como quais transições de status são permitidas ou o formato de um campo — ficam como recomendação no resumo final.
5. **Ignore o que não é código do projeto:** `.git/`, `.venv/`, `venv/`, `env/`, `node_modules/`, `__pycache__/`, `instance/`, `dist/`, `build/`, `.claude/`, `*.db`, `*.sqlite*`, `*.pyc` e lockfiles (estes só para ler versões).
6. **Git pertence ao usuário.** Nunca execute `git add`, `commit`, `checkout`, `restore`, `stash`, `reset` ou `push`.
7. **Sem dependências novas.** Não instale nem atualize pacotes sem perguntar. Use a biblioteca padrão e o que já está instalado. Dependências vulneráveis ficam como pendência no resumo final.
8. **Sem arquivos avulsos.** Não crie notas, planos, `CLAUDE.md`, scripts de apoio ou documentação além do previsto em `mvc-guidelines.md` e do relatório no caminho do argumento.
9. **Validação honesta.** Só marque ✓ com evidência de execução. Se algo falhou, diga o que falhou e por quê.

## Fase 1 — Análise

1. Leia `${CLAUDE_SKILL_DIR}/references/project-analysis.md` e siga suas heurísticas.
2. Imprima o resumo dentro de um bloco de código, neste formato (campo sem informação recebe `não identificado`):

```text
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem e versão>
Framework:     <framework e versão>
Dependencies:  <dependências diretas>
Domain:        <domínio da aplicação em uma linha>
Architecture:  <A, B ou C> — <descrição curta>
Source files:  <n> files analyzed (<linhas> lines)
DB tables:     <tecnologia> — <tabelas>
Entry point:   <arquivo> — run: <comando>
================================
```

3. Em seguida, imprima o **inventário de endpoints** como tabela: método, caminho, handler (`arquivo:linha`), campos de entrada e se a rota é administrativa pela definição da regra 3. Esse inventário é o contrato que a Fase 3 preserva e a lista que ela valida.
4. Siga direto para a Fase 2, sem pedir confirmação.

## Fase 2 — Auditoria

1. Leia `${CLAUDE_SKILL_DIR}/references/anti-patterns-catalog.md` e `${CLAUDE_SKILL_DIR}/references/audit-report-template.md`.
2. **Cobertura.** Com até ~3.000 linhas de código-fonte, leia todos os arquivos-fonte inteiros e confronte cada um com todas as entradas do catálogo. Acima disso, use os sinais de detecção do catálogo para localizar candidatos e leia cada trecho antes de registrá-lo.
3. **Registro.** Para cada problema confirmado, registre anti-pattern (APxx), severidade (pelas regras do catálogo), título, locais exatos, descrição, impacto e recomendação apontando a transformação do playbook (PBxx). Ocorrências da mesma causa formam um único finding com vários locais; problemas distintos formam findings distintos, mesmo que caiam no mesmo anti-pattern.
4. **Fora do catálogo.** Problemas reais que nenhuma entrada cobre também entram, classificados pela escala do catálogo e marcados `(fora do catálogo)`.
5. Ordene por severidade (CRITICAL → HIGH → MEDIUM → LOW), numere F01, F02, … e imprima o relatório completo no formato do template.
6. Termine com exatamente esta linha, sozinha:

```text
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

**PARE AQUI.** Encerre a resposta logo após essa pergunta, sem chamar nenhuma ferramenta, e aguarde a resposta do usuário. Nenhum arquivo pode ter sido criado ou alterado até este ponto.

## Após a resposta do usuário

1. **Relatório.** Se o argumento da skill não estiver vazio, grave nesse caminho o relatório da Fase 2 exatamente como foi impresso, sem a pergunta final, criando o diretório se necessário. Faça isso qualquer que seja a resposta.
2. **Resposta negativa** (qualquer coisa diferente de `y`, `yes`, `s` ou `sim`): encerre informando que nenhum arquivo do projeto foi alterado.
3. **Resposta `y`:** siga para a Fase 3.

## Fase 3 — Refatoração e validação

1. Leia `${CLAUDE_SKILL_DIR}/references/mvc-guidelines.md`, `${CLAUDE_SKILL_DIR}/references/refactoring-playbook.md` e `${CLAUDE_SKILL_DIR}/references/validation.md`.
2. **Baseline.** Antes de alterar qualquer arquivo do projeto, siga a seção "Baseline" de `validation.md`: suba a aplicação original, execute o plano de requisições sobre o inventário de endpoints, registre status e formato de cada resposta, pare a aplicação e remova os arquivos de dados que o baseline criou.
3. **Plano.** Escolha a estratégia pelo tipo de arquitetura da Fase 1 (seção "Estratégia por tipo" de `mvc-guidelines.md`), defina a estrutura alvo e imprima-a junto com os findings que cada etapa resolve. Não peça nova confirmação.
4. **Execução.** Aplique as transformações na ordem do playbook. Recomendações do relatório que as regras 3 e 4 não permitem não são implementadas: vão para "Pending" no resumo final, com o motivo. Ao fim de cada etapa estrutural, faça a checagem estática e uma subida rápida da aplicação; corrija antes de seguir. Remova os módulos antigos substituídos e atualize os imports dos scripts auxiliares.
5. **Validação final.** Siga `validation.md`: checagem estática, subida com o comando original, o mesmo plano de requisições do baseline e a comparação. Toda diferença precisa constar da lista de mudanças intencionais; caso contrário, é falha. Corrija e valide de novo, no máximo 3 tentativas por falha; se persistir, pare e reporte.
6. **Encerramento.** Pare todos os processos que você iniciou, libere as portas e remova os arquivos de dados criados pela validação.
7. Imprima o resumo final neste formato:

````markdown
```text
================================
PHASE 3: REFACTORING COMPLETE
================================
```

## New Project Structure
```text
<árvore da nova estrutura, só código do projeto>
```

## Validation
- ✓|✗ Application boots without errors
- ✓|✗ All endpoints respond correctly (<ok>/<total>)
- ✓|✗ <demais itens do checklist de validation.md>

## Endpoints (baseline → refactored)
| Method | Path | Before | After | Note |
|---|---|---|---|---|

## Intentional behavior changes
- <mudança> — <motivo> (F<xx>)

## Findings
- Resolved: <n>/<total> — F01, F02, …
- Pending: F<xx> — <motivo>

```text
================================
```
````

Escreva "Zero anti-patterns remaining" somente se todos os findings tiverem sido resolvidos.
