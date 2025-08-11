import requests
from datetime import datetime
import os

ALPHAVANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")

def get_alphavantage_quote(symbol):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": ALPHAVANTAGE_API_KEY
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        quote = data.get("Global Quote", {})
        price_str = quote.get("05. price")
        if price_str:
            price = float(price_str)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return price, timestamp, "AlphaVantage"
    except Exception as e:
        print(f"Error fetching {symbol} from AlphaVantage: {e}")
    return None, None, None

def get_nse_quote(symbol):
    url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol.upper()}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": f"https://www.nseindia.com/get-quotes/equity?symbol={symbol.upper()}",
        "Connection": "keep-alive",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        session = requests.Session()
        session.headers.update(headers)
        session.get("https://www.nseindia.com", timeout=5)  # to get cookies
        resp = session.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        last_price_str = data.get("priceInfo", {}).get("lastPrice")
        if last_price_str:
            price = float(last_price_str.replace(',', ''))
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return price, timestamp, "NSE India"
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(f"NSE API unauthorized (401) for symbol {symbol}. Likely blocked by NSE.")
        else:
            print(f"Error fetching {symbol} from NSE: {e}")
    except Exception as e:
        print(f"Error fetching {symbol} from NSE: {e}")
    return None, None, None

def get_stock_price(symbol):
    # Try AlphaVantage first (primary)
    price, timestamp, source = get_alphavantage_quote(symbol)
    if price is not None:
        return price, timestamp, source

    # Fallback to NSE
    price, timestamp, source = get_nse_quote(symbol)
    if price is not None:
        return price, timestamp, source

    # Both failed
    return None, None, None
