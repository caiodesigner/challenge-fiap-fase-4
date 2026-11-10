"""Vídeo local → postura estimada → desvios temporais → relatórios e anotação."""

import importlib
import json
import math
import shutil
import subprocess
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import perf_counter
from typing import Any, Protocol
from uuid import uuid4

from monitoramento_clinico.contracts import Event, Evidence
from monitoramento_clinico.data.fixtures import digest, write_json
from monitoramento_clinico.video_rules import (
    PoseFeatures,
    VideoConfig,
    detect_deviations,
    shoulder_angle,
)


class PoseBackend(Protocol):
    model_id: str

    def detect(self, frame: Any, timestamp_ms: int) -> list[list[Any]]: ...

    def close(self) -> None: ...


class MediaPipeBackend:
    """SDK opcional; os pesos são baixados explicitamente, nunca durante inferência."""

    def __init__(self, model_path: Path) -> None:
        if not model_path.is_file():
            raise ValueError("model missing; run scripts/prepare_pose_model.py")
        self.mp = importlib.import_module("mediapipe")
        self.model_id = "mediapipe-pose-landmarker-lite:sha256:" + digest(model_path)
        options = self.mp.tasks.vision.PoseLandmarkerOptions(
            base_options=self.mp.tasks.BaseOptions(
                model_asset_path=str(model_path),
                delegate=self.mp.tasks.BaseOptions.Delegate.CPU,
            ),
            running_mode=self.mp.tasks.vision.RunningMode.VIDEO,
            num_poses=2,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.landmarker = self.mp.tasks.vision.PoseLandmarker.create_from_options(
            options
        )

    def detect(self, frame: Any, timestamp_ms: int) -> list[list[Any]]:
        cv2 = importlib.import_module("cv2")
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb)
        return list(
            self.landmarker.detect_for_video(image, timestamp_ms).pose_landmarks
        )

    def close(self) -> None:
        self.landmarker.close()


def extract_features(
    poses: list[list[Any]], width: int, height: int, second: float, config: VideoConfig
) -> PoseFeatures:
    if len(poses) != 1:
        return PoseFeatures(
            time_seconds=second, quality="no_person" if not poses else "multiple_people"
        )
    pose = poses[0]
    required = (11, 12, 13, 14, 23, 24)
    if len(pose) < 25 or any(
        not all(
            math.isfinite(value)
            for value in (
                pose[i].x,
                pose[i].y,
                pose[i].visibility or 0,
                pose[i].presence or 0,
            )
        )
        or min(pose[i].visibility or 0, pose[i].presence or 0)
        < config.minimum_visibility
        or not 0 <= pose[i].x <= 1
        or not 0 <= pose[i].y <= 1
        for i in required
    ):
        return PoseFeatures(time_seconds=second, quality="low_confidence")

    def point(index: int) -> tuple[float, float]:
        return pose[index].x * width, pose[index].y * height

    try:
        left = shoulder_angle(point(23), point(11), point(13))
        right = shoulder_angle(point(24), point(12), point(14))
    except ValueError:
        return PoseFeatures(time_seconds=second, quality="low_confidence")
    return PoseFeatures(
        time_seconds=second,
        quality="valid",
        left_angle=left,
        right_angle=right,
        center_x=sum(pose[i].x for i in (11, 12, 23, 24)) / 4,
        center_y=sum(pose[i].y for i in (11, 12, 23, 24)) / 4,
    )


