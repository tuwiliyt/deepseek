# DeepSeek Free CLI — Panduan Lengkap (Google Colab)

Modifikasi dari [qwen_free_cli](https://github.com/Staks-sor/qwen_free_cli) untuk menggunakan **DeepSeek** sebagai backend, lengkap dengan workaround Google Colab Terminal.

---

## Cara Kerja

```
Qwen Code CLI
  → http://localhost:8088/v1   (proxy lokal, format OpenAI)
    → proxy.py                 (menerjemahkan format)
      → https://chat.deepseek.com/api/v0  (DeepSeek internal API)
        → user_token dari browser kamu
```

Kamu tidak perlu API key berbayar. Cukup ambil token dari sesi browser DeepSeek.

---

## Langkah 1 — Ambil Token DeepSeek dari Browser

1. Buka [chat.deepseek.com](https://chat.deepseek.com) dan **login**
2. Tekan **F12** → tab **Application**
3. Di panel kiri: **Local Storage** → `https://chat.deepseek.com`
4. Cari key **`userToken`**
5. Salin nilainya (panjang, dimulai dengan huruf/angka)

> ⚠️ Token akan kadaluarsa saat kamu logout dari browser. Ambil ulang jika perlu.

---

## Langkah 2 — Setup di Google Colab Terminal

Buka terminal Colab (`Runtime → Open Terminal` atau ekstensi terminal).

### 2a. Upload folder ini ke Colab

Dari panel file Colab, upload folder `deepseek_free_cli/` ke `/content/apula/`.

### 2b. Jalankan setup otomatis

```bash
cd /content/apula/deepseek_free_cli
chmod +x scripts/setup_colab.sh
bash scripts/setup_colab.sh
```

Script ini akan:
- Install Node.js 22, git, curl
- Install `@qwen-code/qwen-code` (Qwen Code CLI via npm)
- Buat virtual environment Python
- Install dependency (`flask`, `requests`)
- Set permission script

---

## Langkah 3 — Isi Token

```bash
nano /content/apula/deepseek_free_cli/credentials.json
```

Ubah isi file menjadi:

```json
{
  "sessions": [
    {
      "deepseek_credentials": {
        "user_token": "TOKEN_DEEPSEEK_KAMU_DI_SINI"
      }
    }
  ]
}
```

Simpan: `Ctrl+O` → Enter → `Ctrl+X`

Validasi:
```bash
python3 -m json.tool credentials.json
```

---

## Langkah 4 — Tes Koneksi (Opsional)

Sebelum menjalankan coding agent, tes dulu koneksi lewat chat sederhana:

```bash
cd /content/apula/deepseek_free_cli
source .venv/bin/activate
python3 chat.py
```

Kalau muncul respons dari AI, berarti token dan koneksi sudah benar.

---

## Langkah 5 — Jalankan Coding Agent

```bash
cd /content/apula/deepseek_free_cli
source .venv/bin/activate
./scripts/run_deepseek.sh
```

Contoh perintah ke agent:

```
Jelaskan struktur proyek ini.
```

```
Buat folder ./demo dan file ./demo/hello.py yang mencetak "Halo dari DeepSeek!".
```

```
Buat fungsi Python untuk menghitung fibonacci secara rekursif.
```

### Mode one-shot (satu perintah langsung):

```bash
./scripts/run_deepseek.sh "jawab satu kata: tes" --output-format text
```

---

## Pilihan Model

Edit `credentials.json` tidak perlu diubah, tapi kamu bisa ganti model di `run_deepseek.sh`:

| Model | Nama internal | Deskripsi |
|-------|---------------|-----------|
| `deepseek-chat` | `deepseek_chat` | DeepSeek-V3, cepat, bagus untuk coding |
| `deepseek-reasoner` | `deepseek_r1` | DeepSeek-R1, lambat tapi lebih analitis |

Ubah di `run_deepseek.sh` baris:
```bash
QWEN_ARGS=(
    qwen
    --model "deepseek-chat"   # ← ganti ke deepseek-reasoner untuk R1
    ...
)
```

---

## Struktur File

```
deepseek_free_cli/
├── credentials.json       ← Token DeepSeek kamu (jangan di-push ke GitHub!)
├── config.py              ← Konfigurasi endpoint & model
├── deepseek_client.py     ← Klien Python untuk DeepSeek API
├── proxy.py               ← Proxy lokal OpenAI-compatible → DeepSeek
├── chat.py                ← Tes chat sederhana
├── requirements.txt       ← flask, requests
├── DEEPSEEK.md            ← Aturan untuk coding agent
├── .qwen/
│   └── settings.json      ← Konfigurasi Qwen Code CLI
└── scripts/
    ├── run_deepseek.sh    ← Script utama (jalankan ini!)
    └── setup_colab.sh     ← Setup otomatis untuk Colab
```

---

## Troubleshooting

### ❌ "Token DeepSeek tidak ditemukan"
→ Pastikan `credentials.json` sudah diisi dengan token yang benar dan bukan placeholder.

### ❌ Proxy tidak kunjung siap
→ Cek log: `cat /tmp/deepseek_proxy_*.log`
→ Pastikan port 8088 tidak dipakai proses lain: `lsof -i :8088`

### ❌ `qwen: command not found`
→ Npm global path belum di PATH. Jalankan:
```bash
export PATH="$(npm bin -g):$PATH"
```

### ❌ Error `ru_RU.UTF-8` locale
→ Sudah ditangani otomatis oleh `run_deepseek.sh` (memaksa `C.UTF-8`).

### ❌ Token expired / 401 Unauthorized
→ Token dari browser sudah kadaluarsa. Login ulang ke chat.deepseek.com, ambil token baru dari Local Storage.

### ❌ Qwen CLI meminta Qwen OAuth
→ Jangan jalankan `qwen` langsung. Selalu pakai `./scripts/run_deepseek.sh`.

---

## Keamanan

- **Jangan commit** `credentials.json` dengan token asli ke Git.
- File `.gitignore` sudah menyertakan `credentials.json`.
- Token hanya berlaku selama sesi browser aktif.

---

## Tentang Pendekatan Ini

Repo ini menggunakan Qwen Code CLI (`@qwen-code/qwen-code`) sebagai coding agent karena:
- Open source dan gratis
- Support OpenAI-compatible API
- Punya fitur lengkap (edit file, baca direktori, jalankan command)

DeepSeek dijadikan backend melalui proxy lokal yang menerjemahkan format OpenAI ↔ DeepSeek internal.
