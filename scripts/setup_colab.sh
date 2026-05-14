#!/usr/bin/env bash
# =============================================================================
# setup_colab.sh — Setup otomatis DeepSeek Free CLI di Google Colab
# =============================================================================
# Jalankan sekali di terminal Colab:
#   chmod +x setup_colab.sh && bash setup_colab.sh
# Kemudian isi token di credentials.json, lalu:
#   ./scripts/run_deepseek.sh
# =============================================================================

set -e

WORK_DIR="/content/apula"

echo "======================================================="
echo "  DeepSeek Free CLI — Setup Google Colab"
echo "======================================================="

# ── 1. Buat direktori kerja ───────────────────────────────────────────────
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"
echo "[1/8] Direktori kerja: $WORK_DIR"

# ── 2. Paket sistem ───────────────────────────────────────────────────────
echo "[2/8] Install paket sistem (git, curl, nodejs)..."
apt-get update -qq
apt-get install -y -qq git curl python3-venv bsdutils > /dev/null

# Install Node.js 22 jika belum ada atau versinya lama
if ! node --version 2>/dev/null | grep -q "^v2[0-9]"; then
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - > /dev/null 2>&1
    apt-get install -y -qq nodejs > /dev/null
fi
echo "    Node $(node -v) | npm $(npm -v)"

# ── 3. Clone repo ─────────────────────────────────────────────────────────
echo "[3/8] Clone deepseek_free_cli..."
if [[ -d "deepseek_free_cli/.git" ]]; then
    echo "    Repo sudah ada, skip clone."
else
    # Ganti URL ini dengan URL repo kamu sendiri setelah upload ke GitHub
    git clone https://github.com/Staks-sor/qwen_free_cli.git deepseek_free_cli_base
    # Salin file dari repo ini (hardcoded files sudah ada di deepseek_free_cli/)
    # Untuk sementara, asumsikan user sudah meng-upload deepseek_free_cli/ sendiri
    echo "    Catatan: Pastikan folder deepseek_free_cli/ sudah ada di $WORK_DIR"
fi

cd "$WORK_DIR/deepseek_free_cli" 2>/dev/null || {
    echo "[ERROR] Folder deepseek_free_cli tidak ditemukan."
    echo "        Upload folder ini ke Colab lalu jalankan ulang setup ini."
    exit 1
}

# ── 4. Install Qwen Code CLI (npm) ───────────────────────────────────────
echo "[4/8] Install Qwen Code CLI..."
npm install -g @qwen-code/qwen-code@latest --quiet 2>/dev/null
echo "    qwen $(qwen --version 2>/dev/null || echo '(versi tidak tersedia)')"

# ── 5. Python virtual environment ────────────────────────────────────────
echo "[5/8] Buat virtual environment Python..."
if [[ ! -d ".venv" ]]; then
    python3 -m venv .venv --without-pip
    source .venv/bin/activate
    curl -s https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
    python /tmp/get-pip.py --quiet
else
    source .venv/bin/activate
    echo "    .venv sudah ada, skip."
fi
echo "    Python: $(python --version)"

# ── 6. Install dependency Python ─────────────────────────────────────────
echo "[6/8] Install dependency Python..."
pip install -q -r requirements.txt
echo "    Selesai."

# ── 7. Locale ─────────────────────────────────────────────────────────────
echo "[7/8] Set locale..."
unset LC_ALL 2>/dev/null || true
export LANG="C.UTF-8"
export LC_ALL="C.UTF-8"

# ── 8. Permission script ──────────────────────────────────────────────────
echo "[8/8] Set permission skrip..."
chmod +x scripts/run_deepseek.sh

# ── Selesai ───────────────────────────────────────────────────────────────
echo ""
echo "======================================================="
echo "  SETUP SELESAI!"
echo "======================================================="
echo ""
echo "  Langkah selanjutnya:"
echo ""
echo "  1. Ambil token DeepSeek dari browser:"
echo "     Buka chat.deepseek.com → Login → F12"
echo "     → Application → Local Storage"
echo "     → https://chat.deepseek.com → cari key 'userToken'"
echo ""
echo "  2. Isi token di credentials.json:"
echo "     nano $WORK_DIR/deepseek_free_cli/credentials.json"
echo ""
echo "  3. (Opsional) Tes koneksi dulu:"
echo "     cd $WORK_DIR/deepseek_free_cli && python3 chat.py"
echo ""
echo "  4. Jalankan Coding Agent:"
echo "     ./scripts/run_deepseek.sh"
echo ""
echo "======================================================="
