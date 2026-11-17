# Prontidão da entrega — revisão local v2

Conforme orientação do professor comunicada pelo autor nesta conversa, o uso de
Azure é opcional. O projeto mantém processamento local e não exige configuração,
execução ou demonstração de serviços Azure. Esta atualização registra a orientação
recebida; o PDF original permanece preservado sem alterações.

A dispensa de Azure não foi interpretada como dispensa das funcionalidades:
transcrição, termos críticos, análise de sentimentos e alterações vocais.
Sentimentos estão implementados por regras lexicais locais em português, com
evidências e limitações em [sentimentos-locais.md](sentimentos-locais.md).

## Rodar

Na instalação nova, execute `make install-full`. Baixe os modelos conforme
[execucao-local.md](execucao-local.md). Nesta máquina, ambos já estão disponíveis.

```bash
make ready
make delivery
make ui
```

`make delivery` executa qualidade, testes, validação dos dados, demonstração de
fusão e avaliação das três partições sintéticas. Não baixa modelos nem publica
arquivos. Novas evidências ficam em `outputs/entrega/`. `make ready` confere o
ambiente; `python scripts/check_delivery.py --require-submission` também exige
os metadados de entrega preenchidos. Use `.venv/bin/python` ao executar scripts.

Os bancos v2 do painel são separados dos antigos: os históricos existentes são
preservados. Para as prescrições/fusão, configurações diferentes exigem banco
separado, evitando misturar decisões de regras diferentes.

## O que foi implementado

- Tendência monotônica em janela móvel de quatro segundos e pelo menos três
  amostras. A mudança mínima é 15% da amplitude configurada de cada sinal.
  São parâmetros sintéticos, configuráveis em `VitalsConfig`, sem significado
  clínico estabelecido. Artefatos e lacunas reiniciam a janela; registros
  duplicados/atrasados não avançam o detector. O estado sobrevive a reinícios.
- Eventos e referências de sinais identificam explicitamente o sinal. O
  pareamento exige essa identidade quando a referência a fornece. As referências
  v2 são derivadas da definição dos cenários, separadas das previsões. A rampa
  também inclui o desvio persistente diastólico observado por três segundos.
- Prescrições: avaliação de mudança de dose, suspensão e unidade incompatível.
  Erros de sequência têm testes funcionais, mas requerem mais casos anotados
  para métricas representativas.
- Fusão: um alerta combinado por episódio compatível, atualizado enquanto aberto;
  janela total limitada a 30 segundos, sem encadeamento temporal ilimitado.
  Alertas reconhecidos/encerrados não têm suas evidências alteradas.
- Avaliação de vídeo por relatório e intervalos manuais, com conferência do hash
  da mídia e modo de análise, separada da inferência.

## Evidências

A suíte final contém **160 testes aprovados**, além de Ruff, formatação e Mypy.
O painel respondeu HTTP 200; Whisper/MediaPipe foram conferidos em CPU.

A execução das três partições sintéticas produziu precisão/recall/F1 de 1,0 para
regras temporais de sinais, incluindo tendências. A baseline imediata produziu
precisão 0,8182, recall 1,0 e F1 0,9. As partições compartilham templates:
esses valores demonstram consistência funcional, sem estimar generalização.

A demonstração de fusão passou de sete eventos/22 alertas na revisão histórica
para sete eventos/oito alertas: sete isolados e um combinado. A redução de volume
não comprova melhora de precisão ou utilidade clínica.

As evidências atuais estão em `reports/evaluation/*-v2.json`; resultados v1 são
históricos e não comparáveis diretamente, pois as referências foram versionadas.

## Avaliar mídias da apresentação

Grave relatos naturais em WAV PCM mono, 16-bit, 16 kHz, de até 30 segundos e
vídeos com câmera fixa, uma pessoa e até 120 segundos. Anote referências antes
de consultar as previsões. Separe pessoas/locutores entre desenvolvimento e teste.
O procedimento de fala está em [validacao-local.md](validacao-local.md).

```bash
.venv/bin/python scripts/analyze_audio.py gravacoes/relato.wav --whisper --device cpu
.venv/bin/python scripts/analyze_video.py gravacoes/exercicio.mp4 --mode rehabilitation
.venv/bin/python scripts/analyze_video.py gravacoes/internacao.mp4 --mode inpatient
.venv/bin/python scripts/evaluate_video.py caminho/report.json caminho/referencia.json
```

O modelo de referência é `data/evaluation/video-reference.example.json`. Use
`labels: []` em vídeo anotado sem desvios. O nome do evento precisa corresponder
às regras, por exemplo `asymmetry`, `interruption`, `rise_candidate` ou
`activity_change`. Os relatórios podem ser importados no painel de fusão com
paciente/sessão e origem temporal explicitamente associados.

## O que ainda depende da preparação da entrega

Fala/vídeo representativos, referências humanas e teste independente não foram
fabricados nem declarados concluídos. Permanece registrada a falha de transcrição
da sonda sintética original. Confira manualmente a transcrição da demonstração.

Preencha equipe e commit em `docs/entrega.json`, revise o relatório/roteiro usando
os resultados v2, grave/publique o vídeo de até 900 segundos, confira acesso sem
login, confirme o prazo e faça a submissão. `final_submission_ready` permanece
falso até concluir esses itens e a avaliação representativa.

## Correção em gravação real com pausas

A versão `energy-pauses-v2` estima o ruído de fundo ao calcular atividade e
mantém o critério de dois segundos para pausas prolongadas. A versão
`sentiment-pt-lexicon-v2` trata “Bem, ...” introdutório como marcador discursivo.
A gravação de 17,45 s fornecida pelo autor foi reprocessada: sentimento neutro,
menção crítica e três eventos de pausas prolongadas. Evidência em
`reports/validation/pauses-noisy-local.json`. São resultados de desenvolvimento,
sem validação clínica. Reanalise arquivos para gerar relatórios com os detectores
v2; os relatórios antigos não são alterados.

## Exemplos externos de áudio — SPIRA

Foram preparados cinco exemplos de treino em `outputs/spira-review/selected/`,
com conversão e execução real. Consulte [analise-spira.md](analise-spira.md)
para escolher os arquivos, resultados esperados e limitações.

## Exemplos externos de vídeo — REHAB24-6

Foram analisados 12 trechos Arm VW e separados quatro exemplos em
`outputs/rehab24-review/selected/`. Consulte [analise-rehab24.md](analise-rehab24.md)
para cortes, rótulos originais, resultados reais e limitações de cobertura.

## Vídeos em cadeira — Sit-to-Stand

Os dois MP4 de Subject 14 foram analisados no modo Internação. O conteúdo e
formato são adequados. Com `pose-rules-v2`, o modo Internação exige ombros e
quadris, sem cotovelos: ambos ficaram avaliáveis. After gerou um candidato a
levantamento (28,8–29,8 s); before não gerou eventos confirmados. Consulte
[analise-sit-to-stand.md](analise-sit-to-stand.md) para resultados e limitações.
