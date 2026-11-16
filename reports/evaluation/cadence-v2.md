# Avaliação funcional local

Partição: `development`. Cadência: `cadence_1x_synthetic_playback`.
Fixtures sintéticas; avaliação com mídias representativas permanece pendente.

| Alternativa | TP | FP | FN | Precisão | Recall | F1 | p95 (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| instant | 4 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 2.8844 |
| temporal | 4 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 2.7078 |

O JSON registra pareamentos, erros, referências e latência por caso.

## Limites dos rótulos

- Signal-specific synthetic references v2; trend and limit deviations are scored separately
- Prescription references cover dose changes, stop and unit issues; sequence errors require additional annotated cases
- Negative duration is last minus first observed timestamp, not the full session; short recordings do not establish long-term rates
