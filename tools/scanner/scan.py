"""코스피200 + S&P500을 훑어 최근 발생한 차트 패턴 후보를 찾는다.

  python3 scan.py                 # 전체(한국+미국), 최근 5거래일 신호
  python3 scan.py --market kr     # 한국만
  python3 scan.py --days 3        # 최근 3거래일만
  python3 scan.py --pattern 골든크로스 갭상승
  python3 scan.py --refresh       # 시세 캐시 무시하고 새로 받기

결과는 report/ 아래 HTML로 저장된다. 탐지는 기계적 규칙이라 오탐이 섞이므로,
차트를 눈으로 확인할 후보 목록으로만 쓴다. 매매 신호가 아니다.
"""
import argparse
import pickle
import sys
import time
import warnings
from datetime import date, datetime, timedelta
from pathlib import Path

warnings.filterwarnings("ignore")

import pandas as pd
import yfinance as yf

import universe
from detectors import DETECTORS

BASE = Path(__file__).parent
CACHE = BASE / ".cache"
REPORT = BASE / "report"
CACHE.mkdir(exist_ok=True)
REPORT.mkdir(exist_ok=True)

SITE = "https://byun-jingyu.github.io/Stock_Playbook"


# ────────────────────────────── 시세 수집 ──────────────────────────────
def fetch_prices(tickers, refresh=False, chunk=40):
    """야후에서 2년치 일봉을 받아 {ticker: DataFrame}으로 돌려준다. 하루 단위 캐시."""
    cache_file = CACHE / f"prices-{date.today().isoformat()}.pkl"
    if cache_file.exists() and not refresh:
        data = pickle.loads(cache_file.read_bytes())
        missing = [t for t in tickers if t not in data]
        if not missing:
            print(f"  캐시 사용: {len(data)}종목 ({cache_file.name})")
            return data
    else:
        data = {}
        missing = list(tickers)

    start = (datetime.now() - timedelta(days=760)).strftime("%Y-%m-%d")
    print(f"  야후에서 {len(missing)}종목 수신 중...")
    for s in range(0, len(missing), chunk):
        part = missing[s:s + chunk]
        for attempt in range(3):
            try:
                raw = yf.download(
                    part, start=start, progress=False,
                    auto_adjust=False, group_by="ticker", threads=True,
                )
                break
            except Exception as e:
                if attempt == 2:
                    print(f"    ! 청크 실패({part[0]}...): {type(e).__name__}")
                    raw = None
                else:
                    time.sleep(3 * (attempt + 1))
        if raw is None:
            continue
        for t in part:
            try:
                d = raw[t] if isinstance(raw.columns, pd.MultiIndex) else raw
                d = d[["Open", "High", "Low", "Close", "Volume"]].dropna()
                if len(d) < 60:
                    continue
                d.columns = ["o", "h", "l", "c", "v"]
                data[t] = d
            except Exception:
                continue
        done = min(s + chunk, len(missing))
        print(f"    {done}/{len(missing)}", end="\r", flush=True)
        time.sleep(0.6)
    print(f"\n  수집 완료: {len(data)}종목")
    cache_file.write_bytes(pickle.dumps(data))
    return data