def analyze_video(
    source: Path,
    output_root: Path,
    model_path: Path,
    config: VideoConfig | None = None,
    patient_id: str = "PAT-SYN-001",
    session_id: str | None = None,
    backend: PoseBackend | None = None,
) -> dict[str, Any]:
    """Falhas deixam relatório rastreável; artefatos recebem diretório exclusivo."""
    config = config or VideoConfig()
    run_id = str(uuid4())
    output = output_root / run_id
    output.mkdir(parents=True, exist_ok=False)
    started = datetime.now(UTC)
    timer = perf_counter()
    report: dict[str, Any] = {
        "run_id": run_id,
        "started_at": started.isoformat(),
        "status": "running",
        "patient_id": patient_id,
        "session_id": session_id or f"VIDEO-{run_id}",
        "config": config.model_dump(),
        "source_name": source.name,
        "timeline_origin": "processing_start_assigned_not_capture_time",
        "timing_assumption": "constant_frame_rate_nominal_fps",
        "clinical_validation": False,
    }
    capture = None
    writer = None
    estimator = backend
    try:
        if not source.is_file() or source.stat().st_size > 200 * 1024**2:
            raise ValueError("missing video or file exceeds 200 MB")
        report["source_sha256"] = digest(source)
        cv2 = importlib.import_module("cv2")
        capture = cv2.VideoCapture(str(source))
        if not capture.isOpened():
            raise ValueError("unreadable video")
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        if not math.isfinite(fps) or not 1 <= fps <= 120:
            raise ValueError("invalid or unsupported frame rate")
        if 1 / fps > config.max_gap_seconds:
            raise ValueError("source frame interval exceeds temporal gap limit")
        estimated_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if estimated_frames / fps > config.max_duration_seconds:
            raise ValueError("video exceeds configured duration")
        estimator = estimator or MediaPipeBackend(model_path)
        report["model_id"] = estimator.model_id
        features: list[PoseFeatures] = []
        index = 0
        next_time = 0.0
        width = height = 0
        while True:
            success, frame = capture.read()
            if not success:
                break
            second = index / fps
            index += 1
            if second > config.max_duration_seconds:
                raise ValueError("decoded video exceeds configured duration")
            if second + 1e-8 < next_time:
                continue
            next_time += 1 / min(fps, config.sample_fps)
            height, width = frame.shape[:2]
            scale = min(1, 960 / width, 720 / height)
            width, height = int(width * scale) // 2 * 2, int(height * scale) // 2 * 2
            if width < 2 or height < 2:
                raise ValueError("invalid video dimensions")
            frame = cv2.resize(frame, (width, height))
            poses = estimator.detect(frame, round(second * 1000))
            feature = extract_features(poses, width, height, second, config)
            features.append(feature)
            if writer is None:
                writer = cv2.VideoWriter(
                    str(output / "posture.avi"),
                    cv2.VideoWriter_fourcc(*"MJPG"),
                    min(fps, config.sample_fps),
                    (width, height),
                )
                if not writer.isOpened():
                    raise ValueError("video encoder unavailable")
            if len(poses) == 1:
                for a, b in (
                    (11, 12),
                    (11, 13),
                    (13, 15),
                    (12, 14),
                    (14, 16),
                    (11, 23),
                    (12, 24),
                    (23, 24),
                ):
                    if len(poses[0]) > max(a, b):
                        pa, pb = poses[0][a], poses[0][b]
                        if (
                            min(pa.visibility or 0, pb.visibility or 0)
                            >= config.minimum_visibility
                        ):
                            cv2.line(
                                frame,
                                (int(pa.x * width), int(pa.y * height)),
                                (int(pb.x * width), int(pb.y * height)),
                                (0, 255, 0),
                                2,
                            )
            text = f"t={second:.2f}s {feature.quality}"
            if feature.quality == "valid":
                text += f" L={feature.left_angle:.0f} R={feature.right_angle:.0f}"
            cv2.putText(
                frame, text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 220, 255), 1
            )
            writer.write(frame)
        if not features:
            raise ValueError("video has no readable frames")
        if estimated_frames > 0 and index < estimated_frames - 1:
            raise ValueError("video truncated before declared frame count")
        assert writer is not None
        writer.release()
        writer = None
        capture.release()
        deviations = detect_deviations(features, config)
        # Second pass overlays final temporal intervals, without rerunning inference.
        capture = cv2.VideoCapture(str(output / "posture.avi"))
        writer = cv2.VideoWriter(
            str(output / "annotated.avi"),
            cv2.VideoWriter_fourcc(*"MJPG"),
            min(fps, config.sample_fps),
            (width, height),
        )
        if not writer.isOpened():
            raise ValueError("annotated video encoder unavailable")
        for feature in features:
            success, frame = capture.read()
            if not success:
                raise ValueError("annotated intermediate video truncated")
            active = [
                d.event_type
                for d in deviations
                if d.start_seconds <= feature.time_seconds <= d.end_seconds
            ]
            if active:
                cv2.putText(
                    frame,
                    ", ".join(active),
                    (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 255),
                    1,
                )
            writer.write(frame)
        writer.release()
        writer = None
        annotated = output / "annotated.avi"
        browser_playable = False
        if shutil.which("ffmpeg"):
            command = [
                "ffmpeg",
                "-nostdin",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(annotated),
                "-an",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(output / "annotated.mp4"),
            ]
            result = subprocess.run(command, capture_output=True, timeout=120)
            if result.returncode == 0:
                annotated = output / "annotated.mp4"
                browser_playable = True
        events = [
            Event(
                event_id=f"{run_id}-{i}",
                patient_id=patient_id,
                session_id=report["session_id"],
                event_type=d.event_type,
                occurred_at=started + timedelta(seconds=d.start_seconds),
                ended_at=started + timedelta(seconds=d.end_seconds),
                processed_at=datetime.now(UTC),
                detector_version=config.version,
                evidence=[
                    Evidence(
                        source_id=report["source_sha256"],
                        modality="video"
                        if config.mode == "rehabilitation"
                        else "movement",
                        start_seconds=d.start_seconds,
                        end_seconds=d.end_seconds,
                        description="Exploratory posture rule; "
                        "inspect annotated interval",
                    )
                ],
            )
            for i, d in enumerate(deviations)
        ]
        qualities = Counter(frame.quality for frame in features)
        quality_intervals: list[dict[str, Any]] = []
        previous_quality = "valid"
        for feature in features:
            if feature.quality == "valid":
                previous_quality = "valid"
                continue
            if (
                quality_intervals
                and previous_quality == feature.quality
                and quality_intervals[-1]["reason"] == feature.quality
                and feature.time_seconds - quality_intervals[-1]["end_seconds"]
                <= config.max_gap_seconds
            ):
                quality_intervals[-1]["end_seconds"] = feature.time_seconds
            else:
                quality_intervals.append(
                    {
                        "reason": feature.quality,
                        "start_seconds": feature.time_seconds,
                        "end_seconds": feature.time_seconds,
                    }
                )
            previous_quality = feature.quality
        report.update(
            status="completed",
            decoded_frames=index,
            source_fps=fps,
            sampled_frames=len(features),
            duration_seconds=index / fps,
            quality_counts=dict(qualities),
            quality_intervals=quality_intervals,
            assessment="insufficient"
            if not qualities["valid"]
            else "partial"
            if qualities["valid"] < len(features)
            else "assessable",
            deviations=[d.model_dump() for d in deviations],
            events=[event.model_dump(mode="json") for event in events],
            features=[feature.model_dump() for feature in features],
            annotated_video=annotated.name,
            browser_playable=browser_playable,
        )
        (output / "posture.avi").unlink(missing_ok=True)
    except Exception as error:
        report.update(
            status="failed", error_type=type(error).__name__, error=str(error)
        )
        raise
    finally:
        if capture is not None:
            capture.release()
        if writer is not None:
            writer.release()
        if estimator is not None:
            try:
                estimator.close()
            except Exception as close_error:
                report["backend_close_error"] = type(close_error).__name__
        report.update(
            finished_at=datetime.now(UTC).isoformat(),
            elapsed_seconds=perf_counter() - timer,
        )
        write_json(output / "report.json", report)
        lines = [
            "# Relatório automático de vídeo",
            "",
            f"Execução: {run_id}",
            f"Status: {report['status']}",
            "",
            "Análise exploratória; não constitui avaliação clínica.",
            "",
            f"Qualidade: {json.dumps(report.get('quality_counts', {}))}",
            "",
            "| Desvio | Início (s) | Fim (s) |",
            "| --- | --- | --- |",
        ]
        lines.extend(
            f"| {d['event_type']} | {d['start_seconds']:.2f} | {d['end_seconds']:.2f} |"
            for d in report.get("deviations", [])
        )
        if report.get("quality_intervals"):
            lines.extend(
                [
                    "",
                    "## Intervalos sem avaliação confiável",
                    "",
                    "| Motivo | Início (s) | Fim (s) |",
                    "| --- | --- | --- |",
                ]
            )
            lines.extend(
                f"| {q['reason']} | {q['start_seconds']:.2f} | {q['end_seconds']:.2f} |"
                for q in report["quality_intervals"]
            )
        if report.get("error"):
            lines.extend(["", f"Erro: {report['error']}"])
        elif not report.get("deviations"):
            lines.extend(
                [
                    "",
                    "Nenhum desvio confirmado nos intervalos avaliáveis; "
                    "consulte as contagens de qualidade e os pontos de postura.",
                ]
            )
        (output / "report.md").write_text("\n".join(lines) + "\n")
    return report
