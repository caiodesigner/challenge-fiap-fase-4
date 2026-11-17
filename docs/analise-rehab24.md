# REHAB24-6 — exemplos para demonstração

Análise local em 16/11/2026. Os originais permanecem preservados. Foram
processados 12 trechos com MediaPipe real em CPU e as regras atuais, sem
alterar limiares ou interpretar todo rótulo incorreto como assimetria.

## Arquivos prontos

Local: `outputs/rehab24-review/selected/`. Envie no painel **Vídeo**, contexto
**Reabilitação**. São cópias recortadas temporalmente, H.264/MP4, 960×540,
30 FPS constantes, sem áudio, sem alteração de velocidade. Todos cabem nos
limites de duração/tamanho da aplicação. Os originais estão no diretório fornecido.

| Arquivo | Duração | Rótulo da base | Resultado da aplicação |
| --- | --- | --- | --- |
| `01_ex2_correto.mp4` | 8.03 s | Correto | Sem eventos; assessable |
| `02_ex2_assimetria.mp4` | 16.03 s | Incorreto | asymmetry (1.20–2.80 s); assessable |
| `03_ex2_incorreto_sem_evento.mp4` | 16.70 s | Incorreto | Sem eventos; assessable |
| `04_ex2_qualidade_parcial.mp4` | 15.20 s | Incorreto | Sem eventos; partial |

## Ordem sugerida

1. `01_ex2_correto.mp4`: demonstrar processamento postural sem desvio emitido.
2. `02_ex2_assimetria.mp4`: demonstrar assimetria entre 1,20 e 2,80 s. O evento
   corresponde a aproximadamente 91,87–93,47 s do vídeo original. O trecho
   pertence à primeira repetição incorreta incluída, conforme anotações oficiais.
3. Baixe vídeo anotado e relatórios. Confira a evidência e, se desejar, importe
   o relatório no painel de fusão com associação temporal explícita.
4. `03_ex2_incorreto_sem_evento.mp4`: mostrar erro anotado não coberto pelas regras.
5. `04_ex2_qualidade_parcial.mp4`: mostrar avaliação parcial por um quadro
   classificado como múltiplas pessoas pelo estimador (75 válidos e um com múltiplas).

Os dois exemplos principais são da mesma pessoa (person_id 8), permitindo
comparação demonstrativa. Isso não os torna um teste entre pessoas independentes.
A ausência de evento significa apenas que as regras não confirmaram seus
critérios; não equivale à aprovação clínica do exercício.

## Rastreabilidade dos cortes

| Arquivo | Original em Ex2/ | Intervalo no original | Repetições |
| --- | --- | --- | --- |
| `01_ex2_correto.mp4` | `PM_110-Camera17-30fps.mp4` | 5.33–13.37 s | 1 |
| `02_ex2_assimetria.mp4` | `PM_110-Camera17-30fps.mp4` | 90.67–106.70 s | 8, 9, 10 |
| `03_ex2_incorreto_sem_evento.mp4` | `PM_040-Camera17-30fps.mp4` | 49.33–66.03 s | 7, 8, 9, 10 |
| `04_ex2_qualidade_parcial.mp4` | `PM_033-Camera17-30fps.mp4` | 52.00–67.20 s | 8, 9, 10, 11 |

O corte usa `first_frame/30` e final exclusivo `(last_frame+1)/30`.
Os intervalos de evento nos relatórios são relativos ao início do trecho, não
ao início do vídeo original. Hashes dos originais, dos cortes e das anotações,
linhas originais do CSV e caminhos dos relatórios estão em
[`reports/validation/rehab24-review.json`](../reports/validation/rehab24-review.json).
Os relatórios completos e vídeos anotados estão em
`outputs/rehab24-review/analysis/<run-id>/`; o mapeamento está em
`outputs/rehab24-review/selection.json`.

## Resultado da triagem e limites

- 130 vídeos: 65 gravações em duas câmeras. 36 excedem 120 segundos.
- Exercícios: Ex1 (26 vídeos), Ex2 (24), Ex3 (20), Ex4 (24), Ex5 (18), Ex6 (18).
- As anotações oficiais têm 1.072 repetições, dez participantes e rótulos de
  orientação, iluminação, presença de outras pessoas e execução correta/incorreta.
- A seleção inicial foi por Ex2 (Arm VW), câmera 17 frontal, luz ligada e
  ausência de pessoa extra anotada, escolhendo blocos homogêneos de até 20 s.
- Nos 12 candidatos: seis corretos sem eventos; dos seis incorretos, um gerou
  assimetria e cinco não geraram eventos. Onze foram avaliáveis e um parcial.
- Não houve evento de interrupção nesses candidatos. Esses arquivos não
  demonstram movimentação durante internação ou em cadeira.

A base avalia execução de forma mais ampla que nossas regras de ângulo do
ombro/interrupção. Os rótulos não especificam automaticamente a classe do erro:
não converter todos os rótulos incorretos para referências de `asymmetry`.
Os resultados revelam cobertura limitada; não declaram reconhecimento geral
de falhas, sensibilidade clínica ou precisão/recall por evento.

Ex1 é abdução unilateral prevista pelo protocolo. Uma regra bilateral pode
alertar nesse exercício mesmo com execução correta; ele não foi escolhido como
caso de anomalia. Ex3–Ex6 também não foram apresentados como exercícios de braços.

Foram inspecionados quadros em diferentes momentos dos vídeos e do evento
selecionado. Isso não substitui revisão completa por fisioterapeuta. Os casos
finais foram selecionados após observar as saídas e são demonstrações de desenvolvimento.

## Origem e uso

[REHAB24-6 no Zenodo](https://zenodo.org/records/13305826).
Os arquivos `Segmentation.csv` e `Segmentation.txt`, ausentes na pasta de vídeos,
foram baixados da distribuição oficial. O MD5 do CSV corresponde ao publicado:
`90b8fbd7445dd050bf27b17126c78fbe`.

A distribuição restringe o uso a pesquisa acadêmica ou de organizações sem fins
lucrativos, não comercial, e pede citação do trabalho:
Černek, A.; Sedmidubsky, J.; Budikova, P. REHAB24-6: Physical Therapy Dataset
for Analyzing Pose Estimation Methods. SISAP, 2024.
Credite a fonte no relatório e na apresentação. As mídias ficam em `outputs/`,
ignoradas pelo Git; não foram copiadas para os arquivos versionados.
