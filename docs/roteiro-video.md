# Roteiro de produção — demonstração do Tech Challenge

**Autor:** Caio Lucas Santos Silva · **RM:** RM373689 · **Turma:** 9IADT.

**Etapa:** roteiro preparado; capturas finais, locução e montagem ainda pendentes.

**Duração planejada:** 12:30 (750 segundos); limite do challenge: 15 minutos.

**Voz:** português brasileiro, ritmo moderado. Tempos incluem navegação, reprodução e pausas; ajustar após gerar a voz.

## Preparação da captura

1. Iniciar a aplicação atualizada com `.venv/bin/python -m streamlit run app.py`.
2. Usar navegador em 1920×1080, zoom legível, sem notificações ou janelas pessoais.
3. Conferir modelos locais e arquivos abaixo. Fechar mensagens promocionais do Streamlit.
4. Verificar previamente um alerta aberto e os resultados dos áudios encenados. Não apagar o histórico para repetir ações.
5. Capturar cenas separadamente, incluindo ações de upload, execução e resultado. Esperas podem ser cortadas com indicação “tempo de processamento reduzido”.
6. Nas duas reproduções de sinais, preservar cadência 1×. A prévia amostrada de 40 segundos não serve de evidência de cadência nem substitui estas capturas.
7. Ao reproduzir áudios de pacientes, pausar a locução para permitir escuta. Não expor dados pessoais de outras gravações.
8. Conferir cada resultado antes de associá-lo à fala. Se divergir do esperado, inspecionar o relatório; não editar a tela para aparentar outro resultado.

## Arquivos de entrada

| Uso | Caminho |
| --- | --- |
| REHAB correto | `outputs/rehab24-review/selected/01_ex2_correto.mp4` |
| REHAB assimetria | `outputs/rehab24-review/selected/02_ex2_assimetria.mp4` |
| Cadeira | `/home/caio-lucas/Documentos/IA-PARA-DEVS/fase_4_base_de_dados/sit-to-stand/out_Subject_14_before.mp4` e `out_Subject_14_after.mp4` |
| SPIRA | `outputs/spira-review/selected/01_controle_continuo.wav` e `02_paciente_pausas.wav` |
| Áudios encenados | `/home/caio-lucas/Documentos/IA-PARA-DEVS/audios-fase4/`: `positivo.wav`, `negativo.wav`, `sintoma.wav`, `negacao.wav` |
| Fusão | JSONs recém-exportados do vídeo com assimetria e do áudio SPIRA com pausa; identificar pelo conteúdo, não pelo nome genérico do download |

No painel de áudio: Whisper local, execução `cpu`, modelo `faster-whisper-small`, referência acústica vazia.
Na fusão, a identidade de demonstração deve ser `PAT-SYN-001`. Não associar um relatório de outra identidade.

## Agenda

| Cena | Intervalo | Conteúdo |
| --- | --- | --- |
| 01 | 00:00–00:35 | Apresentação |
| 02 | 00:35–01:20 | Arquitetura e processamento local |
| 03 | 01:20–02:05 | Fisioterapia — execução sem desvio |
| 04 | 02:05–03:00 | Fisioterapia — assimetria |
| 05 | 03:00–04:15 | Cadeira — antes e depois |
| 06 | 04:15–05:40 | Áudio SPIRA — controle e paciente |
| 07 | 05:40–06:45 | Sentimentos, sintomas e negação |
| 08 | 06:45–08:05 | Sinais vitais — persistência e tendência |
| 09 | 08:05–08:50 | Reconhecimento e encerramento |
| 10 | 08:50–09:40 | Prescrições e alertas |
| 11 | 09:40–11:20 | Importação e fusão multimodal |
| 12 | 11:20–12:30 | Resultados, limitações e fechamento |

## Cena 01 — Apresentação

**Janela:** 00:00–00:35 (35 s, incluindo ações e pausas).

**Captura:** Cartela com título, nome, RM e turma; abrir README.

**Evidência a exibir:** Exibir autoria individual e objetivo. Sem simular resultados.

**Texto na tela:** Monitoramento multimodal · Tech Challenge Fase 4

**Locução:**

Este é o projeto de monitoramento multimodal desenvolvido individualmente por Caio Lucas Santos Silva, da turma nove IADT, para o Tech Challenge da fase quatro. A proposta é combinar sinais vitais, prescrições, áudio e vídeo para identificar alterações observáveis e gerar alertas rastreáveis. Nesta demonstração, veremos a aplicação funcionando com bases públicas e cenários sintéticos. Trata-se de um protótipo acadêmico, sem validação para decisões clínicas.

## Cena 02 — Arquitetura e processamento local

