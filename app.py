from flask import Flask, render_template, request, redirect
from nsetools import Nse
from datetime import datetime

app = Flask(__name__)
nse = Nse()

# In-memory watchlist (resets if app restarts on Render free plan)
watchlist = {}


def get_stock_price(symbol):
    """
    Fetches stock price using NSE India via nsetools.
    """
    try:
        # NSE expects lowercase stock codes (e.g., 'reliance', 'tcs')
        data = nse.get_quote(symbol.lower())

        if not data or 'lastPrice' not in data:
            return None, None, None

        # Remove commas from price string and convert to float
        price = float(data['lastPrice'].replace(',', ''))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return price, timestamp, "NSE India"
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None, None, None


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        symbol = request.form["symbol"].upper()

        price, timestamp, source = get_stock_price(symbol)
        if price:
            watchlist[symbol] = {
                "added_price": price,
                "added_time": timestamp,
                "source": source
            }
        return redirect("/")

    # Prepare watchlist with updated prices
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
                "change_pct": round(change_pct, 2),
                "source": source
            })

    return render_template("index.html", watchlist=display_list)


@app.route("/remove/<symbol>")
def remove(symbol):
    watchlist.pop(symbol.upper(), None)
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
