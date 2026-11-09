# Escopo, cenários e critérios de aceite

Status: definição inicial, anterior à implementação e à avaliação.
Esta é a primeira fase de execução solicitada; corresponde à **Etapa 0** do
plano. A Etapa 1 do plano continua sendo a extração seletiva da fase 3.

## 1. Base da definição

Requisitos: PDF “IADT - Fase 4 - Tech challenge”, páginas 2–4.
Os cenários, números e protocolos abaixo são decisões do projeto, não exigências
numéricas da FIAP. Nenhum resultado ou desempenho é declarado nesta etapa.

Objetivo: demonstrar acompanhamento de um adulto sintético em internação e
reabilitação, processando vídeo, voz, texto e registros clínicos para emitir
alertas automáticos, rastreáveis e sujeitos à revisão da equipe.

## 2. Escopo da primeira entrega

| Frente | Recorte definido | Saída |
| --- | --- | --- |
| Vídeo clínico | Exercício bilateral de elevação dos braços, com câmera fixa e uma pessoa; detectar assimetria e interrupção do movimento | Vídeo anotado, eventos temporais e relatório por sessão |
| Movimentação na internação | Observação de uma pessoa em leito/cadeira; identificar mudança de padrão de atividade e tentativa encenada de levantar | Eventos com trechos de evidência; sem afirmar previsão de queda |
| Voz | Relato curto em português; avaliar pausas e continuidade da fala frente à referência do cenário | Características acústicas e indicação de alteração; sem diagnóstico de fadiga/disartria |
| Texto | Transcrição Azure, sentimentos e termos críticos contextualizados | Transcrição, resultado real do serviço e evidências de menção/negação |
| Sinais vitais | Frequência cardíaca, pressão sistólica/diastólica e oxigenação em séries temporais | Desvios persistentes, tendência e gráficos |
| Prescrições | Histórico sintético com inclusão, suspensão e mudanças de dose/unidade | Mudanças inesperadas segundo regras do cenário, sem recomendar doses |
| Fusão | Paciente, sessão e horários compatíveis | Linha do tempo e alerta combinado com rastreabilidade |
| Operação | Upload de arquivos e reprodução incremental em cadência real | Painel local, alertas persistidos e revisão humana |

Uma pessoa por vídeo é o limite inicial; mídias com múltiplas pessoas devem ser
sinalizadas como fora do escopo. O teste de viabilidade pode exigir ajuste do
exercício ou enquadramento, documentado antes da avaliação reservada.

Fora do escopo obrigatório: análise cirúrgica, diagnóstico, prescrição automática,
integração com sensores/prontuários hospitalares reais, aplicação móvel, chat,
novo fine-tuning e hospedagem integral em nuvem. A análise cirúrgica é uma
alternativa de contexto no enunciado; será atendido o contexto de fisioterapia.

## 3. Fluxo demonstrável

1. Selecionar paciente sintético e sessão; validar arquivos e registros.
2. Processar vídeo e áudio e carregar histórico clínico temporal.
3. Chamar Azure Speech para transcrição e Azure Language para análise textual.
4. Emitir eventos padronizados com origem, horário e versão do detector.
5. Persistir alertas independentes e correlacionar evidências compatíveis.
6. Exibir motivo, severidade experimental e evidência no painel.
7. Registrar reconhecimento e revisão humana sem bloquear a emissão inicial.
8. Exportar relatório da sessão e trilha de execução.

## 4. Catálogo mínimo de cenários

Cada linha é um caso funcional, não uma amostra suficiente de avaliação. Os
arquivos e rótulos serão produzidos/selecionados na etapa de dados.

