# Validação da execução local — 10/11/2026

Evidência: `reports/validation/local-stage-tests.json`.

## Resultado funcional

| Verificação | Resultado |
| --- | --- |
| Suíte automatizada | 78 testes aprovados |
| Lint, formatação, tipos e dependências | Aprovados |
| Whisper real | CPU/int8; transcrição offline concluída em aproximadamente 3,46 s |
| MediaPipe real | Dez quadros de postura avaliáveis e dez quadros sem pessoa corretamente sinalizados |
| Vídeo anotado | Gerado |
| Painel de áudio | Transcrição automática, dois downloads e persistência após recarregar, em diretório temporário |
| APIs externas | Zero chamadas Azure; Hugging Face em modo offline |
| Verificação de rede | Zero tentativas nas funções de socket Python bloqueadas durante inferência; não instrumenta sockets de bibliotecas nativas |
| Bancos do usuário | Hashes preservados antes/depois |
| GPU | Zero dispositivos CUDA visíveis neste ambiente; não validada |

## Resultado do ensaio de reconhecimento

A amostra é a frase sintetizada localmente com eSpeak NG, não uma gravação clínica
representativa. Sua referência é conhecida:

> Estou com falta de ar e sinto cansaço.

Resultado observado:

> Estou com falta de adicinho do cansaço.

Após normalização de caixa, acentos e pontuação: 3 erros de edição em 8 palavras,
WER de **37,5%**. Dos dois termos críticos esperados, foi reconhecido apenas
`cansaço`: recuperação de **50% nesse exemplo**. A expressão `falta de ar` não
chegou corretamente ao analisador textual, que depende da transcrição recebida.

Esses valores são de uma única amostra sintética curta; não estimam desempenho
em fala natural nem substituem avaliação independente. Ainda assim, mostram
que instalação bem-sucedida e saída não vazia não garantem preservação de termos
críticos. Não foram ajustados parâmetros usando esse ensaio para aparentar aprovação.

## Conclusão e pendências

Instalação, inferência local e integração funcional aprovadas nos cenários
executados. **Qualidade de transcrição não aprovada para conclusões clínicas.**
É necessário avaliar áudios representativos com transcrição manual, incluindo
menções afirmativas, negações, diferentes locutores e condições acústicas.
Comparações de modelos/parâmetros devem usar desenvolvimento/validação e ser
confirmadas em um conjunto independente, conforme o plano de avaliação.

As verificações do painel usaram Streamlit AppTest, com entrada de arquivo
controlada; não houve inspeção visual automatizada de navegador. O teste de
postura usa imagem de referência repetida; não prova detecção de desvios em
fisioterapia. A pendência de integração Azure exigida no enunciado continua aberta.

