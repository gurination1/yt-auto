import os
import base64
import time
import wave
import urllib.parse
import requests
from pipeline.config import (
    GEMINI_API_KEYS, GEMINI_FLASH, GEMINI_TTS_MODEL, GEMINI_API_BASE
)


class TTSError(Exception):
    pass


class _KeyPool:
    """Round-robin Gemini API key pool. Rotates instantly on 429."""

    def __init__(self, keys: list[str]):
        if not keys:
            raise RuntimeError(
                "No Gemini API keys configured. Set GEMINI_API_KEY or GEMINI_API_KEYS."
            )
        self._keys = keys
        self._idx  = 0

    def current(self) -> str:
        return self._keys[self._idx % len(self._keys)]

    def rotate(self) -> str:
        self._idx += 1
        slot = (self._idx % len(self._keys)) + 1
        print(f"[KeyPool] Rotated to key slot {slot}/{len(self._keys)}")
        return self.current()

    def __len__(self) -> int:
        return len(self._keys)


# One shared pool for all GeminiClient instances that don't pin a key
_shared_pool = _KeyPool(GEMINI_API_KEYS)


def _post_with_rotation(
    url_template: str, payload: dict, timeout: int = 120, quick: bool = False
) -> requests.Response:
    """
    POST using the shared key pool.
    url_template must contain {key}, e.g.:
        "https://.../models/X:generateContent?key={key}"

    Rotation strategy:
      - On 429: immediately rotate to next key (no long wait).
      - After exhausting all keys once: sleep 15 s and retry.
      - Give up after len(pool) * 4 total attempts.
    """
    max_attempts = len(_shared_pool) if quick else len(_shared_pool) * 4
    for attempt in range(max_attempts):
        key  = _shared_pool.current()
        url  = url_template.format(key=key)
        try:
            resp = requests.post(
                url, json=payload, timeout=timeout,
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code == 429:
                print(
                    f"[GeminiClient] 429 on key slot "
                    f"{(_shared_pool._idx % len(_shared_pool)) + 1}. Rotating…"
                )
                _shared_pool.rotate()
                if not quick and (attempt + 1) % len(_shared_pool) == 0:
                    print("[GeminiClient] All keys rate-limited. Waiting 15 s…")
                    time.sleep(15)
                continue
            resp.raise_for_status()
            return resp
        except requests.exceptions.HTTPError:
            raise
        except Exception as exc:
            if attempt == max_attempts - 1:
                raise
            print(f"[GeminiClient] Request error (attempt {attempt+1}): {exc}. Retrying…")
            time.sleep(3)
    raise RuntimeError("Gemini: all keys exhausted. Try again later.")


class GeminiClient:
    """
    Thin wrapper around Gemini REST API.
    Pass api_key to pin a specific key (used by Judge).
    Omit api_key to use the shared rotating pool.
    """

    def __init__(self, api_key: str | None = None):
        self._pinned = api_key

    def _post(self, url_tmpl: str, payload: dict, timeout: int = 120, quick: bool = False) -> requests.Response:
        if self._pinned:
            url = url_tmpl.format(key=self._pinned)
            for attempt in range(5):
                resp = requests.post(
                    url, json=payload, timeout=timeout,
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code == 429:
                    wait = (attempt + 1) * 10
                    print(f"[GeminiClient][pinned] 429. Waiting {wait}s…")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp
            raise RuntimeError("Pinned key is rate-limited after 5 retries.")
        return _post_with_rotation(url_tmpl, payload, timeout, quick)

    # ── Text generation ──────────────────────────────────────────────────────

    def generate_text(
        self,
        prompt: str,
        use_grounding: bool = False,
        temperature: float = 0.8,
        max_tokens: int = 8192,
    ) -> str:
        url = f"{GEMINI_API_BASE}/models/{GEMINI_FLASH}:generateContent?key={{key}}"
        payload: dict = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }
        if use_grounding:
            payload["tools"] = [{"google_search": {}}]

        resp = self._post(url, payload)
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        # Strip any markdown fences Gemini sometimes adds
        for fence in ("```json", "```"):
            if text.startswith(fence):
                text = text[len(fence):]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    # ── Image generation (Pollinations – no key needed) ──────────────────────

    def generate_image(self, prompt: str, width: int = 1080, height: int = 1920) -> bytes:
        encoded = urllib.parse.quote(prompt)
        for model in ["flux", "flux-realism", "turbo"]:
            try:
                url = (
                    f"https://image.pollinations.ai/prompt/{encoded}"
                    f"?width={width}&height={height}&model={model}&nologo=true"
                )
                r = requests.get(url, timeout=90)
                if r.status_code == 200 and len(r.content) > 5000:
                    return r.content
            except Exception as e:
                print(f"[GeminiClient] Pollinations {model} failed: {e}")
        raise RuntimeError("All Pollinations models failed")

    # ── TTS ──────────────────────────────────────────────────────────────────

    def generate_tts(self, text: str, voice: str = "Aoede") -> tuple[bytes, str]:
        """Returns (audio_bytes, mime_type). Raises TTSError on failure."""
        url = f"{GEMINI_API_BASE}/models/{GEMINI_TTS_MODEL}:generateContent?key={{key}}"
        payload = {
            "contents": [{"role": "user", "parts": [
                {"text": f"Say this clearly with natural pacing: {text}"}
            ]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}
                },
            },
        }
        try:
            resp = self._post(url, payload, quick=True)
        except Exception as exc:
            raise TTSError(str(exc)) from exc
        try:
            inline = resp.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
            return base64.b64decode(inline["data"]), inline["mimeType"]
        except Exception as exc:
            raise TTSError(f"TTS response parse error: {exc}") from exc