| ID | Entrada/situação | Resultado esperado |
| --- | --- | --- |
| VID-01 | Exercício simétrico completo | Processar sem desvio de movimento |
| VID-02 | Assimetria encenada persistente | Evento com intervalo e lados envolvidos |
| VID-03 | Interrupção inesperada de uma repetição | Evento temporal, distinguindo fim normal da sessão |
| VID-04 | Oclusão, saída de quadro ou segunda pessoa | Qualidade insuficiente/fora do escopo; sem inventar postura |
| VID-05 | Arquivo inválido ou sem quadros legíveis | Erro rastreável e demais frentes disponíveis |
| MOV-01 | Mudança habitual de posição no leito | Sem alerta de alteração inesperada |
| MOV-02 | Atividade persistentemente diferente da referência | Evento de mudança de padrão |
| MOV-03 | Tentativa encenada de levantar sem evento previsto | Alerta com trecho de evidência |
| MOV-04 | Imobilidade com pessoa ocluída | Indicar impossibilidade de avaliar, sem inferir imobilidade |
| MOV-05 | Pausa da gravação ou salto de horário | Sinalizar lacuna, sem somá-la como tempo de inatividade |
| AUD-01 | Fala contínua sem termos críticos | Transcrição/análise; sem alteração acústica esperada |
| AUD-02 | Pausas prolongadas encenadas frente à referência | Alteração acústica observável, sem diagnóstico |
| AUD-03 | “Estou com falta de ar” | Menção crítica afirmada, com trecho da transcrição |
| AUD-04 | “Não estou com falta de ar” | Negação identificada; não gerar o mesmo alerta afirmativo |
| AUD-05 | Silêncio, ruído excessivo ou arquivo inválido | Qualidade insuficiente/erro; não fabricar transcrição |
| AUD-06 | Relato histórico e sentimento negativo sem sintoma atual | Distinguir temporalidade e sentimento de urgência |
| VIT-01 | Série estável nos limites sintéticos configurados | Sem alerta |
| VIT-02 | Desvio persistente em cada sinal monitorado | Evento após duração mínima, com valor/unidade/regra |
| VIT-03 | Tendência gradual anormal sem pico isolado | Evento temporal conforme detector configurado |
| VIT-04 | Pico isolado/artefato | Não confundir com persistência; registrar qualidade quando aplicável |
| VIT-05 | Unidade inválida, ausência ou desordem temporal | Rejeitar ou ordenar por política explícita; não completar silenciosamente |
| PRE-01 | Tratamento estável | Sem alerta |
| PRE-02 | Mudança prevista com justificativa sintética registrada | Registrar mudança sem classificá-la como inesperada |
| PRE-03 | Mudança abrupta não prevista no cenário | Alerta com versões anterior/posterior e regra |
| PRE-04 | Unidade incompatível ou informação insuficiente | Sinalizar inconsistência, sem calcular comparação inválida |
| PRE-05 | Registro duplicado, suspensão e reinício | Preservar sequência e não duplicar alerta pela mesma entrada |
| INT-01 | Dois sinais compatíveis do mesmo paciente/sessão | Alerta combinado citando ambas as evidências |
| INT-02 | Eventos de pacientes distintos ou fora da janela | Não correlacionar |
| INT-03 | Azure indisponível/timeout | Falha explícita; sinais e vídeo continuam emitindo seus alertas |
| INT-04 | Mesmo evento reprocessado e aplicação reiniciada | Sem duplicação; estado dos alertas persistido |
| INT-05 | Eventos atrasados ou modalidade ausente | Aplicar política temporal e indicar cobertura parcial |
| INT-06 | Equipe reconhece e revisa alerta | Persistir ator de demonstração, horário, decisão e comentário |

## 5. Requisitos e aceite funcional

