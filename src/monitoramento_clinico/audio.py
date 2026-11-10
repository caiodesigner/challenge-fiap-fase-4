"""Áudio local e integração Azure explícita, com evidências separadas por etapa."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from monitoramento_clinico.acoustics import (
    AcousticConfig,
    acoustic_events,
    analyze_acoustics,
)
from monitoramento_clinico.azure_audio import (
    AzureAudioClient,
    AzureSettings,
    CloudError,
)
from monitoramento_clinico.clinical_text import analyze_mentions
from monitoramento_clinico.contracts import Event, Evidence, Modality
from monitoramento_clinico.data.anonymization import PATTERNS
from monitoramento_clinico.data.fixtures import digest, write_json
from monitoramento_clinico.local_speech import LocalSpeechClient


def sanitize_transcript(text: str) -> str:
    for kind, pattern in PATTERNS.items():
        text = pattern.sub(f"[{kind.upper()}]", text)
    return text


def analyze_audio(
    source: Path,
    output_root: Path,
    config: AcousticConfig | None = None,
    reference: Path | None = None,
    manual_transcript: str | None = None,
    use_azure: bool = False,
    client: AzureAudioClient | None = None,
    patient_id: str = "PAT-SYN-001",
    session_id: str | None = None,
    use_whisper: bool = False,
    local_client: LocalSpeechClient | None = None,
) -> dict[str, Any]:
    if use_whisper and (use_azure or manual_transcript is not None):
        raise ValueError("select only one transcription source")
    if use_azure and manual_transcript is not None:
        raise ValueError(
            "manual transcript cannot replace Azure recognition in cloud mode"
        )
    config = config or AcousticConfig()
    run_id = str(uuid4())
    output = output_root / run_id
    output.mkdir(parents=True, exist_ok=False)
    started = datetime.now(UTC)
    timer = perf_counter()
    report: dict[str, Any] = {
        "run_id": run_id,
        "status": "running",
        "started_at": started.isoformat(),
        "source_name": source.name,
        "patient_id": patient_id,
        "session_id": session_id or f"AUDIO-{run_id}",
        "clinical_validation": False,
        "cloud_requested": use_azure,
        "real_azure_validation": False,
        "cloud_request_count": 0,
        "timeline_origin": "processing_start_assigned_not_capture_time",
        "transcript": None,
        "transcript_source": None,
        "mentions": [],
        "events": [],
        "cloud": {
            "speech": {"status": "not_requested"},
            "sentiment": {"status": "not_requested"},
            "key_phrases": {"status": "not_requested"},
        },
    }
    try:
        features = analyze_acoustics(source, config)
        report["source_sha256"] = digest(source)
        report["acoustics"] = features
        reference_features = None
        if reference is not None:
            reference_features = analyze_acoustics(reference, config)
            report["reference"] = {
                "sha256": digest(reference),
                "quality": reference_features["quality"],
            }
            if reference_features["quality"] != "assessable":
                raise ValueError("reference audio has insufficient quality")
        deviations = acoustic_events(features, reference_features)
        report["acoustic_deviations"] = deviations
        transcript = manual_transcript
        if manual_transcript is not None:
            report["transcript_source"] = "manual_not_azure"
        if use_whisper:
            if features["quality"] != "assessable":
                report["local_speech"] = {"status": "skipped_quality"}
            else:
                local_client = local_client or LocalSpeechClient(
                    Path("models/faster-whisper-small")
                )
                try:
                    result = local_client.transcribe(source)
                    transcript = result.pop("text", "")
                    segments = result.pop("segments", [])
                    # Do not retain unsanitized segment/word text in reports.
                    result["segments"] = [
                        {
                            "start_seconds": segment["start_seconds"],
                            "end_seconds": segment["end_seconds"],
                            "word_count": len(segment.get("words", [])),
                        }
                        for segment in segments
                    ]
                    report["local_speech"] = result
                    report["transcript_source"] = (
                        "faster_whisper_local" if transcript else None
                    )
                except (ImportError, ValueError, RuntimeError):
                    report["local_speech"] = {
                        "status": "failed",
                        "error": "local_transcription_failed",
                    }
        if use_azure:
            client = client or AzureAudioClient(AzureSettings.from_env())
            report["cloud_transport"] = (
                "azure_https" if client.live_transport else "test_transport"
            )
            initial_calls = client.calls
            availability = client.settings.availability()
            report["azure_configuration"] = availability
            if features["quality"] != "assessable":
                report["cloud"]["speech"] = {"status": "skipped_quality"}
            elif not availability["speech"]:
                report["cloud"]["speech"] = {"status": "not_configured"}
            else:
                try:
                    result = client.transcribe(source)
                    transcript = result.pop("text", "")
                    report["cloud"]["speech"] = result
                    report["transcript_source"] = (
                        "azure_speech" if result["status"] == "completed" else None
                    )
                except (CloudError, ValueError) as error:
                    report["cloud"]["speech"] = {
                        "status": "failed",
                        "error": str(error)
                        if isinstance(error, CloudError)
                        else "invalid_configuration",
                    }
            for name, kind in (
                ("sentiment", "SentimentAnalysis"),
                ("key_phrases", "KeyPhraseExtraction"),
            ):
                if not transcript:
                    report["cloud"][name] = {"status": "blocked_no_transcript"}
                elif not availability["language"]:
                    report["cloud"][name] = {"status": "not_configured"}
                else:
                    try:
                        report["cloud"][name] = client.analyze_text(
                            sanitize_transcript(transcript), kind
                        )
                    except (CloudError, ValueError) as error:
                        report["cloud"][name] = {
                            "status": "failed",
                            "error": str(error)
                            if isinstance(error, CloudError)
                            else "invalid_configuration",
                        }
            report["cloud_request_count"] = client.calls - initial_calls
            report["real_azure_validation"] = client.live_transport and all(
                result["status"] == "completed" for result in report["cloud"].values()
            )
        if transcript:
            if len(transcript) > 5000:
                raise ValueError("transcript exceeds 5000 characters")
            report["transcript"] = sanitize_transcript(transcript)
            report["mention_offsets"] = "sanitized_transcript_unicode_characters"
            report["mentions"] = analyze_mentions(report["transcript"])
        evidence: list[tuple[str, Modality, float, float, str]] = []
        for deviation in deviations:
            evidence.append(
                (
                    deviation["event_type"],
                    "audio",
                    deviation["start_seconds"],
                    deviation["end_seconds"],
                    "Internal low-energy pause; not a diagnosis",
                )
            )
        for mention in report["mentions"]:
            if (mention["assertion"], mention["temporality"], mention["subject"]) == (
                "affirmed",
                "current",
                "patient",
            ):
                evidence.append(
                    (
                        "critical_mention",
                        "text",
                        0,
                        0,
                        f"Term {mention['term']}; characters "
                        f"{mention['start_character']}:{mention['end_character']}; "
                        "no word-level audio alignment available",
                    )
                )
        report["events"] = [
            Event(
                event_id=f"{run_id}-{index}",
                patient_id=patient_id,
                session_id=report["session_id"],
                event_type=kind,
                occurred_at=started + timedelta(seconds=begin),
                ended_at=started + timedelta(seconds=end),
                processed_at=datetime.now(UTC),
                detector_version=config.version,
                evidence=[
                    Evidence(
                        source_id=report["source_sha256"],
                        modality=modality,
                        start_seconds=begin,
                        end_seconds=end,
                        description=description,
                    )
                ],
            ).model_dump(mode="json")
            for index, (kind, modality, begin, end, description) in enumerate(evidence)
        ]
        report["status"] = (
            "completed"
            if not use_azure or report["real_azure_validation"]
            else "partial"
        )
        if use_whisper and report["local_speech"]["status"] != "completed":
            report["status"] = "partial"
    except Exception as error:
        report.update(
            status="failed",
            error_type=type(error).__name__,
            error=str(error)
            if isinstance(error, ValueError)
            else "audio_processing_failed",
        )
        raise
    finally:
        report.update(
            finished_at=datetime.now(UTC).isoformat(),
            elapsed_seconds=perf_counter() - timer,
        )
        write_json(output / "report.json", report)
        lines = [
            "# Relatório automático de áudio",
            "",
            f"Execução: {run_id}",
            f"Status: {report['status']}",
            "",
            "Medidas acústicas exploratórias; sem diagnóstico clínico.",
            f"Qualidade: {report.get('acoustics', {}).get('quality', 'unavailable')}",
            f"Azure real comprovado nesta execução: {report['real_azure_validation']}",
            "",
            "| Evento | Início (s) | Fim (s) |",
            "| --- | --- | --- |",
        ]
        lines.extend(
            f"| {item['event_type']} | {item['start_seconds']:.2f} | "
            f"{item['end_seconds']:.2f} |"
            for item in report.get("acoustic_deviations", [])
        )
        lines.extend(
            [
                "",
                "Transcrição sanitizada:",
                report.get("transcript") or "Não disponível.",
            ]
        )
        (output / "report.md").write_text("\n".join(lines) + "\n")
    return report
