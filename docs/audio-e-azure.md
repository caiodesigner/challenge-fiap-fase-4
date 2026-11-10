# Áudio, análise acústica e Azure

## Estado

Implementados análise acústica, comparação com referência, termos críticos,
adaptadores HTTPS reais, painel e relatórios persistidos. Não foram criados
recursos Azure nem realizadas chamadas reais: as credenciais estão ausentes.
R03/R04 permanecem pendentes de comprovação real. Testes com respostas controladas
são marcados como `test_transport` e nunca como validação real.

A demonstração em `reports/audio/local-demo.json` usa tons sintéticos, não fala
humana. Não constitui avaliação clínica. A validação inicial teve 73 testes aprovados, incluindo
os fluxos de interface e os requisitos anteriores.

## Caminho gratuito

- [Speech F0](https://azure.microsoft.com/en-us/pricing/details/speech/): 5 horas
  gratuitas de transcrição padrão por mês; repetições também consomem uso.
- [Language F0](https://azure.microsoft.com/en-au/pricing/details/language/):
  5.000 registros mensais gratuitos compartilhados entre funcionalidades.
  Sentimentos e frases-chave são operações distintas. Registros são medidos em
  blocos de 1.000 caracteres, conforme a tabela do serviço.
- [Azure for Students](https://azure.microsoft.com/en-ca/free/students): US$ 100
  por 12 meses, sem cartão, para estudantes elegíveis.

Priorizar recursos **F0** e conferir disponibilidade/nível no portal antes de
criar. Crédito estudantil e franquia gratuita são benefícios distintos. A análise
local não consome Azure; a aplicação não cria recursos, muda níveis nem repete
requisições automaticamente. Confirmar condições vigentes nos links ao configurar.

## Configuração

1. Verificar elegibilidade no Azure for Students.
2. Criar no portal um recurso Speech e um Language com nível F0 disponível.
3. Copiar `.env.example` para `.env` e preencher as chaves localmente, sem enviá-las
   pelo chat ou versioná-las.
4. Preencher a região do Speech ou seu endpoint de recurso; preencher o endpoint
   Language mostrado no portal, sem o caminho da API.
5. Executar o modo Azure explicitamente com áudio apropriado para envio.

```dotenv
AZURE_SPEECH_KEY=chave-local
AZURE_SPEECH_REGION=regiao-do-recurso
AZURE_SPEECH_ENDPOINT=
AZURE_LANGUAGE_KEY=chave-local
AZURE_LANGUAGE_ENDPOINT=https://recurso.cognitiveservices.azure.com
```

O endpoint Speech opcional prevalece sobre a região. Apenas HTTPS em domínios
Azure suportados é aceito, sem redirects. O carregador `.env` não executa comandos
nem expande variáveis. O ambiente prevalece sobre o arquivo; reiniciar Streamlit
após alterar uma chave já carregada.

## Uso

```bash
.venv/bin/python scripts/demo_audio.py
.venv/bin/python scripts/analyze_audio.py caminho/audio.wav
.venv/bin/python scripts/analyze_audio.py caminho/audio.wav --reference caminho/referencia.wav
# Somente com recursos configurados e arquivo apropriado para envio:
.venv/bin/python scripts/analyze_audio.py caminho/audio.wav --azure
.venv/bin/python -m streamlit run app.py
```

No painel, escolher **Áudio**. O padrão atual é **Whisper local**, descrito em
[execucao-local.md](execucao-local.md). **Somente local** permite análise sem modelo. A transcrição manual
opcional é identificada como manual e não pode substituir Speech no modo Azure.
O modo **Azure Speech + Language** envia o WAV e analisa sua transcrição. A
referência acústica é sempre local. Resultados JSON/Markdown em
`outputs/audio/<run-id>/` continuam acessíveis após recarregar a página.

Formato: WAV PCM 16-bit, mono, 16 kHz, de 0,3 a 30 segundos, até 4 MB.
Outros formatos exigem conversão explícita.

## Acústica e limites

São medidos RMS global/por janela de 20 ms em dBFS, saturação, atividade por
energia, cruzamentos de zero e pausas internas de baixa energia. Pausas no início
ou fim não são confundidas com pausas internas. O padrão indica pausas internas
≥2 s; com referência, precisam exceder também sua maior pausa por pelo menos 1 s.

Qualidade insuficiente impede eventos vocais e chamadas Azure. Energia não prova
fala: ruído e tons também podem apresentar atividade. Não se estima SNR sem
referência de ruído, nem se diagnostica fadiga, dificuldade respiratória ou
disartria. Calibração com fala e rótulos independentes continua necessária.

## Serviços e texto

Speech usa [REST de áudio curto](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-speech-to-text-short)
com `pt-BR` e resposta detalhada. Essa opção evita dependência binária do SDK no
ambiente atual. Retorna resultado final, sem transcrição parcial.
Language usa [REST de análise textual](https://learn.microsoft.com/en-us/rest/api/language/),
versão `2023-04-01`, com `SentimentAnalysis` e `KeyPhraseExtraction` em português.
Há até três tentativas por execução normal, sem retries. A contagem de tentativas
não substitui a medição de faturamento no portal.

Chaves, cabeçalhos e respostas remotas brutas não são gravados. CPF, e-mail e
telefone são mascarados na transcrição antes de persistir e enviar ao Language.
Isso não anonimiza nomes, voz ou todos os dados sensíveis. O WAV original é enviado
ao Speech quando esse modo é escolhido.

O vocabulário contempla falta de ar, dor no peito, tontura, cansaço e dificuldade
para respirar. Regras locais distinguem afirmação, negação, incerteza, histórico
e alguns casos referentes a outra pessoa; não cobrem toda a linguagem natural.
Sentimento negativo sozinho não gera evento de risco. Menção afirmada, atual e
atribuída ao paciente gera `critical_mention`.

Os offsets são do texto sanitizado. Não há alinhamento palavra a palavra ao
áudio; eventos textuais têm tempo zero explicitamente não alinhado. O horário
da sessão é atribuído ao processamento, não presumido como captura da consulta.
Fusão temporal e fila de alertas continuam na etapa de integração.

`real_azure_validation` só é verdadeiro se o transporte real concluir Speech e
as duas análises Language. Configuração ausente, ausência de reconhecimento,
timeout, quota e falhas parciais ficam explícitos. Evidência acústica é preservada
em falhas dos serviços, sem apresentar resultado parcial como validação real.

## Pendências

- Configurar recursos gratuitos e executar as três chamadas reais com áudio adequado.
- Preservar evidências sanitizadas de resultados, latência e uso observado.
- Comparar transcrição com referência manual e avaliar termos/voz separadamente,
  com fontes e locutores independentes entre partições.
- Ampliar exemplos antes de inferir robustez ou qualidade clínica.
