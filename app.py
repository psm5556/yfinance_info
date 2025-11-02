import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import io
import time

st.set_page_config(page_title="📊 재무지표 조회기 (Runway 포함)", layout="wide")
st.title("📊 미국주식 재무지표 분석기 — Yahoo Finance 기반")
st.caption("부채비율(D/E), 유동비율(Current Ratio), ROE, Runway, 현금/현금흐름(M$) 계산")

# ---------------------------
# 재무 데이터 조회 함수
# ---------------------------
def get_financial_ratios(ticker_symbol):
    """Yahoo Finance 제공 지표(D/E, Current Ratio, ROE) + freeCashflow 기반 Runway 계산"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        dte = info.get("debtToEquity")
        cr = info.get("currentRatio")
        roe = info.get("returnOnEquity")
        total_cash = info.get("totalCash")
        free_cf = info.get("freeCashflow")

        if cr is not None:
            cr = round(cr * 100, 2)
        if roe is not None:
            roe = round(roe * 100, 2)

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
        st.warning(f"⚠️ {ticker_symbol}: 데이터 불러오기 실패 ({e})")
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
# Streamlit UI 구성
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

    # ---------------------------
    # CSV 다운로드 기능
    # ---------------------------
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
