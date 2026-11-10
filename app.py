"""Painel local do primeiro fluxo incremental de sinais vitais."""

import json
from pathlib import Path

import streamlit as st

from monitoramento_clinico.audio_ui import render_audio_panel
from monitoramento_clinico.contracts import Measurement
from monitoramento_clinico.replay import load_case, replay
from monitoramento_clinico.video_ui import render_video_panel
from monitoramento_clinico.vitals import ProcessingResult, VitalsConfig, VitalsMonitor

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Monitoramento de sinais vitais", layout="wide")
area = st.sidebar.radio("Área", ["Sinais vitais", "Vídeo", "Áudio"])
if area == "Áudio":
    render_audio_panel(ROOT)
    st.stop()
if area == "Vídeo":
    render_video_panel(ROOT)
    st.stop()
st.title("Monitoramento de sinais vitais")
st.caption("Demonstração acadêmica com dados sintéticos e limites experimentais.")
config = VitalsConfig.model_validate_json((ROOT / "configs/vitals.json").read_text())
# Each fixture has an independent DB to avoid mixing overlapping synthetic timelines.
case = st.selectbox(
    "Cenário",
    [
        "development-vitals-1",
        "development-vitals-2",
        "development-vitals-3",
        "development-vitals-4",
    ],
)
monitor = VitalsMonitor(ROOT / f"outputs/{case}.db", config)
accelerated = st.checkbox("Reprodução acelerada (sem comprovação de cadência real)")
selected_signal = st.selectbox(
    "Sinal no gráfico", ["heart_rate", "systolic", "diastolic", "spo2"]
)
live = st.empty()
chart = st.empty()
table = st.empty()
alert_panel = st.empty()

if st.button("Reproduzir sessão"):
    session, samples = load_case(ROOT / "data/fixtures", case)
    points: list[dict[str, object]] = []
    seconds: list[float] = []
    values: list[float] = []

    def update(sample: Measurement, result: ProcessingResult) -> None:
        points.append(
            {
                "horário": sample.occurred_at.isoformat(),
                "sinal": sample.signal,
                "valor": sample.value,
                "unidade": sample.unit,
                "qualidade": sample.quality,
                "resultado": result.status,
            }
        )
        live.write(f"{sample.signal}: {sample.value} {sample.unit} — {result.status}")
        table.dataframe(points, hide_index=True)
        if sample.signal == selected_signal:
            seconds.append((sample.occurred_at - session.started_at).total_seconds())
            values.append(sample.value)
            chart.line_chart(
                {"segundos": seconds, "valor": values}, x="segundos", y="valor"
            )
        alert_panel.dataframe(monitor.snapshot()["alerts"], hide_index=True)

    summary = replay(
        monitor, session, samples, 0 if accelerated else 1, update, source_id=case
    )
    st.json(summary)
    st.caption("Repetir a mesma sessão preserva os alertas e não duplica as amostras.")

snapshot = monitor.snapshot()
st.subheader("Histórico de reproduções")
if snapshot["runs"]:
    runs = {run["run_id"]: run for run in snapshot["runs"]}
    selected_run = st.selectbox(
        "Execução registrada",
        list(runs),
        format_func=lambda key: (
            f"{runs[key]['started_at']} — "
            f"{runs[key]['status']} — velocidade {runs[key]['speed']}×"
        ),
    )
    st.json(runs[selected_run])
else:
    st.info(
        "Nenhuma reprodução registrada nesta versão. Dados antigos foram preservados."
    )
st.subheader("Alertas e evidências")
st.dataframe(snapshot["alerts"], hide_index=True)
with st.expander("Evidências e histórico"):
    st.json({"events": snapshot["events"], "history": snapshot["history"]})
open_alerts = {
    alert["alert_id"]: alert
    for alert in snapshot["alerts"]
    if alert["status"] != "closed"
}
if open_alerts:
    with st.form("review"):
        identifier = st.selectbox("Alerta", list(open_alerts))
        actor = st.text_input("Responsável (demonstração)")
        comment = st.text_input("Comentário")
        action = st.selectbox("Ação", ["Reconhecer", "Encerrar"])
        review = st.selectbox(
            "Revisão ao encerrar", ["confirmed", "false_positive", "inconclusive"]
        )
        if st.form_submit_button("Registrar"):
            try:
                monitor.review_alert(
                    identifier,
                    "acknowledge" if action == "Reconhecer" else "close",
                    actor,
                    comment,
                    None if action == "Reconhecer" else review,
                )
                st.rerun()
            except ValueError as error:
                st.error(str(error))

st.download_button(
    "Exportar alertas e evidências",
    data=json.dumps(snapshot, indent=2, ensure_ascii=False),
    file_name="monitoramento.json",
    mime="application/json",
)
