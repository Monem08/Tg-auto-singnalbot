import asyncio
from openai import AsyncOpenAI
from utils.config import HF_TOKEN, HF_BASE_URL, MODEL_NAME, logger

client = AsyncOpenAI(
    base_url=HF_BASE_URL,
    api_key=HF_TOKEN
)

async def generate_smc_analysis(symbol: str, current_price: float) -> str:
    prompt = f"""
    You are a professional smart money concept (SMC) forex trader.
    Current price of {symbol} is {current_price}.
    Generate a brief, highly professional trading analysis with the following format exactly:
    
    📈 **Trend:** (Bullish/Bearish)
    💧 **Liquidity Zones:** (Prices)
    🎯 **Entry Zone:** (Price range)
    🏁 **Target (TP):** (Price)
    🛑 **Risk Level:** (Low/Med/High)
    
    Keep it concise. Do not add fluff.
    """
    
    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": prompt}],
            max_tokens=300,
            temperature=0.3
        )
        # DeepSeek-R1 sometimes outputs <think> tags. We strip them if present.
        content = response.choices[0].message.content
        if "</think>" in content:
            content = content.split("</think>")[-1].strip()
        return content
    except Exception as e:
        logger.error(f"AI Engine Error: {e}")
        return "❌ AI Analysis currently unavailable."
