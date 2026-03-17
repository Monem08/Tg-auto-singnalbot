import asyncio
import uvicorn
from fastapi import FastAPI
from telegram.ext import Application, CommandHandler
from bot.handlers import (
    start_cmd, price_cmd, alert_cmd, stopalert_cmd,
    analysis_cmd, enable_signals_cmd, disable_signals_cmd,
    live_cmd, stoplive_cmd, copytrade_cmd
)
from services.alert_engine import check_alerts_job
from api.webhook import router as webhook_router
from utils.config import TELEGRAM_BOT_TOKEN, PORT

app = FastAPI(title="Trading Bot API")
app.include_router(webhook_router)

@app.get("/")
def health_check():
    return {"status": "Bot is Online and Trading!"}

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

    # 3. Background Jobs (Alerts & Live Stream checking every 15s)
    ptb_app.job_queue.run_repeating(check_alerts_job, interval=15)

    # 4. Inject Bot into FastAPI State for Webhooks
    app.state.bot = ptb_app.bot

    # 5. Start Telegram Polling
    await ptb_app.initialize()
    await ptb_app.start()
    await ptb_app.updater.start_polling()

    # 6. Start FastAPI Server
    config = uvicorn.Config(app, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

    # 7. Shutdown Gracefully
    await ptb_app.updater.stop()
    await ptb_app.stop()
    await ptb_app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
