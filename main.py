import sys
from telegram.ext import ApplicationBuilder, CommandHandler

import config
from logs.logger import setup_logger
from bot.handlers import start, add_address_handler, list_monitors_handler, remove_monitor_handler
from bot.monitor_loop import setup_monitor_scheduler
from db import init_db

logger = setup_logger("main_entry", "./logs")

def validate_config():
    """
    Validates that critical configuration variables from config.py are loaded.
    """
    # 檢查 config.py 中的變數是否為 None
    if not config.TELEGRAM_TOKEN:
        logger.critical("Missing TELEGRAM_TOKEN in .env (loaded via config.py).")
        sys.exit(1)
        
    if not config.DATABASE_URL:
        logger.critical("Missing DATABASE_URL in .env (loaded via config.py).")
        sys.exit(1)

    return config.TELEGRAM_TOKEN

def main():
    logger.info("Starting Ether.fi Cash Monitor Bot...")
    
    # Initialize database tables
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully.")
    
    # Validate before building app
    token = validate_config()

    try:
        # Use the token from config
        app = ApplicationBuilder().token(token).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("add", add_address_handler))
        app.add_handler(CommandHandler("list", list_monitors_handler))
        app.add_handler(CommandHandler("remove", remove_monitor_handler))

        # 設置監控迴圈（每 5 分鐘檢查一次）
        setup_monitor_scheduler(app)

        logger.info("Bot successfully initialized. Polling started.")
        app.run_polling()

    except Exception as e:
        logger.critical(f"Fatal crash: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()