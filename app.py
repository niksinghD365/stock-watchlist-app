from flask import Flask, render_template, request, redirect
import requests
import datetime

app = Flask(__name__)

# ---------------------------
# Config
# ---------------------------
ALPHA_API_KEY = "demo"  # Replace with your AlphaVantage API key
watchlist = {}  # {symbol: {"added_price": float, "added_time": str}}
# ---------------------------

def fetch_alpha(symbol):
    """Primary source: AlphaVantage"""
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_API_KEY}"
        print("URL:", url)
        r = requests.get(url)
        data = r.json()
        print("Fetched data:", data)
        if "Global Quote" in data and "05. price" in data["Global Quote"]:
            price = float(data["Global Quote"]["05. price"])
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            return price, timestamp, "AlphaVantage"
    except:
        pass
    return None, None, None

def fetch_nse(symbol):
    """Fallback source: NSE API"""
    try:
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Referer": f"https://www.nseindia.com/get-quotes/equity?symbol={symbol}"
        }
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers)
        r = session.get(url, headers=headers)
        data = r.json()
        price = float(data["priceInfo"]["lastPrice"])
        timestamp = data["metadata"]["lastUpdateTime"]
        return price, timestamp, "NSE API"
    except:
        pass
    return None, None, None

def get_stock_price(symbol_alpha, symbol_nse):
    # Try AlphaVantage first
    price, timestamp, source = fetch_alpha(symbol_alpha)
    if price is not None:
        return price, timestamp, source

    # Fallback to NSE
    price, timestamp, source = fetch_nse(symbol_nse)
    if price is not None:
        return price, timestamp, source

    return None, None, None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        symbol = request.form["symbol"].upper()
        symbol_alpha = f"{symbol}.BSE"  # Adjust as per your exchange
        symbol_nse = symbol

        price, timestamp, source = get_stock_price(symbol_alpha, symbol_nse)
        if price:
            watchlist[symbol] = {
                "added_price": price,
                "added_time": timestamp,
                "source": source
            }
        return redirect("/")

    # Prepare watchlist with price changes
    display_list = []
    for symbol, info in watchlist.items():
        current_price, timestamp, source = get_stock_price(f"{symbol}.BSE", symbol)
        if current_price:
            change = current_price - info["added_price"]
            change_pct = (change / info["added_price"]) * 100
            display_list.append({
                "symbol": symbol,
                "added_price": info["added_price"],
                "added_time": info["added_time"],
                "current_price": current_price,
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "source": source
            })

    return render_template("index.html", watchlist=display_list)

@app.route("/remove/<symbol>")
def remove(symbol):
    watchlist.pop(symbol.upper(), None)
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
