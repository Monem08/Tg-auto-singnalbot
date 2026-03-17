import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from bot.handlers import (
    start_cmd, price_cmd, alert_cmd, stopalert_cmd,
    analysis_cmd, enable_signals_cmd, disable_signals_cmd,
    live_cmd, stoplive_cmd, copytrade_cmd, button_callback
)
from services.alert_engine import check_alerts_job
from utils.config import TELEGRAM_BOT_TOKEN

async def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is missing!")

    # Telegram Bot App
    ptb_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Handlers
    ptb_app.add_handler(CommandHandler("start", start_cmd))
    ptb_app.add_handler(CommandHandler("price", price_cmd))
    ptb_app.add_handler(CommandHandler("alert", alert_cmd))
    ptb_app.add_handler(CommandHandler("stopalert", stopalert_cmd))
    ptb_app.add_handler(CommandHandler("analysis", analysis_cmd))
    ptb_app.add_handler(CommandHandler("enable_signals", enable_signals_cmd))
    ptb_app.add_handler(CommandHandler("disable_signals", disable_signals_cmd))
    ptb_app.add_handler(CommandHandler("live", live_cmd))
    ptb_app.add_handler(CommandHandler("stoplive", stoplive_cmd))
    ptb_app.add_handler(CommandHandler("copytrade", copytrade_cmd))
    ptb_app.add_handler(CallbackQueryHandler(button_callback))

    # Background Job
    ptb_app.job_queue.run_repeating(check_alerts_job, interval=15)

    # Start Polling (এটিই এখন সবচেয়ে কার্যকর উপায়)
    print("Bot is starting...")
    await ptb_app.initialize()
    await ptb_app.start()
    await ptb_app.updater.start_polling()

    # Bot running
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
