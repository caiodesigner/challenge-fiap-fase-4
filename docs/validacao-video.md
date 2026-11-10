# Validação funcional — interface e vídeo

Validação executada em 10/11/2026, com Python 3.14.4 e dependências opcionais
de interface/vídeo instaladas. Evidência estruturada:
`reports/validation/stage-video.json`.

| Verificação | Resultado |
| --- | --- |
| Streamlit iniciado pelo usuário | Página e `/_stcore/health` responderam HTTP 200 na porta 8501 |
| Suíte automatizada | 53 testes aprovados, incluindo regressão do painel |
| Qualidade | Ruff, formatação, mypy e consistência das dependências aprovados |
| Histórico do painel | Duas reproduções persistidas; segunda com 80 duplicações, sem novos alertas |
| Revisão | Reconhecimento e encerramento persistidos, com duas entradas de histórico |
| Navegação | Área de vídeo renderizada sem exceções |
| Vídeo com postura | Inferência real MediaPipe em CPU; dez quadros válidos, MP4/relatórios disponíveis e três downloads renderizados |
| Vídeo sem pessoa | Dez quadros sinalizados como `no_person`; avaliação insuficiente, sem desvios inventados |
| Vídeo corrompido | Falha tratada no painel, relatório de erro e dois downloads de relatório |
| Persistência das análises | Resultados e downloads continuam acessíveis após recarregar, sem nova análise automática |
| Bancos do usuário | Hashes conferidos antes/depois; nenhum banco de sessão modificado pelos testes |

Os widgets foram testados com Streamlit AppTest e diretórios temporários. No
teste de vídeo, o uploader recebeu bytes controlados; a inferência subsequente
usou o modelo real. Isso não equivale a automação de seleção de arquivo em
um navegador nem inspeção visual da página. O serviço em execução foi conferido
por HTTP separadamente.

A entrada com postura é uma imagem de referência repetida em vídeo, não um
exercício clínico. As regras de desvio têm testes positivos/negativos com
características controladas. Precisão/recall em gravações representativas,
consentidas/licenciadas e anotadas de forma independente continuam pendentes.

Resultado: validação funcional aprovada, sem falhas encontradas nos cenários
executados. Esse resultado não representa validação clínica ou conclusão de
todos os requisitos do challenge.

## Reprodução

```bash
.venv/bin/python -m pip install -e '.[ui,video,dev]'
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy
.venv/bin/python -m pip check
```

O teste permanente `tests/test_interface.py` usa bancos temporários e verifica
reprodução repetida, histórico e revisão no painel. Sem Streamlit instalado,
ele é explicitamente ignorado; a CI foi configurada para instalar a dependência.
Os testes de vídeo com OpenCV também exigem o extra `video`; o job de vídeo da
CI o instala. A execução remota da CI não foi realizada nesta validação local.
