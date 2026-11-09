# Dados, contratos e conjuntos de avaliação

## Estado desta etapa

Preparados contratos executáveis, schemas JSON, fixtures reproduzíveis e um
subconjunto externo para ingestão de sinais. Não há detectores ou métricas de
desempenho produzidos nesta etapa. A preparação funcional está concluída; a
composição de um teste independente com fala e vídeo permanece aberta.

## Camadas de dados disponíveis

| Camada | Conteúdo | Uso permitido pela evidência |
| --- | --- | --- |
| `data/fixtures` | 90 casos JSON, três pacientes/sessões/fontes sintéticos e três WAVs de tons técnicos | Testar contratos, integridade, regras e fluxo; não avaliar doença ou estimador de postura |
| `data/external/bidmc` | Seis registros numéricos públicos de 481 linhas cada, versão 1.0.0, com licença e manifesto | Avaliar ingestão e disponibilidade de frequência cardíaca/oxigenação; sem verdade de referência de anomalia |
| `data/schemas` | Schemas derivados dos modelos Pydantic | Documentar formato e integrar componentes |
| `configs/evaluation.json` | Protocolo funcional versionado | Fixar comparação, pareamento, tratamento de divisões por zero e metas internas |

As fixtures usam a semente 42 e não dependem da fase 3, de rede ou de serviços.
Há cinco casos por frente em cada partição: sinais vitais, prescrições, vídeo,
movimentação, áudio e texto. Arquivos de vídeo são **características artificiais
em JSON**, não vídeos clínicos; envelopes de áudio não são extraídos dos tons WAV.
Os WAVs servem somente para testar leitura de um arquivo PCM mono de 16 kHz.
Textos são roteiros escritos, não resultados de reconhecimento de fala.

Rótulos positivos indicam a intervenção do gerador no instante descrito, não
anotação clínica. `expected_outcome` inclui também erros, insuficiência, negação
e histórico. Variações da mesma fonte ficam na mesma partição; os templates
compartilhados entre fontes limitam independência estatística. Mesmo o diretório
`test` destas fixtures é um teste funcional público, não um teste clínico cego.

## Fonte externa e atribuição

