import os
import requests
from flask import Flask, render_template, request, redirect
from nsetools import Nse
from datetime import datetime

app = Flask(__name__)
nse = Nse()

ALPHAVANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

watchlist = {}

def get_stock_price_alpha(symbol):
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHAVANTAGE_API_KEY}"
        r = requests.get(url, timeout=5)
        data = r.json()
        price_str = data.get("Global Quote", {}).get("05. price")
        if price_str:
            return float(price_str), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "AlphaVantage"
    except Exception as e:
        print(f"AlphaVantage error for {symbol}: {e}")
    return None, None, None

def get_stock_price(symbol):
    # Try NSE first
    try:
        data = nse.get_quote(symbol.lower())
        if data and "lastPrice" in data:
            price = float(data["lastPrice"].replace(',', ''))
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return price, timestamp, "NSE India"
    except Exception as e:
        print(f"Error fetching {symbol} from NSE: {e}")

    # Fallback to AlphaVantage
    if ALPHAVANTAGE_API_KEY:
        return get_stock_price_alpha(symbol)
    else:
        print("No AlphaVantage API key set for fallback.")

    return None, None, None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        symbol = request.form["symbol"].upper()
        # We try with symbol as-is for NSE (lowercase inside get_stock_price)
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

    # Prepare watchlist with price changes
    display_list = []
    for symbol, info in watchlist.items():
        current_price, timestamp, source = get_stock_price(symbol)
        if current_price:
            change = current_price - info["added_price"]
            change_pct = (change / info["added_price"]) * 100
            display_list.append({
                "symbol": symbol,
                "added_price": info["added_price"],
                "added_time": info["added_time"],
                "current_price": current_price,
                "change": round(change, 2),
                "pct": round(change_pct, 2),
                "source": source,
                "timestamp": timestamp
            })
        else:
            # Show old data with None price if fresh fetch fails
            display_list.append({
                "symbol": symbol,
                "added_price": info["added_price"],
                "added_time": info["added_time"],
                "current_price": None,
                "change": None,
                "pct": None,
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
    # Just redirect to "/" GET, prices are fetched live on page load
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
