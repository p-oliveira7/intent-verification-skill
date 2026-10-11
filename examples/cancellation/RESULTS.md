# Comparação observada da simulação

O harness concluiu a execução dos três casos. Este relatório descreve o resultado local observado; a revisão independente concluída está no [relatório de validação](project/.specs/features/order-cancellation/validation.md).

## Regras de referência

PRD, TDD e spec exigem prazo inclusivo de sete dias e reembolso integral. A refatoração só altera uma variável local e mantém a assinatura pública.

| Caso | Passaram | Falharam | Erros de runner | Decisão de Intent | Continuidade |
|---|---|---|---|---|---|
| Correto | 9 | 0 | 0 | PASS | Permitida |
| Refatoração equivalente | 9 | 0 | 0 | PASS; um candidato textual excluído | Permitida |
| Regressão proposital | 7 | 2 | 0 | BLOCK; duas causas distintas | Permitida |

As duas falhas não foram escondidas ou marcadas como testes aprovados. O teste do harness passou porque verificou exatamente os resultados esperados, incluindo nomes dos testes falhos, ausência de erros e integridade do checkout.

## Efeito concreto

Para um pedido de 12345 centavos:

| Entrada | Esperado | Correto | Regressão |
|---|---|---|---|
| pending, 0 dias | cancelled, 12345, None | Igual | cancelled, 9876, None |
| pending, 7 dias | cancelled, 12345, None | Igual | rejected, 0, window_expired |
| pending, 8 dias | rejected, 0, window_expired | Igual | Igual |

## Diferença de código

```diff
- if order.days_since_purchase > 7:
+ if order.days_since_purchase >= 7:
      return Cancellation("rejected", 0, "window_expired")

- return Cancellation("cancelled", order.total_cents, None)
+ return Cancellation("cancelled", order.total_cents * 80 // 100, None)
```

O primeiro candidato relaciona CANCEL-01 à condição de prazo. O segundo relaciona CANCEL-02 à expressão do valor. Os candidatos têm causas e correções distintas, por isso não são agrupados como um único problema. Ambos contradizem obrigações mandatórias e bloqueiam aprovação pela política.

## Como reproduzir

```bash
python3 examples/cancellation/run_demo.py --out /tmp/intent-cancellation-comparison
```

Usar um diretório novo. Cada execução salva bundle, análise, implementação, resultados dos testes e resultado do gate. A interpretação de referência foi produzida pelo agente; o harness não faz uma nova inferência semântica. Não usar o resultado como evidência de detecção geral, redução de falsos positivos ou prontidão corporativa.

## Revisão independente

Seis de seis requisitos tiveram suas expectativas conferidas. Os 27 testes do hospedeiro e nove de aceitação passaram; sete mutações de comportamento foram detectadas em cópias temporárias, sem modificar o checkout. O verificador produziu análises próprias antes de consultar a referência e concordou com PASS, PASS e BLOCK para estes casos. Isso valida esta simulação, sem medir generalização para mudanças desconhecidas.
