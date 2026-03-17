from telegram.ext import ContextTypes
from services.market_data import fetch_prices
from utils.state import alerts_db, live_streams
from utils.config import logger

async def check_alerts_job(context: ContextTypes.DEFAULT_TYPE):
    prices = await fetch_prices()
    if not prices: return

    # Check Alerts
    for chat_id, alerts in list(alerts_db.items()):
        for alert in alerts[:]:
            sym = alert['symbol']
            target = alert['price']
            dir = alert['direction']
            curr = prices.get(sym)

            if not curr: continue

            if (dir == 'up' and curr >= target) or (dir == 'down' and curr <= target):
                msg = f"🚨 **ALERT TRIGGERED**\n\n**{sym}** reached **{target}**!\nCurrent: {curr}"
                await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                alerts.remove(alert)

    # Update Live Streams
    for chat_id, stream_data in list(live_streams.items()):
        sym = stream_data['symbol']
        curr = prices.get(sym)
        if curr:
            msg = f"🔴 **LIVE PRICE STREAM**\n\n**{sym}:** `{curr}`\n_Updating every 15s..._"
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id, message_id=stream_data['message_id'],
                    text=msg, parse_mode="Markdown"
                )
            except Exception:
                pass # Ignore "Message is not modified" errors
