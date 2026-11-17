# Auditoria de aderência — Tech Challenge Fase 4

Autor: Caio Lucas Santos Silva · RM373689 · Turma 9IADT.

Base: PDF original em `docs/IADT - Fase 4 - Tech challenge.pdf`, especialmente
requisitos obrigatórios (p. 3) e entregáveis (p. 4). Azure tratado como opcional,
conforme orientação do professor relatada pelo autor. A auditoria é técnica e
funcional; não constitui aprovação do professor nem validação clínica.

## Parecer

O projeto tem implementação funcional para as frentes exigidas e demonstrações
reais nos motores de áudio e vídeo. Os principais materiais estão produzidos.
Não é correto afirmar conformidade clínica ou atendimento sem ressalvas: a análise
vocal é exploratória, a movimentação hospitalar é simulada por exercícios e a
operação contínua com sensores não foi implementada. Há uma inconsistência entre
o tipo de pausa emitido pelo áudio e a configuração padrão de correlação, detalhada
abaixo. A submissão ainda depende de publicação do vídeo e do código final.

## Requisitos e evidências

| Exigência | Verificação | Avaliação |
| --- | --- | --- |
| Processar vídeo clínico | REHAB24-6 Arm VW com MediaPipe real; entrada e relatório disponíveis | Atendido na demonstração de fisioterapia |
| Detectar movimento fora do padrão e emitir relatório | Assimetria entre 1,20 e 2,80 s; relatório JSON/Markdown e vídeo anotado | Atendido para as regras implementadas, sem cobertura de todos os erros |
| OpenPose/YOLOv8 | PDF usa “modelos como”; aplicação usa MediaPipe | Exemplos do PDF, sem obrigação explícita de usar ambos |
| Processar áudio de consulta | Pipeline WAV/Whisper com relatos encenados e fala SPIRA | Funcional; SPIRA é leitura e não consulta espontânea; representatividade limitada |
| Alterações vocais indicativas | Pausas e energia; pausa SPIRA de 2,64 s | Cobertura exploratória; não detecta clinicamente fadiga/disartria |
| Transcrição, termos críticos e sentimentos | Whisper local e regras em português, com negação e evidências | Implementados; substituição de Azure documentada |
| Séries temporais de sinais vitais | Frequência, pressão sistólica/diastólica e SpO₂; persistência e tendência | Atendido em séries sintéticas |
| Alterações inesperadas de prescrição | Histórico, razão de dose, suspensão, sequência e unidade | Atendido com contratos/unidades sintéticos |
| Movimentação em internação | Contexto Internação; Sit-To-Stand after com evento 28,8–29,8 s | Funcionalidade demonstrada por simulação; não é observação de paciente internado |
| Alertas automáticos à equipe | Painel emite e persiste; reconhecimento/encerramento auditáveis | Atendido no protótipo; não há autenticação hospitalar ou notificação externa |
| Fusão de texto, áudio e vídeo | Eventos alinhados explicitamente e agrupados por episódio | Implementada; pausa observada sem referência não é elegível para correlação |
| Tempo real | Ingestão incremental de sinais e reprodução 1×; mídia por upload | Demonstração temporal local, sem streaming hospitalar ou garantia de latência ponta a ponta |
| Código e relatório técnico no Git | Código, Markdown/PDF, fluxo, modelos, resultados e fontes | Materiais locais disponíveis; últimas alterações ainda não publicadas |
| Vídeo até 15 minutos | MP4 de 555,021 s, Full HD, locução, demonstrações, revisão do autor | Produzido e revisado pelo autor; URL YouTube/Vimeo ainda pendente |

## Verificações executadas

