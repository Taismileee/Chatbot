# Telegram → Google Calendar Bot (template)

**Mục tiêu**: nhận text / ảnh / voice từ Telegram, trích thông tin sự kiện và tạo event trong Google Calendar của người dùng.

## File trong repo
- `bot_main.py` : main application (Telegram + Flask)
- `google_auth.py` : OAuth helpers + Calendar insertion
- `nlp_helpers.py` : simple extraction helpers (date/title/location)
- `requirements.txt` : dependencies
- `Procfile` : để Railway biết cách start app
- `.gitignore`

## Yêu cầu hệ thống
- Python 3.8+
- ffmpeg (system) — để convert audio
- tesseract (nếu dùng OCR với pytesseract)

## Biến môi trường quan trọng
- `TELEGRAM_TOKEN` (bắt buộc) — token từ BotFather
- `OAUTH_REDIRECT_URI` (bắt buộc) — ví dụ: https://<your-railway>.up.railway.app/oauth2callback
- `GOOGLE_CLIENT_SECRET_JSON` (bắt buộc) — nội dung JSON file `client_secret.json` từ Google Cloud (paste nguyên nội dung JSON vào biến env)
- `VOSK_MODEL_PATH` (tùy chọn) — đường dẫn model VOSK nếu dùng STT offline

## Chạy local (test)
1. Tạo virtualenv & cài dependency:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Dùng `ngrok` để expose local port:
   ```bash
   ngrok http 5000
   ```
   Lấy URL `https://xxxx.ngrok.io` và set `OAUTH_REDIRECT_URI` = `https://xxxx.ngrok.io/oauth2callback` trong Google Cloud OAuth client và trong env.
3. Set env var `TELEGRAM_TOKEN` và `GOOGLE_CLIENT_SECRET_JSON`.
4. Chạy:
   ```bash
   python bot_main.py
   ```
5. Trong Telegram chat với bot: `/auth` → mở link → grant permission → send event text.

## Deploy Railway (tóm tắt)
- Push repo lên GitHub
- Railway: New Project → Deploy from GitHub → chọn repo
- Add env vars on Railway: `TELEGRAM_TOKEN`, `OAUTH_REDIRECT_URI`, `GOOGLE_CLIENT_SECRET_JSON`, (optional) `VOSK_MODEL_PATH`
- Deploy → copy app URL → update OAuth redirect in Google Cloud to `https://<railway>/oauth2callback`