| ID | Requisito | Cenários | Critério verificável e evidência |
| --- | --- | --- | --- |
| R01 | Análise de vídeo clínico | VID-01–05 | Executar casos e exportar vídeo anotado e relatório com intervalos, detector e desvios |
| R02 | Alterações vocais | AUD-01–02,05 | Extrair medidas do áudio e comparar com referência; avaliar separado do texto |
| R03 | Azure Speech | AUD-01,03–06 | Preservar evidência sanitizada de transcrição real e configuração, sem credenciais |
| R04 | Azure Text Analytics | AUD-03,04,06 | Registrar sentimentos e extração textual reais; termos críticos/negação podem receber regras complementares |
| R05 | Anomalias de sinais vitais | VIT-01–05 | Cobrir frequência, pressão sistólica/diastólica e oxigenação com eventos e gráficos |
| R06 | Evolução de prescrições | PRE-01–05 | Comparar histórico temporal e explicar diferenças sem sugerir tratamento |
| R07 | Movimentação durante internação | MOV-01–05 | Identificar eventos temporais no contexto de leito/cadeira com evidência visual |
| R08 | Fusão multimodal | INT-01,02,05 | Correlacionar vídeo, áudio/texto e registros na mesma linha do tempo, sem mistura de pacientes |
| R09 | Alertas automáticos | INT-01–06 | Persistir e exibir sem aprovação prévia; permitir reconhecimento e revisão posteriores |
| R10 | Monitoramento em tempo real | VIT-02, INT-01,03 | Executar reprodução em cadência real e registrar latência; distinguir de lote/reprodução acelerada |
| R11 | Código e relatório | Todos | README reproduzível, matriz de evidências, descrição dos modelos e resultados novos |
| R12 | Vídeo de entrega | R01–10 | Até 15 minutos, Azure real, áudio/vídeo, anomalia e resposta da equipe; link YouTube/Vimeo acessível |

Serviços simulados permitem testes offline, mas não satisfazem R03/R04 na entrega.
O fluxo multimodal não depende de todas as modalidades concordarem para alertar.

## 6. Regras de operação iniciais

- Eventos: identificador estável, paciente, sessão, modalidade, tipo, intervalo,
  medida/unidade quando aplicável, evidência, regra/modelo e versão.
- Horários persistidos em UTC; guardar horário de ocorrência, ingestão e emissão.
  Interface apresenta o fuso informado ao usuário.
- Fusão inicial: eventos do mesmo paciente e sessão em janela de 30 segundos;
  prescrições compõem contexto vigente, não um evento artificialmente simultâneo.
- Atraso de até 5 segundos: reordenar no buffer; acima disso, identificar evento
  tardio e registrar atualização, sem apagar o alerta já emitido. Esses valores
  serão calibrados na validação e congelados antes do teste reservado.
- Deduplicação: chave de origem e tipo do evento; reprocessamento idêntico não
  cria novo alerta. Novas evidências podem atualizar um alerta com histórico.
- Estados: aberto → reconhecido → encerrado. Revisão registra confirmado,
  falso positivo ou inconclusivo. Não presumir autenticação de produção.
- Severidade é experimental e baseada em regras versionadas, sem classificação
  clínica validada. Limites de sinais/prescrições serão definidos em fixtures
  sintéticas e configuração, sem apresentá-los como recomendações médicas.
- Falta de dado e baixa confiança são estados explícitos; não equivalem a normalidade.

## 7. Avaliação e metas iniciais

Para responder ao feedback anterior, comparar baseline e solução final nas
mesmas entradas, sem escolher apenas exemplos favoráveis. Baseline: regras
simples por modalidade sem fusão; solução: análise temporal e fusão. Reportar
também modalidades isoladas versus fusão e os casos em que esta piorar resultados.
Se não houver melhoria, registrar o resultado sem alegar ganho.

