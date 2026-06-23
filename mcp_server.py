import os
import math
from datetime import datetime

import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

from stock_library import process_ticker_input, KOREAN_STOCKS, search_stocks


def _safe(v):
    """NaN/Inf → None, 나머지는 float 반환."""
    if v is None:
        return None
    try:
        f = float(v)
        return None if (not math.isfinite(f)) else f
    except (TypeError, ValueError):
        return None

mcp = FastMCP("Stock Analyzer")


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


@mcp.custom_route("/agents.md", methods=["GET"])
async def agents_md(request: Request) -> PlainTextResponse:
    agents_path = os.path.join(os.path.dirname(__file__), "agents.md")
    with open(agents_path, encoding="utf-8") as f:
        content = f.read()
    return PlainTextResponse(content, media_type="text/markdown; charset=utf-8")


# ── 데이터 수집 내부 함수 ──────────────────────────────────────────────────────

def _get_qqq_data():
    try:
        qqq = yf.Ticker("QQQ")
        hist = qqq.history(period="200d")["Close"]
        if len(hist) < 200:
            return None, None
        return float(hist.iloc[-1]), float(hist.mean())
    except Exception:
        return None, None


def _get_vix_data():
    for symbol in ["^VIX", "VIX", "VIXY"]:
        try:
            data = yf.Ticker(symbol).history(period="5d")
            if not data.empty:
                return float(data["Close"].iloc[-1])
        except Exception:
            continue
    return None


def _get_usd_krw_rate():
    try:
        data = yf.Ticker("USDKRW=X").history(period="5d")
        if len(data) >= 2:
            cur = float(data["Close"].iloc[-1])
            prev = float(data["Close"].iloc[-2])
            chg = cur - prev
            return cur, chg, (chg / prev) * 100
    except Exception:
        pass
    return None, None, None


def _fetch_fgi():
    try:
        url = "https://feargreedmeter.com/"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        el = soup.find("div", class_="text-center text-4xl font-semibold mb-1 text-white")
        if el:
            t = el.text.strip()
            return int(t) if t.isdigit() else None
    except Exception:
        pass
    return None


def _fetch_pci():
    try:
        url = "https://ycharts.com/indicators/cboe_equity_put_call_ratio"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for td in soup.find_all("td", class_="col-6"):
            try:
                return float(td.text.strip().replace(",", ""))
            except ValueError:
                continue
    except Exception:
        pass
    return None


def _fetch_buffett():
    try:
        w = yf.Ticker("^W5000").history(period="1d")
        if not w.empty:
            ratio = float(w["Close"].iloc[-1]) / 29184 * 100
            return ratio, "wilshire"
    except Exception:
        pass
    try:
        spy = yf.Ticker("SPY").history(period="1d")
        if not spy.empty:
            return float(spy["Close"].iloc[-1]) / 400 * 180, "estimated"
    except Exception:
        pass
    return None, None


