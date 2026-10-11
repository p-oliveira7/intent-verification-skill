# Order Cancellation Specification

## Problem Statement

Clientes precisam cancelar pedidos pendentes dentro do prazo e receber o total. Uma mudança sem alinhamento documental não pode encurtar o prazo nem reduzir o reembolso.

## Goals

- Verificar seis regras com resultados exatos.
- Comparar código correto, refatoração equivalente e regressão intencional.

## Out of Scope

| Feature | Reason |
|---|---|
| Pagamento real, HTTP e persistência | Simulação pura e isolada |
| Cálculo de datas e autenticação | Idade e estado são entradas sintéticas |
| Novo motor de análise semântica | Usar a skill existente com análise registrada pelo agente |

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
|---|---|---|---|
| Prazo | 7 dias inclusive | Criar fronteira precisa para testar intenção | Default sintético autorizado pela solicitação |
| Reembolso | 100% em centavos inteiros | Evitar arredondamento e expectativa ambígua | Default sintético |
| Repetição | Estado atualizado entregue pelo chamador | Função pura, sem persistência | Default sintético |
| Estados | pending, shipped, cancelled | Manter domínio pequeno e completo | Default sintético |

**Open questions:** none — all resolved or logged above.

## User Stories

### P1: Cancelar pedido pendente

**User Story**: Como cliente, quero cancelar dentro do prazo para receber o total.

**Why P1**: Jornada principal da simulação.

**Acceptance Criteria**:
1. WHEN um pedido pending com idade inteira entre 0 e 7 dias inclusive é cancelado THEN the system SHALL retornar status cancelled. (CANCEL-01)
2. WHEN um cancelamento é permitido THEN the system SHALL retornar refund_cents exatamente igual a total_cents e error igual a None. (CANCEL-02)
3. IF um pedido pending tem idade superior a 7 dias THEN the system SHALL retornar Cancellation(rejected, 0, window_expired). (CANCEL-03)

**Independent Test**: Executar casos de 0, 7 e 8 dias com valor de 12345 centavos.

### P1: Preservar estados e validação

**User Story**: Como cliente, quero respostas consistentes para pedidos enviados, já cancelados e inválidos.

**Why P1**: Impede cancelamento inválido e reembolso duplicado no modelo.

**Acceptance Criteria**:
1. IF o pedido está shipped THEN the system SHALL retornar Cancellation(rejected, 0, not_pending). (CANCEL-04)
2. WHEN um pedido já cancelled é solicitado novamente THEN the system SHALL retornar Cancellation(cancelled, 0, None). (CANCEL-05)
3. IF a idade não é inteiro não negativo, o total não é inteiro positivo ou o estado é desconhecido THEN the system SHALL lançar ValueError com mensagem invalid_order. (CANCEL-06)

**Independent Test**: Executar estados shipped e cancelled e entradas inválidas sem dependências externas.

## Edge Cases

- WHEN o prazo é exatamente 7 dias THEN the system SHALL permitir cancelamento com reembolso integral.
- IF uma idade ou total é booleano THEN the system SHALL lançar ValueError com mensagem invalid_order.
- IF o pedido já está cancelled com idade superior a 7 dias THEN the system SHALL retornar Cancellation(cancelled, 0, None).

## Implicit Requirement Dimensions

Validação: CANCEL-06. Repetição/estado: CANCEL-04 e CANCEL-05. Falha: motivos e exceções acima. Persistência, observabilidade, chamadas externas, concorrência, autenticação e demais dimensões N/A porque a função é pura, isolada e não modela serviços reais.

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
|---|---|---|---|
| CANCEL-01 | P1 cancelamento | Execute | Verified |
| CANCEL-02 | P1 cancelamento | Execute | Verified |
| CANCEL-03 | P1 cancelamento | Execute | Verified |
| CANCEL-04 | P1 estados | Execute | Verified |
| CANCEL-05 | P1 estados | Execute | Verified |
| CANCEL-06 | P1 validação | Execute | Verified |

Coverage: 6 total, 6 mapped to implementation and harness tasks, 0 unmapped.

## Success Criteria

- Testes de aceitação passam na implementação correta e na refatoração equivalente.
- Os mesmos testes identificam duas violações na regressão intencional.
- Intent retorna PASS para comportamento equivalente e BLOCK para as violações registradas, mantendo continuidade automática.
