# server.py
from fastapi import FastAPI
from decimal import Decimal
from datetime import datetime
import requests
from bs4 import BeautifulSoup

app = FastAPI()

URL = "https://th.investing.com/commodities/gold"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}

@app.get("/")
def root():
    return {"ok": True, "service": "my-fastapi"}

@app.get("/health")
def health():
    return {"status": "ok"}
    
@app.get("/gold")
def gold():
    r = requests.get(URL, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    price = soup.select_one("div[data-test='instrument-price-last']").text
    change = soup.select_one("span[data-test='instrument-price-change']").text

    price = Decimal(price.replace(",", ""))
    change = Decimal(change.replace("+", "").replace(",", ""))

    return {
        "symbol": "XAUUSD",
        "price": float(price),
        "change": float(change),
        "server_time": datetime.utcnow().isoformat()
    }
