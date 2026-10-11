# Contrato e limites da primeira versão

## Arquitetura

O agente coleta e interpreta intenção. O coletor lê Git sem alterar o checkout. O motor valida contratos e decide de forma determinística. A primeira versão usa exclusivamente Python 3.10+ e biblioteca padrão, sem chamada automática a um provedor de modelo e sem credenciais. A análise semântica é executada pelo agente que invoca a skill, seguindo `SKILL.md`.

Hash de conteúdo detecta divergência no bundle apresentado; não constitui assinatura ou prova de origem. O analista pode editar JSON, portanto bundle e análise precisam de cadeia de custódia confiável em uma integração corporativa. O motor não comprova por conta própria a veracidade de `supported`, `scope_complete`, impacto, estado da obrigação ou resolução.

## Bundle e análise

`collect` resolve base/head para commits completos e inclui diff e documentos do head. Alterações locais não commitadas não são analisadas. Documentos precisam estar versionados no checkout; fontes externas e comparação com versões anteriores dos documentos são extensões futuras. Se a intenção mudou na própria mudança, investigar e citar o histórico relevante antes de concluir; v1 não resolve precedência documental automaticamente.

O contrato de entrada é validado estritamente por `intent_gate/core.py`; campos desconhecidos, IDs repetidos, referências inexistentes, tipos inválidos, hashes divergentes e mudança incompatível são rejeitados. O carregador CLI rejeita chaves JSON duplicadas. `examples/analysis.json` fornece um exemplo completo.

Obrigações: `satisfied`, `violated`, `unverified`, `inconclusive`, `not_applicable`. A ausência de candidatos não apaga obrigações. Uma obrigação satisfeita precisa referenciar documento e diff; isso valida vínculo mecânico, não suficiência semântica. Não aplicabilidade precisa ser justificada. Análise vazia só pode aprovar com escopo explicitamente completo e motivo; esse julgamento é responsabilidade do analista.

Candidatos: `requirement_contradiction`, `requirement_omission`, `behavior_change`, `document_conflict`, `traceability_gap`. Assessment: `supported`, `uncertain`, `text_only`, `compensated`. Resolução: `open` ou `fixed`. Confiança: `high`, `medium`, `low`, independente da severidade. Candidatos devem citar obrigação conhecida e evidência de documento e mudança.

## Rubrica inicial de consequência

| Impacto | Severidade | Critério inicial a adaptar ao domínio |
|---|---|---|
| `critical` | P0 | Consequência grave de alcance sistêmico, exposição sensível abrangente ou violação de invariante crítica; exige cenário e sustentação concreta. |
| `high` | P1 | Violação relevante de comportamento ou controle importante, com alcance e consequência demonstrados. |
| `moderate` | P2 | Consequência localizada e tratável segundo a política; sem invariante crítica violada. |
| `low` | P3 | Consequência limitada, sem obrigação impeditiva; não basta divergência textual. |

A tabela mapeia impacto estruturado a severidade determinística. Selecionar o impacto ainda envolve interpretação; não é uma medição objetiva automática. Calibrar exemplos positivos/negativos com especialistas do domínio antes de produção.

## Política e precedência

`BLOCK` → `REVIEW_REQUIRED` → `WARN` → `PASS`. Todos os motivos permanecem no resultado, mesmo se uma saída prevalece.

- Obrigação mandatória violada: BLOCK. Não mandatória violada: WARN.
- Obrigação mandatória não verificada com evidência exigida: BLOCK. Outra obrigação não verificada: REVIEW_REQUIRED.
- Obrigação inconclusiva e escopo incompleto: REVIEW_REQUIRED.
- Candidato supported, aberto e P0: BLOCK. Contradição/omissão supported, aberta e P1 ou relativa a obrigação mandatória: BLOCK.
- Hipótese uncertain P0/P1: REVIEW_REQUIRED; não reduzir impacto pela confiança. Hipótese uncertain P2/P3: WARN, salvo motivo mais forte da obrigação.
- Conflito documental ou lacuna de rastreabilidade supported de impacto alto/crítico: revisão; P0 aberto já prevalece como bloqueio nesta política conservadora.
- Mudança de comportamento sem violação demonstrada: WARN; não bloquear automaticamente por P1. P0 supported aberto segue a regra conservadora acima.
- Divergência apenas textual ou controle compensatório demonstrado: excluir com motivo. Isso não modifica automaticamente a obrigação relacionada.
- Resolução fixed não elimina obrigação violada/não verificada nem conflito estruturado. Atualizar evidências e estado da obrigação para representar uma resolução real.
- Não há autorização de waivers/aceites nesta versão. Um campo desconhecido de aceite é rejeitado.

`can_continue` depende exclusivamente de dependências de execução declaradas e validadas, nunca de BLOCK. Como a skill é independente, a situação padrão é não haver próximo estágio. Uma integração futura pode declarar o consumidor e a informação indispensável.

## Agrupamento e auditoria

Agrupar apenas por causa e correção demonstradas. O resultado preserva todos os membros e referências; a severidade do grupo é a maior dos membros. Chaves distintas não são unificadas por semelhança textual. Ordem é estável independentemente da ordem de listas. O fingerprint identifica a serialização das entradas; reordenar listas pode mudar o fingerprint sem mudar a decisão.

Exclusões, warnings, reviews, blockers e obrigações são separados. `input_fingerprint`, ref da mudança e versão da política permitem rastrear a execução. CLI exit 0 significa contrato válido e avaliação concluída, inclusive quando a decisão é BLOCK; pipelines precisam verificar `decision`. Exit 2 significa entrada inválida/evidência indisponível, sem aprovação.

## Extensões posteriores

Schemas JSON formais; adaptadores de documentos externos; evidências de código mais granulares; políticas específicas do domínio; protocolo autenticado de exceção; armazenamento auditável e assinaturas; testes semânticos com avaliações de referência; integração com Security/Coverage independentes. Não criar essas extensões sem necessidade demonstrada pela primeira avaliação.
