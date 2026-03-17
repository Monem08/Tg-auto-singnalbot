import httpx
from utils.config import TWELVEDATA_API_KEY, SYMBOLS_MAP, logger

async def fetch_prices() -> dict:
    if not TWELVEDATA_API_KEY:
        return {}
    
    symbols = ",".join(SYMBOLS_MAP.values())
    url = f"https://api.twelvedata.com/price?symbol={symbols}&apikey={TWELVEDATA_API_KEY}"
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)
            data = resp.json()
            
            prices = {}
            for my_sym, td_sym in SYMBOLS_MAP.items():
                if td_sym in data and "price" in data[td_sym]:
                    prices[my_sym] = float(data[td_sym]["price"])
            return prices
    except Exception as e:
        logger.error(f"Price fetch error: {e}")
        return {}

async def check_smart_features(symbol: str, current_price: float) -> str:
    """Mock smart feature detection (Liquidity Sweep, Breakout)."""
    # In a real scenario, fetch 24h High/Low and compare.
    # We return a simulated response for demonstration of the architecture.
    return "🔍 *Smart Scan*: Minor Liquidity Sweep detected on 15m timeframe. Volume spiking."