# ────────────────────────────── 미니 차트 ──────────────────────────────
def mini_chart(df, event_i, hlines=None, extra=None, smas=None, n=45, w=460, h=170):
    """신호 지점을 표시한 작은 캔들 SVG를 만든다. (사이트와 동일하게 상승=빨강)"""
    lo_i = max(0, event_i - n + 12)
    hi_i = min(len(df), event_i + 13)
    win = df.iloc[lo_i:hi_i]
    ev = event_i - lo_i
    pmin, pmax = win.l.min(), win.h.max()
    if pmax <= pmin:
        return ""
    pad, rng = 16, pmax - pmin
    ph = h - pad * 2

    def y(p):
        return pad + (pmax - p) / rng * ph

    cw = (w - pad * 2) / len(win)

    def x(i):
        return pad + cw * (i + 0.5)

    parts = []
    for hl in (hlines or []):
        if pmin <= hl["price"] <= pmax:
            yy = y(hl["price"])
            parts.append(
                f'<line x1="{pad}" y1="{yy:.1f}" x2="{w - pad}" y2="{yy:.1f}" '
                f'stroke="#888" stroke-width="1" stroke-dasharray="4 3"/>'
                f'<text x="{pad + 2}" y="{yy - 3:.1f}" font-size="9" fill="#888">{hl["label"]}</text>'
            )
    for i, k in enumerate(win.itertuples()):
        up = k.c >= k.o
        col = "#e34948" if up else "#2a78d6"
        cx = x(i)
        top, bot = y(max(k.o, k.c)), y(min(k.o, k.c))
        parts.append(
            f'<line x1="{cx:.1f}" y1="{y(k.h):.1f}" x2="{cx:.1f}" y2="{y(k.l):.1f}" '
            f'stroke="{col}" stroke-width="1"/>'
            f'<rect x="{cx - cw * 0.32:.1f}" y="{top:.1f}" width="{cw * 0.64:.1f}" '
            f'height="{max(1, bot - top):.1f}" fill="{"none" if not up else col}" '
            f'stroke="{col}" stroke-width="1"/>'
        )
    # 이동평균선 (전체 시계열로 계산한 뒤 창 구간만 그린다 — 왼쪽 끝도 정확)
    for period, col in zip(smas or [], ["#f0b429", "#8b7fe8"]):
        full = df.c.rolling(period).mean()
        pts = [
            f'{x(i):.1f},{y(v):.1f}'
            for i, v in enumerate(full.iloc[lo_i:hi_i].values)
            if v == v and pmin <= v <= pmax
        ]
        if len(pts) > 1:
            parts.append(
                f'<polyline points="{" ".join(pts)}" fill="none" stroke="{col}" '
                f'stroke-width="1.3" opacity="0.95"/>'
            )
    if 0 <= ev < len(win):
        parts.append(
            f'<line x1="{x(ev):.1f}" y1="{pad}" x2="{x(ev):.1f}" y2="{h - pad}" '
            f'stroke="#f0a020" stroke-width="1.5" stroke-dasharray="3 2" opacity="0.9"/>'
        )
    for m in (extra or []):
        mi = m["i"] - lo_i
        if 0 <= mi < len(win):
            parts.append(
                f'<circle cx="{x(mi):.1f}" cy="{y(win.l.iloc[mi]) + 7:.1f}" r="2.5" fill="#6b7fd7"/>'
            )
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" preserveAspectRatio="xMidYMid meet">'
            + "".join(parts) + "</svg>")


# ────────────────────────────── 리포트 ──────────────────────────────
CSS = """
*{box-sizing:border-box} body{margin:0;padding:28px 20px 60px;background:#0f1115;color:#e6e8ee;
font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Segoe UI',sans-serif;line-height:1.55}
.wrap{max-width:1180px;margin:0 auto}
h1{font-size:23px;margin:0 0 6px} .sub{color:#98a0b3;font-size:13.5px;margin:0 0 18px}
.warn{background:#2a1f12;border:1px solid #6b4a1f;color:#f0c893;padding:11px 14px;
border-radius:9px;font-size:13px;margin:0 0 22px}
.tabs{display:flex;flex-wrap:wrap;gap:7px;margin:0 0 20px}
.tab{background:#1a1e27;border:1px solid #2b3140;color:#c7cddb;border-radius:8px;
padding:6px 11px;font-size:12.5px;cursor:pointer}
.tab.on{background:#2f6fe0;border-color:#2f6fe0;color:#fff}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:13px}
.card{background:#161a22;border:1px solid #262c39;border-radius:11px;padding:13px 14px}
.card h3{margin:0 0 2px;font-size:15px}
.meta{color:#98a0b3;font-size:12px;margin:0 0 3px}
.detail{color:#c7cddb;font-size:12.5px;margin:6px 0 2px}
.badges{display:flex;flex-wrap:wrap;gap:5px;margin:8px 0 0}
.b{font-size:11px;border:1px solid #2b3140;border-radius:5px;padding:2px 7px;color:#aab2c4}
.b.hot{border-color:#7a4a1d;color:#f0b070} .b.new{border-color:#1d5a3a;color:#5fd39a}
.b a{color:#7aa7f0;text-decoration:none}
.empty{color:#7a8296;padding:30px 0}
"""

JS = """
const tabs=[...document.querySelectorAll('.tab')];
tabs.forEach(t=>t.onclick=()=>{
  tabs.forEach(x=>x.classList.toggle('on',x===t));
  const k=t.dataset.k;
  document.querySelectorAll('.card').forEach(c=>{
    c.style.display=(k==='all'||c.dataset.k===k)?'':'none';});
});
"""


