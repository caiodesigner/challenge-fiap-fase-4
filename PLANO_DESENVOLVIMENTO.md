# Plano de execução — Tech Challenge Fase 4

## 1. Objetivo e limites

Construir um protótipo acadêmico que processe vídeo, áudio e registros clínicos,
correlacione resultados por paciente e tempo e emita alertas explicáveis à equipe.
A base será reaproveitada seletivamente de `../challenge-fiap-fase-3`, sem alterar
esse diretório. Não há exigência de começar do zero no enunciado analisado.

Fonte de requisitos: “IADT - Fase 4 - Tech challenge.pdf”, páginas 2–4.
Este plano distingue requisitos do documento de decisões propostas de execução.
O documento não informa prazo, volume mínimo de dados ou desempenho mínimo.

Escopo proposto: acompanhamento de adultos sintéticos em internação e
reabilitação, com vídeo de exercício, observação de movimentação no leito,
relato de voz, sinais vitais e histórico de prescrições. Os dois contextos de
vídeo cobrem tanto análise de sessão clínica quanto movimentação na internação.
Dados de fontes independentes não serão apresentados como registros reais de
um mesmo paciente; associações para demonstração serão identificadas como sintéticas.

## 2. Leitura do feedback da fase 3

| Feedback | Interpretação e ação na fase 4 | Evidência planejada |
| --- | --- | --- |
| Mascaramento e remoção de repetições foram pontos fortes | Preservar curadoria; ampliar para identificadores em transcrições e tratamento de mídias antes do envio à nuvem | Manifesto de origem, consentimento/licença, hashes e relatório de duplicações |
| Treinamento real e resultados registrados | Preservar a disciplina de registrar configurações, versões, entradas e saídas de execuções reais | Relatórios por execução e amostras verificáveis de vídeo, áudio e Azure |
| Busca cuidadosa e validação humana | Reutilizar controles pertinentes; separar alerta automático de decisão sobre conduta | Alerta emitido sem aguardar aprovação; reconhecimento e revisão posteriores |
| Testes e organização foram positivos | Manter modularidade e testes de contratos, integração e falhas | CI e cenário E2E reproduzível |
| Falta comparação direta antes/depois do treinamento | Comparar alternativas nas mesmas entradas e condições; não inferir ganho a partir de loss ou sucesso de validação de schema | Baseline e solução final pareados, com erros, acertos, latência e exemplos de regressão |
| Poucos exemplos limitam casos menos comuns | Ampliar diversidade, reservar teste independente e registrar cobertura por cenário | Distribuição por classe, paciente/locutor/vídeo e análise de casos raros |

O feedback não exige novo fine-tuning para a fase 4. Caso a LLM anterior seja
mantida e haja alegação de ganho do adaptador, comparar modelo-base e adaptador
com as mesmas perguntas, contexto, parâmetros e conjunto de teste não usado no
treino. Esse experimento é opcional e não bloqueia os requisitos multimodais.
Métricas da fase 3 não serão reutilizadas como resultados da fase 4.

## 3. Análise e reaproveitamento da fase anterior

Análise estática inicial realizada: README, `pyproject.toml`, schema SQL,
repositório clínico, serviço da interface, estado do grafo, auditoria, Makefile e CI.
Não foi executada a aplicação anterior nesta etapa; a compatibilidade precisa
ser verificada durante a extração.

| Componente da fase 3 | Decisão proposta | Adaptação necessária |
| --- | --- | --- |
| Organização Python, Pydantic e configurações | Reaproveitar convenções e partes úteis | Identidade da fase 4 e contratos de medições, eventos, sessões e alertas |
| Pacientes sintéticos, anonimização e validação | Reaproveitar seletivamente | Ampliar cenários; mascaramento textual não anonimiza automaticamente voz ou imagem |
| SQLite e `ClinicalRepository` | Adaptar | Consulta atual é somente leitura; criar gravação controlada para ingestão, mantendo consultas parametrizadas |
| Schema de medicamentos | Redesenhar histórico | Lista ativa atual não representa evolução temporal; registrar início/fim, alteração, unidade, dose e motivo quando disponível |
| Auditoria JSONL | Adaptar | Incluir detector, versão, modalidade, evidência e tempos de ocorrência/processamento |
| Streamlit | Reaproveitar estrutura | Substituir fluxo centrado em chat por painel multimodal e linha do tempo |
| LangGraph e revisão | Avaliar extração após contratos | Grafo atual é orientado a solicitações; evitar dependência obrigatória da LLM para alertar |
| Políticas de segurança | Reutilizar princípios e regras pertinentes | Analisar mudanças de prescrições sem gerar prescrição nem bloquear a leitura do histórico |
| Testes, CI e Makefile | Adaptar estrutura | Testes próprios da fase 4; revisar dependências e ações antes de fixar versões |
| Qwen, LoRA, E5 e RAG | Opcionais | Somente se agregarem contexto/explicações mensuráveis; fora do caminho crítico |
| Pesos, ambientes, caches e relatórios históricos | Não copiar por padrão | Registrar referência ao projeto original e produzir evidências novas |