[BIDMC PPG and Respiration Dataset v1.0.0](https://physionet.org/content/bidmc/1.0.0/):
Pimentel, Johnson, Charlton e Clifton. A publicação de referência é Pimentel et al.,
“Towards a Robust Estimation of Respiratory Rate from Pulse Oximeters”,
[DOI 10.1109/TBME.2016.2613124](https://doi.org/10.1109/TBME.2016.2613124).
Dados distribuídos sob Open Data Commons Attribution License v1.0; o aviso
original está em `data/external/bidmc/LICENSE` e se aplica a esses arquivos,
independentemente da licença proprietária do código deste projeto.

Recorte: arquivos `Numerics.csv` dos registros 01–06. Desenvolvimento: 01/02;
validação: 03/04; teste: 05/06. A separação é por registro/fonte; não afirmamos
independência entre indivíduos além do que a identificação pública permite.
Sem download de arquivos demográficos ou prontuários. Não associar esses registros
aos pacientes sintéticos como se pertencessem à mesma pessoa. Não há upload
automático para a nuvem.

Os CSVs permanecem na forma original, com valores ausentes quando existentes.
O validador confere hashes, colunas, unicidade de fontes, cobertura das partições
e ordem temporal. A conversão futura precisa tratar valores ausentes e qualidade,
sem preencher silenciosamente. Não há referência de anomalias para classificar
trechos como normais/anormais e não há pressão arterial neste recorte.

[AudioSet](https://research.google.com/audioset/) foi analisado como sugestão do
enunciado: é um conjunto de eventos sonoros, não de diagnósticos de alterações
vocais. Não foi incorporado nesta etapa nem tratado como evidência clínica.

## Contratos implementados

Em `src/monitoramento_clinico/contracts.py`:

- `Patient` e `Session`: adulto sintético, vínculo e intervalo da sessão.
- `Measurement`: sinal/unidade compatíveis, valor finito e horários explícitos.
- `PrescriptionVersion`: medicamento sintético, início/alteração/suspensão,
  dose/unidade e justificativa para mudança prevista. Unidades incompatíveis
  são representáveis para testar inconsistência sem efetuar conversão indevida.
- `MediaAsset`: caminho, hash, duração, origem, licença/consentimento e permissão
  explícita de upload, inicialmente falsa.
- `Evidence`, `Event` e `Alert`: evidência temporal, detector versionado, vínculo
  de paciente/sessão, chave de deduplicação e estados de revisão.
- `ReferenceLabel`, `EvaluationCase` e `Manifest`: rótulo de referência, cenário,
  partição, status de entrada e procedência.

Os timestamps exigem fuso e são normalizados para UTC; intervalos invertidos e
campos extras são rejeitados. Contratos de referência não são tabelas persistentes.
O ciclo de vida de alertas, a autorização de revisões e os vínculos de eventos
serão validados pelo serviço de operação quando implementado. O schema SQLite
de contexto da fase anterior ainda não é o banco multimodal.

## Validação e isolamento

O comando `validate` confere hashes, caminhos restritos à raiz, duplicações de
IDs/conteúdo exato, vínculos de paciente/sessão, fontes em uma única partição,
índices de partição e intervalos de rótulos. Payloads inválidos intencionais só
são aceitos no catálogo quando realmente falham a validação de entrada.
O scanner textual verifica campos e padrões de identificadores; hashes válidos
no campo tipado `sha256` não são interpretados como números de telefone.
Ele não certifica anonimização, consentimento ou segurança de uma mídia.

Nos dados reais futuros, o grupo deve abranger pessoa, locutor, vídeo original e
seus derivados. Hash exato não detecta cópias recortadas ou reencodificadas;
o manifesto precisa registrar a fonte comum, e a curadoria deve conferir isso.

## Avaliação preparada

O protocolo funcional compara baseline simples com solução temporal e modalidades
isoladas com fusão. Calibrar apenas em desenvolvimento/validação. O teste funcional
não será usado para alegar generalização. O conjunto independente de mídia deve
ser congelado e versionado antes da calibração final dos detectores.

Reportar precisão/recall/F1 por evento, contagens, falsos alertas por hora,
latência e falhas; denominador zero retorna resultado não definido, não 100%.
Pareamento temporal é um a um por paciente/sessão/classe com tolerância de 5 s;
texto e prescrições devem usar identificadores de registro/menção. Rótulos de
texto são eventos pontuais; sua referência à menção será expandida na avaliação textual.
WER exige fala e transcrição manual: não calcular a partir dos roteiros isolados.
Nenhuma métrica será calculada sobre saídas simuladas de Azure como se fossem reais.

## Aquisição e cobertura pendentes

| Necessidade | Preparação definida | Evidência ainda necessária |
| --- | --- | --- |
| Vídeo de fisioterapia | Roteiros VID-01–05 e contrato de mídia/eventos | Gravações consentidas/licenciadas, enquadramento viável, intervalos anotados |
| Movimentação em leito/cadeira | Roteiros MOV-01–05 | Vídeos encenados com pessoa e trechos normais/alterados anotados |
| Fala em português | Roteiros de menção, negação, histórico e pausas | Áudios consentidos, locutores separados, transcrição manual e autorização de nuvem |
| Pressão arterial | Séries sintéticas com sistólica e diastólica | Fonte real adequada se for alegada avaliação em sinais reais de pressão |
| Integração | Contratos de eventos/alertas | Fixtures de fluxo INT-01–06 junto à implementação da correlação/persistência |
| Casos raros | Insuficiência, artefato, lacuna e unidades incompatíveis no catálogo | Mais fontes e variantes antes de conclusões sobre robustez |

Para aquisição de mídias, planejar inicialmente três grupos distintos de
participantes/fontes por partição, com versões normal/alterada e qualidade
degradada, sem compartilhar locutor/pessoa entre partições. Esse mínimo é um
plano de diversidade, não cálculo de tamanho amostral. Confirmar acesso, consentimento
e quantidade real no inventário antes de congelar o teste. Fadiga encenada não
equivale a um rótulo de condição médica. Não foi declarado atendimento dos
requisitos de análise de áudio/vídeo apenas com as fixtures atuais.

## Reprodução

```bash
.venv/bin/python -m monitoramento_clinico.data generate
.venv/bin/python -m monitoramento_clinico.data validate
.venv/bin/python -m monitoramento_clinico.data schemas --root data/schemas
.venv/bin/python scripts/prepare_bidmc.py validate
# Opcional: refazer download público; requer rede e preserva licença/origem.
.venv/bin/python scripts/prepare_bidmc.py download
```

O gerador sobrescreve os arquivos conhecidos no diretório dedicado de fixtures.
Use `--root /tmp/fixtures-fase4` para gerar uma cópia isolada. Não apontar para
dados coletados manualmente. As distribuições constam no manifesto; não há
dependência de caminhos externos ao repositório para reproduzir a validação.
