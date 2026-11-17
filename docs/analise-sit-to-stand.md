# Sit-to-Stand — análise dos vídeos Subject 14

Análise realizada em 16/11/2026 com MediaPipe real em CPU, modo Internação
(`inpatient`). Os originais não foram modificados.

## Resultado após a correção

| Arquivo | Duração | Quadros amostrados válidos | Avaliação | Eventos |
| --- | --- | --- | --- | --- |
| `out_Subject_14_before.mp4` | 31,50 s | 158/158 | assessable | Nenhum confirmado |
| `out_Subject_14_after.mp4` | 35,13 s | 176/176 | assessable | rise_candidate de 28,8 a 29,8 s |

Ambos são MP4, 1920×1080, 30 FPS, menores que 200 MB e 120 s. Os totais
originais (945 e 1.054 quadros) coincidem com as planilhas antes inspecionadas.

## Correção aplicada

A versão anterior rejeitou todos os quadros: exigia ambos os cotovelos mesmo
na Internação. O cotovelo distante da câmera estava ocluído, com visibilidade
aproximada entre 0,02 e 0,08 nas amostras diagnósticas, abaixo de 0,60.

Em `pose-rules-v2`, a Internação exige ombros e quadris para calcular o centro
do tronco. Os ângulos dos braços ficam nulos. A Reabilitação continua exigindo
os dois cotovelos para analisar os ângulos. Os limiares temporais, de movimento
e de confiança não foram alterados para produzir estes resultados.

O evento em after é um candidato exploratório, não confirmação clínica de
levantamento ou risco de queda. Before não atingiu as condições de confirmação:
a ausência de evento não significa ausência de movimentos de levantar.
Os rótulos before/after indicam antes/depois do exercício, não normal/anormal.
A aplicação não classifica fadiga clínica de joelho. A associação ao cenário
de internação deve ser identificada como demonstração sintética.

## Marcações prévias e entrega

Os vídeos têm fundo removido e linhas/ângulos já desenhados pela fonte.
O PDF original (p. 3) não exige explicitamente vídeos crus nem proíbe essas
marcações. Exige processamento de vídeos, detecção de desvios e relatórios.
A aplicação executou MediaPipe sobre as imagens, sem consumir as planilhas
ou os ângulos escritos. Identifique as marcações originais na apresentação e
mostre entrada, saída gerada e relatório; não as atribua ao nosso sistema.
Elas podem influenciar a estimativa e não são validação independente.

## Evidências

Inventário, relatórios completos e vídeos anotados estão em
`outputs/sit-to-stand-review/`. O resumo com hashes, parâmetros, diagnóstico
e resultados antes/depois da correção está em
[reports/validation/sit-to-stand-review.json](../reports/validation/sit-to-stand-review.json).

[Origem do dataset](https://dataverse.telkomuniversity.ac.id/dataset.xhtml?persistentId=doi:10.34820/FK2/VAEGNR).
