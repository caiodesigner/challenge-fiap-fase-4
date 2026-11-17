# Política de pausas na fusão multimodal

## Decisão de escopo

A pausa sem referência acústica é uma **observação**, não uma mudança comprovada
em relação ao padrão de fala do paciente. Sua importação preserva o evento,
o intervalo e a origem, mas não eleva prioridade nem reforça um alerta combinado.
Essa é a política padrão explicitada nesta revisão.

| Tipo | Origem | Alerta isolado | Participa da correlação? |
| --- | --- | --- | --- |
| `long_pause_observed` | Pausa ≥ 2 s, sem referência acústica | `observation` | Não |
| `pause_change` | Pausa ≥ 2 s e pelo menos 1 s acima da maior pausa interna da referência | `attention` | Sim, com outra família elegível e dentro da janela |
| `long_pause` | Tipo sintético legado, mantido por compatibilidade de configurações persistidas | `attention` | Sim; não é o tipo emitido pelo pipeline atual sem referência |

A fusão de um `pause_change` com uma assimetria, por exemplo, pode gerar
`priority` experimental quando paciente, sessão, janela temporal e famílias de
fontes atendem às regras. A elegibilidade não é diagnóstico nem garante utilidade
clínica. Áudio e texto pertencem à mesma família e não se reforçam entre si.

## Efeito no exemplo SPIRA

O `02_paciente_pausas.wav` foi processado sem referência. Por isso, sua pausa de
13,50–16,14 s é importada como `long_pause_observed`: aparece na linha do tempo
e produz observação, mas não compõe o alerta combinado com o vídeo. A integração
está funcionando segundo a política; não apresentar esse exemplo como prova de
correlação acústica com aumento de prioridade.

Para demonstrar uma mudança acústica com referência, usar uma gravação adequada
do mesmo paciente/cenário e processar novamente com a referência opcional no painel.
Não usar um controle do SPIRA como referência longitudinal de outro paciente nem
alterar manualmente o tipo de um relatório já gerado para obter prioridade.

## Implementação e verificação

A interface de Histórico e fusão explica a política junto aos alertas. A
configuração mantém os mesmos valores e fingerprint; não exige migração ou
apagamento dos bancos de demonstração existentes. O tipo legado permanece
explicitamente identificado como tal no código.

O teste parametrizado `test_actual_acoustic_event_policy_in_fusion` usa os tipos
emitidos por `acoustic_events` e exercita os dois modos, nas duas ordens de chegada.
Confere armazenamento, severidade, presença/ausência de alerta combinado,
persistência após reabertura e deduplicação. Resultado: quatro casos novos,
suíte completa com 167 testes aprovados. Evidência resumida em
[pause-fusion-policy.json](../reports/validation/pause-fusion-policy.json).

A montagem de vídeo já explica que nem toda importação gera prioridade e é
compatível com esta política. A contagem de 163 testes narrada corresponde à
verificação documentada antes dos quatro novos casos desta revisão.
