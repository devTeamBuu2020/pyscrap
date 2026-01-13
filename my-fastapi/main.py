from fastapi import FastAPI, HTTPException
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

app = FastAPI()

URL = "https://th.investing.com/commodities/gold"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Connection": "keep-alive",
}

def _to_decimal(text: str) -> Decimal:
    """
    Convert text like '2,345.67', '+12.34', '−1.23' safely to Decimal.
    """
    if text is None:
        raise InvalidOperation("empty")
    s = text.strip()
    # Normalize unicode minus to hyphen
    s = s.replace("−", "-")
    # Remove + and thousands separators
    s = s.replace("+", "").replace(",", "")
    return Decimal(s)

@app.get("/")
def root():
    return {"ok": True, "service": "my-fastapi"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/gold")
def gold():
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        # ถ้าโดนบล็อกจะเจอ 403/451 ฯลฯ
        if r.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"Upstream error from Investing: HTTP {r.status_code}"
            )

        soup = BeautifulSoup(r.text, "html.parser")

        price_el = soup.select_one("div[data-test='instrument-price-last']")
        change_el = soup.select_one("span[data-test='instrument-price-change']")

        # ถ้า HTML เปลี่ยน หรือโดนเสิร์ฟหน้าอื่น จะหาไม่เจอ
        if not price_el or not change_el:
            raise HTTPException(
                status_code=502,
                detail="Failed to parse Investing page (selectors not found). "
                       "Page structure may have changed or request was blocked."
            )

        price_text = price_el.get_text(strip=True)
        change_text = change_el.get_text(strip=True)

        try:
            price = _to_decimal(price_text)
            change = _to_decimal(change_text)
        except (InvalidOperation, ValueError):
            raise HTTPException(
                status_code=502,
                detail=f"Failed to parse numbers. price='{price_text}', change='{change_text}'"
            )

        return {
            "symbol": "GOLD",
            "price": float(price),
            "change": float(change),
            "server_time": datetime.now(timezone.utc).isoformat()
        }

    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Timeout fetching Investing")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Request error: {e}")
