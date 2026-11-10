# Primeiro fluxo completo de sinais vitais

Implementação correspondente à quarta etapa da sequência apresentada ao usuário
e à Etapa 3 do plano: entrada → regra temporal → evento → alerta → revisão.
O conjunto independente de áudio/vídeo continua pendente; não bloqueia esta integração.

## Comportamento implementado

- Quatro sinais: frequência cardíaca, pressão sistólica/diastólica e oxigenação.
- Entrada validada por `Measurement`, paciente/sessão registrados e horário dentro
  da sessão. Unidade incompatível e conflito de identidade são rejeitados.
- Regras experimentais em `configs/vitals.json`. Um desvio abaixo/acima do limite
  precisa persistir por três segundos, com lacuna máxima de dois segundos entre
  amostras válidas. Limites não são recomendações clínicas.
- Normalização ou mudança de direção do desvio reinicia a contagem. Artefato ou
  qualidade ausente também interrompe a persistência. Não se infere normalidade
  de informação ausente. A primeira amostra após lacuna reinicia a janela.
- Um evento/alerta por episódio persistente e sinal. Após recuperação, outro
  episódio pode gerar novo alerta. O intervalo de evidência representa a primeira
  confirmação, não o término completo do episódio.
- Emissão automática sem aguardar revisão. Estado aberto → reconhecido → encerrado;
  encerramento exige revisão confirmada, falso positivo ou inconclusiva.
- Identificação estável por sessão, paciente, sinal, configuração e início do
  episódio. Repetir registros idênticos é idempotente; mesmo ID com outro conteúdo
  gera erro, sem sobrescrever a entrada anterior.

O SQLite do monitor é separado do banco clínico somente leitura. Amostra, estado
do detector, evento e alerta são gravados atomicamente; falha na persistência
reverte a operação. O estado necessário à continuidade sobrevive ao reinício.
A configuração recebe um fingerprint calculado do conteúdo, além da versão legível.

Cada reprodução agora tem registro próprio em `monitoring_runs`, com UUID,
paciente/sessão, origem, início/fim, velocidade, configuração, status e resumo.
Mesmo uma execução com 80 duplicações fica registrada e pode ser analisada após
reinício. O painel permite selecionar e exportar históricos; a CLI usa o mesmo
registro. Dados existentes são preservados por criação incremental da tabela.
Execuções antigas não recebem métricas inventadas retroativamente. Uma interrupção
capturada registra falha; encerramento abrupto do processo pode deixar o registro
como `running`, que deve ser interpretado como não concluído.

A verificação isolada em `reports/vitals/replay-history.json` reproduziu novamente
80 registros em 1×, por aproximadamente 19 s, sem novos alertas e com resumo
persistido. O script `scripts/verify_replay_history.py` reproduz essa verificação
sem modificar os bancos que o usuário utiliza no painel.

## Reprodução e painel

```bash
.venv/bin/python scripts/demo_vitals.py
.venv/bin/python -m pip install -e '.[ui]'
.venv/bin/python -m streamlit run app.py
```

O script usa bancos temporários para evitar resultados de execuções anteriores e
grava um relatório novo em `reports/vitals/demo.json`. O cenário com desvio é
reproduzido a 1×; estável e artefato são controles acelerados. Para uma execução
inteiramente acelerada, use `scripts/demo_vitals.py --speed 0`; ela não comprova
cadência real e sobrescreve o relatório padrão, salvo se usar outro `--report`.

No painel, selecione o cenário e o sinal do gráfico antes de iniciar. Ele mostra as amostras em tabela
durante a reprodução, os alertas e suas evidências; registra reconhecimento,
encerramento e comentário da equipe. A saída completa pode ser exportada em JSON.
Cada cenário tem banco próprio; o painel preserva o histórico em `outputs/`.
Não há autenticação de produção: o responsável informado é um ator de demonstração.

## Uso sem interface

```bash
.venv/bin/python -m monitoramento_clinico.monitor replay \
  --database outputs/monitoring.db --case development-vitals-2 \
  --speed 1 --report outputs/vitals-replay.json
.venv/bin/python -m monitoramento_clinico.monitor status
```

Para reconhecer/encerrar, copie o identificador exibido no `status`:

```bash
.venv/bin/python -m monitoramento_clinico.monitor acknowledge \
  --alert-id 'alert-IDENTIFICADOR' --actor 'demo-professional' --comment 'Alerta visto'
.venv/bin/python -m monitoramento_clinico.monitor close \
  --alert-id 'alert-IDENTIFICADOR' --actor 'demo-professional' \
  --comment 'Conferido com o cenário sintético' --review confirmed
```

Para outro cenário sobreposto no tempo, use outro `--database`; misturar as
fixtures da mesma sessão faria os registros antigos serem considerados atrasados.
Para experimentar outra configuração sobre as mesmas amostras, use um banco novo;
registros previamente ingeridos não são recalculados automaticamente.

## Evidência e métricas

Em `reports/vitals/demo.json` estão configuração, fingerprint, ambiente,
contagens, latências e snapshots com eventos/alertas/histórico. Na demonstração:

| Caso de desenvolvimento | Amostras | Alertas novos esperados |
| --- | --- | --- |
| Estável (`development-vitals-1`) | 80 | 0 |
| Desvio persistente (`development-vitals-2`) | 80 | 4, um por sinal |
| Artefato isolado (`development-vitals-4`) | 80 | 0; quatro amostras com qualidade sinalizada |

O cenário anômalo dura 19 segundos entre primeira e última amostra. O desvio
começa no segundo 10 e a confirmação ocorre no 13. A janela de três segundos
faz parte do atraso percebido pelo usuário e é reportada separadamente.

- `processing_p95_ms`: conexão, detecção e commit por amostra, medidos com relógio
  monotônico; exclui a espera programada da reprodução.
- `confirmation_to_alert_seconds`: atraso entre o instante agendado da amostra
  que confirma o desvio e o retorno após commit; inclui eventual atraso acumulado
  da reprodução. Disponível somente em 1×, para alertas novos.
- `onset_to_alert_seconds`: início do desvio na linha do tempo reproduzida até
  emissão persistida, incluindo a janela de confirmação.
- `received_at` registra recebimento real; `occurred_at` permanece o horário da
  captura sintética. Não subtrair a data histórica da fixture do relógio atual.

São medidas locais de uma execução pequena; não demonstram SLA nem desempenho
em sensores, nuvem ou carga concorrente. Nenhuma métrica de acurácia clínica é
inferida a partir desses três casos funcionais.

## Testes e limites

Testes cobrem persistência e retomada, recuperação e novo episódio, artefatos,
lacunas, dados atrasados, conflito de IDs, isolamento de pacientes e sessões,
transições de revisão e rollback de falha simulada no banco. O E2E atravessa
fixtures → validação → detecção → SQLite → alerta → reinício/deduplicação.

Amostras fora de ordem são persistidas com status `out_of_order` e não alteram
o detector. O buffer de reordenação de cinco segundos previsto no escopo fica
para a integração temporal posterior; não está declarado como implementado.
Este baseline detecta persistência fora dos limites, não todas as tendências,
prescrições ou anomalias de movimento. A expansão e a comparação de modelos
continuam nas etapas seguintes. Alertas são exibidos localmente; não são enviados
por e-mail ou a sistemas hospitalares.
