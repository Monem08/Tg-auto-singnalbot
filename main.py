import asyncio
import uvicorn
import os
from fastapi import FastAPI
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from bot.handlers import (
    start_cmd, price_cmd, alert_cmd, stopalert_cmd,
    analysis_cmd, enable_signals_cmd, disable_signals_cmd,
    live_cmd, stoplive_cmd, copytrade_cmd, button_callback
)
from services.alert_engine import check_alerts_job
from api.webhook import router as webhook_router
from utils.config import TELEGRAM_BOT_TOKEN, PORT

app = FastAPI(title="Trading Bot API")
app.include_router(webhook_router)

@app.get("/")
def health_check():
    return {"status": "Bot is Online!"}

async def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is missing!")

    # 1. Initialize Telegram Bot
    ptb_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # 2. Add Handlers
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

    # 3. Background Jobs
    ptb_app.job_queue.run_repeating(check_alerts_job, interval=15)

    # 4. Inject Bot into FastAPI State
    app.state.bot = ptb_app.bot

    # --- ফিক্সড পার্ট: এখানে polling সরিয়ে ফেলে শুধু bot চালু করা হয়েছে ---
    await ptb_app.initialize()
    await ptb_app.start()

    # 5. Start FastAPI Server
    config = uvicorn.Config(app, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

    # 6. Shutdown Gracefully
    await ptb_app.stop()
    await ptb_app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
