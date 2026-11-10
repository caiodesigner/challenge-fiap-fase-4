"""Adaptadores REST reais, com transporte substituível somente para testes."""

import json
import os
import re
import shlex
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path
from time import perf_counter
from typing import Any

from pydantic import SecretStr

from monitoramento_clinico.contracts import Contract

ENV_KEYS = {
    "AZURE_SPEECH_KEY",
    "AZURE_SPEECH_REGION",
    "AZURE_SPEECH_ENDPOINT",
    "AZURE_LANGUAGE_KEY",
    "AZURE_LANGUAGE_ENDPOINT",
}
Transport = Callable[[str, bytes, dict[str, str], float], dict[str, Any]]


class CloudError(RuntimeError):
    """Mensagem segura: não inclui chave, resposta remota ou conteúdo clínico."""


def load_local_env(path: Path) -> None:
    if not path.is_file():
        return
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition("=")
        key = key.strip()
        if key not in ENV_KEYS:
            continue
        try:
            tokens = shlex.split(value, comments=True)
        except ValueError:
            raise ValueError(f"invalid .env syntax on line {number}") from None
        if not separator or len(tokens) > 1:
            raise ValueError(f"invalid .env syntax on line {number}")
        if tokens:
            os.environ.setdefault(key, tokens[0])


