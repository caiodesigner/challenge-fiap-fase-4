# Guia de execução e preparação da entrega

Este guia reúne os comandos para reproduzir o projeto e apresentar a entrega.
O estado atual e os itens ainda abertos constam de [entrega.json](entrega.json).
O [relatório técnico](relatorio-tecnico.md) descreve resultados e limitações.

## 1. Instalar a partir do repositório

No Linux, com Python 3.12–3.14 e suporte a `venv`/`pip`:

```bash
git clone https://github.com/caiodesigner/challenge-fiap-fase-4.git
cd challenge-fiap-fase-4
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[audio,video,ui,dev]'
.venv/bin/python -m pip check
```

Use uma revisão que contenha os arquivos citados neste guia; antes de divulgar a
entrega, confira que as alterações locais foram commitadas e enviadas ao remoto.
Os resultados de instalação registrados usaram Python 3.14.4 e CPU. As faixas de
dependências estão em `pyproject.toml`; as versões efetivamente observadas estão
nos relatórios em `reports/`. FFmpeg instalado no sistema permite gerar MP4 de
vídeo; OpenCV/MediaPipe podem exigir bibliotecas gráficas da distribuição Linux.

Baixe explicitamente os dois modelos antes da demonstração:

```bash
.venv/bin/python scripts/prepare_local_speech.py --model small \
  --revision 536b0662742c02347bc0e980a01041f333bce120
.venv/bin/python scripts/prepare_pose_model.py
```

O download requer rede. Depois dele, a inferência usa os arquivos em `models/`.
Não são necessárias credenciais Azure. O guia de instalação detalhado é
[execucao-local.md](execucao-local.md).

## 2. Conferir o código e os dados

```bash
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy
.venv/bin/python -m pytest
.venv/bin/python -m monitoramento_clinico.data validate
.venv/bin/python scripts/prepare_bidmc.py validate
```

O registro mais recente da suíte contém 113 testes aprovados. Os testes usam
entradas e bancos temporários. Não é preciso regenerar fixtures para executar o
projeto: o catálogo e seus hashes já estão no repositório.

## 3. Executar as demonstrações e a avaliação

```bash
# Sinais em cadência 1×, com confirmação temporal e persistência.
.venv/bin/python scripts/demo_vitals.py --speed 1 \
  --report outputs/entrega/vitals.json

# Integração sintética: sinais, prescrições e eventos de texto/vídeo de fixture.
.venv/bin/python scripts/demo_clinical_fusion.py \
  --database outputs/entrega/clinical.db \
  --report outputs/entrega/clinical.json

# Comparação de regras e contagem de alertas combinados.
.venv/bin/python scripts/evaluate_local.py \
  --fusion-report outputs/entrega/clinical.json \
  --output outputs/entrega/evaluation.json

# Cadência 1× pareada: aproximadamente 38 segundos.
.venv/bin/python scripts/evaluate_local.py \
  --case development-vitals-2 --speed 1 \
  --output outputs/entrega/cadence.json
```

O primeiro comando também verifica reprocessamento e estados de revisão em um
banco temporário. O segundo usa eventos textuais/visuais gerados para demonstrar
integração; ele não executa modelos de mídia. Os demais geram JSON e Markdown.
Novas saídas ficam em `outputs/entrega/`, preservando os relatórios históricos.

## 4. Abrir o painel e analisar mídia

```bash
.venv/bin/python -m streamlit run app.py
```

Abra o endereço informado no terminal. Na primeira execução, caso o Streamlit
solicite e-mail, pode deixar o campo em branco e pressionar Enter.

- **Sinais vitais:** selecione o caso, execute a reprodução e confira alertas,
  evidências e histórico. A caixa de reprodução acelerada altera a cadência.
- **Vídeo:** selecione exercício ou internação, envie uma gravação compatível e
  gere vídeo anotado e relatórios. Limite atual: 120 segundos, taxa de quadros
  constante, câmera fixa e enquadramento de uma pessoa.
- **Áudio:** selecione Whisper local, CPU e modelo instalado. Envie WAV mono,
  PCM 16-bit/16 kHz, com 0,3 a 30 segundos. Ouça o áudio, confira a transcrição e
  use a referência manual para avaliação.
- **Histórico e fusão:** processe um cenário, confira mudanças previstas e
  inesperadas, disponibilidade, eventos e alertas. A importação de relatórios
  exige início de captura com fuso e identificação da associação temporal.

Exemplos de execução por CLI, substituindo os caminhos pelas mídias preparadas:

```bash
.venv/bin/python scripts/analyze_audio.py caminho/relato.wav --whisper \
  --device cpu --output outputs/entrega/audio
.venv/bin/python scripts/analyze_video.py caminho/exercicio.mp4 \
  --mode rehabilitation --output outputs/entrega/video
.venv/bin/python scripts/analyze_video.py caminho/internacao.mp4 \
  --mode inpatient --output outputs/entrega/movement
```

Os processadores geram subdiretórios por execução. Use os respectivos arquivos
`report.json` para integração. Os formatos e limites estão nos guias de
[vídeo](video-e-relatorios.md), [áudio](execucao-local.md) e
[fusão](anomalias-e-fusao.md).

## 5. Organizar os materiais de entrega

| Material | Local e estado |
| --- | --- |
| Código e instalação | Repositório, `README.md`, `pyproject.toml` |
| Relatório técnico | [relatorio-tecnico.md](relatorio-tecnico.md), preparado para revisão |
| Matriz de atendimento | [matriz-atendimento.md](matriz-atendimento.md), com pendências explícitas |
| Dados e origem | `data/fixtures/manifest.json`, `data/external/bidmc/manifest.json`, manifesto de reaproveitamento |
| Resultados | `reports/evaluation/`, `reports/validation/` e saídas novas em `outputs/entrega/` |
| Vídeo | [roteiro-video.md](roteiro-video.md); gravação e link pendentes |
| Identificação da entrega | [entrega.json](entrega.json); preencher autor/equipe e dados do vídeo |

O relatório está em Markdown e pode ser exportado para PDF pelo editor que será
usado na submissão. Confira tabelas, diagrama e links na versão exportada. Caso o
renderizador não suporte Mermaid, apresente a arquitetura descrita em texto ou
exporte o diagrama por uma ferramenta compatível.

Modelos, ambientes, bancos, caches e mídias geradas não integram o Git. O código
inclui instruções para obter os pesos e gerar as saídas. Dados externos preservam
suas licenças; a origem da fase 3 consta do manifesto correspondente.

## 6. Gravar, conferir e publicar o vídeo

Siga o [roteiro de 13min30s](roteiro-video.md). Prepare modelos e arquivos antes
da gravação; deixe a execução 1× visível por alguns segundos para mostrar a
cadência. Apresente os erros conhecidos e diferencie as fontes sintéticas das
gravações utilizadas nos motores locais.

Confira a duração do arquivo final com FFprobe, se disponível:

```bash
ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 caminho/video-final.mp4
```

O resultado deve ser maior que zero e no máximo **900 segundos**. Depois de
publicar no YouTube ou Vimeo, confirme o link em uma sessão sem autenticação e
atualize `video.url`, `video.duration_seconds` e `video.state` em `entrega.json`.

A gravação/publicação e a submissão na plataforma ainda não foram realizadas.
Antes do fechamento, revise as pendências experimentais do relatório e confirme
prazo, identificação da equipe, versão do código e links de entrega.
