# config.py - Konfigurasi DeepSeek Free CLI
# Endpoint internal DeepSeek (dari sesi browser, bukan API resmi)
# PENTING: endpoint asli adalah /chat/completion (tanpa 's')
# bukan /chat/completions seperti OpenAI standard
DEEPSEEK_API_BASE      = "https://chat.deepseek.com/api/v0"
DEEPSEEK_CHAT_ENDPOINT = f"{DEEPSEEK_API_BASE}/chat/completion"

# Endpoint proxy lokal yang dijalankan oleh proxy.py
# Qwen Code CLI akan terhubung ke sini
PROXY_HOST          = "127.0.0.1"
PROXY_PORT          = 8088
PROXY_BASE_URL      = f"http://{PROXY_HOST}:{PROXY_PORT}/v1"

# Model tersedia di DeepSeek web internal
# "deepseek_chat"   → DeepSeek-V3 (chat umum, cepat)
# "deepseek_r1"     → DeepSeek-R1 (reasoning/thinking, lambat)
DEFAULT_MODEL       = "deepseek_chat"

DEFAULT_TEMPERATURE = 0.7
DEFAULT_TIMEOUT     = 120   # detik

# Header tambahan supaya request mirip browser asli
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Origin":  "https://chat.deepseek.com",
    "Referer": "https://chat.deepseek.com/",
    "Accept":  "application/json",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}
