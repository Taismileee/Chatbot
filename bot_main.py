import os
import threading
import tempfile
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google_auth import make_oauth_flow, save_credentials_for_user, create_event_for_user, load_credentials_for_user
from nlp_helpers import extract_datetime, extract_title, extract_location
from pydub import AudioSegment

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise Exception("Set TELEGRAM_TOKEN or TELEGRAM_BOT_TOKEN environment variable")

app = Flask(__name__)

# ---------------- Telegram handlers ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Chào! Gõ /auth để cấp quyền Google Calendar.')

async def auth_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    redirect_uri = os.environ.get('OAUTH_REDIRECT_URI')
    if not redirect_uri:
        await update.message.reply_text('Chưa cấu hình OAUTH_REDIRECT_URI.')
        return
    flow = make_oauth_flow(redirect_uri)
    auth_url, _ = flow.authorization_url(access_type='offline', include_granted_scopes='true', prompt='consent')
    # pass telegram user id via state
    auth_url_with_state = auth_url + f'&state={user_id}'
    await update.message.reply_text(f'Vui lòng mở link để cấp quyền:\n{auth_url_with_state}')

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    title = extract_title(text)
    dt = extract_datetime(text)
    loc = extract_location(text)

    if not dt:
        await update.message.reply_text('Không tìm thấy ngày/giờ. Vui lòng ghi rõ (ví dụ: "Ngày 3/10/2025 14:00").')
        return

    # default 1 hour duration
    start_iso = dt.isoformat()
    try:
        end_iso = dt.replace(hour=(dt.hour + 1) if dt.hour is not None else dt.hour).isoformat()
    except Exception:
        end_iso = dt.isoformat()

    event_body = {
        'summary': title,
        'location': loc or '',
        'description': text,
        'start': {'dateTime': start_iso},
        'end': {'dateTime': end_iso},
    }

    user_id = update.effective_user.id
    creds = load_credentials_for_user(user_id)
    if not creds:
        await update.message.reply_text('Bạn chưa cấp quyền Google Calendar. Gõ /auth để cấp quyền.')
        return
    try:
        event = create_event_for_user(user_id, event_body)
        await update.message.reply_text(f'Đã tạo sự kiện: {event.get("htmlLink")}')
    except Exception as e:
        await update.message.reply_text('Lỗi khi tạo event: ' + str(e))

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
    await file.download_to_drive(tmp.name)
    # OCR with pytesseract if available
    try:
        from PIL import Image
        import pytesseract
        txt = pytesseract.image_to_string(Image.open(tmp.name), lang='vie+eng')
        await update.message.reply_text('Đã trích text từ ảnh:\n' + (txt[:800] + '...' if len(txt) > 800 else txt))
        # reuse text handler
        fake_update = update
        fake_update.message.text = txt
        await handle_text(fake_update, context)
    except Exception as e:
        await update.message.reply_text('Lỗi OCR: ' + str(e))

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice or update.message.audio
    if not voice:
        await update.message.reply_text('Không có file âm thanh.')
        return
    file = await context.bot.get_file(voice.file_id)
    tmp_ogg = tempfile.NamedTemporaryFile(delete=False, suffix='.ogg')
    await file.download_to_drive(tmp_ogg.name)
    tmp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    try:
        audio = AudioSegment.from_file(tmp_ogg.name)
        audio.export(tmp_wav.name, format='wav')
    except Exception as e:
        await update.message.reply_text('Lỗi chuyển đổi audio: ' + str(e))
        return

    # STT: try VOSK if configured
    try:
        from vosk import Model, KaldiRecognizer
        import wave, json
        MODEL_PATH = os.environ.get('VOSK_MODEL_PATH')
        if not MODEL_PATH:
            await update.message.reply_text('VOSK_MODEL_PATH chưa cấu hình. Nếu muốn dùng Google STT, bạn cần thay phần STT trong mã.')
            return
        wf = wave.open(tmp_wav.name, 'rb')
        model = Model(MODEL_PATH)
        rec = KaldiRecognizer(model, wf.getframerate())
        results = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                results.append(rec.Result())
        results.append(rec.FinalResult())
        text = ' '.join([json.loads(r).get('text','') for r in results])
        await update.message.reply_text('Nội dung STT:\n' + text)
        fake_update = update
        fake_update.message.text = text
        await handle_text(fake_update, context)
    except Exception as e:
        await update.message.reply_text('Lỗi STT: ' + str(e))

# ---------------- Flask OAuth callback ----------------
from flask import Flask, request
app = Flask(__name__)

@app.route('/oauth2callback')
def oauth2callback():
    code = request.args.get('code')
    state = request.args.get('state')
    if not code or not state:
        return 'Missing code/state', 400
    try:
        telegram_user_id = int(state)
    except Exception:
        return 'Invalid state', 400

    redirect_uri = os.environ.get('OAUTH_REDIRECT_URI')
    flow = make_oauth_flow(redirect_uri)
    flow.fetch_token(code=code)
    credentials = flow.credentials
    save_credentials_for_user(telegram_user_id, credentials)
    # notify user on Telegram
    try:
        bot = Bot(token=os.environ.get('TELEGRAM_TOKEN'))
        bot.send_message(chat_id=telegram_user_id, text='Đã cấp quyền Google Calendar thành công!')
    except Exception as e:
        print('Không gửi được tin nhắn Telegram:', e)
    return 'OK. Bạn có thể quay lại Telegram.'

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

def main():
    import asyncio
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('auth', auth_cmd))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))

    application.run_polling()

if __name__ == '__main__':
    main()