def _calculate_rsi(series: pd.Series, window: int = 14):
    try:
        delta = series.diff()
        gain = delta.where(delta > 0, 0).rolling(window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        v = rsi.iloc[-1]
        return None if pd.isna(v) else float(v)
    except Exception:
        return None


# ── 해석 함수 ─────────────────────────────────────────────────────────────────

def _interpret_fgi(v):
    if v is None:
        return "데이터 없음", "neutral"
    if v <= 25:
        return "극심한 공포", "bullish"   # 공포 = 매수 기회
    if v <= 45:
        return "공포", "bullish"
    if v <= 55:
        return "중립", "neutral"
    if v <= 75:
        return "탐욕적", "bearish"        # 탐욕 = 매도 고려
    return "극도로 탐욕적", "bearish"


def _interpret_vix(v):
    if v is None:
        return "데이터 없음", "neutral"
    if v < 15:
        return "변동성 낮음 (상승장)", "bullish"
    if v < 25:
        return "변동성 중간", "neutral"
    return "변동성 높음 (하락장)", "bearish"


def _interpret_pci(v):
    if v is None:
        return "데이터 없음", "neutral"
    if v > 0.95:
        return "하락 베팅 증가", "bullish"  # 풋 많음 = 공포 = 역발상 매수
    if v < 0.65:
        return "상승 베팅 증가", "bearish"  # 콜 많음 = 탐욕 = 역발상 매도
    return "중립적", "neutral"


def _interpret_rsi(v):
    if v is None:
        return "데이터 없음", "neutral"
    if v < 30:
        return "과매도", "bullish"   # 과매도 = 매수 신호
    if v > 70:
        return "과매수", "bearish"   # 과매수 = 매도 신호
    return "중립", "neutral"


def _interpret_buffett(ratio, dtype):
    if ratio is None:
        return "데이터 없음", "neutral"
    suffix = " (Wilshire 5000)" if dtype == "wilshire" else " (추정)" if dtype == "estimated" else ""
    if ratio <= 80:
        return f"심각한 저평가{suffix}", "bullish"   # 저평가 = 매수 신호
    if ratio <= 100:
        return f"저평가{suffix}", "bullish"
    if ratio <= 120:
        return f"적정 가치{suffix}", "neutral"
    if ratio <= 140:
        return f"약간 고평가{suffix}", "neutral"
    if ratio <= 180:
        return f"고평가{suffix}", "bearish"           # 고평가 = 매도 신호
    return f"심각한 고평가{suffix}", "bearish"


def _interpret_usd_krw(rate, chg, chg_pct):
    if rate is None:
        return "데이터 없음", "neutral"
    if chg is None or chg == 0:
        return "보합", "neutral"
    if chg > 0:
        return f"전일 대비 +{chg:.1f}원 (+{chg_pct:.2f}%)", "bearish"
    return f"전일 대비 {chg:.1f}원 ({chg_pct:.2f}%)", "bullish"


# ── N일 분석 헬퍼 ─────────────────────────────────────────────────────────────

def _trading_day_after(index, base_date, days_after):
    target = base_date + pd.Timedelta(days=days_after)
    future = index[index >= target]
    return future[0] if len(future) > 0 else None


def _add_nday_prices(signal_days: pd.DataFrame, data: pd.DataFrame, days_after: int) -> pd.DataFrame:
    prices, actual_days = [], []
    for sig_date in signal_days.index:
        fd = _trading_day_after(data.index, sig_date, days_after)
        if fd is not None and fd in data.index:
            prices.append(data.loc[fd, "Close"])
            actual_days.append((fd - sig_date).days)
        else:
            prices.append(None)
            actual_days.append(None)
    signal_days[f"Price_{days_after}D_Later"] = prices
    signal_days["Actual_Days_Later"] = actual_days
    return signal_days


# ── MCP 도구 ──────────────────────────────────────────────────────────────────

@mcp.tool()
def get_market_indicators() -> dict:
    """현재 시장 심리 지표 전체 조회.
    Fear & Greed Index, VIX, Put/Call Ratio, RSI(S&P500), QQQ vs 200일 이동평균,
    버핏 지수(시가총액/GDP), 원달러 환율을 반환합니다."""
    qqq_price, qqq_sma = _get_qqq_data()
    vix = _get_vix_data()
    fgi = _fetch_fgi()
    pci = _fetch_pci()
    usd_krw, usd_krw_chg, usd_krw_chg_pct = _get_usd_krw_rate()
    buffett_ratio, buffett_type = _fetch_buffett()

    rsi = None
    try:
        spy_close = yf.Ticker("SPY").history(period="50d")["Close"]
        rsi = _calculate_rsi(spy_close)
    except Exception:
        pass

    fgi_label, fgi_signal = _interpret_fgi(fgi)
    vix_label, vix_signal = _interpret_vix(vix)
    pci_label, pci_signal = _interpret_pci(pci)
    rsi_label, rsi_signal = _interpret_rsi(rsi)
    buffett_label, buffett_signal = _interpret_buffett(buffett_ratio, buffett_type)
    usd_label, usd_signal = _interpret_usd_krw(usd_krw, usd_krw_chg, usd_krw_chg_pct)

    qqq_signal = "neutral"
    qqq_label = "데이터 없음"
    if qqq_price is not None and qqq_sma is not None:
        diff_pct = (qqq_price - qqq_sma) / qqq_sma * 100
        qqq_signal = "bullish" if qqq_price > qqq_sma else "bearish"
        qqq_label = f"{'상승' if qqq_price > qqq_sma else '하락'} 추세 ({diff_pct:+.1f}%)"

    return {
        "fear_greed_index": {
            "value": fgi,
            "label": fgi_label,
            "signal": fgi_signal,
        },
        "vix": {
            "value": vix,
            "label": vix_label,
            "signal": vix_signal,
        },
        "put_call_ratio": {
            "value": pci,
            "label": pci_label,
            "signal": pci_signal,
        },
        "rsi_sp500": {
            "value": rsi,
            "label": rsi_label,
            "signal": rsi_signal,
        },
        "qqq_vs_200ma": {
            "current": qqq_price,
            "sma200": round(qqq_sma, 2) if qqq_sma else None,
            "label": qqq_label,
            "signal": qqq_signal,
        },
        "buffett_indicator": {
            "value": round(buffett_ratio, 1) if buffett_ratio else None,
            "label": buffett_label,
            "signal": buffett_signal,
        },
        "usd_krw": {
            "rate": round(usd_krw, 2) if usd_krw else None,
            "change": round(usd_krw_chg, 2) if usd_krw_chg else None,
            "change_pct": round(usd_krw_chg_pct, 2) if usd_krw_chg_pct else None,
            "label": usd_label,
            "signal": usd_signal,
        },
        "retrieved_at": datetime.now().isoformat(),
        "note": "가격/지수 데이터는 마지막 거래일 종가 기준입니다. 시장 휴장 중에는 직전 거래일 데이터가 반환됩니다.",
    }


@mcp.tool()
def analyze_stock_drops(
    ticker: str,
    drop_threshold_pct: float = 1.0,
    days_after: int = 3,
    start_date: str = "2020-01-01",
) -> dict:
    """특정 종목이 drop_threshold_pct% 이상 하락한 날 기준으로 days_after일 후 가격 방향을 통계 분석합니다.
    미국 주식(QQQ, AAPL), 한국 주식(삼성전자, 005930), 인덱스, 코인 지원.
    strategy는 'sell'(즉시매도 유리), 'wait'(기다리기 유리), 'neutral' 중 하나입니다."""
    processed_ticker, company_name = process_ticker_input(ticker)

    try:
        data = yf.download(processed_ticker, start=start_date, progress=False, auto_adjust=True)
    except Exception as e:
        return {"error": f"데이터 다운로드 실패: {str(e)}", "ticker": processed_ticker}

    if data.empty:
        return {"error": f"'{processed_ticker}' 데이터를 찾을 수 없습니다.", "ticker": processed_ticker}

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)

    data = data[["Close"]].copy()
    data["Pct_Change"] = data["Close"].pct_change() * 100

    signal_days = data[data["Pct_Change"] <= -drop_threshold_pct].copy()

    if len(signal_days) == 0:
        return {
            "ticker": processed_ticker,
            "company_name": company_name,
            "error": f"{drop_threshold_pct}% 이상 하락한 날이 없습니다.",
            "total_signals": 0,
        }

    signal_days["Price_Today"] = signal_days["Close"]
    signal_days = _add_nday_prices(signal_days, data, days_after)
    signal_days = signal_days.dropna(subset=[f"Price_{days_after}D_Later"])

    if len(signal_days) == 0:
        return {
            "ticker": processed_ticker,
            "error": f"{days_after}일 후 데이터가 있는 하락일이 없습니다.",
            "total_signals": 0,
        }

    signal_days["Result"] = signal_days.apply(
        lambda r: "Win" if r["Price_Today"] > r[f"Price_{days_after}D_Later"] else "Lose",
        axis=1,
    )
    signal_days[f"Change_{days_after}D"] = (
        (signal_days[f"Price_{days_after}D_Later"] - signal_days["Price_Today"])
        / signal_days["Price_Today"]
        * 100
    )

    total = len(signal_days)
    win = int(signal_days["Result"].value_counts().get("Win", 0))
    lose = int(signal_days["Result"].value_counts().get("Lose", 0))
    win_rate = round(win / total * 100, 1)
    avg_change = round(float(signal_days[f"Change_{days_after}D"].mean()), 2)

    if win_rate > 55:
        strategy = "sell"
        recommendation = f"{ticker} 종목이 {drop_threshold_pct}% 이상 하락하면 즉시 매도를 고려하세요."
    elif win_rate < 45:
        strategy = "wait"
        recommendation = f"{ticker} 종목이 {drop_threshold_pct}% 이상 하락해도 {days_after}일 정도는 기다려보세요."
    else:
        strategy = "neutral"
        recommendation = "즉시 매도와 대기 전략의 성공률이 비슷합니다. 다른 지표와 함께 판단하세요."

    return {
        "ticker": processed_ticker,
        "company_name": company_name,
        "drop_threshold_pct": drop_threshold_pct,
        "days_after": days_after,
        "period_start": start_date,
        "total_signals": total,
        "win_count": win,
        "lose_count": lose,
        "win_rate": win_rate,
        "avg_change_pct": avg_change,
        "strategy": strategy,
        "recommendation": recommendation,
    }


