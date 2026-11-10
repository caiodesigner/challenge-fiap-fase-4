# Vídeo e relatórios de desvios

Validação funcional registrada em [validacao-video.md](validacao-video.md).

## Implementação

Vídeo local → OpenCV → MediaPipe Pose Landmarker Lite em CPU → características
posturais → regras temporais → vídeo anotado e relatórios JSON/Markdown.
Cada análise recebe UUID, horários, hash da mídia/modelo e configuração completa.
Falhas deixam relatório com status `failed`, sem declarar conclusão da análise.

O [Pose Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker)
estima pontos corporais em imagens e vídeos. O modelo leve e o SDK 0.10.35 foram
exercitados neste ambiente Python 3.14 em CPU. OpenPose/YOLO são exemplos do
enunciado; este é um estimador postural alternativo, sem dependência do treino
ou da LLM da fase 3.

Os pesos são baixados separadamente do endereço oficial versionado `float16/1`,
com verificação SHA-256 conhecido. Não são incluídos no Git. Revisar os termos
do fornecedor antes de redistribuir pesos; dependências mantêm suas próprias licenças.

## Uso

```bash
.venv/bin/python -m pip install -e '.[ui,video]'
.venv/bin/python scripts/prepare_pose_model.py
.venv/bin/python -m streamlit run app.py
```

Na barra lateral escolha **Vídeo**, selecione o contexto, envie um arquivo e
clique em **Analisar vídeo**. Os resultados anteriores permanecem disponíveis
após recarregar a página. Há download de vídeo anotado, JSON e Markdown.
Nenhuma mídia é enviada à nuvem nesta etapa.

Pré-condições: câmera fixa, uma pessoa, corpo enquadrado e taxa de quadros
constante. Limites padrão: 200 MB e 120 s; até cinco quadros/s para inferência,
imagem reduzida até 960×720. Quadros excessivamente espaçados são rejeitados.
O tempo usa índice/FPS nominal; converter vídeos com taxa variável para taxa
constante antes de analisar, para não distorcer os intervalos.

O FFmpeg no sistema permite exportar H.264/MP4 reproduzível no navegador.
Sem ele ou sem o encoder, o resultado permanece AVI/MJPEG para download.
Em Linux, OpenCV pode precisar de libGL/GLib do sistema. Não instalar múltiplas
distribuições OpenCV no mesmo ambiente, pois compartilham o módulo `cv2`.

CLI alternativa:

```bash
.venv/bin/python scripts/analyze_video.py caminho/do/video.mp4
.venv/bin/python scripts/analyze_video.py caminho/do/video.mp4 --mode inpatient
```

Resultados em `outputs/video/<run-id>/`: `report.json`, `report.md` e
`annotated.mp4` ou `annotated.avi`. Uploads ficam em `outputs/video_uploads/`.
Todos esses diretórios são locais e ignorados pelo Git.

## Regras iniciais

| Contexto | Evento | Critério exploratório |
| --- | --- | --- |
| Elevação bilateral | `asymmetry` | Diferença entre ângulos dos ombros >25° por pelo menos 1 s |
| Elevação bilateral | `interruption` | Após movimento observado, pausa na amplitude intermediária (25–140°), velocidade <5°/s por 1,5 s |
| Leito/cadeira | `rise_candidate` | Centro do tronco sobe >0,15 da altura do quadro frente à referência inicial por 1 s |
| Leito/cadeira | `activity_change` | Após referência inicial ativa de 15 deslocamentos válidos, redução persistente do movimento por 3 s |

Ângulos usam quadril, ombro e cotovelo, com correção da proporção da imagem.
Essas regras não são limites clínicos validados. `rise_candidate` não confirma
levantamento nem prevê queda; movimento de câmera pode gerar falso positivo.
Exercícios com pausas planejadas exigem revisão da regra de interrupção.

Ausência de pessoa, múltiplas poses, baixa confiança ou geometria degenerada
interrompem a confirmação. O estimador procura até duas poses para sinalizar o
limite de uma pessoa; não há garantia de detectar toda pessoa oculta/presente.
Lacunas não são preenchidas. O relatório diferencia `assessable`, `partial` e
`insufficient` e lista intervalos não avaliáveis. Ausência de desvio confirmado
não significa normalidade clínica nem normalidade nos intervalos sem confiança.

Os eventos seguem o contrato `Event`, com hash da mídia e intervalos em segundos.
Como o horário real de captura pode ser desconhecido, a origem temporal é
explicitamente atribuída ao início do processamento. Não correlacionar esse
horário automaticamente com sinais capturados em outra ocasião. A fusão e o
encaminhamento de eventos de vídeo à fila de alertas continuam na integração futura.

## Evidências e limites

- `reports/video/model-smoke.json`: inferência real em CPU, dez quadros de uma
  imagem repetida por dois segundos, todos avaliáveis e nenhum desvio. Verifica
  execução do modelo e encoder, não movimento clínico.
- `reports/video/no-person-smoke.json`: inferência real em dez quadros pretos,
  avaliação insuficiente e nenhum desvio inventado.
- Testes: simetria/assimetria, interrupção, movimento de internação, lacunas,
  qualidade, arquivo inválido e relatório automático.
- O teste completo de codificação e desvio usa backend de teste explicitamente
  identificado; não apresenta sua saída como inferência do modelo real.

A imagem de referência foi obtida do
[exemplo oficial MediaPipe](https://storage.googleapis.com/mediapipe-assets/pose.jpg).
Ela e os vídeos derivados permanecem fora do Git e não são um dataset de fisioterapia.
Para reproduzir smoke tests com pesos preparados:

```bash
.venv/bin/python scripts/demo_video.py caminho/da/imagem.jpg
.venv/bin/python scripts/demo_video.py --blank
```

Implementação e verificação funcional realizadas. Ainda faltam vídeos
representativos consentidos/licenciados, anotações independentes e calibração
para demonstrar precisão/recall em fisioterapia e internação. Nomes de arquivos,
vídeo anotado e pontos corporais não constituem anonimização certificada;
revisar relatórios de mídia real antes de publicar.