Na extração, registrar commit de origem, arquivos reaproveitados, alterações e
atribuições em `docs/reaproveitamento-fase-3.md`. O pacote anterior declara licença
`Proprietary`; documentar a origem autoral e preservar avisos de terceiros.
Não copiar `.git`, `.venv`, credenciais, bancos gerados ou diretórios de cache.

## 4. Matriz de atendimento ao novo challenge

| Requisito | Implementação planejada | Evidência de aceite |
| --- | --- | --- |
| Vídeos clínicos e movimentos/eventos fora do padrão | Extração de postura e características temporais; comparar com padrão do exercício | Vídeo com marcações, instante do desvio e comparação normal/anormal |
| Relatório automático de vídeo | Relatório estruturado por sessão | Arquivo gerado com eventos, intervalos e evidências |
| Alterações vocais | Características acústicas e detector com escopo definido pelos dados disponíveis | Áudios avaliados com rótulos de referência e análise de erros |
| Azure Speech to Text | Adaptador de transcrição real | Execução real com transcrição, duração e versão/configuração |
| Azure Text Analytics | Sentimentos e extração de termos; complementar vocabulário crítico com regras documentadas | Saída real do serviço e termos contextualizados, incluindo negação |
| Anomalias em sinais vitais | Séries de frequência cardíaca, pressão e oxigenação com regras e detector temporal | Gráficos com verdade de referência, eventos e métricas |
| Evolução de prescrições | Histórico ordenado, comparação de mudanças e regras de alterações inesperadas | Caso esperado, caso anômalo e justificativa; sem propor tratamento |
| Movimentação na internação | Eventos temporais em vídeo de contexto de internação | Sequência normal/anormal e alerta com trecho correspondente |
| Fusão multimodal | Correlação por paciente, sessão e janela temporal | Linha do tempo e alerta combinado rastreável às entradas |
| Alertas automáticos em tempo real | Processamento incremental, persistência, exibição e reconhecimento | Medição evento→alerta, tratamento de repetição e demonstração contínua |
| Código e relatório técnico | Instruções reproduzíveis, arquitetura, modelos e resultados | Execução a partir do README e relatório com limitações |
| Vídeo de até 15 minutos | Roteiro incluindo Azure, áudio, vídeo e alerta | Link YouTube/Vimeo e conferência da duração |

OpenPose e YOLOv8 são exemplos de modelos no enunciado, não uma exigência de usar
ambos. Azure Speech e Text Analytics são pedidos explicitamente. Os datasets
PhysioNet e AudioSet são sugestões; disponibilidade e adequação serão avaliadas.

## 5. Arquitetura e tecnologias propostas

Fluxo: ingestão → validação → processadores de vídeo/áudio/dados clínicos →
eventos padronizados → correlação temporal → alertas persistidos → painel e revisão.
Auditoria acompanha todas as etapas. Falha de uma modalidade deve ficar visível,
sem impedir alertas independentes das modalidades disponíveis.

- Python como base; avaliar manutenção de Python 3.12 após verificar compatibilidade.
- Pydantic para contratos; SQLite para o protótipo e repositórios separados de leitura/escrita.
- OpenCV e um estimador de postura, a selecionar por teste de viabilidade.
- Azure Speech e Azure Language, com credenciais em variáveis de ambiente.
- Librosa/SciPy para características acústicas, conforme o experimento escolhido.
- Pandas/NumPy e scikit-learn para preparação, baselines e detectores.
- Streamlit para upload, reprodução, gráficos, relatórios e fila de alertas.
- Pytest, Ruff e verificação de tipos para qualidade; versões serão fixadas após teste de compatibilidade.

Fusão inicial por regras explícitas, com janela temporal e evidências por
modalidade. Não é necessário treinar um modelo multimodal único. A LLM é opcional.
Não é necessário hospedar toda a aplicação na nuvem para demonstrar integração Azure.

## 6. Etapas e critérios de conclusão

### Etapa 0 — Fechar escopo e critérios

- Transformar a matriz acima em checklist de requisitos.
- Definir cenários normais, anormais, raros e entradas inválidas por modalidade.
- Confirmar prazo na plataforma acadêmica, recursos locais e acesso Azure.
- Definir métricas e metas experimentais antes de observar o conjunto de teste.

Conclusão: especificação em `docs/escopo-e-aceite.md`, sem requisitos sem cenário.

