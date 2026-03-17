yimport asyncio
from telegram import Update
from telegram.ext import ContextTypes
from bot.keyboards import main_menu_keyboard
from services.market_data import fetch_prices, check_smart_features
from services.ai_engine import generate_smc_analysis
from utils.state import alerts_db, live_streams, signal_groups, copy_trade_users, signals_history
from utils.config import SYMBOLS_MAP

# --- 1. Startup & Animation ---
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ `[25%] Initializing Bot...`", parse_mode="Markdown")
    await asyncio.sleep(0.8)
    await msg.edit_text("⏳ `[50%] Loading Market Data...`", parse_mode="Markdown")
    await asyncio.sleep(0.8)
    await msg.edit_text("⏳ `[75%] Connecting to Liquidity Engine...`", parse_mode="Markdown")
    await asyncio.sleep(0.8)
    
    welcome = (
        "✅ **SYSTEM READY**\n\n"
        "Welcome to the **Pro SMC Trading Bot** 🤖🏦\n"
        "Use the menu below or commands to navigate."
    )
    await msg.edit_text(welcome, parse_mode="Markdown", reply_markup=main_menu_keyboard())

# --- 2. Price System ---
async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prices = await fetch_prices()
    if not prices:
        return await update.message.reply_text("❌ Price feed offline.")
    
    res = "📊 **LIVE MARKET PRICES**\n\n"
    for sym, price in prices.items():
        res += f"🔸 **{sym}**: `{price}`\n"
    await update.message.reply_text(res, parse_mode="Markdown")

# --- 3. Alert System ---
async def alert_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sym = context.args[0].upper()
        target = float(context.args[1])
    except:
        return await update.message.reply_text("⚠️ Usage: `/alert XAUUSD 2050`", parse_mode="Markdown")
    
    if sym not in SYMBOLS_MAP:
        return await update.message.reply_text("❌ Unsupported symbol.")

    prices = await fetch_prices()
    curr = prices.get(sym)
    if not curr: return await update.message.reply_text("❌ Cannot fetch current price.")

    direction = 'up' if target > curr else 'down'
    chat_id = update.effective_chat.id
    alerts_db.setdefault(chat_id,[]).append({'symbol': sym, 'price': target, 'direction': direction})
    
    await update.message.reply_text(f"✅ Alert set: **{sym}** at **{target}**", parse_mode="Markdown")

async def stopalert_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    alerts_db[chat_id] =[]
    await update.message.reply_text("🛑 All alerts cleared.")

# --- 5. AI Analysis ---
async def analysis_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sym = context.args[0].upper()
    except:
        return await update.message.reply_text("⚠️ Usage: `/analysis XAUUSD`", parse_mode="Markdown")

    prices = await fetch_prices()
    curr = prices.get(sym)
    
    msg = await update.message.reply_text(f"🧠 DeepSeek R1 analyzing **{sym}**...", parse_mode="Markdown")
    analysis = await generate_smc_analysis(sym, curr)
    smart_scan = await check_smart_features(sym, curr)
    
    final_text = f"🏦 **SMC AI ANALYSIS: {sym}**\n\n{analysis}\n\n{smart_scan}"
    await msg.edit_text(final_text, parse_mode="Markdown")

# --- 6. Group Admin System ---
async def enable_signals_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private": return
    signal_groups.add(update.effective_chat.id)
    await update.message.reply_text("✅ Group Signals Enabled!")

async def disable_signals_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    signal_groups.discard(update.effective_chat.id)
    await update.message.reply_text("🛑 Group Signals Disabled.")

# --- 7. Live Price Stream ---
async def live_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sym = context.args[0].upper()
    except:
        return await update.message.reply_text("⚠️ Usage: `/live XAUUSD`", parse_mode="Markdown")

    chat_id = update.effective_chat.id
    msg = await update.message.reply_text(f"🔴 Starting Live Stream for {sym}...")
    live_streams[chat_id] = {'message_id': msg.message_id, 'symbol': sym}

async def stoplive_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in live_streams:
        del live_streams[chat_id]
        await update.message.reply_text("🛑 Live stream stopped.")

# --- 8. Copy Trade System ---
async def copytrade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        state = context.args[0].lower()
    except:
        return await update.message.reply_text("⚠️ Usage: `/copytrade on` or `/copytrade off`")

    user_id = update.effective_user.id
    if state == "on":
        copy_trade_users.add(user_id)
        await update.message.reply_text("🚀 Copy Trading (Simulation) ENABLED.")
    else:
        copy_trade_users.discard(user_id)
        await update.message.reply_text("🛑 Copy Trading DISABLED.")




async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # এটি বাটনের লোডিং এনিমেশন বন্ধ করবে
    
    if query.data == "btn_prices":
        prices = await fetch_prices()
        if not prices:
            await query.message.reply_text("❌ Price feed offline. Check API Key.")
            return
        res = "📊 **LIVE MARKET PRICES**\n\n"
        for sym, price in prices.items():
            res += f"🔸 **{sym}**: `{price}`\n"
        await query.message.reply_text(res, parse_mode="Markdown")
        
    elif query.data == "btn_analysis":
        await query.message.reply_text("🤖 **AI Analysis:**\nTo get deep analysis, please type the command manually like this:\n`/analysis XAUUSD`", parse_mode="Markdown")
        
    elif query.data == "btn_alerts":
        await query.message.reply_text("🚨 **Alert System:**\nTo set an alert, type:\n`/alert XAUUSD 2050`\n\nTo clear alerts, type:\n`/stopalert`", parse_mode="Markdown")
        
    elif query.data == "btn_signals":
        await query.message.reply_text("📊 **Signals:**\nBot is ready to receive signals from TradingView Webhook!", parse_mode="Markdown")
