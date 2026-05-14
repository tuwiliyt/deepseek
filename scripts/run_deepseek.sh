#!/usr/bin/env bash
# =============================================================================
# run_deepseek.sh — Launcher Qwen Code CLI + DeepSeek Proxy
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

PROXY_PORT=8088
PROXY_URL="http://127.0.0.1:${PROXY_PORT}/v1"
PROXY_PID_FILE="/tmp/deepseek_proxy_$$.pid"

# ── Locale (wajib untuk Colab) ─────────────────────────────────────────────
unset LC_ALL 2>/dev/null || true
export LANG="C.UTF-8"
export LC_ALL="C.UTF-8"

# ── Bahasa antarmuka Qwen Code CLI ────────────────────────────────────────
export QWEN_CODE_LANG="${QWEN_CODE_LANG:-id}"

# ── Konfigurasi proxy sebagai endpoint OpenAI ─────────────────────────────
export OPENAI_API_KEY="ds-free-via-proxy"
export OPENAI_BASE_URL="${PROXY_URL}"
export QWEN_API_BASE="${PROXY_URL}"
export QWEN_API_KEY="ds-free-via-proxy"

# ── Fungsi cleanup ─────────────────────────────────────────────────────────
cleanup() {
    if [[ -f "$PROXY_PID_FILE" ]]; then
        PROXY_PID=$(cat "$PROXY_PID_FILE")
        kill "$PROXY_PID" 2>/dev/null || true
        rm -f "$PROXY_PID_FILE"
        echo -e "\n[DeepSeek CLI] Proxy dihentikan (PID $PROXY_PID)."
    fi
}
trap cleanup EXIT INT TERM

# ── Pastikan proxy.py ada ─────────────────────────────────────────────────
PROXY_SCRIPT="${PROJECT_DIR}/proxy.py"
if [[ ! -f "$PROXY_SCRIPT" ]]; then
    echo "[ERROR] proxy.py tidak ditemukan di ${PROJECT_DIR}"
    exit 1
fi

# ── Jalankan proxy di background ──────────────────────────────────────────
echo "[DeepSeek CLI] Menjalankan proxy di port ${PROXY_PORT}..."
python3 "$PROXY_SCRIPT" "$PROXY_PORT" > /tmp/deepseek_proxy_$$.log 2>&1 &
echo $! > "$PROXY_PID_FILE"

# Tunggu proxy siap (maks 10 detik)
MAX_WAIT=10
for i in $(seq 1 $MAX_WAIT); do
    if curl -sf "${PROXY_URL}/models" > /dev/null 2>&1; then
        echo "[DeepSeek CLI] Proxy siap (${i}s)."
        break
    fi
    if [[ $i -eq $MAX_WAIT ]]; then
        echo "[ERROR] Proxy tidak kunjung siap. Cek log: /tmp/deepseek_proxy_$$.log"
        cat /tmp/deepseek_proxy_$$.log
        exit 1
    fi
    sleep 1
done

# ── Pindah ke direktori project ───────────────────────────────────────────
cd "$PROJECT_DIR"

# ── Jalankan Qwen Code CLI ────────────────────────────────────────────────
# Workaround Colab: script -q -c menyediakan PTY buatan.
# JANGAN pipe output ke program lain — Qwen Code adalah TUI interaktif,
# piping (|) akan memutus PTY dan respons tidak tampil.

QWEN_ARGS=(
    qwen
    --model "deepseek-chat"
    --auth-type openai
)

# Tambahkan argumen dari command line jika ada
if [[ $# -gt 0 ]]; then
    QWEN_ARGS+=("$@")
fi

echo "[DeepSeek CLI] Memulai Qwen Code CLI → DeepSeek..."
echo "----------------------------------------------------"

script -q -c "$(printf '%q ' "${QWEN_ARGS[@]}")" /dev/null
