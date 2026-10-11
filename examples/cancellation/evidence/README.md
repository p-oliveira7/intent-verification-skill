# Evidências preservadas da simulação

Este diretório preserva a execução observada durante a revisão independente. São dados sintéticos; não há material corporativo. Os hashes Git nos bundles identificam commits em repositórios temporários descartados, não commits publicados neste repositório. Os caminhos temporários nos logs descrevem aquela execução.

## Ordem de leitura

1. Leia o [PRD](../project/docs/PRD.md), o [TDD](../project/docs/TDD.md) e a [spec](../project/.specs/features/order-cancellation/spec.md).
2. Compare a [implementação correta](../project/cancellation.py) com a [refatoração](../variants/refactor.py) e a [regressão intencional](../variants/regression.py).
3. Leia a [comparação explicada](../RESULTS.md) e o [resumo bruto da execução](summary.json).
4. Inspecione os arquivos de cada caso abaixo e o [relatório da revisão independente](../project/.specs/features/order-cancellation/validation.md).

| Caso | Código executado | Testes observados | Triagem reproduzida | Análise independente | Triagem independente |
|---|---|---|---|---|---|
| Correto | [Código](correct/implementation.py) | [9 passaram](correct/test-results.json) | [PASS](correct/intent-result.json) | [Análise](correct-independent-analysis.json) | [PASS](correct-independent-result.json) |
| Refatoração | [Código](refactor/implementation.py) | [9 passaram](refactor/test-results.json) | [PASS](refactor/intent-result.json) | [Análise](refactor-independent-analysis.json) | [PASS](refactor-independent-result.json) |
| Regressão | [Código](regression/implementation.py) | [7 passaram; 2 falharam](regression/test-results.json) | [BLOCK](regression/intent-result.json) | [Análise](regression-independent-analysis.json) | [BLOCK](regression-independent-result.json) |

Cada pasta contém também `bundle.json` (diff e documentos com referências e hashes) e `analysis.json` (interpretação registrada usada no replay). Os arquivos `*-independent-analysis.json` foram produzidos pelo revisor antes de consultar a resposta de referência. Os respectivos resultados usam o mesmo motor de regras.

## O que foi validado

- Prazo até o sétimo dia, inclusive, e reembolso integral: comportamento correto e refatoração passam; regressão contradiz ambos.
- O bloqueio de aprovação da regressão permite continuar outras análises: `can_continue` permanece verdadeiro.
- [Sete mutações em cópias temporárias](sensor-results.json) foram detectadas pelos testes. O relatório explica o procedimento e as limitações.
- A suíte do motor e do harness teve 27 testes aprovados; a implementação correta teve 9 testes aprovados. As duas falhas intencionais da regressão são preservadas, não contabilizadas como aprovação.

## Limites e reprodução

O harness reproduz interpretações semânticas registradas; ele não chama um modelo para descobrir novos achados. A avaliação independente é uma revisão adicional deste cenário, não uma medição geral de precisão ou de falsos positivos. Os resultados brutos preservados não substituem os testes de uma mudança futura.

Para uma nova execução, siga os comandos do [guia do cenário](../README.md). Use um diretório de saída novo: os hashes dos commits temporários e os caminhos dos logs podem variar, mantendo os mesmos comportamentos esperados. Não sobrescreva estas evidências históricas com uma nova execução.
