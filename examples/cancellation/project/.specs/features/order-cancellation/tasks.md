# Order Cancellation Tasks

## Execution Protocol

Usar artefatos e gates do TLC Spec-Driven 3.3.0 como referência para esta simulação autorizada. Fonte e adaptação registradas no README do cenário. Não tratar o código de regressão como uma implementação aprovada de negócio.

**Design**: design.md
**Status**: In Progress

## Test Coverage Matrix

Guidelines: README e tests/test_intent.py do repositório hospedeiro. Padrão unittest e biblioteca padrão.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
|---|---|---|---|---|
| Documentos | none | Gates estruturais e links | docs e .specs | validate_spec.py |
| Função de cancelamento | unit | Todos os seis ACs e casos de borda | tests/test_cancellation.py | python3 -m unittest discover -s examples/cancellation/project/tests -v |
| Harness | integration | Casos equivalentes e regressão, contratos e preservação | tests/test_cancellation_demo.py | python3 -m unittest discover -s tests -v |

## Gate Check Commands

| Gate Level | When to Use | Command |
|---|---|---|
| Quick | Função pura | python3 -m unittest discover -s examples/cancellation/project/tests -v |
| Full | Harness | python3 -m unittest discover -s tests -v |
| Build | Encerramento | Executar Quick e Full; validar sintaxe e diff |

## Execution Plan

### Phase 1: Simulation

```text
T1 -> T2 -> T3
```

## Task Breakdown

### T1: Definir os artefatos da simulação

**What**: Criar PRD, TDD e specs coerentes para o mesmo comportamento.
**Where**: `examples/cancellation/project/`
**Depends on**: None
**Reuses**: Estrutura TLC v3 e contrato do repositório.
**Requirement**: CANCEL-01 até CANCEL-06
**Tests**: none
**Gate**: build
**Done when**:
- [x] Spec passa no validator estrutural oficial e todos os defaults estão explícitos.

### T2: Implementar o comportamento correto com testes

**What**: Entregar função pura e testes derivados dos seis ACs.
**Where**: `examples/cancellation/project/`
**Depends on**: T1
**Reuses**: unittest e dataclasses.
**Requirement**: CANCEL-01 até CANCEL-06
**Tests**: unit
**Gate**: quick
**Done when**:
- [x] Nove testes verificam valores exatos e todos os casos de borda passam.

### T3: Comparar variantes e alimentar a skill

**What**: Entregar harness que coleta Git, executa variantes e aplica análises de referência.
**Where**: `examples/cancellation/`
**Depends on**: T2
**Reuses**: Coletor e motor de Intent existentes.
**Requirement**: CANCEL-01 até CANCEL-06
**Tests**: integration
**Gate**: full
**Done when**:
- [ ] Versões corretas passam e regressão falha nos dois comportamentos previstos.
- [ ] Gate produz PASS para equivalente e BLOCK para violações, sem pausa.
- [ ] Reexecução preserva checkout; verificador independente escreve relatório.

## Diagram-Definition Cross-Check

| Task | Depends On | Diagram Shows | Status |
|---|---|---|---|
| T1 | None | None | Match |
| T2 | T1 | T1 | Match |
| T3 | T2 | T2 | Match |

## Test Co-location Validation

| Task | Code Layer | Matrix Requires | Task Says | Status |
|---|---|---|---|---|
| T1 | Documentos | none | none | Match |
| T2 | Função | unit | unit | Match |
| T3 | Harness | integration | integration | Match |
