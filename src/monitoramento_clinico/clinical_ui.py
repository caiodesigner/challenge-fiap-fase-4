"""Painel de histórico clínico e fusão; cenários sintéticos de desenvolvimento."""

import importlib
import json
from datetime import datetime
from pathlib import Path

from monitoramento_clinico.clinical_monitor import ClinicalMonitor
from monitoramento_clinico.contracts import PrescriptionVersion
from monitoramento_clinico.media_alignment import align_media_report
from monitoramento_clinico.replay import load_case, replay
from monitoramento_clinico.vitals import VitalsConfig


def render_clinical_panel(root: Path) -> None:
    st = importlib.import_module("streamlit")
    st.title("Histórico clínico e fusão multimodal")
    st.caption(
        "Regras experimentais e dados sintéticos. Alertas não prescrevem condutas."
    )
    case = st.selectbox(
        "Cenário de prescrição",
        [1, 2, 3, 4, 5],
        format_func=lambda n: {
            1: "1 — dose estável",
            2: "2 — mudança prevista",
            3: "3 — mudança inesperada",
            4: "4 — unidade incompatível",
            5: "5 — interrupção, duplicação e reinício",
        }[n],
    )
    session, samples = load_case(root / "data/fixtures", "development-vitals-2")
    config = VitalsConfig.model_validate_json(
        (root / "configs/vitals.json").read_text()
    )
    monitor = ClinicalMonitor(root / f"outputs/clinical-scenario-{case}.db", config)
    monitor.register_session(session)
    st.write(f"Paciente: {session.patient_id} · Sessão: {session.session_id}")
    st.caption("Cada cenário usa banco separado; associação sintética de fontes.")
    if st.button("Processar cenário sintético"):
        replay(monitor, session, samples, speed=0, source_id="synthetic-fusion-demo")
        fixture = (
            root / f"data/fixtures/development/development-prescription-{case}.json"
        )
        for payload in json.loads(fixture.read_text())["prescriptions"]:
            monitor.ingest_prescription(PrescriptionVersion.model_validate(payload))
        st.success(
            "Sinais e prescrições processados; alertas emitidos automaticamente."
        )
    prescription_upload = st.file_uploader(
        "Histórico de prescrições JSON (contrato sintético)", type=["json"]
    )
    if st.button("Importar prescrições", disabled=prescription_upload is None):
        try:
            versions = [
                PrescriptionVersion.model_validate(row)
                for row in json.loads(prescription_upload.getvalue())["prescriptions"]
            ]
            if any(
                (v.patient_id, v.session_id) != (session.patient_id, session.session_id)
                for v in versions
            ):
                raise ValueError("prescription identity differs from selected session")
            results = [monitor.ingest_prescription(v) for v in versions]
            st.json(results)
        except (ValueError, KeyError, TypeError) as error:
            st.error(f"Importação de prescrições interrompida: {error}")
    st.subheader("Importar relatório de áudio ou vídeo")
    upload = st.file_uploader(
        "Relatório JSON gerado pelo painel de áudio/vídeo", type=["json"]
    )
    capture = st.text_input(
        "Início da captura com fuso horário (ISO 8601)",
        value=session.started_at.isoformat(),
    )
    association = st.selectbox(
        "Associação temporal",
        ["synthetic", "capture_time_informed"],
        format_func=lambda s: {
            "synthetic": "Associação sintética de demonstração",
            "capture_time_informed": "Horário de captura informado pelo responsável",
        }[s],
    )
    st.caption(
        "Texto usa o início do relato, sem alinhamento por palavra. "
        "Fontes independentes não comprovam simultaneidade real."
    )
    if st.button("Integrar eventos de mídia", disabled=upload is None):
        try:
            aligned = align_media_report(
                json.loads(upload.getvalue()),
                session,
                datetime.fromisoformat(capture),
                association,
            )
            monitor.ingest_events(aligned)
            st.success(f"{len(aligned)} eventos integrados; repetições deduplicadas.")
        except (ValueError, KeyError, TypeError) as error:
            st.error(f"Importação rejeitada: {error}")
    st.subheader("Disponibilidade das modalidades")
    modality = st.selectbox(
        "Modalidade", ["vitals", "prescription", "audio", "text", "video", "movement"]
    )
    availability = st.selectbox(
        "Disponibilidade", ["available", "unavailable", "degraded"]
    )
    reason = st.text_input("Motivo da disponibilidade")
    if st.button("Registrar disponibilidade"):
        try:
            monitor.set_availability(
                session.session_id, session.patient_id, modality, availability, reason
            )
        except ValueError as error:
            st.error(str(error))
    snapshot = monitor.snapshot()
    st.dataframe(snapshot["availability"], hide_index=True)
    st.caption(
        "Sem registro: disponibilidade desconhecida. "
        "Falhas não bloqueiam alertas das demais modalidades."
    )
    st.subheader("Evolução das prescrições")
    st.dataframe(snapshot["prescriptions"], hide_index=True)
    st.subheader("Linha do tempo de eventos")
    st.dataframe(
        [
            {
                "evento": event["event_type"],
                "início": event["occurred_at"],
                "fim": event["ended_at"],
                "modalidades": ", ".join(
                    sorted({e["modality"] for e in event["evidence"]})
                ),
                "id": event["event_id"],
            }
            for event in sorted(snapshot["events"], key=lambda e: e["occurred_at"])
        ],
        hide_index=True,
    )
    st.subheader("Alertas automáticos")
    st.caption(
        "attention: isolado; priority: correlação entre fontes; "
        "observation: inconsistência de dado. Severidade experimental."
    )
    st.dataframe(snapshot["alerts"], hide_index=True)
    active = {a["alert_id"]: a for a in snapshot["alerts"] if a["status"] != "closed"}
    if active:
        with st.form("clinical-review"):
            identifier = st.selectbox("Alerta para revisão", list(active))
            actor = st.text_input("Responsável")
            comment = st.text_input("Comentário da revisão")
            action = st.selectbox("Ação de revisão", ["acknowledge", "close"])
            review = st.selectbox(
                "Resultado ao encerrar", ["confirmed", "false_positive", "inconclusive"]
            )
            if st.form_submit_button("Registrar revisão"):
                try:
                    monitor.review_alert(
                        identifier,
                        action,
                        actor,
                        comment,
                        review if action == "close" else None,
                    )
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
    with st.expander("Evidências, origem e histórico de revisão"):
        st.json(
            {
                k: snapshot[k]
                for k in ("events", "event_provenance", "history", "clinical_config")
            }
        )
    st.download_button(
        "Exportar histórico clínico e fusão",
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        file_name="clinical-fusion.json",
        mime="application/json",
    )
