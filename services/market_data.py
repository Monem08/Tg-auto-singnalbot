async def fetch_prices() -> dict:
    if not TWELVEDATA_API_KEY:
        logger.error("API KEY IS MISSING!") # এটি লগে দেখুন
        return {}
    
    symbols = ",".join(SYMBOLS_MAP.values())
    url = f"https://api.twelvedata.com/price?symbol={symbols}&apikey={TWELVEDATA_API_KEY}"
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)
            data = resp.json()
            
            # Debugging: কি ডাটা আসছে তা লগে প্রিন্ট করুন
            logger.info(f"TwelveData Response: {data}") 
            
            if "code" in data: # TwelveData এরর কোড দিলে এটি ধরবে
                 logger.error(f"TwelveData Error: {data.get('message')}")
                 return {}

            prices = {}
            # ... আগের কোড ...
            return prices
    except Exception as e:
        logger.error(f"Price fetch error: {e}")
        return {}
