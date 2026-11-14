# Roteiro do vídeo — duração planejada de 13min30s

Limite da entrega: 15 minutos. A agenda reserva 90 segundos para variações de
execução e transições. O vídeo final ainda precisa ser gravado e publicado.
Este roteiro apresenta a solução local adotada pelo autor.

## Preparação

Abra o painel, o relatório técnico, a matriz e os resultados antes da gravação.
Tenha os modelos instalados, um WAV e os vídeos que serão demonstrados. Declare
se cada mídia é natural, encenada, imagem repetida ou síntese técnica. Confira os
arquivos e o enquadramento no ensaio para manter a apresentação no tempo previsto.
As instruções de execução estão em [guia-entrega.md](guia-entrega.md).

A demonstração de vídeo deve incluir o modo de exercício e o de internação.
Enquanto as gravações representativas estiverem pendentes, a apresentação deve
explicar o alcance do material técnico disponível e manter essa lacuna explícita.

## Agenda e fala sugerida

| Intervalo | Duração | Tela e ação | Mensagem principal |
| --- | --- | --- | --- |
| 00:00–00:40 | 40 s | README e objetivo | Problema, escopo e solução local |
| 00:40–01:30 | 50 s | Arquitetura e origem da fase 3 | Entradas, eventos, persistência e revisão |
| 01:30–03:20 | 110 s | Painel de sinais | Cadência, desvio, emissão e revisão do alerta |
| 03:20–05:00 | 100 s | Vídeo e relatórios | Postura, movimentação, qualidade e evidência visual |
| 05:00–07:00 | 120 s | Áudio local | Transcrição, acústica, termos e conferência manual |
| 07:00–09:15 | 135 s | Prescrições e fusão | Histórico, associação temporal e alertas combinados |
| 09:15–11:15 | 120 s | Avaliação | Comparação, erros, latência e limitações |
| 11:15–12:30 | 75 s | Guia e testes | Como reproduzir e localizar as evidências |
| 12:30–13:30 | 60 s | Matriz e fechamento | Pendências e materiais de entrega |

### 00:00–00:40 — Contexto

“Este projeto acompanha adultos sintéticos em internação e reabilitação,
combinando sinais, vídeo, áudio e registros clínicos para emitir alertas
rastreáveis. A equipe revisa os alertas depois da emissão. Adotamos processamento
local com Whisper e MediaPipe. A diferença em relação ao uso de Azure no
escopo original está registrada no plano.”

### 00:40–01:30 — Arquitetura e reaproveitamento

Mostre o diagrama do relatório e o manifesto da fase 3.

“Da fase anterior reaproveitamos componentes de mascaramento, auditoria e
leitura de contexto. Os contratos e processadores multimodais foram construídos
para esta fase. Cada evento mantém paciente, sessão, intervalo, detector e
fontes de evidência. O SQLite preserva alertas, execuções e revisões.”

### 01:30–03:20 — Sinais vitais e alerta

Selecione `development-vitals-2`, mantenha a reprodução acelerada desmarcada e
execute a sessão. Mostre alguns segundos de atualização e o histórico gravado.
Escolha um alerta aberto, registre reconhecimento e encerramento com comentário;
se estiver usando registros já revisados, abra o histórico da revisão.

“As regras cobrem frequência cardíaca, pressão sistólica e diastólica e
oxigenação. A confirmação temporal exige três segundos de desvio. O alerta é
emitido automaticamente. O histórico registra o processamento e a revisão, e
repetir a mesma série preserva os registros sem duplicar os alertas.”

### 03:20–05:00 — Vídeo e movimentação

No painel **Vídeo**, apresente o arquivo de exercício, o resultado anotado e um
intervalo do relatório. Mostre também o modo de internação e o tratamento de
qualidade insuficiente. Identifique a origem de cada arquivo exibido.