Definição documental realizada em [Escopo e aceite](docs/escopo-e-aceite.md).
Prazo, recursos, acesso Azure e fontes de dados permanecem pendentes conforme
o registro do documento; a extração seletiva pode prosseguir.

### Etapa 1 — Extrair a base útil da fase 3

- Registrar a revisão de origem e inspecionar acoplamentos e testes relacionados.
- Trazer somente código necessário; adaptar identidade, configurações e imports.
- Preservar contexto clínico, validação, auditoria e a estrutura de qualidade.
- Criar instalação mínima; separar dependências opcionais de modelos pesados.
- Verificar que a fase 3 permanece sem alterações provocadas por este trabalho.

Conclusão: base da fase 4 instala e passa verificações próprias; inventário de
reaproveitamento documentado. Código copiado sem uso não integra o aceite.

### Etapa 2 — Dados, contratos e referência de avaliação

- Criar manifesto com origem, licença/consentimento, formato, duração e rótulos.
- Definir entidades: paciente, sessão, mídia, medição, versão de prescrição,
  evento e alerta; manter horário do evento e horário de processamento separados.
- Separar desenvolvimento, validação e teste por paciente/locutor/vídeo de origem,
  impedindo que trechos da mesma fonte vazem entre conjuntos.
- Incluir exemplos normais, anormais, raros, ruído e ausência de modalidade.
- Planejar inicialmente ao menos cinco cenários funcionais por frente; isso é
  cobertura de demonstração, não tamanho suficiente para validar um detector.
- Dimensionar amostras de avaliação conforme acesso e diversidade; se não houver
  dados suficientes para aprender, usar regras justificadas e declarar o limite.

Conclusão: dados acessíveis e validados, separação registrada e conjunto de
referência com origem dos rótulos, inclusive quando forem sintéticos.

### Etapa 3 — Primeira integração vertical

- Implementar ingestão incremental de sinais vitais e baseline de regras.
- Persistir evento e alerta, exibir no painel e registrar reconhecimento humano.
- Reproduzir uma série gravada em cadência controlada, medindo evento→alerta.
- Separar reexecução acelerada de operação em cadência real e documentar ambas.

Conclusão: um cenário completo funciona da entrada ao alerta, com evidência de
latência. Reprodução é identificada como simulação e não prova integração com sensores.

### Etapa 4 — Vídeo

- Fazer experimento curto de viabilidade e selecionar modelo de postura/detecção.
- Extrair características temporais, como amplitude, assimetria e duração.
- Cobrir exercício clínico e movimentação em contexto de internação.
- Tratar pessoa fora de quadro, oclusão e baixa confiança como limitações observáveis.
- Gerar vídeo anotado e relatório automático com os intervalos relevantes.

Conclusão: exemplos normais/anormais avaliados e eventos integrados ao contrato comum.

### Etapa 5 — Áudio e Azure

- Validar formato e qualidade; executar transcrição real pelo Azure Speech.
- Executar sentimentos e extração textual pelo Azure Language.
- Associar termos críticos a contexto, negação e referência temporal.
- Extrair características acústicas e avaliar alterações vocais separadamente.
- Distinguir sentimento textual, relato de sintoma e alteração acústica.
- Registrar falhas, limites de acesso e latência; não apresentar saída simulada
  como evidência de integração real.

Conclusão: uma execução real de ponta a ponta, com evidências sanitizadas e
avaliação de transcrição/texto/voz separadas.

### Etapa 6 — Anomalias clínicas e fusão

- Ampliar sinais para frequência cardíaca, pressão e oxigenação.
- Implementar histórico de prescrições e distinguir mudanças previstas de inesperadas.
- Comparar baseline de regras com detector estatístico/aprendido quando os dados permitirem.
- Correlacionar eventos de todas as modalidades por paciente e janela temporal.
- Implementar severidade, evidências, deduplicação e estados de alerta.
- Emitir o alerta automaticamente; revisão humana não deve atrasar sua emissão.

Conclusão: todas as linhas da matriz técnica demonstradas, incluindo operação
com modalidade indisponível e sem atribuir eventos a outro paciente.

### Etapa 7 — Avaliação e robustez

- Executar baseline e solução final no mesmo teste reservado.
- Medir precisão, recall e F1 por evento e falsos alertas por unidade de tempo;
  definir tolerância temporal e regra de pareamento antes da execução.
- Para áudio, medir erro de transcrição e resultados de termos críticos e voz;
  para o fluxo, medir latência e disponibilidade das modalidades.
- Reportar quantidade de exemplos, distribuição, erros por cenário e incerteza;
  não usar acurácia global isoladamente em dados desbalanceados.
- Comparar detecção isolada e fusão para verificar se a combinação ajuda ou piora.
- Testar isolamento de pacientes, ordenação temporal, duplicações, dados ausentes,
  falhas Azure e persistência/reconhecimento de alertas.
