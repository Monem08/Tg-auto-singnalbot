from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard():
    keyboard = [[
            InlineKeyboardButton("📈 Prices", callback_data="btn_prices"),
            InlineKeyboardButton("🤖 AI Analysis", callback_data="btn_analysis")
        ],[
            InlineKeyboardButton("🚨 My Alerts", callback_data="btn_alerts"),
            InlineKeyboardButton("📊 Signals", callback_data="btn_signals")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
