import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from bs4 import BeautifulSoup


try:
    from stock_library import (
        KOREAN_STOCKS, 
        get_ticker_from_name, 
        process_ticker_input,
        get_stock_count
    )
    print(f"주식 라이브러리 로드 완료! {get_stock_count()}개 종목 지원")
except ImportError as e:
    print(f" stock_library.py 파일을 찾을 수 없습니다: {e}")
    

# Page configuration
st.set_page_config(
    page_title="Stock Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
/* ── Streamlit 기본 UI 숨김 ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }

/* ── 전체 배경 ── */
.stApp { background: #f4f6fa; }
.block-container { padding: 2rem 2.5rem 3rem; max-width: 1280px; }

/* ── 앱 헤더 ── */
.app-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 2rem;
    padding-bottom: 1.25rem;
    border-bottom: 1px solid #e2e8f0;
}
.app-header .logo {
    font-size: 1.6rem;
    font-weight: 800;
    color: #1e293b;
    letter-spacing: -0.5px;
}
.app-header .logo span { color: #4f46e5; }
.app-header .badge {
    background: #ede9fe;
    color: #4f46e5;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 999px;
    letter-spacing: 0.3px;
    text-transform: uppercase;
}

/* ── 메트릭 카드 ── */
.metric-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 1.1rem 1.25rem;
    margin-bottom: 0.9rem;
    border-left: 4px solid #cbd5e1;
    transition: box-shadow 0.15s;
}
.metric-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.07); }
.metric-card.bullish { border-left-color: #10b981; background: #f0fdf8; }
.metric-card.bearish { border-left-color: #ef4444; background: #fff5f5; }
.metric-card.neutral  { border-left-color: #f59e0b; background: #fffbeb; }

.metric-card .mc-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    color: #94a3b8;
    margin-bottom: 0.35rem;
}
.metric-card .mc-value {
    font-size: 1.35rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.2rem;
    line-height: 1.2;
}
.metric-card .mc-value.bullish { color: #059669; }
.metric-card .mc-value.bearish { color: #dc2626; }
.metric-card .mc-interp {
    font-size: 0.82rem;
    color: #64748b;
    line-height: 1.4;
}

/* ── 신호 배지 ── */
.signal-pill {
    display: inline-block;
    font-size: 0.68rem;
    font-weight: 700;
    padding: 2px 9px;
    border-radius: 999px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    margin-left: 0.4rem;
    vertical-align: middle;
}
.pill-bullish { background: #d1fae5; color: #065f46; }
.pill-bearish { background: #fee2e2; color: #991b1b; }
.pill-neutral  { background: #fef3c7; color: #92400e; }

/* ── 인포 박스 ── */
.info-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin: 1rem 0;
}
.info-card h4 {
    font-size: 0.85rem;
    font-weight: 700;
    color: #475569;
    margin-bottom: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}
.info-card ul { margin: 0; padding-left: 1.2rem; }
.info-card li { font-size: 0.85rem; color: #64748b; margin-bottom: 0.3rem; }
.info-card li strong { color: #334155; }
.info-card .tip {
    margin-top: 0.75rem;
    font-size: 0.78rem;
    color: #94a3b8;
    border-top: 1px solid #f1f5f9;
    padding-top: 0.6rem;
}

/* ── 결과 박스 ── */
.result-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 1.5rem;
    text-align: center;
    margin: 0.5rem 0;
}
.result-card h4 { font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem; color: #94a3b8; }
.result-card .big-num { font-size: 2.2rem; font-weight: 800; line-height: 1; margin-bottom: 0.4rem; }
.result-card p { font-size: 0.82rem; color: #64748b; margin: 0; }
.result-card.sell { border-top: 3px solid #ef4444; }
.result-card.sell .big-num { color: #dc2626; }
.result-card.buy  { border-top: 3px solid #10b981; }
.result-card.buy  .big-num { color: #059669; }

/* ── 전략 카드 ── */
.strategy-card {
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin: 0.5rem 0;
    border: 1px solid #e2e8f0;
    background: #ffffff;
}
.strategy-card.sell-strat { border-left: 5px solid #ef4444; }
.strategy-card.buy-strat  { border-left: 5px solid #10b981; }
.strategy-card.neutral-strat { border-left: 5px solid #f59e0b; }
.strategy-card h4 { font-size: 0.95rem; font-weight: 700; color: #1e293b; margin-bottom: 0.4rem; }
.strategy-card p { font-size: 0.85rem; color: #64748b; margin: 0.2rem 0; }
.strategy-card strong { color: #334155; }

/* ── 탭 스타일 ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #ffffff;
    border-radius: 12px;
    padding: 4px;
    border: 1px solid #e2e8f0;
    margin-bottom: 1.5rem;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px;
    padding: 0.5rem 1.5rem;
    font-weight: 600;
    font-size: 0.88rem;
    color: #64748b;
}
.stTabs [aria-selected="true"] {
    background: #4f46e5 !important;
    color: #ffffff !important;
}

/* ── 분리선 ── */
hr { border: none; border-top: 1px solid #e2e8f0; margin: 1.5rem 0; }

/* ── 섹션 제목 ── */
.section-title {
    font-size: 1rem;
    font-weight: 700;
    color: #1e293b;
    margin: 1.5rem 0 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

/* ── 모바일 ── */
@media (max-width: 768px) {
    .block-container { padding: 1rem 1rem 2rem; }
    .metric-card .mc-value { font-size: 1.1rem; }
    .result-card .big-num { font-size: 1.6rem; }
}
</style>
""", unsafe_allow_html=True)

# Market data functions
@st.cache_data(ttl=60)  # Cache for 1 minute
def get_qqq_data():
    try:
        qqq = yf.Ticker("QQQ")
        data = qqq.history(period="1d")
        if data.empty:
            return None, None
        qqq_price = data['Close'].iloc[-1]
        qqq_history = qqq.history(period="200d")['Close']
        if len(qqq_history) < 200:
            return None, None
        qqq_sma = qqq_history.mean()
        return qqq_price, qqq_sma
    except Exception:
        return None, None

@st.cache_data(ttl=60)
def get_vix_data():
    try:
        vix_symbols = ["^VIX", "VIX", "VIXY"]
        
        for symbol in vix_symbols:
            try:
                vix = yf.Ticker(symbol)
                data = vix.history(period="5d")  # 더 긴 기간으로 시도
                if not data.empty and len(data) > 0:
                    return data['Close'].iloc[-1]
            except:
                continue
        
        
        return None
    except Exception:
        return None

@st.cache_data(ttl=60)
def get_usd_krw_rate():
    """원달러 환율 정보 가져오기"""
    try:
        # yfinance로 USD/KRW 환율 가져오기
        usd_krw = yf.Ticker("USDKRW=X")
        data = usd_krw.history(period="5d")  # 더 많은 데이터로 확실한 전날 비교
        if not data.empty and len(data) >= 2:
            current_rate = data['Close'].iloc[-1]
            prev_rate = data['Close'].iloc[-2]
            
            # 변화량과 변화율 계산
            change_amount = current_rate - prev_rate
            change_pct = (change_amount / prev_rate) * 100
            
            return current_rate, change_amount, change_pct
        return None, None, None
    except Exception:
        return None, None, None

@st.cache_data(ttl=300)  # Cache for 5 minutes due to web scraping
def fetch_fgi():
    try:
        url = 'https://feargreedmeter.com/'
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        fgi_element = soup.find('div', class_='text-center text-4xl font-semibold mb-1 text-white')
        if fgi_element:
            fgi_text = fgi_element.text.strip()
            return int(fgi_text) if fgi_text.isdigit() else None
        return None
    except Exception:
        return None

@st.cache_data(ttl=300)
def fetch_pci():
    try:
        url = 'https://ycharts.com/indicators/cboe_equity_put_call_ratio'
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        td_elements = soup.find_all('td', class_='col-6')
        for td in td_elements:
            try:
                return float(td.text.strip().replace(',', ''))
            except ValueError:
                continue
        return None
    except Exception:
        return None

@st.cache_data(ttl=300)
def fetch_buffett_indicator():
    """버핏 지수 (미국 주식 시가총액 대비 GDP 비율) 가져오기"""
    try:
        # Wilshire 5000 지수를 yfinance로 직접 가져오기
        wilshire = yf.Ticker("^W5000")
        wilshire_data = wilshire.history(period="1d")
        
        if not wilshire_data.empty:
            wilshire_value = wilshire_data['Close'].iloc[-1]
            
            # Wilshire 5000은 미국 전체 시장 시가총액을 나타냄 (단위: 십억 달러)
            # GDP는 약 25조 달러 (2024년 기준)
            # 실제 GDP 데이터는 FRED API가 필요하지만, 최근 추정치 사용
            gdp_estimate = 29184  # 27조 달러 (2024년 추정)
            # 29184890
            # 버핏 지수 계산: (시가총액 / GDP) * 100
            # Wilshire 5000 지수는 포인트당 약 10억 달러를 나타냄
            market_cap = wilshire_value  # 십억 달러 단위
            buffett_ratio = (market_cap / gdp_estimate) * 100
            
            return buffett_ratio, "wilshire"
        
        # Wilshire 5000이 실패한 경우 SPY 기반 추정
        spy = yf.Ticker("SPY")
        spy_data = spy.history(period="1d")
        if spy_data.empty:
            return None, None
            
        # SPY ETF 가격을 기반으로 S&P 500 추정 시가총액 계산
        spy_price = spy_data['Close'].iloc[-1]
        
        # 대략적인 버핏 지수 계산 (SPY 기반 추정)
        # 역사적으로 SPY $400 수준에서 버핏 지수가 약 180% 정도
        estimated_ratio = (spy_price / 400) * 180
        
        # 더 정확한 방법: 웹 스크래핑으로 실제 버핏 지수 가져오기
        try:
            url = 'https://www.longtermtrends.net/market-cap-to-gdp-the-buffett-indicator/'
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 페이지에서 현재 비율 찾기
            ratio_elements = soup.find_all('span', class_='indicator-value')
            if ratio_elements:
                for element in ratio_elements:
                    text = element.text.strip()
                    if '%' in text:
                        ratio_str = text.replace('%', '').strip()
                        try:
                            actual_ratio = float(ratio_str)
                            return actual_ratio, "actual"
                        except ValueError:
                            continue
        except:
            pass
            
        # 실제 데이터를 가져올 수 없는 경우 추정치 사용
        return estimated_ratio, "estimated"
        
    except Exception:
        return None, None

def calculate_rsi(data, window=14):
    try:
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not rsi.empty else None
    except:
        return None

# Interpretation functions
def interpret_fgi(fgi):
    if fgi is None:
        return "데이터 없음", "neutral"
    if fgi <= 25:
        return "극심한 공포 (매수 신호)", "bullish"
    elif fgi <= 45:
        return "공포 (매수 신호)", "bullish"
    elif fgi <= 55:
        return "중립적 (유지 또는 관망)", "neutral"
    elif fgi <= 75:
        return "탐욕적 (매도 신호)", "bearish"
    else:
        return "극도로 탐욕적 (매도 신호)", "bearish"

def interpret_vix(vix):
    if vix is None:
        return "데이터 없음", "neutral"
    if vix < 15:
        return "변동성 낮음 (안정적 상승장)", "bullish"
    elif vix < 25:
        return "변동성 중간 (중립)", "neutral"
    else:
        return "변동성 높음 (불안정)", "bearish"

def interpret_pci(pci):
    if pci is None:
        return "데이터 없음", "neutral"
    if pci > 0.95:
        return "하락 베팅 증가 (역발상 매수 신호)", "bullish"
    elif pci < 0.65:
        return "상승 베팅 증가 (역발상 매도 신호)", "bearish"
    else:
        return "중립적 상태", "neutral"

def interpret_rsi(rsi):
    if rsi is None:
        return "데이터 없음", "neutral"
    if rsi < 30:
        return "과매도 (매수 신호)", "bullish"
    elif rsi > 70:
        return "과매수 (매도 신호)", "bearish"
    else:
        return "중립", "neutral"

def interpret_buffett_indicator(ratio, data_type):
    if ratio is None:
        return "데이터 없음", "neutral"
    
    if data_type == "wilshire":
        data_suffix = " (Wilshire 5000 기준)"
    elif data_type == "estimated":
        data_suffix = " (추정)"
    else:
        data_suffix = ""
    
    if ratio <= 80:
        return f"심각한 저평가{data_suffix} (강력한 매수 신호)", "bullish"
    elif ratio <= 100:
        return f"저평가{data_suffix} (매수 신호)", "bullish"
    elif ratio <= 120:
        return f"적정 가치{data_suffix} (중립)", "neutral"
    elif ratio <= 140:
        return f"약간 고평가{data_suffix} (주의)", "neutral"
    elif ratio <= 180:
        return f"고평가{data_suffix} (매도 신호)", "bearish"
    else:
        return f"심각한 고평가{data_suffix} (강력한 매도 신호)", "bearish"

def interpret_usd_krw(rate, change_amount, change_pct):
    if rate is None:
        return "데이터 없음", "neutral"
    
    if change_amount > 0:
        arrow = "↗️"
        amount_text = f"(↗️ {change_amount:.1f}원, +{change_pct:.2f}%)"
        sentiment = "bearish"  # 원화 약세
        trend_text = "전일 대비"
    elif change_amount < 0:
        arrow = "↘️"
        amount_text = f"(↘️ {abs(change_amount):.1f}원, {change_pct:.2f}%)"
        sentiment = "bullish"  # 원화 강세
        trend_text = "전일 대비"
    else:
        arrow = "➡️"
        amount_text = "(➡️ 보합)"
        sentiment = "neutral"
        trend_text = "보합"
    
    return f"{trend_text} {amount_text}", sentiment

def get_trading_day_after(data_index, target_date, days_after):
    """
    특정 날짜로부터 정확히 N 달력일 후의 가장 가까운 거래일을 찾는 함수
    """
    try:
        # N 달력일 후의 날짜 계산
        target_calendar_date = target_date + pd.Timedelta(days=days_after)
        
        # 해당 날짜 이후의 첫 번째 거래일 찾기
        future_dates = data_index[data_index >= target_calendar_date]
        
        if len(future_dates) > 0:
            return future_dates[0]
        else:
            return None
    except (KeyError, IndexError):
        return None

def add_nday_later_prices(signal_days, data, days_after):
    """
    각 신호일로부터 정확히 N 달력일 후의 가격을 추가하는 함수
    """
    nday_later_prices = []
    actual_days_list = []
    
    for signal_date in signal_days.index:
        # N 달력일 후의 거래일 찾기
        future_date = get_trading_day_after(data.index, signal_date, days_after)
        
        if future_date is not None and future_date in data.index:
            nday_later_prices.append(data.loc[future_date, 'Close'])
            # 실제 경과된 달력일 계산
            actual_days = (future_date - signal_date).days
            actual_days_list.append(actual_days)
        else:
            nday_later_prices.append(None)
            actual_days_list.append(None)
    
    signal_days[f'Price_{days_after}D_Later'] = nday_later_prices
    signal_days[f'Actual_Days_Later'] = actual_days_list
    return signal_days

def display_metric(title, value, interpretation, sentiment):
    pill_class = f"pill-{sentiment}"
    pill_label = {"bullish": "매수 고려", "bearish": "매도 고려", "neutral": "중립"}.get(sentiment, "")
    value_class = sentiment if sentiment in ("bullish", "bearish") else ""
    st.markdown(f"""
    <div class="metric-card {sentiment}">
        <div class="mc-label">{title}</div>
        <div class="mc-value {value_class}">{value}
            <span class="signal-pill {pill_class}">{pill_label}</span>
        </div>
        <div class="mc-interp">{interpretation}</div>
    </div>
    """, unsafe_allow_html=True)

# Tab 1: Market Sentiment
def market_sentiment_tab():
    col_refresh, col_auto = st.columns([1, 3])
    with col_refresh:
        if st.button("새로고침", key="refresh_market"):
            st.cache_data.clear()
            st.rerun()
    with col_auto:
        auto_refresh = st.checkbox("자동 새로고침 (60초)", key="auto_refresh")

    with st.spinner("시장 데이터 불러오는 중..."):
        # Get all market data
        qqq_price, qqq_sma = get_qqq_data()
        vix = get_vix_data()
        fgi = fetch_fgi()
        pci = fetch_pci()
        usd_krw_rate, usd_krw_change_amount, usd_krw_change_pct = get_usd_krw_rate()
        buffett_ratio, buffett_type = fetch_buffett_indicator()
        
        # Get RSI data
        try:
            spy_data = yf.Ticker("SPY").history(period="50d")["Close"]
            rsi = calculate_rsi(spy_data)
        except:
            rsi = None

    # Display metrics in responsive columns (2x4 grid)
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Fear & Greed Index
        if fgi is not None:
            fgi_interp, fgi_sentiment = interpret_fgi(fgi)
            display_metric("😨 공포 & 탐욕 지수", f"{fgi}/100", fgi_interp, fgi_sentiment)
        else:
            display_metric("😨 공포 & 탐욕 지수", "N/A", "데이터 로딩 실패", "neutral")
        
        # Buffett Indicator (moved to second position)
        if buffett_ratio is not None:
            buffett_interp, buffett_sentiment = interpret_buffett_indicator(buffett_ratio, buffett_type)
            display_metric("💰 버핏 지수 (시총/GDP)", f"{buffett_ratio:.1f}%", buffett_interp, buffett_sentiment)
        else:
            display_metric("💰 버핏 지수 (시총/GDP)", "N/A", "데이터 로딩 실패", "neutral")
        
        # VIX
        if vix is not None:
            vix_interp, vix_sentiment = interpret_vix(vix)
            display_metric("📈 VIX (변동성 지수)", f"{vix:.2f}", vix_interp, vix_sentiment)
        else:
            display_metric("📈 VIX (변동성 지수)", "로딩중...", "데이터 새로고침 중 (잠시 후 다시 시도)", "neutral")
        
        # QQQ vs 200-day SMA
        if qqq_price is not None and qqq_sma is not None:
            price_vs_sma = "bullish" if qqq_price > qqq_sma else "bearish"
            trend_text = "상승 추세" if qqq_price > qqq_sma else "하락 추세"
            percentage_diff = ((qqq_price - qqq_sma) / qqq_sma) * 100
            display_metric("🚀 QQQ vs 200일 이동평균", 
                          f"현재: ${qqq_price:.2f} | 200일 평균: ${qqq_sma:.2f} ({percentage_diff:+.1f}%)", 
                          f"{trend_text} - 200일 이동평균 {'위' if qqq_price > qqq_sma else '아래'}", 
                          price_vs_sma)
        else:
            display_metric("🚀 QQQ vs 200일 이동평균", "N/A", "데이터 로딩 실패", "neutral")

    with col2:
        # Put/Call Ratio
        if pci is not None:
            pci_interp, pci_sentiment = interpret_pci(pci)
            display_metric("⚖️ Put/Call 비율", f"{pci:.3f}", pci_interp, pci_sentiment)
        else:
            display_metric("⚖️ Put/Call 비율", "N/A", "데이터 로딩 실패", "neutral")
        
        # RSI
        if rsi is not None:
            rsi_interp, rsi_sentiment = interpret_rsi(rsi)
            display_metric("📊 RSI (S&P500)", f"{rsi:.1f}", rsi_interp, rsi_sentiment)
        else:
            display_metric("📊 RSI (S&P500)", "N/A", "데이터 로딩 실패", "neutral")
        
        # USD/KRW 환율
        if usd_krw_rate is not None:
            usd_krw_interp, usd_krw_sentiment = interpret_usd_krw(usd_krw_rate, usd_krw_change_amount, usd_krw_change_pct)
            display_metric("🔁 원달러 환율", f"₩{usd_krw_rate:.2f}", usd_krw_interp, usd_krw_sentiment)
        else:
            display_metric("🔁 원달러 환율", "N/A", "데이터 로딩 실패", "neutral")

    st.markdown("""
    <div class="info-card">
        <h4>지표 설명</h4>
        <ul>
            <li><strong>공포 & 탐욕 지수</strong>: 0–100 시장 심리 지표 (0=극도 공포, 100=극도 탐욕)</li>
            <li><strong>VIX</strong>: 시장 변동성 예상 지수. 낮을수록 안정, 높을수록 불안</li>
            <li><strong>Put/Call 비율</strong>: 풋옵션 대비 콜옵션 거래량 비율</li>
            <li><strong>RSI</strong>: 상대강도지수 — 30 이하 과매도, 70 이상 과매수</li>
            <li><strong>QQQ vs 200일 이동평균</strong>: 나스닥 ETF 장기 추세 분석</li>
            <li><strong>버핏 지수</strong>: 미국 시가총액 / GDP. 100% 이하 저평가, 180% 이상 고평가</li>
            <li><strong>원달러 환율</strong>: 상승 시 원화 약세, 하락 시 원화 강세</li>
        </ul>
        <div class="tip">여러 지표를 종합적으로 해석하여 투자 판단에 활용하세요.</div>
    </div>
    """, unsafe_allow_html=True)

    if auto_refresh:
        import time
        time.sleep(60)
        st.rerun()

# Tab 2: N-Day Drop Analysis
def nday_analysis_tab():
    st.markdown("""
    <div class="info-card">
        <h4>분석 개요</h4>
        <ul>
            <li>특정 주식이 N% 이상 하락한 날 기준으로, <strong>며칠 후 주가 방향</strong>을 통계적으로 분석합니다.</li>
            <li><strong>해외 주식</strong>: 티커 입력 (QQQ, AAPL ...) &nbsp;|&nbsp; <strong>국내 주식</strong>: 종목명 또는 6자리 코드</li>
        </ul>
        <div class="tip">주가 하락 시 즉시 매도할지, 기다릴지 통계 근거로 판단하세요.</div>
    </div>
    """, unsafe_allow_html=True)
    

    
    # Input controls
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        ticker_input = st.text_input("📊 종목 입력", 
                                   value="QQQ", 
                                   help="예: QQQ, SPY, AAPL, 삼성전자, 005930 등")
    
    with col2:
        drop_threshold = st.slider("📉 하락 기준 (%)", 
                                 min_value=0.5, max_value=20.0, 
                                 value=1.0, step=0.5,
                                 help="전일 대비 이 퍼센트 이상 하락한 날을 분석")
    
    with col3:
        day_options = {
            "1일": 1,
            "3일": 3,
            "5일": 5,
            "1주(7일)": 7,
            "2주(14일)": 14,
            "1개월(30일)": 30,
            "3개월(90일)": 90,
            "6개월(180일)": 180,
            "1년(365일)": 365
        }
        
        selected_label = st.selectbox(
            "📆 분석 기간 (일)", 
            options=list(day_options.keys()),
            index=1,  # "3일"이 기본값
            help="하락일로부터 며칠 후를 분석할지 선택"
        )
    
        # 실제 값 가져오기
        days_after = day_options[selected_label]
    
    with col4:
        start_date = st.date_input("📅 분석 시작일", 
                                 value=pd.to_datetime("2020-01-01"),
                                 min_value=pd.to_datetime("1990-01-01"),  # 원하는 최소 날짜
                                 max_value=pd.to_datetime("today"),       # 최대 날짜는 오늘로 제한
                                 help="이 날짜부터 현재까지 분석")
    
    # 티커 처리 및 표시
    processed_ticker, company_name = process_ticker_input(ticker_input)
    
    if company_name:
        st.info(f"🇰🇷 한국 주식: **{company_name}** ({processed_ticker}) 분석 준비")
    elif processed_ticker != ticker_input.upper():
        st.info(f"🌏 해외 주식: **{processed_ticker}** 분석 준비")
    
    if st.button("🔍 분석 실행", type="primary", use_container_width=True):
        with st.spinner("데이터를 불러오고 분석 중... 잠시만 기다려주세요."):
            try:
                # Download data
                data = yf.download(processed_ticker, start=start_date)
                
                if data.empty:
                    st.error(f"❌ {processed_ticker} 데이터를 찾을 수 없습니다. 티커를 확인해주세요.")
                    
                    # 한국 주식의 경우 추가 도움말 제공
                    if processed_ticker.endswith(".KS"):
                        st.info("""
                        💡 **한국 주식 입력 방법**:
                        - 회사명 입력: "삼성전자", "SK하이닉스" 등
                        - 6자리 숫자 코드: "005930", "000660" 등
                        - 전체 티커: "005930.KS", "000660.KS" 등
                        """)
                    return
                
                # Process data
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.droplevel(1)
                
                data = data[['Close']].copy()
                data['Pct_Change'] = data['Close'].pct_change() * 100
                
                # Filter signal days (하락 기준 이상 하락한 날)
                signal_days = data[data['Pct_Change'] <= -drop_threshold].copy()
                
                if len(signal_days) == 0:
                    st.warning(f"⚠️ {drop_threshold}% 이상 하락한 날이 없습니다. 기준을 낮춰보세요.")
                    return
                
                # Add N-day later data
                signal_days['Price_Today'] = signal_days['Close']
                
                # 정확한 거래일 기준으로 N일 후 가격 계산
                signal_days = add_nday_later_prices(signal_days, data, days_after)
                
                # NaN 값 제거 (N일 후 데이터가 없는 경우)
                signal_days = signal_days.dropna(subset=[f'Price_{days_after}D_Later'])
                
                # 실제 달력일 수 검증을 위한 추가 정보 표시
                if len(signal_days) > 0:
                    avg_actual_days = signal_days['Actual_Days_Later'].mean()
                    st.info(f"📅 목표: {days_after}일 후 → 실제 평균: {avg_actual_days:.1f}일 후 데이터 사용 (주말/공휴일로 인한 차이)")
                
                if len(signal_days) == 0:
                    st.warning(f"⚠️ {days_after}일 후 데이터가 있는 하락일이 없습니다. 기간을 조정해보세요.")
                    return
                
                # Win/Lose 판단
                signal_days['Result'] = signal_days.apply(
                    lambda row: 'Win' if row['Price_Today'] > row[f'Price_{days_after}D_Later'] else 'Lose',
                    axis=1
                )
                
                # Calculate price change
                signal_days[f'Price_Change_{days_after}D'] = (
                    (signal_days[f'Price_{days_after}D_Later'] - signal_days['Price_Today']) / signal_days['Price_Today'] * 100
                )
                
                # 결과 요약
                counts = signal_days['Result'].value_counts()
                total_signals = len(signal_days)
                win_count = counts.get('Win', 0)
                lose_count = counts.get('Lose', 0)
                winrate = (win_count / total_signals) if total_signals > 0 else 0
                rate = winrate*100
                
                # Display main results
                display_ticker = f"{company_name} ({processed_ticker})" if company_name else processed_ticker
                st.success(f"✅ **{display_ticker}** 분석 완료! {total_signals}개의 하락 신호를 분석했습니다.")
                
                # Main metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📊 총 신호", f"{total_signals}회")
                
                with col2:
                    st.metric("📈 평균 하락률", f"{signal_days['Pct_Change'].mean():.2f}%")
                    
                with col3:
                    st.metric("📉 최대 하락률", f"{signal_days['Pct_Change'].min():.2f}%")
                    
                with col4:
                    avg_nd_change = signal_days[f'Price_Change_{days_after}D'].mean()
                    st.metric(f"🔄 평균 {days_after}일 변화", f"{avg_nd_change:+.2f}%")
                
                st.markdown("---")
                
                # Win/Lose breakdown
                st.subheader(f"🎯 {days_after}일 후 하락 여부 분석 결과")
                
                result_cols = st.columns(2)
                
                with result_cols[0]:
                    win_percentage = (win_count / total_signals) * 100
                    st.markdown(f"""
                    <div class="result-card sell">
                        <h4>즉시 매도가 유리했던 경우</h4>
                        <div class="big-num">{win_percentage:.1f}%</div>
                        <p>{win_count}회 — 하락일 즉시 매도 시 {days_after}일 후보다 유리</p>
                    </div>
                    """, unsafe_allow_html=True)

                with result_cols[1]:
                    lose_percentage = (lose_count / total_signals) * 100
                    st.markdown(f"""
                    <div class="result-card buy">
                        <h4>기다리는 것이 유리했던 경우</h4>
                        <div class="big-num">{lose_percentage:.1f}%</div>
                        <p>{lose_count}회 — {days_after}일 후 가격이 하락일보다 높았음</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown('<hr>', unsafe_allow_html=True)
                st.markdown('<div class="section-title">투자 전략 제안</div>', unsafe_allow_html=True)

                ticker_display = company_name if company_name else processed_ticker

                if winrate > 0.55:
                    strategy_html = f"""
                    <div class="strategy-card sell-strat">
                        <h4>즉시 매도 전략 추천</h4>
                        <p><strong>{rate:.1f}%</strong> 확률로 즉시 매도가 유리했습니다.</p>
                        <p>{ticker_display} 종목이 {drop_threshold}% 이상 하락하면 매도를 고려하세요.</p>
                    </div>"""
                elif winrate < 0.45:
                    strategy_html = f"""
                    <div class="strategy-card buy-strat">
                        <h4>대기 전략 추천</h4>
                        <p><strong>{(100-rate):.1f}%</strong> 확률로 {days_after}일 기다리는 것이 유리했습니다.</p>
                        <p>{ticker_display} 종목이 {drop_threshold}% 이상 하락해도 {days_after}일은 기다려보세요.</p>
                    </div>"""
                else:
                    strategy_html = f"""
                    <div class="strategy-card neutral-strat">
                        <h4>중립적 결과</h4>
                        <p>즉시 매도 {rate:.1f}% vs 대기 {(100-rate):.1f}% — 성공률이 비슷합니다.</p>
                        <p>다른 지표와 함께 종합적으로 판단하세요.</p>
                    </div>"""

                st.markdown(strategy_html, unsafe_allow_html=True)
                
                # Recent examples
                if len(signal_days) > 0:
                    st.markdown("---")
                    st.subheader("📅 최근 하락 신호 사례 (최근 50개)")
                    
                    recent_signals = signal_days.tail(50).sort_index(ascending=False).copy()          
                    recent_signals.index = recent_signals.index.strftime('%Y-%m-%d')
                    
                    # Prepare display data
                    display_data = recent_signals[['Pct_Change', 'Price_Today', f'Price_{days_after}D_Later', f'Price_Change_{days_after}D', 'Result']].copy()
                    
                    # 가격 단위 조정 (한국 주식의 경우)
                    if company_name:
                        display_data.columns = ['하락률(%)', '당일종가(₩)', f'{days_after}일후종가(₩)', f'{days_after}일간변화(%)', '결과']
                        # 한국 주식은 원 단위로 표시 (소수점 제거)
                        display_data['당일종가(₩)'] = display_data['당일종가(₩)'].round(0).astype(int)
                        display_data[f'{days_after}일후종가(₩)'] = display_data[f'{days_after}일후종가(₩)'].round(0).astype(int)
                        display_data['하락률(%)'] = display_data['하락률(%)'].round(2)
                        display_data[f'{days_after}일간변화(%)'] = display_data[f'{days_after}일간변화(%)'].round(2)
                    else:
                        display_data.columns = ['하락률(%)', '당일종가($)', f'{days_after}일후종가($)', f'{days_after}일간변화(%)', '결과']
                        display_data = display_data.round(2)

                    display_data['결과'] = display_data['결과'].map({
                        'Win': f'{days_after}일 후 📉',
                        'Lose': f'{days_after}일 후 📈'
                    })
                    
                    # Color code the results
                    def color_result(val):
                        if val == f'{days_after}일 후 📉':
                            return 'background-color: #f8d7da; color: #721c24'
                        elif val == f'{days_after}일 후 📈':
                            return 'background-color: #d4edda; color: #155724'
                        return ''
                    
                    def color_change(val):
                        if val > 0:
                            return 'color: #28a745; font-weight: bold'
                        elif val < 0:
                            return 'color: #dc3545; font-weight: bold'
                        return ''

                    styled_df = display_data.style.applymap(color_result, subset=['결과']) \
                                                  .applymap(color_change, subset=[f'{days_after}일간변화(%)'])
                    
                    st.dataframe(styled_df, use_container_width=True)
                        
                # Additional statistics
                st.markdown("---")
                st.subheader("📈 상세 통계")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    avg_win_change = signal_days[signal_days['Result'] == 'Win'][f'Price_Change_{days_after}D'].mean()
                    st.metric(f"하락 시 평균 {days_after}일 변화", f"{avg_win_change:+.2f}%" if not pd.isna(avg_win_change) else "N/A")
                
                with col2:
                    avg_lose_change = signal_days[signal_days['Result'] == 'Lose'][f'Price_Change_{days_after}D'].mean()
                    st.metric(f"상승 시 평균 {days_after}일 변화", f"{avg_lose_change:+.2f}%" if not pd.isna(avg_lose_change) else "N/A")
                
                with col3:
                    median_change = signal_days[f'Price_Change_{days_after}D'].median()
                    st.metric(f"{days_after}일 변화 중간값", f"{median_change:+.2f}%")
                
                st.markdown("""
                <div class="info-card">
                    <h4>주의사항</h4>
                    <ul>
                        <li>과거 데이터 기반 통계 분석입니다. 미래 수익을 보장하지 않습니다.</li>
                        <li>실제 투자 결정 시 기술적·기본적 분석과 함께 활용하세요.</li>
                        <li>시장 상황에 따라 과거 패턴이 반복되지 않을 수 있습니다.</li>
                        <li>미국 주식은 환율 변동 등 추가 요인을 고려해야 합니다.</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ 분석 중 오류가 발생했습니다: {str(e)}")
                st.info("💡 다른 티커를 시도하거나 날짜 범위를 조정해보세요.")
                
                # 한국 주식 관련 오류인 경우 추가 도움말
                if processed_ticker.endswith(".KS"):
                    st.warning("""
                    🇰🇷 **한국 주식 관련 팁**:
                    - 일부 한국 주식은 yfinance에서 데이터가 제한적일 수 있습니다.
                    - 상장 폐지되었거나 최근 상장한 종목은 데이터가 없을 수 있습니다.
                    - 분석 시작일을 더 최근으로 설정해보세요.
                    """)

# Main App
def main():
    st.markdown("""
    <div class="app-header">
        <div class="logo">Stock<span>Analyzer</span></div>
        <span class="badge">Beta</span>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["시장 심리 지표", "N일 후 하락 분석"])

    with tab1:
        market_sentiment_tab()

    with tab2:
        nday_analysis_tab()

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    st.markdown(f"""
    <hr>
    <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.78rem; color:#94a3b8; padding: 0 0.25rem;">
        <span>StockAnalyzer &nbsp;·&nbsp; 미국·한국 주식, 인덱스, 코인 지원</span>
        <span>업데이트 {current_time} &nbsp;·&nbsp; 투자 참고용, 실제 투자 결정의 근거로 사용하지 마세요</span>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()








