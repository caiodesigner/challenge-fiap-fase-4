# Avaliação funcional local

Partição: `development`. Cadência: `processing_only_accelerated`.
Fixtures sintéticas; avaliação com mídias representativas permanece pendente.

| Alternativa | TP | FP | FN | Precisão | Recall | F1 | p95 (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| instant | 1 | 6 | 1 | 0.1429 | 0.5000 | 0.2222 | 0.3957 |
| prescription_rules | 1 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0.4997 |
| temporal | 1 | 4 | 1 | 0.2000 | 0.5000 | 0.2857 | 0.4269 |

O JSON registra pareamentos, erros, referências e latência por caso.

## Limites dos rótulos

- Vitals labels are episode-level, with no signal identifier; extra signal events count as unmatched under the one-to-one protocol
- No trend-specific detector implemented; trend labels are not remapped to persistent deviations
- Prescription scoring covers unexpected dose changes only; stop, unit and sequence events are reported without quality metrics
- Negative duration is last minus first observed timestamp, not the full session; short recordings do not establish long-term rates

## Volume de alertas na fusão

7 eventos: 7 alertas isolados e 15 combinados.
Sem referências multimodais, não há precisão/recall da fusão.
