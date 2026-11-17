# Texto de locução — versão para produção

Autor: Caio Lucas Santos Silva · RM373689 · Turma 9IADT.

Usar por cena, com pausas para as demonstrações. Conferir a pronúncia e as instruções de edição em [roteiro-video.md](roteiro-video.md). Esta é a fala planejada, não uma comprovação de execução.

## Cena 01 — Apresentação

Este é o projeto de monitoramento multimodal desenvolvido individualmente por Caio Lucas Santos Silva, da turma nove IADT, para o Tech Challenge da fase quatro. A proposta é combinar sinais vitais, prescrições, áudio e vídeo para identificar alterações observáveis e gerar alertas rastreáveis. Nesta demonstração, veremos a aplicação funcionando com bases públicas e cenários sintéticos. Trata-se de um protótipo acadêmico, sem validação para decisões clínicas.

## Cena 02 — Arquitetura e processamento local

Conforme orientação do professor relatada pelo autor, o uso do Azure é opcional. Por isso, a solução utiliza processamento local. O Whisper transcreve a fala; regras em português analisam sentimentos, termos críticos e negações. O MediaPipe estima pontos corporais, e regras temporais analisam postura e movimento. Sinais e prescrições também passam por regras explícitas. Os eventos guardam paciente, sessão, intervalo e evidências. O SQLite preserva o histórico, e o painel permite reconhecer e encerrar alertas. As regras não recomendam tratamentos.

## Cena 03 — Fisioterapia — execução sem desvio

Começamos pela fisioterapia, com um trecho do exercício Arm VW da base REHAB24-6. Selecionamos o contexto de elevação bilateral dos braços e enviamos o arquivo. A aplicação estima a postura e compara os ângulos dos dois lados ao longo do tempo. Neste exemplo, os quadros são avaliáveis e não há desvio confirmado. Isso significa que as condições das regras não foram atingidas, e não uma aprovação clínica geral do exercício.

## Cena 04 — Fisioterapia — assimetria

Agora processamos um segundo trecho da mesma base e da mesma pessoa. O sistema identifica uma assimetria entre um vírgula vinte e dois vírgula oitenta segundos do trecho. A regra exige diferença angular superior a vinte e cinco graus, persistente por pelo menos um segundo. O relatório registra o intervalo e a evidência associada ao arquivo. A base anota diferentes tipos de execução incorreta, mas nossa regra cobre apenas parte deles. Portanto, não afirmamos reconhecer todo erro de fisioterapia.

## Cena 05 — Cadeira — antes e depois

Para movimentação em cadeira, usamos o par antes e depois do exercício da base Sit-To-Stand. Esses nomes indicam o momento da coleta, não uma classificação de risco. No modo de internação, o sistema usa ombros e quadris para acompanhar o centro do tronco. Não exige cotovelos, que podem ficar ocultos na vista lateral. Ambos os vídeos são avaliáveis. O primeiro não gera evento confirmado; no segundo há um candidato a levantamento entre vinte e oito vírgula oito e vinte e nove vírgula oito segundos. A ausência de evento não significa ausência de movimento. As linhas e os ângulos originais já pertencem ao dataset; a aplicação executa sua própria estimativa sobre essas imagens.

## Cena 06 — Áudio SPIRA — controle e paciente

Na área de áudio, selecionamos o Whisper local em português, executado em CPU. Os exemplos da base SPIRA foram convertidos para WAV mono, dezesseis bits e dezesseis quilohertz. O controle selecionado não apresenta pausa interna prolongada. Já o exemplo de paciente apresenta uma pausa de aproximadamente dois vírgula sessenta e quatro segundos. Podemos ouvir a gravação e conferir a transcrição e o intervalo identificado. Os grupos paciente e controle são metadados da base; a aplicação não prevê esses grupos. Um paciente pode não ter pausas, e um controle também pode apresentar uma pausa longa. Os dois textos selecionados retornam sentimento neutro e não contêm menções críticas detectadas.

