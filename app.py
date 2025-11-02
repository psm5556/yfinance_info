import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import io
import time

st.set_page_config(page_title="📊 재무지표 조회기 (Runway 포함)", layout="wide")
st.title("📊 미국주식 재무지표 분석기 — 안정 버전")
st.caption("Yahoo Finance 최신 API 기반 (info 폐기 대응 버전)")

# ---------------------------
# 안전한 재무 지표 계산 함수
# ---------------------------
def safe_get(df, key):
    try:
        return df.loc[key].iloc[0]
    except Exception:
        return None

def get_financial_ratios(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        bs = ticker.balance_sheet
        cf = ticker.cashflow
        is_ = ticker.income_stmt
        fast = ticker.fast_info

        total_debt = 0
        total_assets = 0
        current_assets = 0
        current_liab = 0
        total_equity = 0
        total_cash = None
        free_cf = None

        if bs is not None and not bs.empty:
            total_debt = (safe_get(bs, "Long Term Debt") or 0) + (safe_get(bs, "Short Long Term Debt") or 0)
            total_assets = safe_get(bs, "Total Assets") or 0
            current_assets = safe_get(bs, "Total Current Assets") or 0
            current_liab = safe_get(bs, "Total Current Liabilities") or 0
            total_equity = safe_get(bs, "Total Stockholder Equity") or 0
            total_cash = safe_get(bs, "Cash") or safe_get(bs, "Cash And Cash Equivalents")

        if cf is not None and not cf.empty:
            free_cf = safe_get(cf, "Total Cash From Operating Activities")

        # D/E, Current Ratio, ROE
        dte = round(total_debt / total_equity * 100, 2) if total_equity else None
        cr = round(current_assets / current_liab * 100, 2) if current_liab else None

        roe = None
        if is_ is not None and not is_.empty and total_equity:
            net_income = safe_get(is_, "Net Income")
            if net_income:
                roe = round(net_income / total_equity * 100, 2)

        # Runway 계산
        total_cash_m = round(total_cash / 1_000_000, 2) if total_cash else None
        free_cf_m = round(free_cf / 1_000_000, 2) if free_cf else None
        runway_years = None
        if total_cash and free_cf:
            if free_cf < 0:
                runway_years = round(total_cash / abs(free_cf), 2)
            elif free_cf >= 0:
                runway_years = float('inf')

        return {
            "Ticker": ticker_symbol,
            "D/E(%)": dte,
            "CurrentRatio(%)": cr,
            "ROE(%)": roe,
            "Runway(Years)": runway_years,
            "TotalCash(M$)": total_cash_m,
            "FreeCashflow(M$)": free_cf_m,
            "LastUpdated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    except Exception as e:
        st.warning(f"⚠️ {ticker_symbol}: 데이터 오류 ({e})")
        return {
            "Ticker": ticker_symbol,
            "D/E(%)": None,
            "CurrentRatio(%)": None,
            "ROE(%)": None,
            "Runway(Years)": None,
            "TotalCash(M$)": None,
            "FreeCashflow(M$)": None,
            "LastUpdated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

# ---------------------------
# Streamlit UI
# ---------------------------
st.sidebar.header("⚙️ 설정")
st.sidebar.markdown("티커를 쉼표(,) 또는 줄바꿈으로 구분해서 입력하세요.")
tickers_input = st.sidebar.text_area("티커 입력", "AAPL\nMSFT\nNVDA")
run_btn = st.sidebar.button("🚀 실행")

if run_btn:
    tickers = [t.strip().upper() for t in tickers_input.replace(",", "\n").split("\n") if t.strip()]
    st.write(f"✅ 총 {len(tickers)}개 티커 분석 시작")

    results = []
    progress_bar = st.progress(0)
    status = st.empty()

    for i, tkr in enumerate(tickers, 1):
        status.text(f"⏳ {i}/{len(tickers)} 처리 중: {tkr}")
        res = get_financial_ratios(tkr)
        results.append(res)
        progress_bar.progress(i / len(tickers))
        time.sleep(0.5)

    df = pd.DataFrame(results)
    st.success("✅ 모든 티커 처리 완료!")
    st.dataframe(df, use_container_width=True)

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="📥 CSV로 다운로드",
        data=csv_buffer.getvalue(),
        file_name=f"financial_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
else:
    st.info("왼쪽 사이드바에 티커를 입력하고 **[🚀 실행]**을 눌러주세요.")
