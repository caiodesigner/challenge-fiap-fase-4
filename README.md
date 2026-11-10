# Challenge FIAP — Fase 4

Repositório do projeto Challenge FIAP — Fase 4.

Evolução seletiva do assistente médico desenvolvido na fase 3, com foco em
monitoramento multimodal de pacientes e detecção de anomalias. O projeto da
fase 3 será preservado em seu repositório original.

O projeto tem uma base Python instalável e um primeiro fluxo completo de sinais
vitais: ingestão incremental, detecção por regras sintéticas, alertas persistidos
e painel de revisão. A análise postural de vídeo já gera desvios, relatórios e
vídeo anotado. Áudio já possui análise acústica local, termos críticos e adaptadores
Azure; a comprovação real na nuvem e a fusão ainda estão pendentes.

- [Plano de execução e análise do feedback da fase 3](PLANO_DESENVOLVIMENTO.md)
- [Escopo, cenários e critérios de aceite](docs/escopo-e-aceite.md)
- [Origem e análise dos componentes reaproveitados](docs/reaproveitamento-fase-3.md)
- [Dados, contratos e conjuntos de avaliação](docs/dados-e-avaliacao.md)
- [Fluxo de sinais vitais: execução, evidências e limites](docs/fluxo-sinais-vitais.md)
- [Vídeo e relatórios de desvios](docs/video-e-relatorios.md)
- [Áudio, análise acústica e Azure gratuito](docs/audio-e-azure.md)
- [Instalação e execução totalmente local: Whisper e MediaPipe](docs/execucao-local.md)

## Instalação e verificação da base

Requer Python 3.12–3.14 com `venv` e `pip`. Validação local realizada em Python
3.14.4; a CI está configurada para 3.12 e 3.14. Não requer GPU, modelos ou Azure.
No Linux, execute na raiz do projeto:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy
.venv/bin/python -m pytest
.venv/bin/python -m pip check
.venv/bin/python -m monitoramento_clinico.data validate
.venv/bin/python scripts/prepare_bidmc.py validate
```

Se `venv`/`pip` estiverem ausentes, instale os pacotes correspondentes à versão
de Python na sua distribuição. Com GNU Make disponível, `make install` e
`make check` fornecem atalhos para instalação e verificações de qualidade.

Os testes criam bancos e registros sintéticos temporários, sem acessar a fase 3.
O schema de contexto está em `data/database/schema.sql`; não representa ainda
o armazenamento completo da fase 4. O ambiente virtual e saídas são ignorados pelo Git.

Os contratos multimodais estão em `src/monitoramento_clinico/contracts.py`.
Há 90 fixtures funcionais sintéticas e seis registros públicos BIDMC separados
por fonte. Vídeos clínicos e fala consentida ainda precisam ser incorporados;
os dados artificiais não comprovam desempenho clínico. Para recriar as fixtures:

```bash
.venv/bin/python -m monitoramento_clinico.data generate
```

## Primeiro fluxo completo

Para executar a demonstração em cadência real simulada (~19 segundos) e gerar
`reports/vitals/demo.json`, sem precisar do painel:

```bash
.venv/bin/python scripts/demo_vitals.py
```

Para usar o painel local com gráfico, tabela de sinais, alertas, evidências e revisão:

```bash
.venv/bin/python -m pip install -e '.[ui]'
.venv/bin/python -m streamlit run app.py
```

Abra o endereço exibido pelo Streamlit (normalmente `http://localhost:8501`).
Selecione um cenário e reproduza a sessão. Os alertas são emitidos automaticamente;
reconheça e depois encerre com o resultado da revisão. Repetir a sessão não duplica
amostras/alertas. Cada cenário do painel usa um banco próprio em `outputs/`.

Os limites são exclusivamente experimentais para dados sintéticos. A demonstração
não constitui validação clínica nem integração com sensores hospitalares.

O painel salva o histórico de cada reprodução, com duração, velocidade, status
e resumo, inclusive quando todas as amostras forem duplicadas. Esses dados
continuam acessíveis após recarregar ou reiniciar; execuções antigas sem resumo
não recebem métricas retroativas.

## Vídeo e relatórios

```bash
.venv/bin/python -m pip install -e '.[ui,video]'
.venv/bin/python scripts/prepare_pose_model.py
.venv/bin/python -m streamlit run app.py
```

Escolha **Vídeo** na barra lateral e envie um vídeo de até 120 segundos, com câmera
fixa, uma pessoa e taxa de quadros constante. Selecione exercício bilateral ou
movimentação de internação e clique em **Analisar vídeo**. O painel disponibiliza
relatórios JSON/Markdown e vídeo anotado. FFmpeg no sistema permite MP4 reproduzível
no navegador; sem ele, é disponibilizado AVI para download.

A inferência de postura foi verificada em CPU. A avaliação com vídeos clínicos
representativos e rótulos independentes permanece pendente.

## Áudio e Azure

No painel, escolha **Áudio**. O padrão **Whisper local** transcreve em português
sem utilizar Azure. **Somente local** mantém a opção de análise acústica sem modelo.
Aceita WAV PCM mono, 16-bit, 16 kHz, de 0,3 a 30 segundos; mede energia e pausas,
com referência opcional, e gera relatórios persistidos. O painel permite comparar
a transcrição com uma referência manual e selecionar modelos Whisper instalados.
Veja os resultados e o protocolo de fala natural em [validação local](docs/validacao-local.md).

```bash
.venv/bin/python scripts/demo_audio.py
.venv/bin/python scripts/analyze_audio.py caminho/audio.wav
.venv/bin/python scripts/analyze_audio.py caminho/audio.wav --whisper --device cpu
```

O modo Azure exige recursos Speech e Language configurados no `.env` a partir
de `.env.example`. Priorize os níveis gratuitos F0 e confira o
[guia de configuração e custos](docs/audio-e-azure.md). Não houve criação de
recursos nem chamadas reais nesta implementação; essa validação continua pendente.
