"""
chat.py — Tes cepat koneksi DeepSeek via terminal
=================================================
Jalankan: python3 chat.py
Bukan coding agent; hanya untuk verifikasi token & endpoint bekerja.
"""
from __future__ import annotations

import sys
from deepseek_client import DeepSeekClient


def main() -> None:
    print("=" * 55)
    print("  DeepSeek Free CLI — Tes Chat")
    print("  Ketik 'exit' atau tekan Ctrl+C untuk keluar.")
    print("=" * 55)

    try:
        client = DeepSeekClient()
    except RuntimeError as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)

    print("[OK] Token berhasil dimuat.\n")
    history: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "Kamu adalah asisten coding yang membantu. "
                "Jawab dalam Bahasa Indonesia kecuali diminta lain."
            ),
        }
    ]

    while True:
        try:
            user_input = input("Kamu : ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nKeluar.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "keluar"):
            print("Sampai jumpa!")
            break

        history.append({"role": "user", "content": user_input})

        print("AI   : ", end="", flush=True)
        try:
            # Gunakan streaming supaya respons terasa responsif
            full_reply = ""
            for chunk in client.stream_completion(history):
                print(chunk, end="", flush=True)
                full_reply += chunk
            print()  # newline setelah respons selesai
            history.append({"role": "assistant", "content": full_reply})
        except RuntimeError as e:
            print(f"\n[ERROR] {e}")
            # Hapus pesan user terakhir dari history jika gagal
            history.pop()


if __name__ == "__main__":
    main()
