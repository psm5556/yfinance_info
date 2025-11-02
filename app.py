import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime
import time

# 페이지 설정
st.set_page_config(page_title="📊 재무비율 조회기", layout="wide")
st.title("📊 기업 재무비율 조회기 (D/E%, Current%, ROE%)")
st.caption("티커 목록을 입력하면 부채비율·유동비율·ROE를 자동 계산합니다.")

# ===================== 공통 유틸 =====================
def safe_balance_sheet(ticker):
    """balance_sheet를 안전하게 가져오기"""
    try:
        bs = ticker.balance_sheet
        if bs is None or bs.empty:
            bs = ticker.quarterly_balance_sheet
        return bs
    except Exception:
        return None

def safe_financials(ticker):
    """financials를 안전하게 가져오기"""
    try:
        fs = ticker.financials
        if fs is None or fs.empty:
            fs = ticker.quarterly_financials
        return fs
    except Exception:
        return None

def get_balance_sheet_value(bs, patterns):
    """패턴에 맞는 항목을 balance sheet에서 찾기"""
    if bs is None or bs.empty or len(bs.columns) == 0:
        return None
    latest_col = bs.columns[0]
    for pattern in patterns:
        match = [idx for idx in bs.index if pattern.lower() in str(idx).lower()]
        if match:
            val = bs.loc[match[0], latest_col]
            if pd.notna(val) and val != 0:
                return float(val)
    return None

# ===================== 주요 계산 함수 =====================
def get_debt_to_equity(ticker_symbol):
    """부채비율 (Debt / Equity × 100%)"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        bs = safe_balance_sheet(ticker)
        if bs is not None and not bs.empty:
            debt = get_balance_sheet_value(bs, ["Total Debt", "Net Debt"])
            equity = get_balance_sheet_value(bs, ["Stockholders Equity", "Total Equity", "Shareholder Equity"])
            if debt is not None and equity not in (None, 0):
                return round((debt / equity) * 100, 2)
    except Exception as e:
        st.write(f"⚠️ {ticker_symbol} D/E Error: {e}")
    return None

def get_current_ratio(ticker_symbol):
    """유동비율 (Current Assets / Current Liabilities × 100%)"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        bs = safe_balance_sheet(ticker)
        if bs is not None and not bs.empty:
            ca = get_balance_sheet_value(bs, ["Current Assets"])
            cl = get_balance_sheet_value(bs, ["Current Liabilities"])
            if ca is not None and cl not in (None, 0):
                return round((ca / cl) * 100, 2)
    except Exception as e:
        st.write(f"⚠️ {ticker_symbol} Current Ratio Error: {e}")
    return None

def get_roe(ticker_symbol):
    """ROE (Net Income / Equity × 100%)"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        income_stmt = safe_financials(ticker)
        bs = safe_balance_sheet(ticker)
        if income_stmt is not None and not income_stmt.empty and bs is not None and not bs.empty:
            net_income = get_balance_sheet_value(income_stmt, ["Net Income", "NetIncome", "Net Income Common"])
            equity = get_balance_sheet_value(bs, ["Stockholders Equity", "Total Equity", "Shareholder Equity"])
            if net_income is not None and equity not in (None, 0):
                return round((net_income / equity) * 100, 2)
    except Exception as e:
        st.write(f"⚠️ {ticker_symbol} ROE Error: {e}")
    return None

# ===================== UI =====================
st.subheader("티커 목록 입력 (줄바꿈 또는 쉼표로 구분)")
ticker_input = st.text_area("예시: AAPL, MSFT, NVDA, AMZN", height=150)

if st.button("📈 재무비율 조회"):
    tickers = [t.strip().upper() for t in ticker_input.replace("\n", ",").split(",") if t.strip()]
    if not tickers:
        st.warning("❗ 티커를 입력해주세요.")
    else:
        st.info(f"{len(tickers)}개 티커 분석 중... 잠시만 기다려주세요.")
        results = []
        progress = st.progress(0)

        for i, ticker in enumerate(tickers):
            dte = get_debt_to_equity(ticker)
            cr = get_current_ratio(ticker)
            roe = get_roe(ticker)
            results.append({
                "ticker": ticker,
                "debtToEquity(%)": dte,
                "currentRatio(%)": cr,
                "ROE(%)": roe,
                "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            progress.progress((i + 1) / len(tickers))
            time.sleep(0.2)

        df = pd.DataFrame(results)
        st.success("✅ 완료! 아래에서 결과를 확인하세요.")
        st.dataframe(df, use_container_width=True)

        # CSV 다운로드
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📤 결과 CSV 다운로드", csv, "financial_ratios_result.csv", "text/csv")
