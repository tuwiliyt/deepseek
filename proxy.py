"""
proxy.py — Proxy lokal OpenAI-compatible → DeepSeek internal API
================================================================
Cara kerja:
  1. Qwen Code CLI berbicara ke http://localhost:8088/v1  (format OpenAI)
  2. Proxy menerjemahkan request ke format DeepSeek internal
  3. Proxy meneruskan ke https://chat.deepseek.com/api/v0
  4. Response dikembalikan ke CLI dalam format OpenAI (termasuk streaming SSE)

Jalankan:
  python3 proxy.py           # port default 8088
  python3 proxy.py 9090      # port kustom
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import requests
from flask import Flask, Response, jsonify, request

# Tambahkan direktori ini ke path supaya bisa import config
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DEEPSEEK_API_BASE, PROXY_PORT, BROWSER_HEADERS, DEFAULT_TIMEOUT

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_token() -> str:
    env = os.getenv("DEEPSEEK_TOKEN") or os.getenv("DEEPSEEK_USER_TOKEN")
    if env:
        return env

    for cred_path in (
        Path("credentials.json"),
        Path(__file__).resolve().parent / "credentials.json",
    ):
        if not cred_path.exists():
            continue
        data = json.loads(cred_path.read_text(encoding="utf-8"))
        token = (
            data.get("sessions", [{}])[0]
                .get("deepseek_credentials", {})
                .get("user_token")
        )
        if token and token != "PASTE_YOUR_DEEPSEEK_TOKEN_HERE":
            return token

    raise RuntimeError(
        "Token DeepSeek tidak ditemukan di credentials.json atau env DEEPSEEK_TOKEN."
    )


def _map_model(model: str) -> str:
    table = {
        "deepseek-chat":     "deepseek_chat",
        "deepseek-v3":       "deepseek_chat",
        "deepseek-reasoner": "deepseek_r1",
        "deepseek-r1":       "deepseek_r1",
        "deepseek_chat":     "deepseek_chat",
        "deepseek_r1":       "deepseek_r1",
    }
    return table.get((model or "").lower(), "deepseek_chat")


def _ds_headers() -> dict[str, str]:
    return {
        **BROWSER_HEADERS,
        "Authorization": f"Bearer {_load_token()}",
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/v1/models", methods=["GET"])
def list_models():
    """Endpoint wajib agar Qwen Code CLI tidak error saat startup."""
    return jsonify({
        "object": "list",
        "data": [
            {"id": "deepseek-chat",     "object": "model", "owned_by": "deepseek"},
            {"id": "deepseek-reasoner", "object": "model", "owned_by": "deepseek"},
        ],
    })


@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    body = request.get_json(force=True)
    stream = body.get("stream", False)

    ds_payload = {
        "model":       _map_model(body.get("model", "deepseek-chat")),
        "messages":    body.get("messages", []),
        "temperature": body.get("temperature", 0.7),
        "stream":      stream,
    }
    if body.get("max_tokens"):
        ds_payload["max_tokens"] = body["max_tokens"]

    ds_url = f"{DEEPSEEK_API_BASE}/chat/completions"

    # ── Streaming ──────────────────────────────────────────────────────────
    if stream:
        def _generate():
            """
            Parse SSE stream dari DeepSeek baris per baris.
            Masalah utama: Qwen Code CLI mensyaratkan chunk terakhir
            sebelum [DONE] memiliki finish_reason != null.
            DeepSeek internal API kadang mengirim finish_reason: null
            atau stream putus tanpa marker yang benar.
            Fix: track chunk terakhir dan inject finish_reason="stop"
            jika belum ada sebelum mengirim [DONE].
            """
            last_chunk = None
            done_sent  = False

            def flush_finish_reason():
                """Kirim chunk penutup dengan finish_reason='stop' jika perlu."""
                nonlocal last_chunk, done_sent
                if done_sent:
                    return
                if last_chunk is not None:
                    choices = last_chunk.get("choices", [])
                    if choices and choices[0].get("finish_reason") is None:
                        choices[0]["finish_reason"] = "stop"
                        # Pastikan delta tidak kosong agar CLI tidak confused
                        if "delta" in choices[0] and choices[0]["delta"] == {}:
                            choices[0]["delta"] = {"content": ""}
                        yield ("data: " + json.dumps(last_chunk) + "\n\n").encode()
                yield b"data: [DONE]\n\n"
                done_sent = True

            try:
                with requests.post(
                    ds_url,
                    headers=_ds_headers(),
                    json=ds_payload,
                    stream=True,
                    timeout=DEFAULT_TIMEOUT,
                ) as ds_resp:
                    if ds_resp.status_code != 200:
                        err = json.dumps({
                            "error": {"message": ds_resp.text[:500], "type": "deepseek_error"}
                        })
                        yield f"data: {err}\n\n".encode()
                        yield b"data: [DONE]\n\n"
                        return

                    for raw_line in ds_resp.iter_lines():
                        if not raw_line:
                            continue
                        line = raw_line.decode("utf-8", errors="replace")

                        if not line.startswith("data:"):
                            continue

                        data_str = line[5:].strip()

                        # Stream selesai
                        if data_str == "[DONE]":
                            yield from flush_finish_reason()
                            return

                        # Parse chunk JSON
                        try:
                            chunk = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        choices = chunk.get("choices", [])

                        # Jika chunk ini sudah punya finish_reason, kirim langsung
                        # lalu emit [DONE] segera
                        if choices and choices[0].get("finish_reason") is not None:
                            yield ("data: " + json.dumps(chunk) + "\n\n").encode()
                            yield b"data: [DONE]\n\n"
                            done_sent = True
                            return

                        # Chunk biasa — buffer sebagai last_chunk, kirim sekarang
                        last_chunk = chunk
                        yield ("data: " + json.dumps(chunk) + "\n\n").encode()

                # Stream habis tanpa [DONE] eksplisit
                yield from flush_finish_reason()

            except Exception as exc:
                err = json.dumps({"error": {"message": str(exc), "type": "proxy_error"}})
                yield f"data: {err}\n\n".encode()
                if not done_sent:
                    yield b"data: [DONE]\n\n"

        return Response(
            _generate(),
            status=200,
            mimetype="text/event-stream",
            headers={
                "Cache-Control":     "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    # ── Non-streaming ──────────────────────────────────────────────────────
    try:
        ds_resp = requests.post(
            ds_url,
            headers=_ds_headers(),
            json=ds_payload,
            timeout=DEFAULT_TIMEOUT,
        )
        if ds_resp.status_code != 200:
            return (
                jsonify({"error": {"message": ds_resp.text, "type": "deepseek_error"}}),
                ds_resp.status_code,
            )
        return jsonify(ds_resp.json())

    except Exception as exc:
        return jsonify({"error": {"message": str(exc), "type": "proxy_error"}}), 500


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PROXY_PORT
    print(f"[DeepSeek Proxy] Mendengarkan di http://127.0.0.1:{port}/v1")
    print(f"[DeepSeek Proxy] Target upstream : {DEEPSEEK_API_BASE}")
    print("[DeepSeek Proxy] Tekan Ctrl+C untuk berhenti.\n")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
