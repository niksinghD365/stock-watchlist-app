from flask import Flask, render_template, request, redirect
import requests
from datetime import datetime
import os

app = Flask(__name__)

# Your AlphaVantage API key from environment variable (set in Render or locally)
ALPHAVANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# In-memory watchlist dictionary: symbol -> info
watchlist = {}

def get_stock_price_alpha(symbol):
    """Fetch price from AlphaVantage API."""
    if not ALPHAVANTAGE_API_KEY:
        return None, None, None

    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHAVANTAGE_API_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        quote = data.get("Global Quote") or {}
        price_str = quote.get("05. price")
        if price_str:
            price = float(price_str)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return price, timestamp, "AlphaVantage"
    except Exception as e:
        print(f"Error fetching {symbol} from AlphaVantage: {e}")
    return None, None, None

def get_nse_quote(symbol):
    """Fetch price from NSE using raw requests with proper headers and session."""
    url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol.upper()}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": f"https://www.nseindia.com/get-quotes/equity?symbol={symbol.upper()}",
    }
    try:
        session = requests.Session()
        # Visit homepage first to set cookies
        session.get("https://www.nseindia.com", headers=headers, timeout=5)
        resp = session.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        last_price_str = data.get("priceInfo", {}).get("lastPrice")
        if last_price_str:
            price = float(last_price_str.replace(',', ''))
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return price, timestamp, "NSE India"
    except Exception as e:
        print(f"Error fetching {symbol} from NSE: {e}")
    return None, None, None

def get_stock_price(symbol):
    """Try NSE first, then fallback to AlphaVantage."""
    price, timestamp, source = get_nse_quote(symbol)
    if price:
        return price, timestamp, source

    # Fallback to AlphaVantage
    price, timestamp, source = get_stock_price_alpha(symbol)
    if price:
        return price, timestamp, source

    return None, None, None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        symbol = request.form.get("symbol", "").strip().upper()
        if symbol:
            # Try NSE with symbol directly, fallback to AlphaVantage inside get_stock_price()
            price, timestamp, source = get_stock_price(symbol)
            if price:
                watchlist[symbol] = {
                    "added_price": price,
                    "added_time": timestamp,
                    "source": source
                }
            else:
                print(f"Failed to add {symbol}, no price data.")
        return redirect("/")

    display_list = []
    for symbol, info in watchlist.items():
        current_price, timestamp, source = get_stock_price(symbol)
        if current_price:
            change = current_price - info["added_price"]
            change_pct = (change / info["added_price"]) * 100 if info["added_price"] else 0
            display_list.append({
                "symbol": symbol,
                "added_price": info["added_price"],
                "added_time": info["added_time"],
                "current_price": current_price,
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "source": source,
                "timestamp": timestamp
            })
        else:
            # If unable to fetch current price, still display with dashes
            display_list.append({
                "symbol": symbol,
                "added_price": info["added_price"],
                "added_time": info["added_time"],
                "current_price": None,
                "change": None,
                "change_pct": None,
                "source": info.get("source"),
                "timestamp": None
            })

    return render_template("index.html", watchlist=display_list)

@app.route("/remove/<symbol>")
def remove(symbol):
    watchlist.pop(symbol.upper(), None)
    return redirect("/")

@app.route("/refresh", methods=["POST"])
def refresh():
    # Just redirect to index to refresh prices
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
