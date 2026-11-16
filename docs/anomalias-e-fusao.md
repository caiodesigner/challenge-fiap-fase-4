# Anomalias clínicas e fusão multimodal

> Atualização de 15/11/2026: a revisão local v2 implementa tendência monotônica
> por sinal, referências sintéticas por sinal e fusão agrupada por episódio.
> As limitações abaixo sobre detector ausente, granularidade e fusão por pares
> descrevem a revisão histórica v1. Consulte [prontidão da entrega](prontidao-entrega.md)
> para comandos, resultados atuais e pendências externas.


Implementação da Etapa 6 do plano (sétima etapa operacional, pois a numeração
começa em zero). Os cenários e limites são sintéticos; não definem recomendações
médicas. A avaliação com dados representativos permanece para a etapa seguinte.

## Uso no painel

Execute `.venv/bin/python -m streamlit run app.py` e selecione **Histórico e
fusão** na barra lateral. Escolha um dos cinco cenários e clique em **Processar
cenário sintético**. O painel mostra prescrições, eventos, alertas, origem das
evidências, disponibilidade de modalidades e revisão humana. O processamento da
demonstração é acelerado, sem comprovação de cadência real.

Cada cenário usa um banco próprio em `outputs/clinical-scenario-N.db`, separado
dos bancos anteriores. Repetir a demonstração preserva registros e revisões,
sem duplicar eventos/alertas. As séries e prescrições são associadas
**sinteticamente**, não são registros reais simultâneos de um paciente.

O botão **Importar prescrições** recebe JSON com a chave `prescriptions` e versões
no contrato `PrescriptionVersion`, como nas fixtures de desenvolvimento. Paciente
e sessão devem coincidir com os selecionados. Cada versão é gravada atomicamente;
se um conflito interromper um lote, versões anteriores permanecem persistidas.
O retorno registra aceitação, repetição ou rejeição temporal de cada versão.

## Histórico de prescrições

O histórico preserva identificador, medicamento sintético, dose, unidade, ação,
horário, motivo e sinalização de mudança prevista. A comparação é por paciente,
sessão e medicamento, usando a última versão aceita, mesmo após reiniciar.

| Situação | Comportamento |
| --- | --- |
| Dose estável | Preserva versão, sem evento de alteração inesperada |
| Mudança prevista com motivo | Preserva versão e justificativa, sem alerta de dose inesperada |
| Alteração sem previsão, razão entre doses ≥ 2 | Evento `unexpected_prescription_change` |
| Transição entre zero e dose positiva | Também tratada como alteração inesperada quando não prevista |
| Interrupção sem previsão | Evento `unexpected_prescription_stop` |
| Unidade incompatível, mesmo com mudança prevista | Registra inconsistência; não usa a versão como base de dose |
| Alteração sem início, início duplicado ou interrupção de medicamento inativo | Inconsistência de sequência; não altera estado aceito |
| Registro repetido idêntico | Não grava novamente |
| Mesmo identificador com conteúdo diferente | Rejeita e preserva a versão anterior |
| Versão atrasada ou horário igual ao último aceito | Registra `out_of_order`, sem reescrever o estado já processado |

As inconsistências geram alertas de **observação** e ficam fora da fusão de
sinais clínicos. As únicas unidades aceitas para comparação são as sintéticas
do contrato atual. Não há equivalência entre medicamentos, conversão de unidades,
checagem de interação ou sugestão de tratamento. O marcador de mudança prevista
é dado de entrada auditável, não comprovação de autorização profissional.

## Correlação e alertas

`ClinicalMonitor` amplia o monitor persistente de sinais vitais existente. Os
quatro sinais — frequência cardíaca, pressão sistólica/diastólica e SpO₂ — mantêm
as regras e a confirmação temporal já implementadas. Não foi treinado detector
estatístico: faltam dados independentes rotulados para justificar esse avanço.
A comparação entre baseline, detector temporal e fusão permanece na avaliação.

A correlação usa o **início da ocorrência**, nunca o horário de processamento:

- Mesmo paciente e sessão, diferença entre inícios de até **30 segundos**, inclusive.
- Eventos tardios também podem se correlacionar com eventos já persistidos.
- `audio` e `text` pertencem à mesma família; `video` e `movement` também.
  Duas visões dependentes da mesma fonte não geram reforço multimodal entre si.