@mcp.tool()
def get_stock_price(ticker_or_name: str) -> dict:
    """미국 주식(AAPL), 한국 주식(삼성전자 또는 005930), 인덱스(^GSPC), 코인(BTC-USD) 현재가 조회."""
    processed_ticker, company_name = process_ticker_input(ticker_or_name)

    try:
        t = yf.Ticker(processed_ticker)
        hist = t.history(period="5d")
        if hist.empty:
            return {"error": f"'{processed_ticker}' 데이터를 찾을 수 없습니다.", "ticker": processed_ticker}

        close_series = hist["Close"].dropna()
        if close_series.empty:
            return {"error": f"'{processed_ticker}' 가격 데이터가 없습니다.", "ticker": processed_ticker}

        current_price = float(close_series.iloc[-1])
        prev_price = float(close_series.iloc[-2]) if len(close_series) >= 2 else current_price
        change_pct = round((current_price - prev_price) / prev_price * 100, 2) if prev_price else 0.0

        info = {}
        try:
            info = t.info or {}
        except Exception:
            pass

        _kr_ticker = processed_ticker.upper()
        is_korean = (
            processed_ticker.endswith(".KS")
            or processed_ticker.endswith(".KQ")
            or _kr_ticker in {"^KS11", "^KQ11", "^KS200"}
            or info.get("currency") == "KRW"
        )
        currency = info.get("currency", "KRW" if is_korean else "USD")
        display_name = company_name or info.get("shortName") or info.get("longName") or processed_ticker

        vol = None
        if "Volume" in hist.columns:
            raw_vol = hist["Volume"].iloc[-1]
            if not math.isnan(float(raw_vol)):
                vol = int(raw_vol)

        last_date = close_series.index[-1]
        data_as_of = last_date.strftime("%Y-%m-%d") if hasattr(last_date, "strftime") else str(last_date)[:10]

        return {
            "ticker": processed_ticker,
            "company_name": display_name,
            "current_price": round(current_price, 2),
            "currency": currency,
            "change_pct": change_pct,
            "volume": vol,
            "market": "KRX" if is_korean else "US",
            "data_as_of": data_as_of,
        }
    except Exception as e:
        return {"error": str(e), "ticker": processed_ticker}


@mcp.tool()
def search_korean_stock(query: str) -> list:
    """한국 주식 종목명 부분 검색. 최대 20개 반환.
    예: '삼성' → 삼성전자, 삼성SDI 등 / 'SK' → SK하이닉스, SK텔레콤 등"""
    results = search_stocks(query)
    return [
        {"ticker": f"{code}.KS", "name": name, "code": code}
        for code, name in results[:20]
    ]


# ── 서버 실행 ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    mcp.run(transport="http", host="0.0.0.0", port=port)
