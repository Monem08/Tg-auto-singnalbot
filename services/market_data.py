async def fetch_prices() -> dict:
    if not TWELVEDATA_API_KEY:
        return {}
    
    symbols = "XAU/USD,EUR/USD,GBP/USD,BTC/USD"
    url = f"https://api.twelvedata.com/price?symbol={symbols}&apikey={TWELVEDATA_API_KEY}"
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)
            data = resp.json()
            
            # লগে ডাটাটি দেখুন কি আসছে
            logger.info(f"TwelveData Raw Data: {data}")
            
            prices = {}
            # TwelveData সাধারণত এরকম রেসপন্স দেয়: {'XAU/USD': {'price': '2000.00'}, ...}
            # অথবা মাল্টিপল সিম্বল দিলে সরাসরি: {'XAU/USD': {'price': '...'}, ...}
            
            for my_sym, td_sym in SYMBOLS_MAP.items():
                if td_sym in data:
                    prices[my_sym] = float(data[td_sym].get("price", 0))
                elif my_sym in data: # যদি সরাসরি সিম্বল থাকে
                    prices[my_sym] = float(data[my_sym].get("price", 0))
            
            return prices
    except Exception as e:
        logger.error(f"Price fetch error: {e}")
        return {}
