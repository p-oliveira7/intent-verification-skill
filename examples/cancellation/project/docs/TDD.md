# TDD — Technical Design Document: cancelamento

Neste arquivo TDD significa documento de desenho técnico, não test-driven development.

## Contrato

`cancel_order(order: Order) -> Cancellation`, em Python, biblioteca padrão.

`Order` é imutável e possui `status`, `days_since_purchase` e `total_cents`. Estados aceitos: `pending`, `shipped`, `cancelled`. Idade precisa ser inteiro não negativo; total precisa ser inteiro positivo. Booleanos não são aceitos como inteiros de domínio.

`Cancellation` possui `status`, `refund_cents`, `error`. Resultado permitido: `cancelled`, total integral, `None`. Resultado repetido: `cancelled`, zero, `None`. Rejeição por prazo: `rejected`, zero, `window_expired`. Rejeição por envio: `rejected`, zero, `not_pending`.

## Ordem das regras

1. Validar campos e estado; inválido causa ValueError exato.
2. Pedido já cancelado: resultado idempotente, sem reembolso adicional.
3. Pedido enviado: rejeição, sem reembolso.
4. Pedido pendente fora do prazo: rejeição, sem reembolso.
5. Pedido pendente até o sétimo dia inclusive: cancelamento e total integral.

## Desenho e rastreabilidade

| Requisito | Mecanismo | Evidência de teste |
|---|---|---|
| CANCEL-01 | Limite inclusivo de 7 dias | Primeiro dia e sétimo dia |
| CANCEL-02 | Reembolso igual a total_cents | Valor inteiro não redondo, 12345 centavos |
| CANCEL-03 | Rejeição após 7 dias | Oitavo dia, zero e motivo exato |
| CANCEL-04 | Guarda de estado enviado | Estado shipped, zero e motivo exato |
| CANCEL-05 | Retorno idempotente | Estado cancelled, zero adicional |
| CANCEL-06 | Validação explícita | Valores negativos/zero, booleanos e estado desconhecido |

## Testes e isolamento

Testes derivam da spec e verificam todos os campos do resultado. Não usam mocks. Versões alternativas são carregadas em subprocessos e cópias temporárias, sem alterar a implementação correta ou o repositório original. Não há worktrees, stash ou dados externos.

O gate de Intent recebe diff e documentos de um Git temporário. A análise semântica registrada para cada caso é uma referência produzida pelo agente nesta sessão, não uma inferência automática realizada pelo motor de regras.

## Riscos

Implementação de regressão proposital não pode ser usada em produção. Os dois defeitos são exatamente as mudanças de prazo e percentual. Testes da variante errada devem falhar; o harness só é aprovado quando observa as falhas previstas e as distingue de erros de importação/runner. O exemplo mede integração e replay de análises registradas, sem comprovar generalização do modelo.
