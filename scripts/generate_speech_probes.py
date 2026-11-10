"""Sondas sintéticas de desenvolvimento; requer libespeak-ng e ffmpeg locais."""

import ctypes as c
import ctypes.util
import json
import subprocess
import wave
from pathlib import Path

root = Path("outputs/local-installation")
root.mkdir(parents=True, exist_ok=True)
library = c.util.find_library("espeak-ng")
if not library:
    raise RuntimeError("libespeak-ng is required for synthetic probes")
lib = c.CDLL(library)
lib.espeak_Initialize.argtypes = [c.c_int, c.c_int, c.c_char_p, c.c_int]
rate = lib.espeak_Initialize(1, 0, None, 0)
chunks = []
callback = c.CFUNCTYPE(c.c_int, c.POINTER(c.c_short), c.c_int, c.c_void_p)


@callback
def cb(samples, count, events):
    if samples and count:
        chunks.append(c.string_at(samples, count * 2))
    return 0


lib.espeak_SetSynthCallback.argtypes = [callback]
lib.espeak_SetSynthCallback(cb)
lib.espeak_SetVoiceByName.argtypes = [c.c_char_p]
lib.espeak_SetVoiceByName(b"pt-br")
lib.espeak_SetParameter.argtypes = [c.c_int, c.c_int, c.c_int]
lib.espeak_Synth.argtypes = [
    c.c_void_p,
    c.c_size_t,
    c.c_uint,
    c.c_int,
    c.c_uint,
    c.c_uint,
    c.POINTER(c.c_uint),
    c.c_void_p,
]
samples = [
    {
        "id": "original-failure",
        "audio": "portuguese-synthetic.wav",
        "kind": "synthetic",
        "reference": "Estou com falta de ar e sinto cansaço.",
    }
]
for name, text in [
    ("portuguese-synthetic", "Estou com falta de ar e sinto cansaço."),
    ("affirmed", "Estou com falta de ar."),
    ("negated", "Não estou com falta de ar."),
    ("neutral", "Hoje estou bem e vou caminhar no parque."),
    ("history", "Ontem tive tontura."),
    ("other", "Minha mãe está com dor no peito."),
    ("contrast", "Não tenho dor no peito, mas estou com falta de ar."),
]:
    if name == "portuguese-synthetic" and (root / f"{name}.wav").exists():
        continue  # Preserve the original failing recording as evidence.
    chunks.clear()
    lib.espeak_SetParameter(1, 175 if name == "portuguese-synthetic" else 140, 0)
    encoded = text.encode()
    lib.espeak_Synth(encoded, len(encoded) + 1, 0, 1, 0, 1, None, None)
    lib.espeak_Synchronize()
    raw = root / f"{name}-original.wav"
    target = root / f"{name}.wav"
    with wave.open(str(raw), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"".join(chunks))
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(raw),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(target),
        ],
        check=True,
    )
    if name != "portuguese-synthetic":
        samples.append(
            {"id": name, "audio": target.name, "kind": "synthetic", "reference": text}
        )
(root / "speech-probes.json").write_text(
    json.dumps({"samples": samples}, ensure_ascii=False, indent=2)
)
