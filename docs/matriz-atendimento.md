# Matriz de atendimento — requisito, código, execução e evidência

Escopo ativo: solução local. Os IDs preservam a rastreabilidade à definição
inicial. **Implementado** indica funcionalidade disponível; **parcial** indica
lacuna de implementação, validação ou entrega indicada na última coluna.

| ID | Frente | Código principal | Execução | Evidência disponível | Estado e pendência |
| --- | --- | --- | --- | --- | --- |
| R01 | Vídeo e relatório | `src/monitoramento_clinico/video.py`, `video_rules.py`, `video_ui.py` | `scripts/analyze_video.py VIDEO --mode rehabilitation` | [Modelo em CPU](../reports/video/model-smoke.json), [validação](validacao-video.md) | Implementado; avaliação com movimentos anotados pendente |
| R02 | Acústica e alterações vocais | `src/monitoramento_clinico/acoustics.py`, `audio.py` | `scripts/analyze_audio.py AUDIO` | [Demonstração acústica](../reports/audio/local-demo.json) | Medidas e referência implementadas; validação de alterações vocais pendente |
| R03 adaptado | Transcrição local | `src/monitoramento_clinico/local_speech.py`, `audio_ui.py` | `scripts/analyze_audio.py AUDIO --whisper --device cpu` | [Execução local](../reports/validation/local-stack.json), [comparação](../reports/validation/speech-recognition-comparison.json) | Implementado; termo crítico omitido na sonda original e fala natural pendente |
| R04 adaptado | Menções, contexto e sentimentos locais | `src/monitoramento_clinico/clinical_text.py`, `sentiment.py`, `speech_evaluation.py` | Painel **Áudio**, referência manual e relatório | [Validação local](validacao-local.md), `tests/test_audio.py` | Termos, negação, sujeito e tempo implementados; sentimentos locais implementados com evidências; validação representativa pendente |
| R05 | Sinais vitais | `src/monitoramento_clinico/vitals.py`, `event_evaluation.py` | `scripts/evaluate_local.py` e painel **Sinais vitais** | [Desenvolvimento](../reports/evaluation/development.json) | Implementado na revisão v2: limites persistentes, tendência e referências por sinal; validação representativa pendente |
| R06 | Histórico de prescrições | `src/monitoramento_clinico/clinical_monitor.py`, `clinical_ui.py` | `scripts/demo_clinical_fusion.py`, painel **Histórico e fusão** | [Integração](../reports/validation/stage-clinical-fusion.json) | Implementado com unidades sintéticas; referência mais ampla pendente |
| R07 | Movimentação na internação | `src/monitoramento_clinico/video_rules.py` | `scripts/analyze_video.py VIDEO --mode inpatient` | [Regras e limites](video-e-relatorios.md), `tests/test_video_rules.py` | Regras implementadas; gravações de leito/cadeira e rótulos independentes pendentes |
| R08 | Fusão temporal | `src/monitoramento_clinico/clinical_monitor.py`, `media_alignment.py` | `scripts/demo_clinical_fusion.py`, importação no painel | [Integração](../reports/validation/stage-clinical-fusion.json), [avaliação](avaliacao-resultados.md) | Implementado com agrupamento por episódio; validação da utilidade dos alertas pendente |
| R09 | Emissão e revisão de alertas | `src/monitoramento_clinico/vitals.py`, `clinical_monitor.py`, `app.py` | Painel: processar → reconhecer → encerrar | [Histórico de reprodução](../reports/vitals/replay-history.json), testes de painel e persistência | Implementado; usuário de demonstração, sem autenticação de produção |
| R10 | Cadência e latência | `src/monitoramento_clinico/replay.py`, `local_evaluation.py` | `scripts/evaluate_local.py --case development-vitals-2 --speed 1` | [Cadência 1×](../reports/evaluation/cadence-development.json) | Série gravada avaliada; sensores e latência de todas as mídias pendentes |
| R11 | Código, relatório e instruções | `README.md`, `pyproject.toml`, `docs/` | [Guia](guia-entrega.md) | [Relatório técnico](relatorio-tecnico.md), [origem](reaproveitamento-fase-3.md) | Materiais preparados; revisão final após fechar pendências experimentais |
| R12 | Vídeo de até 15 minutos | [Roteiro](roteiro-video.md) | Gravar conforme roteiro, conferir duração e link | [Estado da entrega](entrega.json) | Pendente de gravação e publicação |

Os comandos de scripts acima usam o prefixo `.venv/bin/python`. Substitua
`AUDIO`/`VIDEO` por arquivos locais apropriados. A instalação dos extras e modelos
está no guia; os comandos de mídia exigem os respectivos modelos disponíveis.

Conforme orientação do professor comunicada pelo autor nesta conversa, o uso de
Azure é opcional. O projeto mantém processamento local e não exige configuração,
execução ou demonstração de serviços Azure. Esta atualização registra a orientação
recebida; o PDF original permanece preservado sem alterações.

A dispensa de Azure não foi interpretada como dispensa das funcionalidades:
transcrição, termos críticos, análise de sentimentos e alterações vocais.
Sentimentos estão implementados por regras lexicais locais em português, com
evidências e limitações em [sentimentos-locais.md](sentimentos-locais.md).

Os relatórios em `reports/` são evidências históricas; novas execuções devem
preferir `outputs/` para não substituir resultados já documentados.
