# SPIRA — exemplos preparados para o challenge

Análise técnica realizada em 16/11/2026. Os originais permanecem preservados.
As cinco cópias foram convertidas sem cortes para WAV mono PCM 16-bit/16 kHz e
executadas no fluxo completo com Whisper small CPU/int8, acústica e sentimentos locais.
Nenhuma chamada à nuvem foi utilizada. Esta seleção é de desenvolvimento.

## Onde estão os arquivos

Os arquivos prontos para upload estão em `outputs/spira-review/selected/`.
Cada um tem entre 0,3 e 30 segundos. Os relatórios completos ficam em
`outputs/spira-review/analysis/<run-id>/`. O mapeamento com os originais, hashes e
relatórios está em `outputs/spira-review/selection.json` e na evidência versionável
[`reports/validation/spira-review.json`](../reports/validation/spira-review.json).

| Arquivo pronto | Duração | Maior pausa interna | Evento de pausa longa | Uso |
| --- | --- | --- | --- | --- |
| `01_controle_continuo.wav` | 8.53 s | 0.00 s | Não | Controle sem pausa interna detectada |
| `02_paciente_pausas.wav` | 22.38 s | 2.64 s | Sim | Paciente com pausas longas |
| `03_paciente_pausas.wav` | 24.58 s | 2.50 s | Sim | Segundo paciente com pausas longas |
| `04_controle_com_pausa.wav` | 14.08 s | 3.16 s | Sim | Contraponto: controle também pode ter pausa longa |
| `05_paciente_sem_pausa.wav` | 7.52 s | 0.00 s | Não | Contraponto: paciente pode não ter pausa longa |

## Sequência sugerida no painel

1. Abra **Áudio → Whisper local**, CPU. Deixe a referência acústica vazia.
2. Envie `01_controle_continuo.wav`: demonstrar transcrição e ausência de evento.
3. Envie `02_paciente_pausas.wav`: conferir pausa entre 13,50 e 16,14 s (2,64 s).
4. Envie `03_paciente_pausas.wav`: conferir pausa entre 5,92 e 8,42 s (2,50 s).
5. Use `05_paciente_sem_pausa.wav` para mostrar que ausência de evento não exclui condição clínica.
6. Opcionalmente, confira `04_controle_com_pausa.wav`: pausa de 3,16 s em um controle.
   Esse arquivo contém autoapresentação falada; revise seu conteúdo antes da apresentação pública.
7. Ouça cada arquivo, confira a transcrição e registre os erros. Baixe JSON/Markdown.

## O que esses exemplos demonstram

A base inclui uma frase preparada de leitura relacionada ao enfrentamento do
coronavírus. Isso permite exemplificar transcrição e características acústicas.
Nos cinco exemplos, a aplicação retornou sentimento neutro e nenhuma menção
crítica. Isso é coerente com os termos observados nas transcrições, mas não é
uma avaliação humana da emoção. Seus áudios encenados continuam úteis para
demonstrar sentimento positivo/negativo, afirmação e negação de sintomas.

Os grupos `pacientes` e `controle` vêm da base; a aplicação não prevê esses
grupos. Nos arquivos selecionados há paciente sem pausa e controle com pausa:
não apresentar `long_pause_observed` como diagnóstico de insuficiência respiratória.
Os códigos `class` e `nivel_falta_de_ar` são preservados como metadados, sem
interpretar o código 5 como escala de gravidade clínica.

## Inventário e seleção

- 469 WAVs: 218 pacientes, 235 controles e 16 ruídos hospitalares.
- Todos os arquivos de fala cabem no limite de 30 s, mas os originais estão em 44,1/48 kHz.
- CSVs: 292 linhas de treino, 32 de validação e 108 de teste; 423 caminhos únicos.
- Nove caminhos aparecem tanto no treino quanto na validação. Não foram escolhidos.
- Há 30 gravações de fala fora dos CSVs; não foram escolhidas.
- Foram triados 315 arquivos fora do teste. Todos passaram no critério técnico de qualidade da aplicação.
- Nessa triagem, 20 arquivos de pacientes e dois de controles geraram pausa longa.
- Os cinco selecionados pertencem somente ao treino. Não foi feita inferência no teste reservado.
- O pacote traz arquivos de ruído, não vídeos. Ruídos não substituem relatos de pacientes.

A triagem mediu energia e executou transcrição automática; não incluiu escuta
clínica ou transcrição manual de referência. Arquivos do mesmo grupo não são
necessariamente a mesma pessoa: não use um controle como referência longitudinal
de um paciente. Os casos foram escolhidos observando as saídas; não calcular
precisão/recall clínicos apenas com esta seleção.

## Origem

[Download SPIRA no Zenodo](https://zenodo.org/records/6672451).
[Artigo original](https://aclanthology.org/2021.findings-acl.55/).
Credite os autores e siga os termos da distribuição ao usar os materiais.
Os áudios convertidos e originais não foram adicionados ao Git.