**Janela:** 00:35–01:20 (45 s, incluindo ações e pausas).

**Captura:** Mostrar diagrama do relatório técnico e as quatro áreas do painel.

**Evidência a exibir:** Destacar entrada → processamento → evento → SQLite → alerta → revisão.

**Texto na tela:** Azure opcional conforme orientação do professor relatada pelo autor

**Locução:**

Conforme orientação do professor relatada pelo autor, o uso do Azure é opcional. Por isso, a solução utiliza processamento local. O Whisper transcreve a fala; regras em português analisam sentimentos, termos críticos e negações. O MediaPipe estima pontos corporais, e regras temporais analisam postura e movimento. Sinais e prescrições também passam por regras explícitas. Os eventos guardam paciente, sessão, intervalo e evidências. O SQLite preserva o histórico, e o painel permite reconhecer e encerrar alertas. As regras não recomendam tratamentos.

## Cena 03 — Fisioterapia — execução sem desvio

**Janela:** 01:20–02:05 (45 s, incluindo ações e pausas).

**Captura:** Vídeo → Contexto: Elevação bilateral dos braços → enviar 01_ex2_correto.mp4 → Analisar vídeo.

**Evidência a exibir:** Mostrar nome do arquivo, processamento, assessable e ausência de eventos; reproduzir alguns segundos da saída.

**Texto na tela:** REHAB24-6 · Arm VW · exemplo sem desvio confirmado

**Locução:**

Começamos pela fisioterapia, com um trecho do exercício Arm VW da base REHAB24-6. Selecionamos o contexto de elevação bilateral dos braços e enviamos o arquivo. A aplicação estima a postura e compara os ângulos dos dois lados ao longo do tempo. Neste exemplo, os quadros são avaliáveis e não há desvio confirmado. Isso significa que as condições das regras não foram atingidas, e não uma aprovação clínica geral do exercício.

## Cena 04 — Fisioterapia — assimetria

**Janela:** 02:05–03:00 (55 s, incluindo ações e pausas).

**Captura:** No mesmo contexto, enviar 02_ex2_assimetria.mp4 → Analisar vídeo.

**Evidência a exibir:** Mostrar evento asymmetry 1,20–2,80 s, vídeo nesse intervalo e relatório exportável.

**Texto na tela:** Assimetria detectada: 1,20 a 2,80 s

**Locução:**

Agora processamos um segundo trecho da mesma base e da mesma pessoa. O sistema identifica uma assimetria entre um vírgula vinte e dois vírgula oitenta segundos do trecho. A regra exige diferença angular superior a vinte e cinco graus, persistente por pelo menos um segundo. O relatório registra o intervalo e a evidência associada ao arquivo. A base anota diferentes tipos de execução incorreta, mas nossa regra cobre apenas parte deles. Portanto, não afirmamos reconhecer todo erro de fisioterapia.

## Cena 05 — Cadeira — antes e depois

**Janela:** 03:00–04:15 (75 s, incluindo ações e pausas).

**Captura:** Vídeo → Contexto: Movimentação em leito/cadeira. Processar out_Subject_14_before.mp4 e depois out_Subject_14_after.mp4.

**Evidência a exibir:** Before: 158/158 válidos, sem evento. After: 176/176 válidos, rise_candidate 28,8–29,8 s. Mostrar entrada e saída identificadas.

**Texto na tela:** Sit-To-Stand · marcações prévias pertencem à fonte

**Locução:**

Para movimentação em cadeira, usamos o par antes e depois do exercício da base Sit-To-Stand. Esses nomes indicam o momento da coleta, não uma classificação de risco. No modo de internação, o sistema usa ombros e quadris para acompanhar o centro do tronco. Não exige cotovelos, que podem ficar ocultos na vista lateral. Ambos os vídeos são avaliáveis. O primeiro não gera evento confirmado; no segundo há um candidato a levantamento entre vinte e oito vírgula oito e vinte e nove vírgula oito segundos. A ausência de evento não significa ausência de movimento. As linhas e os ângulos originais já pertencem ao dataset; a aplicação executa sua própria estimativa sobre essas imagens.

## Cena 06 — Áudio SPIRA — controle e paciente

**Janela:** 04:15–05:40 (85 s, incluindo ações e pausas).

**Captura:** Áudio → Whisper local → cpu → faster-whisper-small; referência vazia. Processar 01_controle_continuo.wav e 02_paciente_pausas.wav.

**Evidência a exibir:** Reproduzir trecho curto de cada áudio, sem locução sobreposta. Mostrar transcrição, sentimento neutro e long_pause_observed no paciente: 13,50–16,14 s.