- Somente os tipos permitidos em `ClinicalConfig.fusion_event_types` participam.
  Eventos desconhecidos continuam visíveis como observações.
- Cada evento emite seu alerta isolado, sem depender de outra modalidade.
  Um par de famílias distintas emite um alerta combinado com ambos os IDs.
- Severidade experimental: `observation` para qualidade/consistência,
  `attention` para evento isolado elegível e `priority` para correlação.
- Chaves determinísticas por versão de configuração e IDs ordenados evitam
  duplicação dos mesmos pares. O alerta preserva os eventos completos como
  evidência consultável, sem substituir os alertas isolados.
- Estados persistidos: aberto → reconhecido → encerrado. A emissão acontece antes
  da revisão; reconhecer/encerrar exige responsável, comentário e resultado ao encerrar.

A fusão atual é **por pares**, sem inferência de causalidade nem supressão de
alertas isolados. Um episódio com muitos eventos pode produzir muitos pares;
medir falsos alertas e investigar agrupamento por episódio fazem parte da
avaliação. Correlação não demonstra ganho de precisão por si só.

A configuração clínica é congelada por banco. Para experimentar outra janela,
razão de doses ou lista de eventos, crie outro banco e passe `ClinicalConfig`
ao construtor. O snapshot registra todos os parâmetros. A inferência de sinais e
a correlação têm transações separadas; reprocessar uma amostra também recupera
correlações após uma interrupção entre essas gravações.

## Alinhar áudio e vídeo

Relatórios atuais de mídia são ancorados no início do **processamento**. Por isso,
importá-los diretamente como captura real faria correlações sem fundamento.
No painel, carregue o relatório JSON e informe o início da captura com fuso horário:

- **Associação sintética de demonstração** identifica uma montagem experimental.
- **Horário de captura informado pelo responsável** registra a informação fornecida;
  não certifica relógios, sincronização ou origem da gravação.

`align_media_report` calcula os intervalos na sessão a partir dessa origem
explícita. Rejeita outro paciente, evento incompatível com a identidade do relatório,
relógio desconhecido, ausência de fuso e intervalo fora da sessão. O lote de eventos
e alertas é importado atomicamente; conflitos desfazem todo o lote. A origem inclui
hash do relatório, sessão/evento original, evento completo anterior ao alinhamento,
horário informado e tipo de associação. O relatório de origem não é alterado.

Menções textuais usam o início do relato, **sem alinhamento por palavra**; correlação
mais precisa exige essa evolução. Transcrição incorreta pode omitir sintomas:
a pendência de fala natural continua em `docs/validacao-local.md`.

Disponibilidade pode ser registrada como disponível, indisponível ou degradada,
com motivo e horário. Sem registro, o estado é desconhecido. Isso não equivale
a normalidade e não impede alertas de fontes que continuam disponíveis. Eventos
já observados permanecem no histórico mesmo se a modalidade ficar indisponível.

## Demonstração sem serviços externos

```bash
.venv/bin/python scripts/demo_clinical_fusion.py
```

Saídas: `outputs/clinical-demo.db` e `outputs/clinical-demo.json`. É possível
selecionar outros caminhos com `--database` e `--report`. O roteiro usa sinais e
prescrições das fixtures de desenvolvimento e cria eventos explicitamente
sintéticos de texto/vídeo; não executa Whisper, MediaPipe ou Azure.

Uma execução de desenvolvimento produziu sete eventos, sete alertas isolados e
15 pares combinados. Reexecutar preservou os mesmos eventos e alertas. Isso
verifica integração programada, **não valida qualidade clínica ou latência real**.

## Verificação de implementação

Foram adicionados testes de histórico, transições, unidade, duplicação, chegada
atrasada, persistência, revisão, janela inclusiva, isolamento de paciente/sessão,
fontes dependentes, ausência de modalidade, alinhamento de mídia, rollback de lote
e painel em diretório temporário. A suíte passou com **103 testes**, além de Ruff,
formatação e Mypy. Não foi usado o conjunto reservado para calibrar as regras.

Permanecem para avaliação: gravações representativas, referências independentes,
comparação de alternativas, falsos alertas e latência em cadência real. Azure foi retirado do escopo ativo por decisão do autor; não integra as
pendências desta implementação.
