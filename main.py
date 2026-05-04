import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import config
from database import init_db
from handlers import start_command, clear_command, detect_ai_command, revisi_command, chat_handler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    init_db()
    logging.info("Database SQLite berhasil diinisialisasi.")

    if not config.TELEGRAM_TOKEN:
        logging.error("🚨 TELEGRAM_TOKEN tidak ditemukan di .env!")
        return

    app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("detect", detect_ai_command))
    app.add_handler(CommandHandler("revisi", revisi_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))

    logging.info("🚀 Bot Akademik Qwen 235B sedang berjalan... Tekan Ctrl+C untuk berhenti.")
    app.run_polling()

if __name__ == '__main__':
    main()
