"""스캔 대상 종목 리스트를 가져온다 (코스피200 + S&P500).

네트워크 결과는 캐시에 저장해 하루에 한 번만 받아온다.
"""
import json
import re
import time
from datetime import date
from pathlib import Path

import requests

CACHE = Path(__file__).parent / ".cache"
CACHE.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}


def _cached(name, fn):
    """하루 단위로 캐싱한다."""
    f = CACHE / f"{name}-{date.today().isoformat()}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    data = fn()
    f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def _fetch_kospi200():
    """네이버 금융 코스피200 편입종목 (페이지당 10종목, 약 20페이지)."""
    out = {}
    for page in range(1, 25):
        url = f"https://finance.naver.com/sise/entryJongmok.naver?&page={page}"
        r = requests.get(url, headers=UA, timeout=20)
        r.encoding = "euc-kr"
        # <a href="/item/main.naver?code=005930">삼성전자</a>
        pairs = re.findall(r'code=(\d{6})"[^>]*>([^<]+)</a>', r.text)
        if not pairs:
            break
        for code, name in pairs:
            out[f"{code}.KS"] = name.strip()
        time.sleep(0.2)
    return out


def _fetch_sp500():
    """위키피디아 S&P500 구성종목."""
    import io

    import pandas as pd

    r = requests.get(
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        headers=UA,
        timeout=25,
    )
    t = pd.read_html(io.StringIO(r.text))[0]
    out = {}
    for sym, name in zip(t["Symbol"], t["Security"]):
        # BRK.B -> BRK-B (야후 표기)
        out[str(sym).replace(".", "-")] = str(name)
    return out


def load(market="all"):
    """{ticker: 종목명} 딕셔너리를 반환한다. market: kr | us | all"""
    out = {}
    if market in ("kr", "all"):
        out.update(_cached("kospi200", _fetch_kospi200))
    if market in ("us", "all"):
        out.update(_cached("sp500", _fetch_sp500))
    return out


if __name__ == "__main__":
    kr = _cached("kospi200", _fetch_kospi200)
    us = _cached("sp500", _fetch_sp500)
    print(f"코스피200: {len(kr)}종목  예) {list(kr.items())[:3]}")
    print(f"S&P500  : {len(us)}종목  예) {list(us.items())[:3]}")
