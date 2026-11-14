# Avaliação de resultados, falhas e latência

Esta é a primeira execução da etapa 8 da lista operacional (Etapa 7 do plano).
O escopo ativo usa processamento local. Foram executadas as regras de sinais
vitais e prescrições sobre as **fixtures sintéticas de desenvolvimento**. O
conjunto de teste não foi usado nesta execução; dados representativos de mídia
continuam pendentes.

## Executar novamente

```bash
# Comparação pareada das regras imediatas e temporais, mais prescrições.
.venv/bin/python scripts/evaluate_local.py

# Reprodução 1× do mesmo caso nas duas alternativas: cerca de 38 segundos.
.venv/bin/python scripts/evaluate_local.py \
  --case development-vitals-2 --speed 1 \
  --output outputs/evaluation/cadence.json

# Acrescentar contagem do volume de alertas da demonstração multimodal.
.venv/bin/python scripts/demo_clinical_fusion.py
.venv/bin/python scripts/evaluate_local.py \
  --fusion-report outputs/clinical-demo.json
```

O comando grava JSON e Markdown. Aceita `--split development|validation|test`,
`--fixtures`, `--config`, `--protocol` e `--output`. O padrão é desenvolvimento.
Usar `test` não transforma as fixtures geradas em um teste clínico independente.
Os bancos de avaliação ficam em diretórios temporários, com banco novo para cada
caso e alternativa. Os bancos do painel não são usados pelo avaliador.

A avaliação de fala com referências manuais é um comando separado:
`scripts/evaluate_local_speech.py`, documentado em `docs/validacao-local.md`.
Este experimento não executa Whisper, MediaPipe nem serviços externos.

## Protocolo e comparabilidade

O protocolo está em `configs/evaluation.json`. A revisão `functional-v1-local`
retira a meta Azure do escopo ativo e preserva tolerância, critérios de pareamento
e metas experimentais anteriores. Nenhum rótulo foi alterado nesta avaliação.

A baseline usa o mesmo monitor SQLite, os mesmos limites, entrada, ordenação e
filtros de qualidade, com persistência de **zero segundos**. A alternativa temporal
mantém os três segundos de confirmação configurados. Zero agora é um valor
permitido explicitamente em `VitalsConfig`; o comportamento padrão continua em
três segundos. Ambas emitem uma vez por episódio e sinal.

O pareamento exige paciente, sessão e tipo de evento iguais. Para séries, aceita
início a até cinco segundos, inclusive. Candidatos são ordenados pela menor
distância global, depois por ID de previsão e referência; cada previsão e referência
são usadas uma única vez. Texto/prescrições exigem identidade do registro de origem,
sem tolerância temporal. Previsões extras contam como FP e referências sem par
como FN. O JSON registra os IDs pareados e não pareados, além das métricas por classe.

Precisão, recall e F1 preservam `null` quando seus denominadores são zero.
O p95 usa o método de posto mais próximo. Falsos alertas por hora negativa usam
somente FP de casos negativos e a duração entre o primeiro e último registro
observado desses casos; não usam o minuto inteiro declarado na sessão. Horas
iguais a zero produzem `null`. Contagens e segundos observados acompanham as taxas.

## Resultado funcional de desenvolvimento

Evidência: `reports/evaluation/development.json` e seu resumo Markdown.

| Alternativa | TP | FP | FN | Precisão | Recall | F1 |
| --- | --- | --- | --- | --- | --- | --- |
| Sinais, regra imediata | 1 | 6 | 1 | 0,143 | 0,500 | 0,222 |
| Sinais, confirmação temporal | 1 | 4 | 1 | 0,200 | 0,500 | 0,286 |
| Prescrição, alteração inesperada de dose | 1 | 0 | 0 | 1,000 | 1,000 | 1,000 |

Foram selecionados cinco casos de sinais e cinco de prescrições. Um caso de
sinais contém unidade inválida e foi rejeitado nas duas alternativas; ele aparece
na contagem de integridade, sem ser apresentado como caso negativo bem classificado.

Há dois problemas que impedem interpretar os números como desempenho clínico:

1. **Granularidade dos rótulos de sinais.** A fixture de desvio persistente possui
   um rótulo de episódio, mas quatro sinais alterados. O detector emite quatro
   eventos; o pareamento congelado aceita um e conta três como extras. Isso indica
   incompatibilidade entre anotação e unidade de avaliação, não três diagnósticos
   clínicos errados. Referências por sinal ou um protocolo por episódio deverão
   ser definidos e versionados em desenvolvimento antes de outro teste.
2. **Tendência ainda não tem detector específico.** A referência espera
   `trend_deviation`; o monitor identifica apenas desvios persistentes de limite.
   Essa classe teve recall zero. Os tipos não foram renomeados para obter acerto.
   A confirmação temporal gerou dois eventos extras a menos nesse cenário, sem
   recuperar a referência de tendência.

Os resultados de sinais ficam abaixo das metas experimentais de precisão e
recall de 0,80 no agregado. O único exemplo positivo de dose foi reconhecido;
1,000 nesse pequeno conjunto não estima generalização. Interrupções, unidades e
sequências de prescrição têm seus eventos preservados em `unscored_events`, pois
o catálogo atual não fornece rótulos completos dessas classes. Eles não são
contados artificialmente como acertos nem como erros de dose.

Nos casos negativos foram observados 38 segundos de sinais e 45 de prescrições,
com zero FP para as classes avaliadas. Essa duração não estabelece uma taxa
estável de falsos alertas em operação prolongada. Não foi estimado intervalo de
confiança com essas poucas fontes sintéticas compartilhando templates.

## Latência em cadência 1×

Evidência: `reports/evaluation/cadence-development.json`.
Foi reproduzido o caso `development-vitals-2` separadamente nas duas alternativas.

| Alternativa | p95 após disponibilidade da confirmação | p95 desde o início do desvio |
| --- | --- | --- |
| Regra imediata | aproximadamente 15,6 ms | aproximadamente 15,6 ms |
| Confirmação temporal | aproximadamente 15,2 ms | aproximadamente 3,015 s |

A janela de três segundos explica a diferença entre as duas medidas. Os valores
incluem a reprodução sintética e a emissão persistida naquele ambiente. Não
incluem captura de sensores, rede ou inferência de áudio/vídeo. Latências abrangem
os alertas emitidos, inclusive eventos extras segundo o pareamento.

O modo acelerado mede processamento por amostra, sem demonstrar cadência real;
seus campos de latência desde confirmação/início permanecem `null`. Os resultados
1× são de uma série curta, não uma avaliação de disponibilidade ou p95 de todas
as modalidades. O ambiente, parâmetros, hashes das entradas e protocolo são
registrados no JSON; tempos variam entre execuções.

## Fusão: volume e limitações

Na demonstração de desenvolvimento, sete eventos produziram sete alertas isolados
e 15 combinados: **22 alertas**, ou cerca de 3,14 por evento. A fusão atual é por
pares; esse crescimento merece avaliação de agrupamento por episódio e de alertas
redundantes. A contagem não demonstra que a fusão melhora a detecção.

Não existem referências multimodais independentes para atribuir TP/FP/FN aos
alertas combinados. Por isso, precisão e recall da fusão permanecem indefinidos.
O relatório apresenta a contagem isolada e combinada com hash da fonte utilizada.

## Robustez e próximos passos

A suíte de implementação cobre isolamento de paciente/sessão, ordenação,
duplicações, persistência/revisão, fonte ausente, falha de formato, contexto de
menções e importação de mídia com origem temporal explícita. Com o avaliador,
passaram **113 testes**, Ruff, formatação e Mypy.

Para concluir a etapa, faltam:

- Definir referências por sinal ou protocolo por episódio e registrar a revisão;
  desenvolver um detector de tendência com dados de desenvolvimento adequados.
- Avaliar o volume e a utilidade dos alertas combinados com referências multimodais.
- Coletar fala natural e vídeos com anotações independentes, medir WER, termos,
  alterações acústicas, postura e movimentação e congelar fontes de teste separadas.
- Medir latência e falhas do fluxo com os modelos locais nas mídias representativas.
- Executar as alternativas finais no teste reservado e preparar a entrega técnica.

A etapa avançou em instrumentação e evidência funcional. A avaliação representativa
permanece aberta, sem modificar as referências a partir das previsões observadas.
