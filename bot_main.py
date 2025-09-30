import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from google_auth import create_event
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Các bước hội thoại
SUMMARY, DESCRIPTION, START, END = range(4)

async def start(update, context):
    await update.message.reply_text("Xin chào! Gõ /addevent để thêm sự kiện vào Google Calendar.")

async def add_event_start(update, context):
    await update.message.reply_text("👉 Nhập tên sự kiện:")
    return SUMMARY

async def event_summary(update, context):
    context.user_data["summary"] = update.message.text
    await update.message.reply_text("✍️ Nhập mô tả sự kiện:")
    return DESCRIPTION

async def event_description(update, context):
    context.user_data["description"] = update.message.text
    await update.message.reply_text("📅 Nhập thời gian bắt đầu (VD: 01-10-2025 10:00):")
    return START

def parse_datetime_user(date_str):
    # hỗ trợ dd-mm-YYYY HH:MM hoặc dd/mm/YYYY HH:MM
    for fmt in ("%d-%m-%Y %H:%M", "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

async def event_start(update, context):
    start_str = update.message.text
    start_time = parse_datetime(start_str)

    if not start_time:
        await update.message.reply_text("❌ Sai định dạng! Vui lòng nhập lại (VD: 01-10-2025 10:00):")
        return START

    context.user_data["start_time"] = start_time
    await update.message.reply_text("⏰ Nhập thời gian kết thúc (VD: 01-10-2025 11:00):")
    return END

async def event_end(update, context):
    end_str = update.message.text
    end_dt = parse_datetime_user(end_str)

    if not end_dt:
        await update.message.reply_text("❌ Sai định dạng! Vui lòng nhập lại (VD: 01-10-2025 11:00).")
        return END

    start_dt = context.user_data.get("start_dt")
    if not start_dt:
        await update.message.reply_text("❌ Lỗi nội bộ: không tìm start time. Hãy thử /addevent lại.")
        return ConversationHandler.END

    if end_dt <= start_dt:
        await update.message.reply_text("❌ Thời gian kết thúc phải lớn hơn thời gian bắt đầu. Vui lòng nhập lại.")
        return END

    # chuỗi ISO (không kèm offset) — google_auth sẽ dùng timeZone param
    start_iso = start_dt.strftime("%Y-%m-%dT%H:%M:%S")
    end_iso = end_dt.strftime("%Y-%m-%dT%H:%M:%S")

    try:
        link = create_event(
            context.user_data["summary"],
            context.user_data["description"],
            start_iso,
            end_iso,
            calendar_id=context.user_data.get("calendar_id", "primary")
        )
        await update.message.reply_text(f"✅ Đã tạo sự kiện: {link}")
    except Exception as e:
        # show error detail to user (or summarized)
        await update.message.reply_text(f"❌ Lỗi khi tạo event: {e}")
    return ConversationHandler.END
    
async def cancel(update, context):
    await update.message.reply_text("🚫 Hủy tạo sự kiện.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("addevent", add_event_start)],
        states={
            SUMMARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_summary)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_description)],
            START: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_start)],
            END: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_end)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
