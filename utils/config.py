import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("TradingBot")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY")
PORT = int(os.getenv("PORT", 8000))

# Hugging Face Router for DeepSeek
HF_BASE_URL = "https://router.huggingface.co/v1"
MODEL_NAME = "deepseek-ai/DeepSeek-R1"

SYMBOLS_MAP = {
    "XAUUSD": "XAU/USD",
    "EURUSD": "EUR/USD",
    "GBPUSD": "GBP/USD",
    "BTCUSD": "BTC/USD"
}
