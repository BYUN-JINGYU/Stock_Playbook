"""현재 시점 기준으로 최근에 발생한 차트 패턴을 탐지한다.

각 탐지 함수는 OHLCV 데이터프레임을 받아, 최근 `lookback` 거래일 안에
신호가 발생했으면 dict를 반환하고 아니면 None을 반환한다.

주의: 탐지는 기계적 규칙일 뿐이며 오탐이 섞인다. 결과는 눈으로 확인할 후보 목록이지
매매 신호가 아니다.
"""


def _sma(s, n):
    return s.rolling(n).mean()


def _rsi(close, n=14):
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, 1e-12)
    return 100 - 100 / (1 + rs)


def _vol_ratio(df, i, n=20):
    """당일 거래량 / 직전 n일 평균 거래량."""
    base = df.v.iloc[max(0, i - n):i].mean()
    if not base or base <= 0:
        return 0.0
    return float(df.v.iloc[i] / base)


def golden_cross(df, lookback=5):
    """5일선이 20일선을 상향 돌파."""
    if len(df) < 40:
        return None
    s5, s20 = _sma(df.c, 5), _sma(df.c, 20)
    for k in range(1, lookback + 1):
        i = len(df) - k
        if s5.iloc[i - 1] <= s20.iloc[i - 1] and s5.iloc[i] > s20.iloc[i]:
            return {
                "index": i,
                "daysAgo": k - 1,
                "detail": f"5일선 {s5.iloc[i]:,.0f} > 20일선 {s20.iloc[i]:,.0f}",
                "volRatio": round(_vol_ratio(df, i), 2),
                "smas": [5, 20],
            }
    return None


def dead_cross(df, lookback=5):
    """5일선이 20일선을 하향 이탈."""
    if len(df) < 40:
        return None
    s5, s20 = _sma(df.c, 5), _sma(df.c, 20)
    for k in range(1, lookback + 1):
        i = len(df) - k
        if s5.iloc[i - 1] >= s20.iloc[i - 1] and s5.iloc[i] < s20.iloc[i]:
            return {
                "index": i,
                "daysAgo": k - 1,
                "detail": f"5일선 {s5.iloc[i]:,.0f} < 20일선 {s20.iloc[i]:,.0f}",
                "volRatio": round(_vol_ratio(df, i), 2),
                "smas": [5, 20],
            }
    return None


def breakout_52w(df, lookback=5):
    """52주(250거래일) 신고가 돌파. 거래량 증가를 동반해야 한다."""
    if len(df) < 260:
        return None
    hi = df.h.rolling(250).max()
    for k in range(1, lookback + 1):
        i = len(df) - k
        prev = hi.iloc[i - 1]
        if df.c.iloc[i] > prev and df.c.iloc[i - 1] <= prev:
            vr = _vol_ratio(df, i)
            if vr < 1.2:
                continue
            return {
                "index": i,
                "daysAgo": k - 1,
                "detail": f"직전 52주 고가 {prev:,.0f} 돌파 (종가 {df.c.iloc[i]:,.0f})",
                "volRatio": round(vr, 2),
                "hlines": [{"price": float(prev), "label": "52주 고가"}],
            }
    return None


def gap_up(df, lookback=5):
    """시가가 전일 고가보다 3% 이상 위에서 형성된 상승 갭."""
    if len(df) < 30:
        return None
    for k in range(1, lookback + 1):
        i = len(df) - k
        prev_h = df.h.iloc[i - 1]
        gap = (df.o.iloc[i] / prev_h - 1) * 100
        if gap < 3:
            continue
        vr = _vol_ratio(df, i)
        if vr < 1.5 or df.c.iloc[i] <= df.o.iloc[i]:
            continue
        return {
            "index": i,
            "daysAgo": k - 1,
            "detail": f"전일 고가 대비 +{gap:.1f}% 갭 상승, 양봉 마감",
            "volRatio": round(vr, 2),
        }
    return None


