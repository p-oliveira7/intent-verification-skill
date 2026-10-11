# Estado da simulação

## Decisions

- AD-001 — active: usar Python e biblioteca padrão, conforme o repositório hospedeiro.
- AD-002 — active: negócio sintético de cancelamento; prazo inclusivo e reembolso integral definidos antes do código.
- AD-003 — active: manter código correto separado das variantes defeituosas; nunca enfraquecer testes para a regressão passar.
- AD-004 — active: referência de artefatos TLC Spec-Driven 3.3.0, com EARS, IDs e gates estruturais. A documentação é adaptada para uma simulação, sem alegação de adoção integral do framework corporativo.

## Handoff

Feature: order-cancellation. Documentação, implementação e harness concluídos em commits separados. Verificação independente: seis requisitos confirmados, 27 testes do hospedeiro e nove de aceitação aprovados, sete mutações detectadas. Regressão proposital preserva duas falhas. Próximo passo: avaliar nova mudança sem consultar a análise de referência. Branch: feat/synthetic-intent-scenario.