- `make check`: Ruff, formatação, Mypy, **163 testes aprovados** e validação dos catálogos sintético/BIDMC.
- `.venv/bin/python -m pip check`: nenhuma dependência quebrada.
- `make ready`: execução local pronta; submissão ainda não pronta.
- Reavaliação de desenvolvimento, validação e teste em diretório separado: em cada partição, regras temporais com 9 TP/0 FP/0 FN; baseline imediata com 9 TP/2 FP/0 FN; prescrições com 3 TP/0 FP/0 FN.
- Relatórios reais de áudio e vídeo reimportados em banco temporário para verificar classificação e correlação.
- Inspeção das evidências técnicas do vídeo: H.264/AAC, 1920×1080, 30 FPS, 12 capítulos, decodificação completa e duração abaixo de 900 s. O autor informou ter assistido e considerado o conteúdo correto.

As três partições compartilham templates sintéticos; esses números não comprovam
generalização. As mídias foram selecionadas após observar saídas e não formam teste
independente. Resultados da auditoria em
[final-audit.json](../reports/validation/final-audit.json); arquivos completos da
reavaliação ficam em `outputs/final-audit/`.

## Achado específico — classificação da pausa na fusão

`acoustics.py` emite `long_pause_observed` quando não há referência acústica.
`ClinicalConfig.fusion_event_types` inclui `long_pause` e `pause_change`, mas não
`long_pause_observed`. O primeiro nome não é o tipo emitido pelo fluxo atual sem
referência. A importação não falha, porém o evento é classificado como observação
e excluído da correlação automática.

A reprodução com dois relatórios reais, alinhados sinteticamente à mesma sessão,
produziu uma assimetria às 11,2 s e uma pausa às 13,5 s. Resultado: alerta de
atenção para a assimetria, observação para a pausa e nenhum alerta combinado
entre esses dois eventos. Menções críticas textuais e mudanças acústicas com
referência são tipos elegíveis; a fusão não está inteiramente ausente.

É necessário explicitar a política desejada antes de afirmar correlação acústica
completa: manter a pausa sem referência como observação, documentando a restrição,
ou tornar esse tipo elegível e testar a configuração experimental correspondente.
Incluir na fusão altera severidade, fingerprint e compatibilidade dos bancos; não
foi feita essa mudança silenciosamente durante a auditoria. O vídeo diz que nem
toda importação gera prioridade e permanece compatível com a restrição descrita.

## O que falta e o que não é obrigação adicional do PDF

Para submissão: publicar o vídeo em YouTube/Vimeo, conferir acesso sem login,
publicar o estado final do repositório, registrar link/commit e efetuar a entrega
conforme campos e prazo do portal. Dados de autoria já estão preenchidos.

O PDF técnico anterior à montagem registrava link e duração do vídeo como
pendentes. A revisão de política de pausas também atualizou a duração conhecida
para 9min15s; o link deve ser incluído após publicação, com nova exportação do PDF.

Os indicadores `representative_media_complete` e `independent_test_complete`
permanecem falsos. O verificador local os considera bloqueios de sua prontidão
interna, mas o PDF não exige explicitamente ensaio clínico independente ou um
limiar de precisão. Não interpretar esses campos como entregáveis adicionais.
As limitações devem permanecer no relatório e na apresentação.

Também não há obrigação explícita de slides, deploy público da aplicação,
notificação por email/SMS, treinamento próprio, ambos os modelos citados,
filmagem de paciente real ou voz do autor na apresentação. O PDF exige relatório
técnico, sem fixar PDF como formato; o projeto fornece Markdown e PDF. Isso não
dispensa regras adicionais eventualmente informadas pelo professor ou pelo portal.

Não foram alteradas regras de detecção, severidade ou bancos da demonstração nesta
auditoria. Atualizaram-se apenas registros de revisão e documentação de evidências.

## Resolução do achado de pausas

A opção adotada foi explicitar a política de observação, sem promover pausas sem
referência a evidência de mudança clínica. A interface e o relatório agora
explicam `long_pause_observed` e `pause_change`; `long_pause` está identificado
como legado compatível. Foram adicionados quatro testes de integração dos tipos
reais emitidos pela acústica, incluindo ambas as ordens de chegada e persistência.
A suíte passou a 167 testes. O achado de política ambígua está resolvido por
explicitação; não se ampliou a elegibilidade nem se alterou a severidade existente.
Veja [politica-pausas-fusao.md](politica-pausas-fusao.md).
