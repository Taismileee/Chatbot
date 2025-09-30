from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import google_auth

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Xin chào! Gõ /addevent để tạo sự kiện.")

async def add_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        link = google_auth.create_event(
            summary="Họp nhóm",
            description="Thảo luận project",
            start_time="2025-10-02T10:00:00+07:00",
            end_time="2025-10-02T11:00:00+07:00"
        )
        await update.message.reply_text(f"Sự kiện đã tạo: {link}")
    except Exception as e:
        await update.message.reply_text(f"Lỗi: {e}")

def main():
    app = Application.builder().token("TELEGRAM_BOT_TOKEN").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addevent", add_event))
    app.run_polling()

if __name__ == "__main__":
    main()