| Item | Protocolo/meta interna inicial |
| --- | --- |
| Cenários funcionais | Todos os cenários aplicáveis executados com resultado verificável; falha conhecida impede marcar o requisito correspondente como concluído |
| Detecção | Precisão, recall e F1 por tipo de evento; meta experimental de precisão e recall ≥ 0,80 por família avaliada, sem ocultar famílias abaixo da meta |
| Falsos alertas | Reportar por hora de dados negativos, indicando horas observadas; sem extrapolar estabilidade a partir de clipes curtos |
| Pareamento | Mesmo paciente, sessão e classe; início detectado dentro de ±5 s do início anotado; pareamento um a um, escolhendo menor diferença; detecções extras são falsos positivos |
| Prescrições/texto | Pareamento por registro/menção de referência, não por tolerância de vídeo; incluir negação e temporalidade |
| Transcrição | WER contra transcrição manual e recall de termos críticos; meta inicial de recall ≥ 0,90 nas menções críticas afirmadas |
| Sentimentos | Comparar saída a rótulos de referência documentados e reportar divergências; sentimento não define risco sozinho |
| Latência local | Meta p95 ≤ 5 s entre disponibilidade de todas as amostras da janela necessária e alerta persistido, em reprodução 1× |
| Latência Azure | Medir upload→resultado e fim de captura→alerta separadamente, incluindo falhas; meta inicial p95 ≤ 30 s em clipes de até 30 s |
| Integridade | Zero mistura entre pacientes, zero duplicação em reprocessamento idêntico e preservação após reinício nos casos funcionais |

As metas de desempenho orientam a implementação e não são validação clínica.
Se não forem atingidas, registrar a lacuna e revisar o detector com dados de
desenvolvimento/validação; não mudar a meta após olhar o teste para aparentar sucesso.
Uma revisão de escopo ou meta deve ser versionada e justificada antes de nova avaliação.

Reservar desenvolvimento, validação e teste por pessoa/locutor/vídeo de origem,
mantendo variações da mesma fonte na mesma partição. Duplicações e derivados
devem ser rastreados. Cinco cenários por frente são cobertura funcional, não
tamanho estatístico. O tamanho real e a distribuição das amostras serão definidos
após inventário de acesso; conjunto pequeno implica conclusão exploratória.
Mídia encenada/sintética valida comportamento programado, não detecção de doença.

Registrar hardware, versões, número de exemplos, duração dos dados, parâmetros,
falhas e latência. Distinguir processamento em lote de incremental. Além da
latência computacional, reportar tempo desde o início anotado até o alerta,
incluindo a janela de confirmação. Não aplicar tolerância temporal ao cálculo
de latência. Resultados da fase 3 não contam como evidências desta avaliação.

## 8. Evidências previstas

- `docs/reaproveitamento-fase-3.md`: origem e adaptações do código.
- Manifesto de dados e partições, com origem, consentimento/licença e hashes.
- Configurações versionadas dos detectores e do protocolo de avaliação.
- Relatórios de execuções reais com vídeos anotados, transcrições sanitizadas,
  gráficos, comparativos e erros observados.
- Testes offline de contratos e integração; integração Azure real identificada.
- Relatório técnico final, matriz requisito→comando→artefato e vídeo demonstrativo.

Esses artefatos estão previstos, ainda não produzidos. Modelos e datasets serão
selecionados após ensaios de viabilidade; esta definição não fixa versões de bibliotecas.

## 9. Pendências e passagem para a extração

| Pendência | Quando resolver | Impacto |
| --- | --- | --- |
| Prazo oficial de entrega | Consultar plataforma/informação do autor | Necessário para calendário, não para iniciar extração |
| Assinatura, região e acesso aos dois serviços Azure | Antes da implementação de integração real | Bloqueia comprovação R03/R04, não testes offline |
| Hardware e orçamento de execução | No ensaio de viabilidade | Condiciona modelo, amostragem e metas medidas |
| Fontes de mídia, acesso, licença e rótulos | Na etapa de dados, antes de envio à nuvem | Condiciona abrangência e avaliação |
| Volume e distribuição do conjunto de teste | Após inventário e antes de calibrar detectores | Necessário para interpretar métricas |

Definição documental concluída: escopo, cenários e critérios registrados.
A etapa operacional de confirmação de recursos permanece aberta. A extração
seletiva pode começar sem alterar a fase 3 e sem depender dessas confirmações.
