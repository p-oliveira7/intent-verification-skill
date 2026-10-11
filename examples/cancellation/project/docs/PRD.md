# PRD — Cancelamento de pedidos sintéticos

## Problema e objetivo

Um cliente precisa cancelar um pedido ainda não enviado e receber o valor integral. A simulação permite verificar se uma mudança preserva prazo, estado e valor do reembolso definidos pelo produto.

## Usuário e jornada

Cliente solicita cancelamento. O sistema recebe estado do pedido, dias inteiros desde a compra e valor em centavos. Retorna o estado da decisão, o reembolso e o motivo de rejeição quando aplicável.

## Regras de produto

- CANCEL-01: pedido pendente com idade entre 0 e 7 dias, inclusive, pode ser cancelado.
- CANCEL-02: cancelamento permitido devolve exatamente 100% do total em centavos.
- CANCEL-03: pedido pendente com mais de 7 dias é rejeitado com `window_expired`, sem reembolso.
- CANCEL-04: pedido enviado é rejeitado com `not_pending`, sem reembolso.
- CANCEL-05: repetir cancelamento de pedido já cancelado retorna cancelado, sem reembolso adicional.
- CANCEL-06: idade negativa, total não positivo, tipos não inteiros ou estado desconhecido causam `ValueError("invalid_order")`.

Todas são obrigatórias neste cenário. Prioridade de história P1 significa MVP; não corresponde automaticamente à severidade P1 de um achado.

## Métrica de sucesso

Todas as seis regras têm testes verificáveis. Uma refatoração equivalente não bloqueia o gate; alterar prazo ou percentual sem alterar a intenção documentada produz bloqueio fundamentado.

## Escopo e hipóteses

Valores e estados são sintéticos. Não há usuário real, banco, API HTTP, integração de pagamento ou efeito financeiro. A idade é fornecida pelo chamador; cálculo de datas e fusos está fora do escopo. A função é pura e não persiste o estado; o chamador entrega o estado atualizado na repetição.

Não há novo requisito de autorização, observabilidade, concorrência ou egress. A simulação usa somente os campos e estados definidos; não modela um comércio eletrônico completo.
