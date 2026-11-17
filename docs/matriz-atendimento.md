# Matriz de atendimento — requisito, implementação e evidência

Escopo acadêmico local. Azure opcional conforme orientação do professor relatada
pelo autor. Implementação funcional não equivale a validação clínica. A auditoria
atual está em [auditoria-final.md](auditoria-final.md).

| ID | Frente | Código | Evidência atual | Estado e limites |
| --- | --- | --- | --- | --- |
| R01 | Vídeo e relatórios | `video.py`, `video_rules.py`, `video_ui.py` | [REHAB24-6](analise-rehab24.md) | Implementado; assimetria real demonstrada, cobertura limitada de erros |
| R02 | Alterações vocais | `acoustics.py`, `audio.py` | [SPIRA](analise-spira.md), [regressão de pausas](../reports/validation/pauses-noisy-local.json) | Pausas/energia implementadas; sem classificação clínica de fadiga/disartria |
| R03 adaptado | Transcrição local | `local_speech.py`, `audio_ui.py` | [SPIRA](analise-spira.md), [comparação Whisper](../reports/validation/speech-recognition-comparison.json) | Implementado; exige conferência da transcrição |
| R04 adaptado | Termos críticos, contexto e sentimento | `clinical_text.py`, `sentiment.py` | [Sentimentos locais](sentimentos-locais.md), gravações encenadas | Implementado; regras lexicais, sem validação representativa independente |
| R05 | Sinais vitais | `vitals.py`, `event_evaluation.py` | [Avaliação v2](../reports/evaluation/test-v2.json), [auditoria](../reports/validation/final-audit.json) | Persistência e tendência por sinal; exemplos sintéticos |
| R06 | Prescrições | `clinical_monitor.py`, `clinical_ui.py` | [Avaliação v2](../reports/evaluation/test-v2.json) | Implementado; doses/unidades sintéticas |
| R07 | Movimentação na internação | `video_rules.py`, `video.py` | [Sit-To-Stand](analise-sit-to-stand.md) | Contexto de tronco v2; cadeira demonstrada como simulação, não observação hospitalar |
| R08 | Fusão temporal | `clinical_monitor.py`, `media_alignment.py` | [Auditoria de importação](../reports/validation/final-audit.json) | Episódios e origem explícita; [política de pausas](politica-pausas-fusao.md) documentada e testada |
| R09 | Alertas e revisão | `vitals.py`, `clinical_monitor.py`, `app.py` | 167 testes e captura real das ações | Implementado no painel; identidade demonstrativa, sem autenticação de produção |
| R10 | Cadência e latência | `replay.py`, `local_evaluation.py` | [Cadência 1×](../reports/evaluation/cadence-v2.json) | Reprodução incremental; não mede sensores ou latência completa de mídia |
| R11 | Código e relatório | `README.md`, `docs/` | [Relatório PDF](relatorio-tecnico.pdf), [relatório Markdown](relatorio-tecnico.md) | Produzidos; publicar últimas alterações e registrar revisão final |
| R12 | Vídeo até 15 minutos | [Produção](producao-video.md), [roteiro](roteiro-video.md) | MP4 Full HD de 9min15s, revisado pelo autor | Publicação YouTube/Vimeo e teste do link pendentes |

Os nomes de código acima pertencem a `src/monitoramento_clinico/`, exceto
`app.py`, na raiz. As análises reais exigem modelos locais e arquivos externos;
instalação em [execucao-local.md](execucao-local.md).

Materiais de terceiros mantêm seus créditos e licenças. Mídias e vídeos gerados
permanecem em `outputs/`, ignorado pelo Git; resumos e hashes ficam em `reports/`.
O PDF original não foi alterado. Teste independente e calibração são limitações
de qualidade, sem criação de entregáveis adicionais não previstos no enunciado.
