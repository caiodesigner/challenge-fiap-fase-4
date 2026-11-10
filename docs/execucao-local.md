# Execução local — faster-whisper e MediaPipe

Resultados e limites da validação: [validacao-local.md](validacao-local.md).

## Instalação realizada

Ambiente virtual `.venv`, Python 3.14.4:

| Componente | Versão/configuração testada |
| --- | --- |
| faster-whisper | 1.2.1 |
| CTranslate2 | 4.8.5 |
| PyAV | 16.1.0 |
| Transcrição | Modelo multilíngue `small`, português, CPU/int8, quatro threads |
| MediaPipe | 0.10.35, Pose Landmarker Lite, CPU |

O PyAV 19 apresentou incompatibilidade com a chamada `metadata_errors` do
faster-whisper 1.2.1. O extra `audio` fixa a faixa PyAV 16.x que foi testada.
Não instalar separadamente o PyAV mais recente sobre esse ambiente.

Os pesos estão em `models/`, fora do Git. O modelo de fala foi baixado do
repositório `Systran/faster-whisper-small`, revisão
`536b0662742c02347bc0e980a01041f333bce120`, com hashes locais registrados.
A inferência usa caminho local e `local_files_only=True`: não baixa pesos durante
a análise. O download inicial precisa de internet, mas não exige serviço pago
nem chave Azure. A telemetria de Hugging Face/ONNX Runtime é desabilitada pelo
carregador. Áudio e transcrição não são enviados a uma API no modo local.

## Usar agora

Reinicie o Streamlit, caso ele já estivesse aberto:

```bash
.venv/bin/python -m streamlit run app.py
```

Na barra lateral, escolha **Áudio** e mantenha **Whisper local**. Selecione **cpu**,
envie um WAV mono PCM 16-bit/16 kHz de até 30 s e clique em **Analisar áudio**.
O relatório identifica a origem como `faster_whisper_local`, além de modelo,
dispositivo, tempo e qualidade. A transcrição passa pelo mascaramento textual e
pelas regras de termos críticos existentes. Segmentos são guardados como metadados
temporais, sem duplicar seu texto bruto no relatório.

**Somente local** continua disponível para análise acústica e transcrição manual.
**Azure Speech + Language** permanece opcional e separado; só esse modo utiliza
os serviços configurados. Não há análise de sentimentos por modelo local nesta
instalação: os termos críticos locais não são apresentados como sentimentos Azure.

Para vídeo, escolha **Vídeo**, envie a gravação e analise com o MediaPipe local.
As limitações de enquadramento, taxa de quadros e qualidade permanecem válidas.

CLI de transcrição local:

```bash
.venv/bin/python scripts/analyze_audio.py caminho/audio.wav --whisper --device cpu
```

## Reproduzir a instalação

```bash
.venv/bin/python -m pip install -e '.[audio,video,ui,dev]'
.venv/bin/python scripts/prepare_local_speech.py --model small \
  --revision 536b0662742c02347bc0e980a01041f333bce120
.venv/bin/python scripts/prepare_pose_model.py
.venv/bin/python -m pytest
.venv/bin/python -m pip check
```

Também é possível baixar `base` ou `medium` com `--model` e selecionar seu
diretório pela opção `--model` da CLI. O painel oferece os modelos instalados,
mantendo `small` por padrão. A comparação com `medium`, suas limitações e o
procedimento de avaliação manual estão em [validação local](validacao-local.md).
Reinicie o processo se substituir os pesos: uma instância do modelo fica em cache
para reduzir o tempo das próximas transcrições.

## GPU e diagnóstico

A máquina informada pelo usuário possui GTX 1650 de 4 GB e driver NVIDIA carregado.
O ambiente de execução do agente, contudo, não expõe `/dev/nvidia*` e o CTranslate2
reportou zero dispositivos CUDA. Portanto, **GPU não foi validada**. Isso não
significa ausência de GPU física nem comprova defeito no driver.

Não foram alterados drivers nem instaladas bibliotecas CUDA/cuDNN. O painel
oferece CUDA apenas se um dispositivo for detectado. Detectar a GPU não garante
que as bibliotecas de execução estejam compatíveis; falhas ficam explícitas,
sem troca silenciosa de dispositivo. CPU/int8 é a configuração validada aqui.

## Evidência e limites

`reports/validation/local-stack.json` registra versões, hashes, modo de execução
e resultado da verificação dos dois motores. A fala em português foi sintetizada
localmente com eSpeak NG já disponível no sistema; os WAVs ficam em `outputs/`.
A transcrição foi concluída em aproximadamente quatro segundos nesse ensaio,
com zero chamadas Azure. Houve erros na frase sintetizada; não se afirma precisão
clínica nem tempo real para fala natural com base nesse exemplo.

Também foi exercitado o painel com a inferência real offline em um diretório
temporário, sem alterar bancos de sessões do usuário. A suíte tem 78 testes
aprovados, incluindo origem da transcrição, ausência de modelo, silêncio,
seleção CUDA sem GPU e exclusividade das fontes de transcrição.

Para repetir a verificação funcional dos motores com outro WAV:

```bash
HF_HUB_OFFLINE=1 .venv/bin/python scripts/verify_local_stack.py caminho/audio.wav
```

Isso testa os motores, não calcula qualidade de reconhecimento. Para avaliação,
usar fala representativa com transcrição manual e medir erros, especialmente em
termos críticos e negações. Os requisitos explícitos de Azure do challenge
continuam pendentes; o modo local não é declarado como substituto dessa evidência.