def azure_endpoint(value: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    host = parsed.hostname or ""
    if (
        parsed.scheme != "https"
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.port not in (None, 443)
        or parsed.path not in ("", "/")
        or not any(
            host.endswith(suffix)
            for suffix in (
                ".cognitiveservices.azure.com",
                ".api.cognitive.microsoft.com",
                ".stt.speech.microsoft.com",
                ".services.ai.azure.com",
            )
        )
    ):
        raise ValueError(
            "use an HTTPS Azure resource endpoint without paths or credentials"
        )
    return value.rstrip("/")


class AzureSettings(Contract):
    speech_key: SecretStr | None = None
    speech_region: str = ""
    speech_endpoint: str = ""
    language_key: SecretStr | None = None
    language_endpoint: str = ""

    @classmethod
    def from_env(cls, values: Mapping[str, str] | None = None) -> "AzureSettings":
        values = os.environ if values is None else values
        return cls(
            speech_key=SecretStr(values["AZURE_SPEECH_KEY"])
            if values.get("AZURE_SPEECH_KEY")
            else None,
            speech_region=values.get("AZURE_SPEECH_REGION", ""),
            speech_endpoint=values.get("AZURE_SPEECH_ENDPOINT", ""),
            language_key=SecretStr(values["AZURE_LANGUAGE_KEY"])
            if values.get("AZURE_LANGUAGE_KEY")
            else None,
            language_endpoint=values.get("AZURE_LANGUAGE_ENDPOINT", ""),
        )

    def availability(self) -> dict[str, bool]:
        return {
            "speech": bool(
                self.speech_key and (self.speech_region or self.speech_endpoint)
            ),
            "language": bool(self.language_key and self.language_endpoint),
        }


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> None:
        return None


def https_request(
    url: str, body: bytes, headers: dict[str, str], timeout: float
) -> dict[str, Any]:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.build_opener(NoRedirect()).open(
            request, timeout=timeout
        ) as response:
            value = json.loads(response.read(2 * 1024**2))
    except urllib.error.HTTPError as error:
        raise CloudError(
            f"Azure HTTP {error.code}; check resource, access or quota"
        ) from None
    except (urllib.error.URLError, TimeoutError):
        raise CloudError("Azure connection failed or timed out") from None
    except (ValueError, UnicodeError):
        raise CloudError("Azure returned an invalid JSON response") from None
    if not isinstance(value, dict):
        raise CloudError("Azure returned an invalid response shape")
    return value


class AzureAudioClient:
    def __init__(
        self, settings: AzureSettings, transport: Transport | None = None
    ) -> None:
        self.settings = settings
        self.transport = transport or https_request
        self.live_transport = transport is None
        self.calls = 0

    def _request(
        self, url: str, body: bytes, key: SecretStr, content_type: str
    ) -> dict[str, Any]:
        self.calls += 1
        return self.transport(
            url,
            body,
            {
                "Ocp-Apim-Subscription-Key": key.get_secret_value(),
                "Content-Type": content_type,
                "Accept": "application/json",
            },
            30,
        )

    def transcribe(self, wav: Path) -> dict[str, Any]:
        settings = self.settings
        if not settings.availability()["speech"] or settings.speech_key is None:
            raise CloudError("Azure Speech is not configured")
        if settings.speech_endpoint:
            endpoint = azure_endpoint(settings.speech_endpoint) + "/stt"
        else:
            if not re.fullmatch(r"[a-z0-9-]+", settings.speech_region):
                raise CloudError("invalid Azure Speech region")
            endpoint = azure_endpoint(
                f"https://{settings.speech_region}.stt.speech.microsoft.com"
            )
        started = perf_counter()
        response = self._request(
            endpoint + "/speech/recognition/conversation/cognitiveservices/v1"
            "?language=pt-BR&format=detailed",
            wav.read_bytes(),
            settings.speech_key,
            "audio/wav; codecs=audio/pcm; samplerate=16000",
        )
        status = response.get("RecognitionStatus")
        if status in (
            "NoMatch",
            "InitialSilenceTimeout",
            "BabbleTimeout",
            "EndOfDictation",
        ):
            return {
                "status": "no_match",
                "recognition_status": status,
                "text": "",
                "elapsed_seconds": perf_counter() - started,
            }
        if (
            status != "Success"
            or not isinstance(response.get("NBest"), list)
            or not response["NBest"]
        ):
            raise CloudError("Azure Speech did not return a valid recognition result")
        best = response["NBest"][0]
        if (
            not isinstance(best, dict)
            or not isinstance(best.get("Display"), str)
            or not best["Display"].strip()
        ):
            raise CloudError("Azure Speech returned no usable transcript")
        return {
            "status": "completed",
            "text": best["Display"],
            "confidence": best.get("Confidence"),
            "elapsed_seconds": perf_counter() - started,
            "recognition_status": status,
            "locale": "pt-BR",
        }

    def analyze_text(self, text: str, kind: str) -> dict[str, Any]:
        if kind not in ("SentimentAnalysis", "KeyPhraseExtraction"):
            raise ValueError("unsupported Azure Language task")
        settings = self.settings
        if not settings.availability()["language"] or settings.language_key is None:
            raise CloudError("Azure Language is not configured")
        if not text.strip() or len(text) > 5000:
            raise ValueError("text must contain 1 to 5000 characters")
        endpoint = azure_endpoint(settings.language_endpoint)
        body = {
            "kind": kind,
            "analysisInput": {
                "documents": [{"id": "1", "language": "pt", "text": text}]
            },
            "parameters": {"modelVersion": "latest"},
        }
        started = perf_counter()
        response = self._request(
            endpoint + "/language/:analyze-text?api-version=2023-04-01",
            json.dumps(body).encode(),
            settings.language_key,
            "application/json",
        )
        results = response.get("results", {})
        documents = results.get("documents") if isinstance(results, dict) else None
        if (
            not isinstance(documents, list)
            or len(documents) != 1
            or results.get("errors")
        ):
            raise CloudError("Azure Language did not return a valid document result")
        document = documents[0]
        if not isinstance(document, dict) or document.get("id") != "1":
            raise CloudError("Azure Language document identity mismatch")
        if kind == "SentimentAnalysis":
            if document.get("sentiment") not in (
                "positive",
                "neutral",
                "negative",
                "mixed",
            ):
                raise CloudError("Azure Language returned an invalid sentiment")
            result = {
                "sentiment": document["sentiment"],
                "confidence_scores": document.get("confidenceScores"),
            }
        else:
            phrases = document.get("keyPhrases")
            if not isinstance(phrases, list) or not all(
                isinstance(item, str) for item in phrases
            ):
                raise CloudError("Azure Language returned invalid key phrases")
            result = {"key_phrases": phrases}
        return {
            "status": "completed",
            "task": kind,
            "model_version": results.get("modelVersion"),
            "elapsed_seconds": perf_counter() - started,
            **result,
        }