def build_report(hits, meta, path):
    by = {}
    for h in hits:
        by.setdefault(h["pattern"], []).append(h)
    order = [n for n, _, _ in DETECTORS if n in by]

    tabs = [f'<button class="tab on" data-k="all">전체 {len(hits)}</button>']
    tabs += [f'<button class="tab" data-k="{n}">{n} {len(by[n])}</button>' for n in order]

    cards = []
    for h in sorted(hits, key=lambda x: (x["daysAgo"], -x["volRatio"])):
        badges = [f'<span class="b">거래량 {h["volRatio"]}x</span>']
        if h["volRatio"] >= 2:
            badges[0] = f'<span class="b hot">거래량 {h["volRatio"]}x</span>'
        ago = "오늘" if h["daysAgo"] == 0 else f'{h["daysAgo"]}일 전'
        cls = "b new" if h["daysAgo"] <= 1 else "b"
        badges.append(f'<span class="{cls}">{ago}</span>')
        badges.append(f'<span class="b"><a href="{SITE}/techniques/{h["slug"]}/" '
                      f'target="_blank">기법 설명 ↗</a></span>')
        cards.append(
            f'<div class="card" data-k="{h["pattern"]}">'
            f'<h3>{h["name"]} <span style="color:#7a8296;font-weight:400;font-size:12px">'
            f'{h["ticker"]}</span></h3>'
            f'<p class="meta">{h["pattern"]} · {h["date"]} · 종가 {h["close"]}</p>'
            f'{h["svg"]}'
            f'<p class="detail">{h["detail"]}</p>'
            f'<div class="badges">{"".join(badges)}</div></div>'
        )

    body = "".join(cards) if cards else '<p class="empty">조건에 맞는 신호가 없습니다.</p>'
    html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>패턴 스캔 · {meta['now']}</title><style>{CSS}</style></head><body><div class="wrap">
<h1>차트 패턴 스캔 결과</h1>
<p class="sub">기준 {meta['now']} · 대상 {meta['universe']}종목(시세 확보 {meta['fetched']}종목)
 · 최근 {meta['days']}거래일 내 신호 · 데이터 최신 봉 {meta['latest']}</p>
<div class="warn">⚠️ 기계적 규칙으로 뽑은 <b>후보 목록</b>입니다. 오탐이 섞이므로 반드시 차트를 직접 확인하세요.
매수·매도 추천이 아니며, 어떤 패턴도 수익을 보장하지 않습니다. 개인 학습용으로만 사용하세요.</div>
<div class="tabs">{"".join(tabs)}</div><div class="grid">{body}</div>
</div><script>{JS}</script></body></html>"""
    path.write_text(html, encoding="utf-8")


# ────────────────────────────── 메인 ──────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="all", choices=["kr", "us", "all"])
    ap.add_argument("--days", type=int, default=5, help="최근 N거래일 내 신호만")
    ap.add_argument("--pattern", nargs="*", help="특정 패턴만 (미지정 시 전체)")
    ap.add_argument("--refresh", action="store_true", help="시세 캐시 무시")
    ap.add_argument("--limit", type=int, help="대상 종목 수 제한(테스트용)")
    args = ap.parse_args()

    print("1) 종목 리스트 로드")
    names = universe.load(args.market)
    tickers = list(names)
    if args.limit:
        tickers = tickers[:args.limit]
    print(f"  대상 {len(tickers)}종목")

    print("2) 시세 수집")
    prices = fetch_prices(tickers, refresh=args.refresh)
    if not prices:
        print("시세를 받지 못했습니다. --refresh 로 다시 시도해 보세요.")
        sys.exit(1)

    dets = [d for d in DETECTORS if not args.pattern or d[0] in args.pattern]
    print(f"3) 패턴 탐지 ({len(dets)}종)")

    hits, latest = [], None
    for t, df in prices.items():
        if latest is None or df.index[-1] > latest:
            latest = df.index[-1]
        for pname, fn, slug in dets:
            try:
                r = fn(df, lookback=args.days)
            except Exception:
                continue
            if not r:
                continue
            i = r["index"]
            krw = t.endswith(".KS")
            hits.append({
                "ticker": t,
                "name": names.get(t, t),
                "pattern": pname,
                "slug": slug,
                "date": str(df.index[i].date()),
                "daysAgo": r["daysAgo"],
                "close": f"{df.c.iloc[i]:,.0f}원" if krw else f"${df.c.iloc[i]:,.2f}",
                "detail": r["detail"],
                "volRatio": r.get("volRatio", 0),
                "svg": mini_chart(df, i, r.get("hlines"), r.get("extraMarkers"), r.get("smas")),
            })

    print(f"  신호 {len(hits)}건")
    for pname, _, _ in dets:
        c = sum(1 for h in hits if h["pattern"] == pname)
        if c:
            print(f"    - {pname}: {c}건")

    out = REPORT / f"scan-{datetime.now().strftime('%Y%m%d-%H%M')}.html"
    build_report(hits, {
        "now": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "universe": len(tickers),
        "fetched": len(prices),
        "days": args.days,
        "latest": str(latest.date()) if latest is not None else "-",
    }, out)
    print(f"4) 리포트 저장 -> {out}")
    print(f"   열기: open '{out}'")


if __name__ == "__main__":
    main()
