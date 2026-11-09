# Challenge FIAP — Fase 4

Repositório do projeto Challenge FIAP — Fase 4.

Evolução seletiva do assistente médico desenvolvido na fase 3, com foco em
monitoramento multimodal de pacientes e detecção de anomalias. O projeto da
fase 3 será preservado em seu repositório original.

O projeto tem uma base Python instalável com contexto clínico somente leitura,
detecção de identificadores textuais e auditoria local. Detectores multimodais,
interface, integração Azure e alertas ainda serão implementados.

- [Plano de execução e análise do feedback da fase 3](PLANO_DESENVOLVIMENTO.md)
- [Escopo, cenários e critérios de aceite](docs/escopo-e-aceite.md)
- [Origem e análise dos componentes reaproveitados](docs/reaproveitamento-fase-3.md)
- [Dados, contratos e conjuntos de avaliação](docs/dados-e-avaliacao.md)

## Instalação e verificação da base

Requer Python 3.12–3.14 com `venv` e `pip`. Validação local realizada em Python
3.14.4; a CI está configurada para 3.12 e 3.14. Não requer GPU, modelos ou Azure.
No Linux, execute na raiz do projeto:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy
.venv/bin/python -m pytest
.venv/bin/python -m pip check
.venv/bin/python -m monitoramento_clinico.data validate
.venv/bin/python scripts/prepare_bidmc.py validate
```

Se `venv`/`pip` estiverem ausentes, instale os pacotes correspondentes à versão
de Python na sua distribuição. Com GNU Make disponível, `make install` e
`make check` fornecem atalhos para instalação e verificações de qualidade.

Os testes criam bancos e registros sintéticos temporários, sem acessar a fase 3.
O schema de contexto está em `data/database/schema.sql`; não representa ainda
o armazenamento completo da fase 4. O ambiente virtual e saídas são ignorados pelo Git.

Os contratos multimodais estão em `src/monitoramento_clinico/contracts.py`.
Há 90 fixtures funcionais sintéticas e seis registros públicos BIDMC separados
por fonte. Vídeos clínicos e fala consentida ainda precisam ser incorporados;
os dados artificiais não comprovam desempenho clínico. Para recriar as fixtures:

```bash
.venv/bin/python -m monitoramento_clinico.data generate
```
