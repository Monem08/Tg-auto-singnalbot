import os
import logging
import asyncio
import httpx
from fastapi import FastAPI
import uvicorn
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes
)

# ----------------- Configuration & State ----------------- #
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment Variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_KEY = os.getenv("TWELVEDATA_API_KEY")
PORT = int(os.getenv("PORT", 8000))

# Allowed Symbols and their TwelveData mappings
SYMBOLS_MAP = {
    "XAUUSD": "XAU/USD",
    "EURUSD": "EUR/USD",
    "GBPUSD": "GBP/USD",
    "BTCUSD": "BTC/USD"
}

# In-memory storage for alerts.
# Format: { chat_id:[ {'symbol': 'XAUUSD', 'target': 3000.0, 'direction': 'up'} ] }
alerts = {}

# FastAPI App initialization
app = FastAPI()

# ----------------- API Helper Functions ----------------- #
async def fetch_prices() -> dict:
    """Fetches real-time prices from TwelveData API."""
    if not API_KEY:
        logger.error("TWELVEDATA_API_KEY is missing!")
        return {}

    td_symbols = ",".join(SYMBOLS_MAP.values())
    url = f"https://api.twelvedata.com/price?symbol={td_symbols}&apikey={API_KEY}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            # Handle TwelveData rate limit / error responses
            if data.get("status") == "error":
                logger.error(f"TwelveData API Error: {data.get('message')}")
                return {}

            prices = {}
            for my_sym, td_sym in SYMBOLS_MAP.items():
                if td_sym in data and "price" in data[td_sym]:
                    prices[my_sym] = float(data[td_sym]["price"])
            return prices
    except Exception as e:
        logger.error(f"Error fetching prices: {e}")
        return {}

async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Checks if the user is an admin in a group chat."""
    if update.effective_chat.type == "private":
        return True
    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    admin_ids =[admin.user.id for admin in admins]
    return update.effective_user.id in admin_ids

# ----------------- Telegram Handlers ----------------- #
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "👋 Welcome to the Forex & Crypto Alert Bot!\n\n"
        "Commands:\n"
        "📈 /price - Get current prices (XAUUSD, EURUSD, GBPUSD, BTCUSD)\n"
        "🔔 /alert <SYMBOL> <PRICE> - Set a price alert (e.g. /alert XAUUSD 3000)\n"
        "🛑 /stopalert - Clear all active alerts in this chat"
    )
    await update.message.reply_text(welcome_msg)

async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prices = await fetch_prices()
    if not prices:
        await update.message.reply_text("❌ Could not fetch prices at the moment. Try again later.")
        return

    msg = "📊 **Current Prices:**\n\n"
    for symbol, price in prices.items():
        # Format dynamically depending on asset (e.g. 4 decimals for forex, 2 for others)
        if symbol in ["EURUSD", "GBPUSD"]:
            msg += f"**{symbol}:** {price:.4f}\n"
        else:
            msg += f"**{symbol}:** {price:.2f}\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

async def alert_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check Admin privileges if used in a group
    if not await is_user_admin(update, context):
        await update.message.reply_text("⛔ Only group administrators can set alerts.")
        return

    try:
        symbol = context.args[0].upper()
        target_price = float(context.args[1])
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Usage: `/alert <SYMBOL> <PRICE>`\nExample: `/alert XAUUSD 3000`", parse_mode="Markdown")
        return

    if symbol not in SYMBOLS_MAP:
        await update.message.reply_text(f"❌ Unsupported symbol. Supported: {', '.join(SYMBOLS_MAP.keys())}")
        return

    prices = await fetch_prices()
    current_price = prices.get(symbol)

    if not current_price:
        await update.message.reply_text("❌ Could not fetch the current price. Please try again.")
        return

    # Determine if we are waiting for the price to go UP or DOWN to hit the target
    direction = 'up' if target_price > current_price else 'down'
    chat_id = update.effective_chat.id

    if chat_id not in alerts:
        alerts[chat_id] = []

    alerts[chat_id].append({
        'symbol': symbol,
        'target': target_price,
        'direction': direction
    })

    await update.message.reply_text(f"✅ Alert successfully set for **{symbol}** at **{target_price}**.\n(Current Price: {current_price})", parse_mode="Markdown")

async def stopalert_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, context):
        await update.message.reply_text("⛔ Only group administrators can stop alerts.")
        return

    chat_id = update.effective_chat.id
    if chat_id in alerts and alerts[chat_id]:
        alerts[chat_id] =[]
        await update.message.reply_text("🛑 All active alerts for this chat have been stopped.")
    else:
        await update.message.reply_text("ℹ️ There are no active alerts in this chat.")

# ----------------- Background Polling Job ----------------- #
async def check_alerts_job(context: ContextTypes.DEFAULT_TYPE):
    """Background job executed every 30 seconds to check prices against alerts."""
    if not alerts:
        return  # Skip API call if no alerts are active

    prices = await fetch_prices()
    if not prices:
        return

    for chat_id, chat_alerts in list(alerts.items()):
        for alert in chat_alerts[:]:  # Iterate over a shallow copy
            symbol = alert['symbol']
            target = alert['target']
            direction = alert['direction']
            current_price = prices.get(symbol)

            if not current_price:
                continue

            triggered = False
            if direction == 'up' and current_price >= target:
                triggered = True
            elif direction == 'down' and current_price <= target:
                triggered = True

            if triggered:
                emoji = "🚨" if symbol == "XAUUSD" else "🔔"
                title = "GOLD ALERT" if symbol == "XAUUSD" else f"{symbol} ALERT"
                
                msg = f"{emoji} **{title}**\n{symbol} reached {target}\n\nCurrent Price: {current_price}"

                try:
                    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                    chat_alerts.remove(alert) # Remove alert once triggered
                except Exception as e:
                    logger.error(f"Failed to send alert to {chat_id}: {e}")

# ----------------- FastAPI Web Route ----------------- #
@app.get("/")
def health_check():
    """Dummy endpoint required by Render to bind the port and keep the service alive."""
    return {"status": "Bot is running", "active_alerts": sum(len(a) for a in alerts.values())}

# ----------------- Application Entry Point ----------------- #
async def main():
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is missing!")

    # Initialize Telegram Bot Application
    application = Application.builder().token(TOKEN).build()

    # Register Command Handlers
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("price", price_cmd))
    application.add_handler(CommandHandler("alert", alert_cmd))
    application.add_handler(CommandHandler("stopalert", stopalert_cmd))

    # Add JobQueue to check prices every 30 seconds
    application.job_queue.run_repeating(check_alerts_job, interval=30)

    # Initialize and start bot polling
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # Start FastAPI server concurrently
    config = uvicorn.Config(app=app, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

    # Graceful shutdown
    await application.updater.stop()
    await application.stop()
    await application.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
