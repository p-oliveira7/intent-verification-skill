# Order Cancellation Design

**Spec**: spec.md
**Status**: autorizado como desenho sintético pela solicitação de simulação.

## Architecture Overview

Função pura sobre dataclasses imutáveis. Testes carregam o módulo escolhido por caminho; por padrão, usam a implementação correta. Um harness cria um Git temporário, compara versões e passa artefatos ao coletor e motor existentes.

## Code Reuse Analysis

Reutilizar `intent_gate.collect.collect` e `intent_gate.core.evaluate`, com contrato existente. Não modificar o motor nem adicionar dependências.

## Components

- `cancellation.py`: Order, Cancellation e cancel_order.
- `tests/test_cancellation.py`: resultados ancorados na spec, sem mocks.
- Variantes: refatoração equivalente e dois defeitos propositalmente isolados.
- Harness: executar testes, coletar commits e aplicar análises de referência.

## Risks & Concerns

| Concern | Location | Impact | Mitigation |
|---|---|---|---|
| Variante errada parece código utilizável | Diretório variants | Uso fora da simulação | Marcar fixture e manter implementação correta separada |
| Confundir replay com detecção automática | Harness e README | Superestimar capacidade semântica | Registrar que interpretações são produzidas pelo agente |
| Erro de runner parece regressão detectada | Harness | Falso resultado de validação | Conferir nomes e contagem das falhas, não apenas exit não zero |

## Tech Decisions

Python existente; sem HTTP/banco; Git temporário normal, sem worktree; execução de variantes em subprocessos; resultados detalhados salvos fora do checkout por padrão.
