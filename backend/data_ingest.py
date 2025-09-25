import yfinance as yf
import requests

def get_stock_price(ticker: str = "AAPL") -> float:
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d", interval="1m")
        if data.empty:
            return None
        return float(data.tail(1)['Close'].iloc[0])
    except Exception as e:
        print(f"[ERROR] get_stock_price failed: {e}")
        return None



def fetch_news(query: str = "AAPL") -> list:
    """
    Fetch latest news headlines for a stock (using Yahoo Finance API).
    Returns a list of titles.
    """
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={query}"
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
        news_items = data.get("news", [])
        return [item.get("title", "") for item in news_items]
    except Exception as e:
        print(f"[ERROR] fetch_news failed: {e}")
        return []