- Manter CI offline com doubles de serviços e executar integração real separadamente.

Conclusão: relatório comparativo com ganhos e regressões, configurações e
artefatos reproduzíveis. Cobertura de código não equivale a qualidade do detector.

### Etapa 8 — Documentação e entrega

- README com instalação, credenciais, execução e limitações verificadas.
- Relatório com arquitetura, fluxo multimodal, modelos, dados, resultados,
  exemplos de anomalias, custos observados e limitações.
- Matriz final com requisito → código → comando → evidência.
- Roteiro e vídeo de até 15 minutos cobrindo execução real Azure, vídeo, áudio,
  anomalias, fusão e alerta à equipe.
- Conferir link público/não listado, reprodutibilidade e submissão na plataforma.

Conclusão: entrega técnica revisada e links conferidos; publicação/submissão
serão realizadas na etapa correspondente.

## 7. Sequência, prioridades e riscos

Dependência principal: 0 → 1 → 2 → 3 → 4/5 → 6 → 7 → 8.
Os ensaios de acesso Azure e viabilidade de vídeo começam na etapa 0 para
revelar bloqueios cedo. Avaliação e documentação evoluem desde a etapa 2.
O cronograma por datas depende do prazo de entrega ainda não informado.

Prioridade obrigatória: modalidades, serviços Azure, três frentes de anomalia,
relatórios de vídeo, fusão, alertas e entregáveis. Depois disso: melhorias de
modelos. Chat, RAG, novo fine-tuning, infraestrutura distribuída e aplicativo
móvel não entram no caminho crítico.

| Risco | Resposta planejada |
| --- | --- |
| Poucos dados rotulados ou acesso demorado | Validar acesso cedo, complementar cenários sintéticos identificados e limitar alegações |
| Modelo de postura não reconhecer o contexto escolhido | Experimento curto antes de consolidar o dataset e a arquitetura |
| Recursos locais insuficientes | Medir execução em CPU e usar modelos leves/amostragem de quadros conforme latência |
| Azure indisponível ou sem credenciais | Adaptadores isolados e testes offline; evidência real permanece obrigatória para a entrega |
| Alertas demais ou correlação errada | Avaliar negativos, tolerância temporal, deduplicação e isolamento de pacientes |
| Reaproveitamento carregar complexidade desnecessária | Extrair por funcionalidade e comprovar uso; manter treino e LLM opcionais |

## 8. Estado atual

- [x] Leitura do enunciado da fase 4.
- [x] Análise estática inicial da base da fase 3.
- [x] Análise do feedback e plano de reaproveitamento.
- [x] Registro deste plano no repositório da fase 4.
- [x] Etapa 0: definição documental de escopo, cenários e critérios de aceite.
- [ ] Etapa 0: confirmação de prazo, recursos e acesso Azure.
- [x] Etapa 1: extração seletiva da base e validação local; origem em `docs/reaproveitamento-fase-3.md`.
- [x] Etapa 2: contratos, schemas, fixtures e partições funcionais; subconjunto BIDMC para ingestão.
- [ ] Etapa 2: incorporar fala/vídeo e congelar teste independente; ver `docs/dados-e-avaliacao.md`.
- [x] Etapa 3: primeiro fluxo incremental de sinais vitais, alertas persistidos, painel e demonstração 1×.
- [x] Etapa 3: histórico persistido de cada reprodução, inclusive duplicações; dados anteriores preservados.
- [x] Etapa 4: implementação de postura em CPU, regras temporais, vídeo anotado e relatórios; ver `docs/video-e-relatorios.md`.
- [ ] Etapa 4: calibrar e avaliar com gravações representativas e referências independentes.
- [x] Etapa 5: áudio local, análise acústica, termos críticos, adaptadores HTTPS Azure, painel e testes offline.
- [x] Etapa 5: faster-whisper small CPU/int8 instalado e integrado ao painel, com MediaPipe em CPU; ver `docs/execucao-local.md`.
- [ ] Etapa 5: configurar recursos F0 e executar integração real Speech/Language; ver `docs/audio-e-azure.md`.
- [ ] Etapa 5: avaliar fala com locutores, transcrições e referências independentes.
- [ ] Execução das etapas 6–8.

Na elaboração inicial do plano não houve cópia de componentes. Na Etapa 1,
os componentes úteis foram extraídos para a fase 4; a fase 3 permanece preservada.

### Avaliação adicional do reconhecimento local

- [x] Avaliador offline de WER e menções com negação, temporalidade e sujeito.
- [x] Comparação sintética small/medium e referência manual no painel; evidências em `docs/validacao-local.md`.
- [ ] Validar com fala natural, referências manuais revisadas e locutores separados; a falha automática no áudio sintético original permanece registrada.
