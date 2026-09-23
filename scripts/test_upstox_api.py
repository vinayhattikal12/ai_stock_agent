import asyncio
import httpx
import urllib.parse
from backend.config import settings

async def test_upstox():
    token = settings.UPSTOX_ACCESS_TOKEN
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "Api-Version": "2.0"
    }
    
    print(f"Testing Upstox token: {token[:15]}...{token[-10:]}")
    
    # 1. Test Profile / User details
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get("https://api.upstox.com/v2/user/profile", headers=headers)
            print(f"Profile API status: {r.status_code}, response: {r.text[:200]}")
        except Exception as e:
            print(f"Profile API err: {e}")
            
        # 2. Test Quotes for Nifty and Stocks
        # Try both formats: NSE_INDEX|Nifty 50 and NSE_EQ|INE467B01029 / NSE_EQ|TCS
        for key in ["NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank", "NSE_EQ|INE467B01029", "NSE_EQ|INE002A01018", "NSE_EQ|TCS"]:
            try:
                r = await client.get(f"https://api.upstox.com/v2/market-quote/quotes?instrument_key={key}", headers=headers)
                print(f"Quote for {key}: {r.status_code}, data: {r.text[:300]}")
            except Exception as e:
                print(f"Quote err for {key}: {e}")

        # 3. Test Historical Candles for TCS and NIFTY
        # Upstox V2 historical-candle: /v2/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}
        for ik in ["NSE_INDEX|Nifty 50", "NSE_EQ|INE467B01029", "NSE_EQ|TCS"]:
            encoded_key = urllib.parse.quote(ik, safe='')
            url = f"https://api.upstox.com/v2/historical-candle/{encoded_key}/day/2026-09-23/2025-09-23"
            try:
                r = await client.get(url, headers=headers)
                print(f"Candle for {ik} ({url}): {r.status_code}, data: {r.text[:300]}")
            except Exception as e:
                print(f"Candle err for {ik}: {e}")

if __name__ == "__main__":
    asyncio.run(test_upstox())
