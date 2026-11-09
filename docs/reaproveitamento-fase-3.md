# Extração seletiva da fase 3

## Origem e preservação

Origem: https://github.com/caiodesigner/challenge-fiap-fase-3

Revisão de referência: `66f0a07544202f8dd241b41edb79d12962d5f5ea`.
Foram lidos arquivos do diretório local irmão, que já apresentava alterações
antes desta etapa. Para os cinco arquivos extraídos, o conteúdo foi comparado
ao commit de referência; o resultado individual e os hashes SHA-256 estão em
[reaproveitamento-manifest.json](reaproveitamento-manifest.json).
O estado Git e os hashes dos componentes inspecionados foram comparados antes
e depois da extração, sem alterações introduzidas na fase 3.

## Componentes incorporados

| Origem | Destino | Decisão/adaptação |
| --- | --- | --- |
| `src/assistente_medico/data/anonymization.py` | `src/monitoramento_clinico/data/anonymization.py` | Conteúdo preservado; detecção de padrões explícitos e campos proibidos |
| `src/assistente_medico/audit/recorder.py` | `src/monitoramento_clinico/audit/recorder.py` | Metadados de detector, pipeline e modalidade substituem campos de LLM; referência de sessão substitui thread de chat |
| `src/assistente_medico/repositories/clinical.py` | `src/monitoramento_clinico/repositories/clinical.py` | Conteúdo preservado; consulta parametrizada e somente leitura para contexto sintético |
| `data/database/schema.sql` | `data/database/schema.sql` | Preservado contexto clínico; removida tabela `proposed_alerts`, cujo único estado não atende ao ciclo de alertas da fase 4 |
| `tests/data/test_anonymization.py` | `tests/test_anonymization.py` | Imports adaptados ao pacote novo |

Testes de auditoria e repositório foram escritos para os comportamentos extraídos,
incluindo persistência após recriação do recorder, isolamento de execução/paciente,
bloqueio de escrita e rejeição de identificadores inválidos. O schema atual é uma
base de contexto, não o modelo completo de ingestão multimodal.

## Componentes analisados e adiados

- **Streamlit e serviço de UI:** acoplados a chain, embeddings e modelos de chat.
  A interface será construída sobre os contratos da fase 4, sem trazer esse bootstrap.
- **LangGraph e estado:** orientados a intenções de perguntas. Reconsiderar após
  contratos de eventos; revisão humana não deve bloquear a emissão de alertas.
- **Políticas:** regras de proibição de prescrição são próprias da geração de
  respostas. A análise de histórico de prescrições exige um caminho diferente.
- **Validação e geração sintética:** ligadas ao corpus e aos splits do treino.
  Novos validadores precisam abranger mídias, tempo, origem e partições por pessoa.
- **Qwen, LoRA, E5, RAG e treino:** opcionais, fora do caminho crítico. Nenhum peso,
  cache, banco ou resultado histórico foi copiado.
- **Configuração de qualidade:** reaproveitada como estrutura, sem copiar pins,
  metas de cobertura ou versões de ações indiscriminadamente. CI offline em
  Python 3.12 e 3.14; execução remota ainda não verificada nesta etapa.

## Base instalável e validação

Pacote novo: `monitoramento_clinico`. A única dependência de runtime é Pydantic.
As ferramentas de desenvolvimento são opcionais. O suporte declarado é
Python `>=3.12,<3.15`; a validação local desta extração usou Python 3.14.4 porque
o ambiente não fornece 3.12 e o ambiente virtual antigo não é executável aqui.
A matriz CI verificará os extremos; isso ainda não constitui resultado de CI.

Verificações locais: instalação editável, `pip check`, Ruff, formatação, mypy e
13 testes aprovados. Como Make não está instalado no ambiente de execução,
foram usados diretamente os comandos equivalentes documentados no README.

## Limitações mantidas explícitas

- As expressões regulares não detectam todos os identificadores e não anonimizam
  imagem/voz. Não constituem autorização automática de envio à nuvem.
- Hash sem segredo não garante anonimização de identificadores previsíveis.
- O recorder aceita `details` livres; o chamador deve sanitizar dados. Não há
  garantia de integridade criptográfica, deduplicação ou concorrência entre processos.
- O schema preserva condições HAS/DM2 e pacientes adultos sintéticos. Escrita de
  novas medições, histórico temporal de prescrições e alertas serão implementados
  na etapa de contratos/dados; o repositório de contexto continua somente leitura.
- Não há UI, detector, fusão ou chamada Azure nesta base. Testes de infraestrutura
  não comprovam qualidade clínica nem atendimento aos requisitos multimodais.

## Atribuições

Código de origem: Caio Lucas Santos Silva, projeto acadêmico FIAP fase 3.
Mantida a classificação proprietária como `LicenseRef-Proprietary`; não se
declara uma licença aberta nova para o código extraído. Dependências mantêm
suas próprias licenças. Modelos e datasets externos ainda não foram incorporados.

## Aceite desta etapa

- [x] Origem e hashes registrados.
- [x] Extração sem dependência do diretório da fase 3 em runtime.
- [x] Componentes incorporados exercitados por testes próprios.
- [x] Instalação mínima e verificações locais aprovadas.
- [x] Componentes adiados e limitações documentados.
- [x] Preservação do estado anterior da fase 3 conferida.
- [ ] CI remota executada (depende de envio ao GitHub).

Próximo passo: dados, contratos multimodais e referência de avaliação.
