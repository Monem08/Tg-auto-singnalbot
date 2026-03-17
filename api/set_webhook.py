# একটি নতুন ফাইল 'set_webhook.py' তৈরি করুন
import asyncio
from telegram import Bot
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# আপনার Render URL টি দিন (শেষের '/' ছাড়া)
URL = "https://forex-bot-yx1m.onrender.com/webhook" 

async def set_hook():
    bot = Bot(TOKEN)
    await bot.set_webhook(URL)
    print("Webhook set successfully!")

asyncio.run(set_hook())
