# Avaliação funcional local

Partição: `development`. Cadência: `cadence_1x_synthetic_playback`.
Fixtures sintéticas; avaliação com mídias representativas permanece pendente.

| Alternativa | TP | FP | FN | Precisão | Recall | F1 | p95 (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| instant | 1 | 3 | 0 | 0.2500 | 1.0000 | 0.4000 | 2.3243 |
| temporal | 1 | 3 | 0 | 0.2500 | 1.0000 | 0.4000 | 2.4790 |

O JSON registra pareamentos, erros, referências e latência por caso.

## Limites dos rótulos

- Vitals labels are episode-level, with no signal identifier; extra signal events count as unmatched under the one-to-one protocol
- No trend-specific detector implemented; trend labels are not remapped to persistent deviations
- Prescription scoring covers unexpected dose changes only; stop, unit and sequence events are reported without quality metrics
- Negative duration is last minus first observed timestamp, not the full session; short recordings do not establish long-term rates
