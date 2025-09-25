prev_prices = {}

def detect_anomaly(ticker: str, price: float):
    global prev_prices
    if ticker not in prev_prices:
        prev_prices[ticker] = price
        return None
    
    prev_price = prev_prices[ticker]
    change = (price - prev_price) / prev_price
    prev_prices[ticker] = price

    if abs(change) > 0.05:  # >5% move
        return {"ticker": ticker, "price": price, "change": round(change*100, 2)}
    return None