## Comandos de reprodução da base

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy
.venv/bin/python -m pip check
HF_HUB_OFFLINE=1 .venv/bin/python scripts/verify_local_stack.py caminho/audio.wav
```

O último comando verifica execução dos motores; ele não calcula WER nem garante
que outro áudio tenha o mesmo resultado. Os WAVs sintéticos do ensaio permanecem
em `outputs/local-installation/`, fora do Git; seus hashes estão nas evidências.

## Correção e avaliação do reconhecimento

A falha acima permanece como linha de base histórica. O painel agora permite
selecionar modelos instalados, ouvir o WAV enviado e preencher uma referência
manual para medir a transcrição. A referência não altera a saída, não é enviada
como prompt e não modifica o relatório original. Os metadados do Whisper
registram que revisão manual é necessária e qualidade ainda não está validada.

O novo avaliador calcula WER por distância de edição e compara menções com
**negação, temporalidade e sujeito**. Assim, transcrever “tenho falta de ar”
quando a referência diz “não tenho falta de ar” conta como erro de contexto,
mesmo que o termo esteja presente. WER pode superar 100% quando há inserções.

Para avaliação com fala natural:

1. Grave WAV mono, PCM 16-bit, 16 kHz, entre 0,3 e 30 segundos, com vozes de
   participantes consentidos, sem dados pessoais. Inclua afirmações, negações,
   histórico, menção a terceiros, fala neutra e condições com/sem ruído.
2. Ouça cada gravação e transcreva literalmente **antes** de consultar o modelo.
   Uma segunda pessoa deve revisar negações e termos críticos. A referência é o
   áudio ouvido, não a frase que se pretendia dizer.
3. Copie `data/evaluation/natural-speech.example.json` para `outputs/` e substitua
   caminhos e referências. Os caminhos são relativos à pasta do manifesto.
   Use manifestos distintos para desenvolvimento, validação e teste, separando
   locutores. Não ajuste o modelo com o conjunto de teste.
4. Compare os modelos no mesmo conjunto, sem prompts com as respostas:

   ```bash
   HF_HUB_OFFLINE=1 .venv/bin/python scripts/evaluate_local_speech.py \
     outputs/natural-speech.json \
     --models models/faster-whisper-small models/faster-whisper-medium \
     --output outputs/natural-speech-results.json
   ```

5. Confira WER ponderado, omissões e menções extras por contexto. Analise cada
   erro crítico e reporte os resultados naturais separados dos sintéticos.
   O arquivo de saída contém referências e transcrições: mantenha-o fora do Git.

Não há gravações naturais em português disponíveis neste repositório para essa
validação. Ela permanece pendente até executar esse protocolo com áudios reais;
nenhum ensaio sintético autoriza concluir qualidade clínica.

### Comparação executada nesta correção

Evidência: `reports/validation/speech-recognition-comparison.json`. Sete sondas
**sintéticas de desenvolvimento**, com texto de síntese conhecido, incluindo o
áudio original. Não são referências humanas de fala natural nem teste independente.

| Modelo CPU/int8 | Erros / palavras | WER ponderado | Menções preservadas com contexto |
| --- | --- | --- | --- |
| small | 19 / 48 | 39,6% | 3 / 8 |
| medium | 12 / 48 | 25,0% | 6 / 8 |

O `medium` reconheceu a frase afirmativa curta e preservou a negação em outro
exemplo, mas continuou perdendo `falta de ar` **no áudio original**: 3 erros em 8
palavras também nessa amostra. Em CPU, suas execuções levaram aproximadamente
7,7–11 segundos; isso não demonstra atingir a meta experimental de latência de
5 segundos. Por essas limitações, `small` continua padrão e `medium` fica como
alternativa selecionável, sem promoção automática por um ensaio de desenvolvimento.

Retirar VAD, adicionar silêncio, aumentar beam e usar float32 também não
corrigiram a falha original. Não foi adotada substituição textual de “adicinho”
por “ar”: ela poderia inventar um sintoma ausente. O erro original permanece
visível, e os relatórios automáticos exigem revisão manual.

O modelo adicional já está instalado localmente. Para reproduzir o download:

```bash
.venv/bin/python scripts/prepare_local_speech.py --model medium \
  --revision 08e178d48790749d25932bbc082711ddcfdfbc4f
.venv/bin/python scripts/generate_speech_probes.py
HF_HUB_OFFLINE=1 .venv/bin/python scripts/evaluate_local_speech.py \
  outputs/local-installation/speech-probes.json \
  --models models/faster-whisper-small models/faster-whisper-medium \
  --output outputs/speech-comparison.json
```

A geração usa `libespeak-ng` e `ffmpeg` já presentes no sistema, voz `pt-br`,
175 palavras/minuto no original e 140 nas demais sondas. Preserva o WAV original
se ele já existir. Versões diferentes do sintetizador podem produzir outros
WAVs; compare os hashes registrados. Os pesos ficam em `models/`, fora do Git.

Verificação após as alterações: **83 testes aprovados**, Ruff, formatação,
Mypy e consistência de dependências aprovados.
