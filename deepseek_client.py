"""
deepseek_client.py
Klien Python untuk API internal DeepSeek (chat.deepseek.com).
Menggunakan user_token yang diambil dari browser (Application → Local Storage).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Generator

import requests

from config import (
    DEEPSEEK_API_BASE,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT,
    BROWSER_HEADERS,
)


class DeepSeekClient:
    """Klien ringan untuk DeepSeek internal API."""

    def __init__(self, user_token: str | None = None):
        self.user_token = user_token or self._load_token()
        if not self.user_token or self.user_token == "PASTE_YOUR_DEEPSEEK_TOKEN_HERE":
            raise RuntimeError(
                "Token DeepSeek tidak ditemukan.\n"
                "Edit credentials.json dan isi user_token dengan token dari browser.\n"
                "Cara ambil token: F12 → Application → Local Storage → "
                "https://chat.deepseek.com → cari key 'userToken'."
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_token(self) -> str | None:
        # 1. Cek environment variable
        env = os.getenv("DEEPSEEK_TOKEN") or os.getenv("DEEPSEEK_USER_TOKEN")
        if env:
            return env

        # 2. Cek credentials.json (cari dari direktori script atau cwd)
        for path in (
            Path("credentials.json"),
            Path(__file__).resolve().parent / "credentials.json",
        ):
            if not path.exists():
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            token = (
                data.get("sessions", [{}])[0]
                    .get("deepseek_credentials", {})
                    .get("user_token")
            )
            if token:
                return token

        return None

    def _headers(self) -> dict[str, str]:
        return {
            **BROWSER_HEADERS,
            "Authorization": f"Bearer {self.user_token}",
            "Content-Type": "application/json",
        }

    def _map_model(self, model: str) -> str:
        """Normalisasi nama model ke format internal DeepSeek."""
        aliases = {
            "deepseek-chat":       "deepseek_chat",
            "deepseek-v3":         "deepseek_chat",
            "deepseek-reasoner":   "deepseek_r1",
            "deepseek-r1":         "deepseek_r1",
            "deepseek_chat":       "deepseek_chat",
            "deepseek_r1":         "deepseek_r1",
        }
        return aliases.get(model.lower(), "deepseek_chat")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Non-streaming completion. Mengembalikan dict response penuh."""
        payload: dict[str, Any] = {
            "model": self._map_model(model),
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        resp = requests.post(
            f"{DEEPSEEK_API_BASE}/chat/completions",
            headers=self._headers(),
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"DeepSeek API error {resp.status_code}: {resp.text[:500]}"
            )
        return resp.json()

    def stream_completion(
        self,
        messages: list[dict[str, str]],
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
    ) -> Generator[str, None, None]:
        """Streaming completion. Yield setiap potongan teks saat datang."""
        payload: dict[str, Any] = {
            "model": self._map_model(model),
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        with requests.post(
            f"{DEEPSEEK_API_BASE}/chat/completions",
            headers=self._headers(),
            json=payload,
            stream=True,
            timeout=DEFAULT_TIMEOUT,
        ) as resp:
            if resp.status_code != 200:
                raise RuntimeError(
                    f"DeepSeek API error {resp.status_code}: {resp.text[:500]}"
                )
            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                line = raw_line.decode("utf-8", errors="replace")
                if line.startswith("data:"):
                    line = line[5:].strip()
                if line == "[DONE]":
                    break
                try:
                    chunk = json.loads(line)
                    delta = (
                        chunk.get("choices", [{}])[0]
                              .get("delta", {})
                              .get("content", "")
                    )
                    if delta:
                        yield delta
                except json.JSONDecodeError:
                    pass

    def simple_ask(
        self,
        prompt: str,
        system_prompt: str = "Kamu adalah asisten coding yang membantu. Jawab dalam Bahasa Indonesia.",
    ) -> str:
        """Cara cepat tanya satu pertanyaan, kembalikan teks jawaban."""
        resp = self.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": prompt},
            ]
        )
        return (
            resp.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
        )
