import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import io
import time

st.set_page_config(page_title="📊 재무지표 조회기 (Runway 포함)", layout="wide")
st.title("📊 미국주식 재무지표 분석기 — 안정 완성 버전")
st.caption("Yahoo Finance 최신 구조 대응 — D/E, CurrentRatio, ROE, Runway 자동 계산")

# ---------------------------
# 유틸 함수
# ---------------------------
def flexible_get(df, patterns):
    """여러 패턴 중 일치하는 항목을 찾아 반환"""
    if df is None or df.empty:
        return None
    for p in patterns:
        match = [idx for idx in df.index if p.lower() in str(idx).lower()]
        if match:
            val = df.loc[match[0]].iloc[0]
            if pd.notna(val):
                return val
    return None

# ---------------------------
# 재무 지표 계산 함수
# ---------------------------
def get_financial_ratios(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        bs = ticker.balance_sheet
        cf = ticker.cashflow
        is_ = ticker.income_stmt

        # ✅ Balance Sheet
        total_debt = (
            (flexible_get(bs, ["total debt", "long term debt", "long term debt noncurrent"]) or 0)
            + (flexible_get(bs, ["short term debt", "short long term debt"]) or 0)
        )
        total_equity = flexible_get(bs, ["total stockholder equity", "total shareholders' equity"]) or 0
        total_assets = flexible_get(bs, ["total assets"]) or 0
        current_assets = flexible_get(bs, ["total current assets"]) or 0
        current_liab = flexible_get(bs, ["total current liabilities"]) or 0
        total_cash = flexible_get(bs, ["cash", "cash and cash equivalents"]) or 0

        # ✅ Cashflow
        free_cf = flexible_get(cf, ["free cash flow", "total cash from operating activities"]) or 0

        # ✅ Income Statement
        net_income = flexible_get(is_, ["net income", "net income applicable to common shares"]) or 0

        # 🔹 비율 계산
        dte = round(total_debt / total_equity * 100, 2) if total_equity else None
        cr = round(current_assets / current_liab * 100, 2) if current_liab else None
        roe = round(net_income / total_equity * 100, 2) if total_equity and net_income else None

        # 🔹 Runway 계산
        total_cash_m = round(total_cash / 1_000_000, 2) if total_cash else None
        free_cf_m = round(free_cf / 1_000_000, 2) if free_cf else None

        runway_years = None
        if total_cash and free_cf:
            if free_cf < 0:
                runway_years = round(total_cash / abs(free_cf), 2)
            elif free_cf >= 0:
                runway_years = float("inf")

        return {
            "Ticker": ticker_symbol,
            "D/E(%)": dte,
            "CurrentRatio(%)": cr,
            "ROE(%)": roe,
            "Runway(Years)": runway_years,
            "TotalCash(M$)": total_cash_m,
            "FreeCashflow(M$)": free_cf_m,
            "LastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
            "LastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
