"""Regras temporais exploratórias sobre características posturais observáveis."""

import math
from typing import Literal

from pydantic import Field, model_validator

from monitoramento_clinico.contracts import Contract


class VideoDeviation(Contract):
    event_type: str
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(ge=0)

    @model_validator(mode="after")
    def ordered(self) -> "VideoDeviation":
        if self.end_seconds < self.start_seconds:
            raise ValueError("deviation end precedes start")
        return self


class VideoConfig(Contract):
    version: str = "pose-rules-v1"
    mode: Literal["rehabilitation", "inpatient"] = "rehabilitation"
    sample_fps: float = Field(default=5, ge=1, le=15)
    minimum_visibility: float = Field(default=0.6, ge=0, le=1)
    asymmetry_degrees: float = Field(default=25, gt=0)
    persistence_seconds: float = Field(default=1, gt=0)
    interruption_seconds: float = Field(default=1.5, gt=0)
    max_gap_seconds: float = Field(default=0.5, gt=0)
    max_duration_seconds: float = Field(default=120, gt=0, le=600)

    @model_validator(mode="after")
    def sampling_gap(self) -> "VideoConfig":
        if 1 / self.sample_fps > self.max_gap_seconds:
            raise ValueError("sampling interval exceeds maximum temporal gap")
        return self


class PoseFeatures(Contract):
    time_seconds: float = Field(ge=0)
    quality: Literal["valid", "no_person", "multiple_people", "low_confidence"]
    left_angle: float | None = Field(default=None, ge=0, le=180)
    right_angle: float | None = Field(default=None, ge=0, le=180)
    center_x: float | None = None
    center_y: float | None = None

    @model_validator(mode="after")
    def valid_features(self) -> "PoseFeatures":
        if self.quality == "valid" and any(
            value is None
            for value in (
                self.left_angle,
                self.right_angle,
                self.center_x,
                self.center_y,
            )
        ):
            raise ValueError("valid pose requires all features")
        return self


def shoulder_angle(
    hip: tuple[float, float], shoulder: tuple[float, float], elbow: tuple[float, float]
) -> float:
    a = (hip[0] - shoulder[0], hip[1] - shoulder[1])
    b = (elbow[0] - shoulder[0], elbow[1] - shoulder[1])
    denominator = math.hypot(*a) * math.hypot(*b)
    if denominator < 1e-8:
        raise ValueError("degenerate pose geometry")
    cosine = max(-1, min(1, (a[0] * b[0] + a[1] * b[1]) / denominator))
    return math.degrees(math.acos(cosine))


def detect_deviations(
    frames: list[PoseFeatures], config: VideoConfig
) -> list[VideoDeviation]:
    """Não preenche lacunas; qualidade insuficiente encerra candidatos ativos."""
    events: list[VideoDeviation] = []
    active: dict[str, tuple[float, float, bool]] = {}
    previous: PoseFeatures | None = None
    moved = False
    baseline_y: float | None = None
    baseline_motion: list[float] = []

    def flush(kind: str) -> None:
        start, end, confirmed = active.pop(kind)
        if confirmed:
            events.append(
                VideoDeviation(event_type=kind, start_seconds=start, end_seconds=end)
            )

    for frame in frames:
        if previous is not None and frame.time_seconds <= previous.time_seconds:
            raise ValueError("video timestamps must increase")
        gap = previous is not None and (
            frame.time_seconds - previous.time_seconds > config.max_gap_seconds
        )
        if frame.quality != "valid" or gap:
            for kind in list(active):
                flush(kind)
            moved = False
            baseline_y = None
            baseline_motion = []
        conditions: dict[str, tuple[bool, float]] = {}
        if frame.quality == "valid":
            assert frame.left_angle is not None and frame.right_angle is not None
            assert frame.center_x is not None and frame.center_y is not None
            comparable = (
                previous is not None and previous.quality == "valid" and not gap
            )
            angular_speed = 0.0
            displacement = 0.0
            if comparable:
                assert previous is not None and previous.left_angle is not None
                assert (
                    previous.right_angle is not None and previous.center_x is not None
                )
                assert previous.center_y is not None
                dt = frame.time_seconds - previous.time_seconds
                angular_speed = (
                    max(
                        abs(frame.left_angle - previous.left_angle),
                        abs(frame.right_angle - previous.right_angle),
                    )
                    / dt
                )
                displacement = (
                    math.hypot(
                        frame.center_x - previous.center_x,
                        frame.center_y - previous.center_y,
                    )
                    / dt
                )
            if config.mode == "rehabilitation":
                if angular_speed > 10:
                    moved = True
                angle = (frame.left_angle + frame.right_angle) / 2
                conditions = {
                    "asymmetry": (
                        abs(frame.left_angle - frame.right_angle)
                        > config.asymmetry_degrees,
                        config.persistence_seconds,
                    ),
                    "interruption": (
                        comparable and moved and 25 < angle < 140 and angular_speed < 5,
                        config.interruption_seconds,
                    ),
                }
                if angle <= 25 or angle >= 140:
                    moved = False
            else:
                if baseline_y is None:
                    baseline_y = frame.center_y
                if comparable and len(baseline_motion) < 15:
                    baseline_motion.append(displacement)
                reference = (
                    sum(baseline_motion) / len(baseline_motion)
                    if baseline_motion
                    else 0
                )
                conditions = {
                    "rise_candidate": (
                        baseline_y - frame.center_y > 0.15,
                        config.persistence_seconds,
                    ),
                    "activity_change": (
                        len(baseline_motion) >= 15
                        and reference > 0.02
                        and displacement < 0.003,
                        3,
                    ),
                }
        for kind in list(active):
            if not conditions.get(kind, (False, 0))[0]:
                flush(kind)
        for kind, (present, duration) in conditions.items():
            if present:
                start, _, confirmed = active.get(
                    kind, (frame.time_seconds, frame.time_seconds, False)
                )
                active[kind] = (
                    start,
                    frame.time_seconds,
                    confirmed or frame.time_seconds - start >= duration - 1e-8,
                )
        previous = frame
    for kind in list(active):
        flush(kind)
    return sorted(events, key=lambda event: (event.start_seconds, event.event_type))
