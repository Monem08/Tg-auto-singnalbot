import httpx
from utils.config import TWELVEDATA_API_KEY, SYMBOLS_MAP, logger

async def fetch_prices() -> dict:
    if not TWELVEDATA_API_KEY:
        logger.error("API KEY IS MISSING!")
        return {}
    
    # TwelveData মাল্টিপল সিম্বল ফরম্যাট: "XAU/USD,EUR/USD,GBP/USD,BTC/USD"
    symbols = ",".join(SYMBOLS_MAP.values())
    url = f"https://api.twelvedata.com/price?symbol={symbols}&apikey={TWELVEDATA_API_KEY}"
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)
            data = resp.json()
            
            # লগে ডাটাটি দেখুন কি আসছে
            logger.info(f"TwelveData Raw Data: {data}")
            
            prices = {}
            
            # TwelveData মাল্টিপল রিকোয়েস্টে ডাটা এভাবে পাঠায়: 
            # {'XAU/USD': {'price': '...'}, 'EUR/USD': {'price': '...'}, ...}
            
            for my_sym, td_sym in SYMBOLS_MAP.items():
                if td_sym in data:
                    price_str = data[td_sym].get("price")
                    if price_str:
                        prices[my_sym] = float(price_str)
                else:
                    logger.warning(f"Symbol {td_sym} not found in response!")
            
            return prices
    except Exception as e:
        logger.error(f"Price fetch error: {e}")
        return {}
