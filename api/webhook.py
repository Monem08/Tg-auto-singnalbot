from fastapi import APIRouter, Request, BackgroundTasks
from utils.state import signal_groups, signals_history, copy_trade_users
from utils.config import logger

router = APIRouter()

async def broadcast_signal(bot, signal_text: str, signal_data: dict):
    # Send to Groups
    for chat_id in signal_groups:
        try:
            await bot.send_message(chat_id=chat_id, text=signal_text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to send to {chat_id}: {e}")
            
    # Send to Copy Traders (Simulated MT5 execution notification)
    for user_id in copy_trade_users:
        try:
            await bot.send_message(
                chat_id=user_id, 
                text=f"⚙️ **COPY TRADE EXECUTED**\nPlacing {signal_data['Type']} on {signal_data['Pair']}", 
                parse_mode="Markdown"
            )
        except:
            pass

@router.post("/webhook")
async def tradingview_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Expected JSON format from TradingView:
    {"Pair": "XAUUSD", "Type": "BUY", "Entry": 2045.5, "TP": 2060, "SL": 2035, "Confidence": "95%"}
    """
    bot = request.app.state.bot  # Injected in main.py
    
    try:
        data = await request.json()
        signals_history.append(data)
        
        msg = (
            f"📊 **SIGNAL ALERT**\n\n"
            f"🔹 **Pair:** `{data.get('Pair')}`\n"
            f"🔹 **Type:** `{data.get('Type')}`\n"
            f"🔹 **Entry:** `{data.get('Entry')}`\n"
            f"🔹 **TP:** `{data.get('TP')}`\n"
            f"🔹 **SL:** `{data.get('SL')}`\n"
            f"⚡ **Confidence:** {data.get('Confidence')}"
        )
        
        background_tasks.add_task(broadcast_signal, bot, msg, data)
        return {"status": "success", "message": "Signal processing"}
    except Exception as e:
        logger.error(f"Webhook Error: {e}")
        return {"status": "error"}
