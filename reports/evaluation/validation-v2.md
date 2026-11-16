# Avaliação funcional local

Partição: `validation`. Cadência: `processing_only_accelerated`.
Fixtures sintéticas; avaliação com mídias representativas permanece pendente.

| Alternativa | TP | FP | FN | Precisão | Recall | F1 | p95 (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| instant | 9 | 2 | 0 | 0.8182 | 1.0000 | 0.9000 | 0.5435 |
| prescription_rules | 3 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0.5141 |
| temporal | 9 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0.4751 |

O JSON registra pareamentos, erros, referências e latência por caso.

## Limites dos rótulos

- Signal-specific synthetic references v2; trend and limit deviations are scored separately
- Prescription references cover dose changes, stop and unit issues; sequence errors require additional annotated cases
- Negative duration is last minus first observed timestamp, not the full session; short recordings do not establish long-term rates