## Cena 07 — Sentimentos, sintomas e negação

Para demonstrar a análise textual, usamos gravações encenadas pelo autor. Os exemplos positivo e negativo permitem observar a classificação de sentimento por regras em português. Em seguida, comparamos uma menção afirmativa de sintoma com uma frase que o nega. A regra considera o contexto, evitando tratar automaticamente uma negação como sintoma presente. Um relato de sintoma também pode ser classificado como neutro: sentimento e risco clínico são conceitos diferentes. A transcrição precisa ser conferida, porque erros do reconhecimento de fala podem omitir ou alterar um termo importante.

## Cena 08 — Sinais vitais — persistência e tendência

Nos sinais vitais, a aplicação acompanha frequência cardíaca, pressão sistólica, pressão diastólica e saturação. Este cenário sintético apresenta um desvio persistente, com aumento da frequência cardíaca a partir do décimo segundo. Mantemos a reprodução em velocidade normal para mostrar a evolução temporal. A regra exige três segundos de persistência antes de confirmar o desvio. No segundo cenário, os valores mudam gradualmente, demonstrando o detector de tendência. Os limites são experimentais e servem à demonstração. A reprodução de séries gravadas não equivale à captura de sensores em um hospital.

## Cena 09 — Reconhecimento e encerramento

O alerta é emitido automaticamente e depois passa por revisão humana. Informamos o responsável e um comentário para registrar o reconhecimento. Em seguida, encerramos o alerta com o resultado da revisão. Neste cenário sintético, confirmado significa que o desvio previsto no teste foi verificado. O histórico preserva as ações realizadas. Repetir a mesma sessão não deve duplicar amostras ou alertas. Se um alerta já tiver sido encerrado em um ensaio anterior, mostramos o registro existente.

## Cena 10 — Prescrições e alertas

Na área de histórico e fusão, processamos o cenário de mudança inesperada de prescrição. O exemplo altera uma dose sintética de um para quatro no décimo segundo, sem indicação de mudança prevista. O sistema compara as versões e registra o evento e suas evidências. Existem também regras para interrupções e inconsistências de unidade ou sequência. Essas verificações são demonstrativas e não calculam doses terapêuticas nem substituem revisão de um profissional.

## Cena 11 — Importação e fusão multimodal

Agora integramos os relatórios que a própria aplicação gerou. Primeiro importamos o vídeo com assimetria e informamos um início artificial no décimo segundo da sessão. Depois importamos o áudio do SPIRA com pausa longa, alinhado ao início da sessão. Em ambos, selecionamos associação sintética de demonstração. As gravações são independentes, não foram feitas simultaneamente e não representam o mesmo paciente real. A aplicação preserva a origem e alinha os intervalos para permitir a demonstração da fusão. A linha do tempo reúne sinais, prescrições, áudio e vídeo. Eventos de famílias diferentes podem compor alertas por episódio, em uma janela limitada de trinta segundos. Nem toda importação cria um novo alerta prioritário. Podemos inspecionar as evidências, conferir a associação e exportar o histórico completo.

## Cena 12 — Resultados, limitações e fechamento

A verificação automatizada documentada passou em cento e sessenta e três testes, além das checagens de tipos, estilo e dados. Nos conjuntos sintéticos, as regras temporais alcançaram os resultados registrados no relatório; isso não comprova generalização clínica. As bases públicas demonstraram execução real de fala e postura, mas os exemplos foram selecionados após observar os resultados. Permanecem limitações de transcrição, oclusão, cobertura de erros e falta de avaliação clínica independente. O repositório contém código, instruções, relatório técnico e evidências para reprodução. O trabalho foi desenvolvido individualmente, com produção audiovisual assistida por inteligência artificial. A locução será identificada como sintética caso esse recurso seja utilizado. Os créditos e termos das bases estão no relatório. Obrigado por acompanhar a demonstração.
