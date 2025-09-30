import os
from telegram.ext import Application, CommandHandler
from google_auth import create_event

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update, context):
    await update.message.reply_text("Xin chào! Gõ /addevent để thêm sự kiện vào Google Calendar.")

async def add_event(update, context):
    try:
        summary = "Test Event"
        description = "Sự kiện tạo bởi Telegram bot"
        start_time = "2025-10-01T10:00:00"
        end_time = "2025-10-01T11:00:00"

        link = create_event(summary, description, start_time, end_time)
        await update.message.reply_text(f"✅ Đã tạo sự kiện: {link}")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addevent", add_event))

    app.run_polling()

if __name__ == "__main__":
    main()
