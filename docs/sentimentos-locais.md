# Análise local de sentimentos

O PDF original inclui identificação de sentimentos entre os requisitos de áudio.
Conforme orientação do professor informada pelo autor, Azure é opcional. A análise
agora ocorre localmente, sem serviços externos, downloads ou novas dependências.

## Executar

No painel **Áudio**, analise uma gravação em **Whisper local**. A seção
**Sentimento do relato** mostra a classe e as evidências. Em **Somente local**,
uma transcrição manual opcional também permite analisar o texto, explicitamente
identificado como manual. O resultado vem da transcrição sanitizada, não das
características acústicas. Referências manuais usadas para avaliar Whisper não
alteram o resultado da inferência.

```bash
.venv/bin/python scripts/analyze_audio.py caminho/relato.wav --whisper --device cpu
```

A análise fica em `local_sentiment` nos relatórios JSON e em **Sentimento textual
local** no Markdown. Relatórios antigos não são modificados: execute novamente
a análise para obter o novo campo. Quando não há transcrição ou ela falha,
o sentimento fica indisponível (`not_assessable`, classe e índice `null`).

## Método e interpretação

A versão `sentiment-pt-lexicon-v1` é uma baseline determinística com vocabulário
de expressões afetivas em português e escopo curto de negação por oração.
Não exige modelo adicional. A análise retorna:

| Classe | Exemplo |
| --- | --- |
| Positivo (`positive`) | Estou feliz e tranquila. |
| Negativo (`negative`) | Estou preocupada e com medo. |
| Misto (`mixed`) | Estou tranquila, mas preocupada com o exame. |
| Neutro (`neutral`) | A consulta está marcada para amanhã. |

“Não estou bem” produz evidência negativa. “Não estou triste” neutraliza a
expressão negativa, sem inferir felicidade. “Estou com falta de ar” continua
sendo uma menção crítica; o sintoma isolado não é usado como evidência de
sentimento. Sentimentos negativos não geram eventos ou elevam severidade de
alertas. Menções críticas e medidas acústicas mantêm suas regras próprias.

Cada evidência inclui expressão, contexto, polaridade, negação e posições no
texto sanitizado. Os offsets preservam acentos e caracteres Unicode. Contagens
registram evidências positivas, negativas e neutralizadas. O índice entre -1 e 1
é `(positivas - negativas) / (positivas + negativas)`, ou zero sem evidências
polares; não é confiança nem probabilidade. Uma classe mista pode ter índice zero.

## Limites e avaliação

Esta baseline não interpreta ironia, linguagem figurada, todas as expressões,
alvos de opinião, sujeito e temporalidade do sentimento. Classifica o afeto
expresso no texto, inclusive referências históricas ou a terceiros. Negação tem
janela de quatro tokens, limitada por pontuação e conectivos. Texto sem expressão
reconhecida recebe neutro: isso não comprova neutralidade emocional. Não há
alegação de equivalência com modelos de sentimentos nem de validação clínica.

A qualidade depende da transcrição. Conferir erros de Whisper continua necessário.
Para avaliação representativa, atribua rótulos humanos a relatos antes de executar
a análise e registre divergências. Os testes atuais cobrem comportamento funcional,
negação, mistura de polaridades, sintomas, offsets, persistência e interface;
não estimam generalização em consultas naturais.

A verificação completa passou com **145 testes**, Ruff, formatação e Mypy.
Uma gravação sintética também foi transcrita pelo Whisper real em CPU e
classificada localmente, sem chamadas de nuvem. Exemplos e evidência estão em
[reports/validation/sentiment-local.json](../reports/validation/sentiment-local.json).
