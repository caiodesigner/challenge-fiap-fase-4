"""Interface local de áudio; nuvem somente quando selecionada explicitamente."""

import importlib
import json
from pathlib import Path
from typing import Literal
from uuid import uuid4

from monitoramento_clinico.audio import analyze_audio
from monitoramento_clinico.azure_audio import AzureSettings, load_local_env
from monitoramento_clinico.local_speech import LocalSpeechClient, local_gpu_count
from monitoramento_clinico.speech_evaluation import compare_transcripts


def render_audio_panel(root: Path) -> None:
    st = importlib.import_module("streamlit")
    st.title("Áudio, voz e texto")
    st.caption(
        "Pausas e energia são medidas exploratórias; "
        "não diagnosticam fadiga ou disartria."
    )
    mode = st.radio(
        "Processamento", ["Whisper local", "Somente local", "Azure Speech + Language"]
    )
    use_azure = mode == "Azure Speech + Language"
    use_whisper = mode == "Whisper local"
    model = root / "models/faster-whisper-small"
    device: Literal["cpu", "cuda"] = "cpu"
    if use_whisper:
        st.info(
            "Transcrição automática local em português, "
            "sem envio de áudio para serviços externos."
        )
        gpu = local_gpu_count()
        device = st.selectbox("Execução", ["cpu", "cuda"] if gpu else ["cpu"])
        available_models = [
            path
            for name in ("small", "medium", "base")
            if (
                (path := root / "models" / f"faster-whisper-{name}") / "model.bin"
            ).is_file()
        ]
        if available_models:
            model = st.selectbox(
                "Modelo de transcrição", available_models, format_func=lambda p: p.name
            )
            st.caption("Modelos maiores exigem mais memória e tempo de processamento.")
        if not (model / "model.bin").is_file():
            st.warning("Prepare o modelo local antes da transcrição.")
            st.code(
                ".venv/bin/python -m pip install -e '.[audio]'\n"
                ".venv/bin/python scripts/prepare_local_speech.py"
            )
    try:
        load_local_env(root / ".env")
    except ValueError as error:
        st.error(str(error))
        return
    if use_azure:
        st.info(
            "Este modo envia o WAV ao Azure Speech e o texto sanitizado "
            "ao Azure Language. "
            "O uso está sujeito ao plano e às cotas dos recursos configurados."
        )
        available = AzureSettings.from_env().availability()
        st.json(
            {
                "speech_configurado": available["speech"],
                "language_configurado": available["language"],
            }
        )
        if not all(available.values()):
            st.warning(
                "Configure as variáveis do .env conforme .env.example. "
                "Sem recursos configurados não haverá chamadas Azure."
            )
    else:
        st.info("Modo local: nenhuma chamada ao Azure ou cobrança desse serviço.")
    upload = st.file_uploader(
        "Áudio WAV mono, PCM 16-bit, 16 kHz, de 0,3 a 30 segundos", type=["wav"]
    )
    if upload is not None:
        st.audio(upload.getvalue(), format="audio/wav")
    reference = st.file_uploader(
        "Referência de voz do mesmo cenário (opcional)", type=["wav"]
    )
    manual = (
        None
        if use_azure or use_whisper
        else st.text_area("Transcrição manual opcional (não é resultado do Azure)")
    )
    if st.button("Analisar áudio", disabled=upload is None):
        directory = root / "outputs/audio_uploads" / str(uuid4())
        directory.mkdir(parents=True, exist_ok=False)
        source = directory / "input.wav"
        source.write_bytes(upload.getvalue())
        baseline = None
        if reference is not None:
            baseline = directory / "reference.wav"
            baseline.write_bytes(reference.getvalue())
        try:
            with st.spinner("Analisando áudio…"):
                analyze_audio(
                    source,
                    root / "outputs/audio",
                    reference=baseline,
                    manual_transcript=manual or None,
                    use_azure=use_azure,
                    use_whisper=use_whisper,
                    local_client=LocalSpeechClient(model, device=device)
                    if use_whisper
                    else None,
                )
            st.success(
                "Execução registrada. Confira qualidade e status de cada serviço."
            )
        except Exception as error:
            st.error(
                f"Análise não concluída: {type(error).__name__}. "
                "Confira o relatório de falha."
            )
    reports = sorted(
        (root / "outputs/audio").glob("*/report.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not reports:
        st.info("Nenhuma análise de áudio registrada.")
        return
    selected = st.selectbox(
        "Análise de áudio registrada", reports, format_func=lambda p: p.parent.name
    )
    report = json.loads(selected.read_text())
    st.json({key: value for key, value in report.items() if key != "acoustics"})
    if report.get("transcript_source") == "faster_whisper_local":
        st.warning(
            "Transcrição automática requer conferência com o áudio. "
            "A ausência de uma menção no texto não confirma ausência do sintoma."
        )
        reference_text = st.text_area(
            "Referência manual para avaliar a transcrição",
            key=f"speech-reference-{selected.parent.name}",
            help="Transcreva o que ouviu, incluindo negações. Não altera a inferência.",
        )
        if reference_text.strip():
            st.json(compare_transcripts(reference_text, report.get("transcript", "")))
    if "acoustics" in report:
        features = report["acoustics"]
        st.json({key: value for key, value in features.items() if key != "frames"})
        st.line_chart(
            {
                "segundos": [frame["start_seconds"] for frame in features["frames"]],
                "energia_dbfs": [frame["rms_dbfs"] for frame in features["frames"]],
            },
            x="segundos",
            y="energia_dbfs",
        )
    if report["cloud_requested"] and not report["real_azure_validation"]:
        st.warning("Esta execução não comprova integração real completa com Azure.")
    st.download_button(
        "Baixar relatório de áudio JSON",
        selected.read_bytes(),
        file_name="audio-report.json",
    )
    st.download_button(
        "Baixar relatório de áudio Markdown",
        selected.with_suffix(".md").read_bytes(),
        file_name="audio-report.md",
    )