**Texto na tela:** SPIRA · fala natural de leitura · pausa observada não é diagnóstico

**Locução:**

Na área de áudio, selecionamos o Whisper local em português, executado em CPU. Os exemplos da base SPIRA foram convertidos para WAV mono, dezesseis bits e dezesseis quilohertz. O controle selecionado não apresenta pausa interna prolongada. Já o exemplo de paciente apresenta uma pausa de aproximadamente dois vírgula sessenta e quatro segundos. Podemos ouvir a gravação e conferir a transcrição e o intervalo identificado. Os grupos paciente e controle são metadados da base; a aplicação não prevê esses grupos. Um paciente pode não ter pausas, e um controle também pode apresentar uma pausa longa. Os dois textos selecionados retornam sentimento neutro e não contêm menções críticas detectadas.

## Cena 07 — Sentimentos, sintomas e negação

**Janela:** 05:40–06:45 (65 s, incluindo ações e pausas).

**Captura:** Em Áudio, processar positivo.wav, negativo.wav, sintoma.wav e negacao.wav da pasta audios-fase4; usar cortes de espera identificados.

**Evidência a exibir:** Mostrar sentimento positivo/negativo e diferença entre menção afirmada e negada. Conferir as transcrições antes de narrar o resultado.

**Texto na tela:** Gravações encenadas pelo autor · polaridade não determina risco

**Locução:**

Para demonstrar a análise textual, usamos gravações encenadas pelo autor. Os exemplos positivo e negativo permitem observar a classificação de sentimento por regras em português. Em seguida, comparamos uma menção afirmativa de sintoma com uma frase que o nega. A regra considera o contexto, evitando tratar automaticamente uma negação como sintoma presente. Um relato de sintoma também pode ser classificado como neutro: sentimento e risco clínico são conceitos diferentes. A transcrição precisa ser conferida, porque erros do reconhecimento de fala podem omitir ou alterar um termo importante.

## Cena 08 — Sinais vitais — persistência e tendência

**Janela:** 06:45–08:05 (80 s, incluindo ações e pausas).

**Captura:** Sinais vitais → development-vitals-2 → heart_rate → desmarcar Reprodução acelerada → Reproduzir sessão. Depois development-vitals-3 e repetir.

**Evidência a exibir:** Preservar 1× em ambas as reproduções (~20 s cada). Mostrar evento persistente e trend_deviation.

**Texto na tela:** Dados sintéticos · reprodução 1× · limites experimentais

**Locução:**

Nos sinais vitais, a aplicação acompanha frequência cardíaca, pressão sistólica, pressão diastólica e saturação. Este cenário sintético apresenta um desvio persistente, com aumento da frequência cardíaca a partir do décimo segundo. Mantemos a reprodução em velocidade normal para mostrar a evolução temporal. A regra exige três segundos de persistência antes de confirmar o desvio. No segundo cenário, os valores mudam gradualmente, demonstrando o detector de tendência. Os limites são experimentais e servem à demonstração. A reprodução de séries gravadas não equivale à captura de sensores em um hospital.

## Cena 09 — Reconhecimento e encerramento

**Janela:** 08:05–08:50 (45 s, incluindo ações e pausas).

**Captura:** Escolher alerta aberto → preencher responsável e comentário → Reconhecer → Registrar. No mesmo alerta: Encerrar → confirmed → Registrar.

**Evidência a exibir:** Mostrar aberto → reconhecido → encerrado e histórico. Se já encerrado, mostrar revisão registrada; não apagar bancos.

**Texto na tela:** Revisão humana registrada após a emissão automática

**Locução:**

O alerta é emitido automaticamente e depois passa por revisão humana. Informamos o responsável e um comentário para registrar o reconhecimento. Em seguida, encerramos o alerta com o resultado da revisão. Neste cenário sintético, confirmado significa que o desvio previsto no teste foi verificado. O histórico preserva as ações realizadas. Repetir a mesma sessão não deve duplicar amostras ou alertas. Se um alerta já tiver sido encerrado em um ensaio anterior, mostramos o registro existente.

## Cena 10 — Prescrições e alertas

**Janela:** 08:50–09:40 (50 s, incluindo ações e pausas).

**Captura:** Histórico e fusão → 3 — mudança inesperada → Processar cenário sintético.

**Evidência a exibir:** Mostrar dose sintética 1 → 4 no segundo 10, linha do tempo e alertas. Não fazer upload de prescrição adicional.

**Texto na tela:** Prescrição sintética · não é recomendação de dose

**Locução:**

