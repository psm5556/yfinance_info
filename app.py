import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime
import time

st.set_page_config(page_title="📊 재무비율 조회기", layout="wide")
st.title("📊 기업 재무비율 조회기 (D/E%, Current%, ROE%)")
st.caption("Yahoo Finance에서 재무제표를 자동으로 가져옵니다. (데이터가 없을 경우 N/A 표시)")

# ===================== 안전한 접근 함수 =====================
def safe_balance_sheet(ticker):
    try:
        bs = ticker.get_balance_sheet()
        if bs is None or bs.empty:
            bs = ticker.get_balance_sheet(freq="quarterly")
        return bs
    except Exception:
        return None

def safe_financials(ticker):
    try:
        fs = ticker.get_financials()
        if fs is None or fs.empty:
            fs = ticker.get_financials(freq="quarterly")
        return fs
    except Exception:
        return None

def get_balance_sheet_value(bs, patterns):
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

# ===================== 비율 계산 =====================
def get_debt_to_equity(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        bs = safe_balance_sheet(ticker)
        if bs is not None and not bs.empty:
            debt = get_balance_sheet_value(bs, ["Total Debt", "Net Debt"])
            equity = get_balance_sheet_value(bs, ["Stockholders Equity", "Total Equity", "Shareholder Equity"])
            if debt and equity and equity != 0:
                return round((debt / equity) * 100, 2)

        # fallback (info)
        info = ticker.get_info()
        debt = info.get("totalDebt")
        equity = info.get("totalStockholderEquity")
        if debt and equity and equity != 0:
            return round((debt / equity) * 100, 2)
    except Exception:
        pass
    return "N/A"

def get_current_ratio(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        bs = safe_balance_sheet(ticker)
        if bs is not None and not bs.empty:
            ca = get_balance_sheet_value(bs, ["Current Assets"])
            cl = get_balance_sheet_value(bs, ["Current Liabilities"])
            if ca and cl and cl != 0:
                return round((ca / cl) * 100, 2)

        # fallback
        info = ticker.get_info()
        current_ratio = info.get("currentRatio")
        if current_ratio:
            return round(current_ratio * 100, 2)
    except Exception:
        pass
    return "N/A"

def get_roe(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        fs = safe_financials(ticker)
        bs = safe_balance_sheet(ticker)
        if fs is not None and not fs.empty and bs is not None and not bs.empty:
            net_income = get_balance_sheet_value(fs, ["Net Income"])
            equity = get_balance_sheet_value(bs, ["Stockholders Equity", "Total Equity", "Shareholder Equity"])
            if net_income and equity and equity != 0:
                return round((net_income / equity) * 100, 2)

        # fallback
        info = ticker.get_info()
        roe = info.get("returnOnEquity")
        if roe:
            return round(roe * 100, 2)
    except Exception:
        pass
    return "N/A"

# ===================== Streamlit UI =====================
st.subheader("티커 목록 입력 (줄바꿈 또는 쉼표로 구분)")
ticker_input = st.text_area("예시: AAPL, MSFT, NVDA, AMZN, LMT", height=150)

if st.button("📈 재무비율 조회"):
    tickers = [t.strip().upper() for t in ticker_input.replace("\n", ",").split(",") if t.strip()]
    if not tickers:
        st.warning("티커를 입력해주세요.")
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

        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📤 결과 CSV 다운로드", csv, "financial_ratios_result.csv", "text/csv")
