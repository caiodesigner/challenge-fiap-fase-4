# Produção do vídeo — locução local e captura

## Estado atual

O roteiro tem 12 cenas e orçamento total de 750 segundos (12min30s).
A locução sintética foi gerada localmente com Piper 1.8.0 e a voz brasileira
`pt_BR-faber-medium`. A voz soma aproximadamente 7min07s. Todas as cenas cabem
nos intervalos previstos, reservando tempo para ações, escuta e observação.
A revisão humana de pronúncia e naturalidade permanece pendente.

Arquivos locais, ignorados pelo Git:

- `outputs/video-production/narration/locucao-continua.mp3`: fala completa sem os intervalos silenciosos; útil para revisão.
- `outputs/video-production/narration/locucao-continua.wav`: versão WAV para edição.
- `outputs/video-production/narration/locucao-sincronizada.wav`: fala por cena com silêncio ao final até completar cada intervalo do roteiro; duração de 12min30s.
- `outputs/video-production/narration/01-*.mp3` até `12-*.mp3`: cenas separadas.
- `outputs/video-production/narration/manifest.json`: duração por cena, folga e hashes.
- `outputs/video-production/voice-model/MODEL_CARD`: ficha da voz usada.

O silêncio ao final das cenas é uma marcação inicial: a montagem deve distribuir
as falas em relação às ações, inclusive pausando a voz para ouvir os pacientes.
Não basta sobrepor a faixa ao vídeo preliminar de 40 segundos. As capturas finais
precisam acompanhar as evidências especificadas no roteiro.

## Reprodução da síntese

A ferramenta de produção fica separada das dependências da aplicação. Exemplo
com ambiente próprio, sem alterar o ambiente usado para executar o projeto:

```bash
python3 -m venv /tmp/fiap-video-tts
/tmp/fiap-video-tts/bin/python -m pip install 'piper-tts==1.8.0'
/tmp/fiap-video-tts/bin/python -m piper.download_voices --data-dir outputs/video-production/voice-model pt_BR-faber-medium
/tmp/fiap-video-tts/bin/python scripts/generate_video_narration.py --model outputs/video-production/voice-model/pt_BR-faber-medium.onnx
```

FFmpeg também deve estar instalado. O download do motor e dos pesos requer
internet; a síntese não envia os textos a um serviço externo. O script preserva
texto preparado por cena e usa ajustes de pronúncia para nomes técnicos.
Regerar após alterar o roteiro e conferir novamente a duração.

## Créditos e limites