Na área de histórico e fusão, processamos o cenário de mudança inesperada de prescrição. O exemplo altera uma dose sintética de um para quatro no décimo segundo, sem indicação de mudança prevista. O sistema compara as versões e registra o evento e suas evidências. Existem também regras para interrupções e inconsistências de unidade ou sequência. Essas verificações são demonstrativas e não calculam doses terapêuticas nem substituem revisão de um profissional.

## Cena 11 — Importação e fusão multimodal

**Janela:** 09:40–11:20 (100 s, incluindo ações e pausas).

**Captura:** Importar JSON do REHAB com asymmetry: início 2026-01-01T00:00:10+00:00; associação synthetic; Integrar eventos de mídia. Depois JSON do SPIRA com pausa: início 2026-01-01T00:00:00+00:00; mesma associação; integrar.

**Evidência a exibir:** Mostrar upload do JSON, sucesso, linha do tempo, modalidades/evidências e proveniência synthetic; exportar clinical-fusion.json.

**Texto na tela:** Fontes independentes · associação temporal sintética

**Locução:**

Agora integramos os relatórios que a própria aplicação gerou. Primeiro importamos o vídeo com assimetria e informamos um início artificial no décimo segundo da sessão. Depois importamos o áudio do SPIRA com pausa longa, alinhado ao início da sessão. Em ambos, selecionamos associação sintética de demonstração. As gravações são independentes, não foram feitas simultaneamente e não representam o mesmo paciente real. A aplicação preserva a origem e alinha os intervalos para permitir a demonstração da fusão. A linha do tempo reúne sinais, prescrições, áudio e vídeo. Eventos de famílias diferentes podem compor alertas por episódio, em uma janela limitada de trinta segundos. Nem toda importação cria um novo alerta prioritário. Podemos inspecionar as evidências, conferir a associação e exportar o histórico completo.

## Cena 12 — Resultados, limitações e fechamento

**Janela:** 11:20–12:30 (70 s, incluindo ações e pausas).

**Captura:** Mostrar relatório PDF, evidências de avaliação, README e repositório. Encerrar com créditos das bases e da produção assistida por IA.

**Evidência a exibir:** Mostrar 163 testes da verificação documentada, separar métricas sintéticas de demonstrações externas. Não afirmar teste clínico independente.

**Texto na tela:** Fontes: REHAB24-6 · SPIRA · Sit-To-Stand · BIDMC

**Locução:**

A verificação automatizada documentada passou em cento e sessenta e três testes, além das checagens de tipos, estilo e dados. Nos conjuntos sintéticos, as regras temporais alcançaram os resultados registrados no relatório; isso não comprova generalização clínica. As bases públicas demonstraram execução real de fala e postura, mas os exemplos foram selecionados após observar os resultados. Permanecem limitações de transcrição, oclusão, cobertura de erros e falta de avaliação clínica independente. O repositório contém código, instruções, relatório técnico e evidências para reprodução. O trabalho foi desenvolvido individualmente, com produção audiovisual assistida por inteligência artificial. A locução será identificada como sintética caso esse recurso seja utilizado. Os créditos e termos das bases estão no relatório. Obrigado por acompanhar a demonstração.

## Diretrizes para locução e edição

- Ler RM como “erre eme, três sete três seis oito nove” e turma como “nove, i, a, dê, tê”.
- Pronunciar SPIRA como “espira”, Whisper como “uísper” e MediaPipe como “mídia páip”.
- Não ler caminhos, hashes ou JSONs inteiros. Usar destaques nos intervalos, qualidade e tipo de evento.
- Se a locução for sintética, substituir na última cena a frase condicional por “A locução é sintética” e incluir esse crédito visualmente.
- Legendar a fala e manter fonte suficiente para leitura em tela pequena. Créditos de origem acompanham as respectivas cenas.
- A janela de cada cena não é a duração obrigatória da voz: reservar silêncio para ouvir exemplos e observar resultados. A duração exata depende da síntese e das capturas.
- Nenhuma tela ou resultado clínico deve ser fabricado. Slides explicam o fluxo; as evidências vêm da aplicação.

## Conferência antes da publicação

Conferir áudio/vídeo, sentimentos e termos críticos, sinais persistentes e tendência,
prescrições, emissão e revisão de alertas e associação sintética na fusão.
Incluir fontes, limitações e Azure opcional conforme orientação do professor relatada pelo autor.
Medir o MP4 final: duração máxima de 900 segundos. Publicar no YouTube ou Vimeo,
público ou não listado, e testar acesso sem login. Só então atualizar URL, duração
e estado do vídeo em `docs/entrega.json` e regenerar o relatório PDF se necessário.

O roteiro não declara o vídeo gravado/publicado. A conclusão dessas etapas permanece pendente.
