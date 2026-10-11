# Cenário sintético: cancelamento de pedidos

Este projeto demonstra Intent com artefatos de produto, desenho técnico, specs e código do mesmo domínio. Não envolve dados corporativos nem pagamento real.

## Artefatos

- [PRD](project/docs/PRD.md): objetivos e regras de produto.
- [TDD](project/docs/TDD.md): Technical Design Document e contrato.
- [Spec em EARS](project/.specs/features/order-cancellation/spec.md): seis requisitos rastreáveis.
- [Design](project/.specs/features/order-cancellation/design.md), [tasks](project/.specs/features/order-cancellation/tasks.md) e [estado](project/.specs/STATE.md).

## Referência TLC Spec-Driven v3

Formato adaptado do TLC Spec-Driven **3.3.0**, autor Felipe Rodrigues (felipfr), Tech Lead's Club, sob CC-BY-4.0. Fonte consultada: [SKILL.md oficial](https://github.com/tech-leads-club/agent-skills/blob/6df68d52028b9261058231e0f4998048c0352f45/packages/skills-catalog/skills/(development)/tlc-spec-driven/SKILL.md) e suas referências Specify, Design, Tasks e Validate. [Licença CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).

Adaptações: textos e regras originais desta simulação, em português; escopo pequeno e puro; artefatos completos mantidos para exercitar o consumidor; defaults sintéticos registrados sem decisão corporativa implícita. A referência não equivale a instalação global do TLC nem certificação de conformidade completa. Os validadores oficiais são executados a partir da cópia consultada, sem serem incorporados ao motor de Intent.

Prioridade P1 da história TLC significa MVP. Severidade P1 do Quality Gate significa impacto alto; são dimensões diferentes.

## Casos planejados

| Caso | Comportamento | Testes esperados | Intent esperado |
|---|---|---|---|
| Correto | Prazo inclusivo e reembolso integral | Passam | PASS |
| Refatoração equivalente | Mesmas regras, nomes/organização diferentes | Passam | PASS |
| Regressão intencional | Exclui o sétimo dia e reduz reembolso para 80% | Duas falhas observáveis | BLOCK, continuidade permitida |

As interpretações semânticas serão registradas pelo agente e o harness reproduzirá sua triagem. Esse replay não mede detecção autônoma ou taxa de falsos positivos de um modelo.

## Executar e inspecionar evidências

Da raiz do repositório hospedeiro:

```bash
python3 -m unittest discover -s examples/cancellation/project/tests -v
python3 examples/cancellation/run_demo.py --out /tmp/intent-cancellation-comparison
python3 -m unittest discover -s tests -v
```

O diretório de saída deve ser novo e fora do checkout. Cada caso produz `bundle.json`, `analysis.json`, `test-results.json`, `intent-result.json` e `implementation.py`; `summary.json` compara os três. Git temporário e subprocessos são descartados; o checkout original permanece intacto. O resultado de teste da regressão conserva duas falhas, não as transforma em testes aprovados.

`analysis-reference.json` preserva interpretações semânticas feitas pelo agente. IDs de evidência e head são vinculados ao bundle durante a execução; não usar essa referência em uma mudança desconhecida. Os artefatos podem alimentar uma nova análise independente, sem consultar primeiro a resposta de referência.

## Evidências esperadas

Veja a [comparação observada com mudanças de código e valores concretos](RESULTS.md).

| Caso | Passaram | Falharam | Decisão | Pausa |
|---|---|---|---|---|
| Correto | 9 | 0 | PASS | Não |
| Refatoração equivalente | 9 | 0 | PASS; um candidato textual excluído | Não |
| Regressão intencional | 7 | 2 | BLOCK; duas causas distintas | Não |

Na regressão, o teste de sétimo dia demonstra rejeição indevida; o teste de dia zero demonstra valor abaixo de 100%. O reembolso também estaria errado no sétimo dia se a condição de prazo fosse corrigida isoladamente; não confundir o número de testes falhos com o número total de condições afetadas.