Voz: Piper, `pt_BR-faber-medium`.
[Ficha do modelo](https://huggingface.co/rhasspy/piper-voices/blob/main/pt/pt_BR/faber/medium/MODEL_CARD).
A ficha informa dataset sob CC0 e registra o modelo-base utilizado no treinamento.
O motor e suas dependências mantêm suas próprias licenças.
Esta voz não é uma clonagem da voz do autor. Identificar “Locução sintética”
no vídeo final. As vozes dos pacientes nas mídias de demonstração são distintas
da narração e não devem ser substituídas por essa síntese.

## Próximas ações de montagem

1. Revisar pronúncia, ritmo e qualidade da locução, começando pela cena 01.
2. Capturar as cenas reais do roteiro, incluindo tendência, revisão de alertas e importações.
3. Preservar cadência 1× nas reproduções correspondentes; sinalizar cortes de espera em outros processamentos.
4. Sincronizar ações, voz e evidências; adicionar legendas e créditos.
5. Exportar e revisar o MP4 completo antes de publicar. A duração deve ser ≤ 900 segundos.

O vídeo final não está concluído nem publicado. `docs/entrega.json` preserva
essa pendência; a produção da locução não equivale à gravação final.

## Padrão visual das capturas finais

As novas capturas usam a aplicação real em **1920×1080, proporção 16:9**, com
preferência de sistema por tema escuro no navegador automatizado. Não foi
necessário alterar cores ou componentes do projeto. A imagem de conferência
fica em `outputs/video-production/fullhd/preview.png`.

O script `scripts/capture_video_demo.mjs` utiliza o screencast do Chrome via CDP,
com quadros de origem variáveis limitados a 15 por segundo. A exportação para MP4
usa 30 FPS; isso não cria movimento adicional nos quadros da origem.
Os tempos de captura são medidos por relógio monotônico. As cenas são separadas
para montagem; falhas de automação são registradas e devem ser regravadas.
Os clipes são silenciosos; a fala original dos áudios clínicos, quando necessária,
deve ser inserida a partir do arquivo de entrada em trecho identificado.

Para reutilizar, iniciar Chrome com depuração local na porta 9223 e a aplicação
na porta 8501, em um perfil de navegador reservado à produção. Então:

```bash
node scripts/capture_video_demo.mjs
```

`CAPTURE_DIR` permite escolher outro diretório para uma nova tomada e
`ONLY_SCENES=3,4` limita a execução às cenas indicadas. Cada tomada guarda quadros,
tempos e status. O script executa testes e pode reconhecer/encerrar alertas de
cenários sintéticos no banco local; não deve apontar para uma aplicação clínica.

## Tomada Full HD disponível

Arquivo: `outputs/video-production/fullhd/demonstracao-fullhd-sem-locucao.mp4`.
Exportação conferida: H.264, 1920×1080, 16:9, 30 FPS, 5min45,2s, sem áudio.
O arquivo foi decodificado integralmente com FFmpeg sem erros.
Inclui cenas 03 a 11: fisioterapia, cadeira, SPIRA, sentimentos/negação,
sinais, revisão de alerta, prescrições e importação de eventos para fusão.
As duas cenas de fisioterapia usadas na montagem são a tomada corrigida em
`outputs/video-production/fullhd-fisioterapia/`; as tomadas anteriores com
falha de automação foram excluídas da montagem.

A gravação contém esperas e navegação a editar. Não é o vídeo final de 12min30s:
faltam abertura, arquitetura, encerramento, créditos, legendas e sincronização
da locução. A proporção dos quadros é preservada na exportação com preenchimento
quando necessário. A interface usa tema escuro; o fundo branco dentro do vídeo
Sit-To-Stand pertence à mídia original e foi preservado.

## Primeira montagem narrada

A primeira montagem usa as 12 cenas do roteiro, com cartelas de apresentação,
arquitetura e encerramento. As capturas da aplicação mantêm a velocidade de
origem; onde é necessário prolongar a explicação, uma pausa de imagem é
identificada na tela. Não se afirma cadência de sensor ou latência clínica.

A fala foi alinhada automaticamente por palavras usando Whisper e o texto do
roteiro, evitando adotar como legenda os erros da transcrição de conferência.
O alinhamento requer revisão humana. Na cena de sinais vitais foi inserida uma
pausa de voz para acompanhar a troca do cenário persistente para o de tendência.
A cena SPIRA inclui um trecho real de 7,5 segundos do áudio de paciente, entre
11 e 18,5 segundos da entrada, sem sobrepor a voz do narrador.

Artefatos locais em `outputs/video-production/edit/`:

- `tech-challenge-caio-v1.mp4`: primeira montagem completa para revisão.
- `legendas-completas.srt`: legendas separadas, também incorporadas visualmente ao MP4.
- `assembly-manifest.json`: duração, hash, capítulos e fontes.
- `card-01.png`, `card-02.png`, `card-12.png`: cartelas utilizadas.
- `tools/`: scripts locais de alinhamento e montagem, dependentes dos artefatos desta produção.

A montagem ficou mais curta que o orçamento inicial de 12min30s: a duração
planejada era uma reserva, e não um objetivo de preencher tempo. Antes de publicar,
assistir ao MP4 integralmente e conferir pronúncia, sincronismo, legibilidade,
resultados, créditos e acesso ao repositório. O estado continua como rascunho,
sem URL de publicação e sem aprovação de revisão humana registrada.

### Conferência técnica da primeira montagem

O MP4 mede **9min15s**, em Full HD (1920×1080), 30 FPS, H.264 e áudio AAC
estéreo a 48 kHz, com 12 capítulos. Decodificação integral concluída sem erros;
nenhum trecho preto foi identificado pelo detector configurado. Loudness integrado
medido em −16,2 LUFS e true peak em −4,3 dBFS. Os detalhes estão em
`outputs/video-production/edit/technical-validation.json`.
Essas verificações não substituem a revisão integral de conteúdo e sincronismo.

## Publicação informada pelo autor

Vídeo não listado: [YouTube](https://youtu.be/5SKJyl_HEk4), com duração local medida de 9min15s.
O acesso sem autenticação ainda deve ser conferido: a consulta automática não
conseguiu carregar o YouTube neste ambiente. O link também consta do README,
do relatório e de `docs/entrega.json`.
