"""Painel opcional de vídeo, com resultados persistidos por execução."""

import importlib
import json
from pathlib import Path
from uuid import uuid4

from monitoramento_clinico.video import analyze_video
from monitoramento_clinico.video_rules import VideoConfig


def render_video_panel(root: Path) -> None:
    st = importlib.import_module("streamlit")
    st.title("Análise de vídeo e desvios")
    st.caption(
        "Processamento local. Regras exploratórias; não constitui avaliação clínica."
    )
    model = root / "models/pose_landmarker_lite.task"
    mode = st.selectbox(
        "Contexto",
        ["rehabilitation", "inpatient"],
        format_func=lambda value: (
            "Elevação bilateral dos braços"
            if value == "rehabilitation"
            else "Movimentação em leito/cadeira"
        ),
    )
    st.info(
        "Use câmera fixa, uma pessoa e corpo enquadrado. Vídeos com até 120 segundos "
        "e taxa de quadros constante. Mídias e resultados permanecem neste computador."
    )
    if not model.is_file():
        st.warning("Prepare o modelo de postura antes de analisar.")
        st.code(
            ".venv/bin/python -m pip install -e '.[video]'\n"
            ".venv/bin/python scripts/prepare_pose_model.py"
        )
    upload = st.file_uploader("Vídeo", type=["mp4", "avi", "mov", "mkv"])
    if st.button("Analisar vídeo", disabled=upload is None or not model.is_file()):
        path = root / "outputs/video_uploads" / f"{uuid4()}{Path(upload.name).suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(upload.getvalue())
        try:
            with st.spinner("Estimando postura e gerando relatório…"):
                analyze_video(
                    path, root / "outputs/video", model, VideoConfig(mode=mode)
                )
            st.success(
                "Análise concluída. Confira a qualidade e os intervalos detectados."
            )
        except Exception as error:
            st.error(f"Não foi possível concluir: {error}")
    reports = sorted(
        (root / "outputs/video").glob("*/report.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not reports:
        st.info("Nenhuma análise de vídeo registrada.")
        return
    selected = st.selectbox(
        "Análise registrada", reports, format_func=lambda path: path.parent.name
    )
    report = json.loads(selected.read_text())
    st.json({key: value for key, value in report.items() if key != "features"})
    if report.get("status") == "completed":
        if report["assessment"] != "assessable":
            st.warning(
                "Há intervalos sem avaliação confiável; ausência de desvios "
                "não significa movimento normal nesses intervalos."
            )
        annotated = selected.parent / report["annotated_video"]
        if report["browser_playable"]:
            st.video(annotated.read_bytes())
        st.download_button(
            "Baixar vídeo anotado", annotated.read_bytes(), file_name=annotated.name
        )
    st.download_button(
        "Baixar relatório JSON", selected.read_bytes(), file_name="video-report.json"
    )
    st.download_button(
        "Baixar relatório Markdown",
        selected.with_suffix(".md").read_bytes(),
        file_name="video-report.md",
    )