def double_bottom(df, lookback=5):
    """비슷한 높이의 저점 2개 형성 후 넥라인 상향 돌파."""
    if len(df) < 80:
        return None
    lo, cl = df.l.values, df.c.values
    n = len(df)
    w = 8
    for k in range(1, lookback + 1):
        b = n - k  # 돌파 후보일
        # 돌파일 직전 60일 안에서 두 저점을 찾는다
        seg_start = max(w, b - 60)
        lows = [
            i for i in range(seg_start, b - 3)
            if lo[i] == min(lo[max(0, i - w):i + w + 1])
        ]
        if len(lows) < 2:
            continue
        second = lows[-1]
        for first in reversed(lows[:-1]):
            if not (14 <= second - first <= 60):
                continue
            if abs(lo[second] - lo[first]) / lo[first] * 100 > 4:
                continue
            neck = max(df.h.values[first:second + 1])
            if neck / lo[first] - 1 < 0.06:
                continue
            # 돌파일에 처음으로 넥라인을 종가로 넘겼는지
            if cl[b] > neck and max(cl[second:b]) <= neck:
                return {
                    "index": b,
                    "daysAgo": k - 1,
                    "detail": (
                        f"저점 {lo[first]:,.0f} / {lo[second]:,.0f} 형성 후 "
                        f"넥라인 {neck:,.0f} 종가 돌파"
                    ),
                    "volRatio": round(_vol_ratio(df, b), 2),
                    "hlines": [{"price": float(neck), "label": "넥라인"}],
                    "extraMarkers": [
                        {"i": int(first), "label": "저점1"},
                        {"i": int(second), "label": "저점2"},
                    ],
                }
    return None


def rsi_oversold_bounce(df, lookback=5):
    """RSI가 30 아래로 내려갔다가 다시 30 위로 올라온 반등 신호."""
    if len(df) < 40:
        return None
    r = _rsi(df.c)
    for k in range(1, lookback + 1):
        i = len(df) - k
        if r.iloc[i - 1] < 30 <= r.iloc[i]:
            recent_min = r.iloc[max(0, i - 10):i].min()
            return {
                "index": i,
                "daysAgo": k - 1,
                "detail": f"RSI {recent_min:.0f} 저점 후 {r.iloc[i]:.0f}로 회복",
                "volRatio": round(_vol_ratio(df, i), 2),
            }
    return None


def bollinger_squeeze_break(df, lookback=5):
    """볼린저밴드 폭이 최근 6개월 최저 수준까지 좁아진 뒤 상단을 돌파."""
    if len(df) < 150:
        return None
    mid = _sma(df.c, 20)
    sd = df.c.rolling(20).std()
    upper = mid + 2 * sd
    width = (upper - (mid - 2 * sd)) / mid
    for k in range(1, lookback + 1):
        i = len(df) - k
        w_now = width.iloc[i - 1]
        w_min = width.iloc[max(0, i - 120):i].min()
        # 돌파 직전 밴드폭이 6개월 최저권(하위 20% 이내)이었는지
        if w_now > w_min * 1.2:
            continue
        if df.c.iloc[i] > upper.iloc[i] and df.c.iloc[i - 1] <= upper.iloc[i - 1]:
            return {
                "index": i,
                "daysAgo": k - 1,
                "detail": f"밴드폭 {w_now * 100:.1f}%로 수축 후 상단 돌파",
                "volRatio": round(_vol_ratio(df, i), 2),
            }
    return None


# 표시명, 함수, 사이트 내 해당 글 slug
DETECTORS = [
    ("골든크로스", golden_cross, "moving-average"),
    ("데드크로스", dead_cross, "moving-average"),
    ("52주 신고가 돌파", breakout_52w, "breakout-52week"),
    ("쌍바닥 넥라인 돌파", double_bottom, "double-top-bottom"),
    ("갭 상승", gap_up, "gap-trading"),
    ("RSI 과매도 반등", rsi_oversold_bounce, "rsi"),
    ("볼린저 스퀴즈 돌파", bollinger_squeeze_break, "bollinger-bands"),
]