“O MediaPipe fornece pontos posturais e regras temporais geram candidatos a
desvios. Há fluxos para exercício e movimentação na internação. O relatório
preserva intervalos e características. Pessoa ausente, enquadramento e baixa
confiança são tratados como limitações observáveis. A avaliação com vídeos
representativos e referências independentes ainda está pendente.”

### 05:00–07:00 — Áudio e texto

Selecione **Whisper local**, CPU e modelo instalado. Reproduza o WAV, processe-o
e mostre transcrição, energia, pausas e termos com contexto. Insira uma referência
manual e mostre a comparação. Identifique se o áudio foi sintetizado.

“O áudio é processado localmente. Medimos características acústicas e
transcrevemos com faster-whisper. As regras textuais tratam negação, sujeito e
tempo. A referência manual permite verificar o reconhecimento. No ensaio
sintético original, o modelo perdeu ‘falta de ar’; esse erro continua registrado.
As medidas acústicas não foram validadas para diagnosticar fadiga ou disartria.”

### 07:00–09:15 — Histórico e fusão

Em **Histórico e fusão**, mostre os cenários de mudança prevista e inesperada.
Abra a linha do tempo, evidências e disponibilidade. Mostre a importação de um
relatório com origem temporal explícita ou a evidência da demonstração CLI.

“O histórico compara versões do mesmo medicamento sintético e distingue
mudanças previstas, alterações inesperadas e inconsistências. A correlação
exige o mesmo paciente e sessão e uma janela de 30 segundos. Áudio e texto são
tratados como fontes dependentes, assim como vídeo e movimentação. Os relatórios
de mídia exigem horário de captura informado ou associação marcada como
sintética. A ausência de uma modalidade permite alertas das fontes disponíveis.”

Ao exibir a demonstração CLI, acrescente: “Os eventos textuais e visuais desta
demonstração são fixtures de integração. A inferência dos motores foi apresentada
nos respectivos painéis.”

### 09:15–11:15 — Resultados e erros

Abra `reports/evaluation/development.md`, os JSONs de desenvolvimento/cadência e
a comparação de fala. Mostre os contadores e uma referência não pareada.

“A comparação usa as mesmas entradas e os mesmos limites, com zero ou três
segundos de confirmação. A precisão agregada de sinais foi de 0,143 para 0,200,
com recall de 0,500. Esses números têm uma limitação de anotação: há um rótulo
por episódio e vários eventos por sinal. A classe de tendência também não foi
reconhecida. Na reprodução 1×, o p95 temporal foi de cerca de 15 milissegundos
após a confirmação e 3,015 segundos desde o início. Na fusão, sete eventos
geraram 22 alertas, mostrando a necessidade de avaliar redundância.”

### 11:15–12:30 — Reprodução e evidências

Mostre o guia, comandos do avaliador, configuração e arquivos de saída. Exiba o
registro de testes; execute apenas comandos curtos no tempo disponível.

“O guia reúne a instalação, preparação dos modelos, painel e demonstrações.
Os resultados registram configurações, hashes e ambiente. A suíte possui 113
testes aprovados. Os testes verificam integridade e comportamento programado;
a avaliação com fala natural e movimentos representativos precisa ser ampliada.”

### 12:30–13:30 — Fechamento

Mostre a matriz e o estado da entrega.

“O protótipo integra as frentes locais e registra evidências de cada alerta.
As próximas melhorias são o detector de tendência, referências compatíveis com
os eventos por sinal, avaliação com mídias independentes e controle de alertas
redundantes. O repositório contém código, instruções, relatório e resultados
para reprodução. A matriz identifica o que está implementado e o que ainda
precisa de avaliação.”

## Conferência do arquivo e do link

Após editar, confira áudio inteligível, textos legíveis e duração total ≤ 900 s.
O roteiro de 810 s deixa 90 s de margem; a duração real deve ser medida no arquivo.
Registre caminho, duração e URL em [entrega.json](entrega.json). Confira o link
publicado em uma sessão sem autenticação antes de incluí-lo na submissão.
