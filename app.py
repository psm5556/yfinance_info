import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import io

# ---------------------------
# Streamlit 기본 설정
# ---------------------------
st.set_page_config(page_title="📊 재무지표 조회기 (FMP API)", layout="wide")
st.title("📊 미국주식 재무지표 분석기 — FMP API 기반")
st.caption("D/E, Current Ratio, ROE, Runway, TotalCash, FreeCashflow (USD, M$)")

# ---------------------------
# API 설정
# ---------------------------
API_KEY = st.secrets.get("FMP_API_KEY", None)
if not API_KEY:
    st.warning("⚠️ FMP API Key가 설정되어 있지 않습니다. [https://financialmodelingprep.com/developer/docs/] 에서 발급 후 secrets.toml에 추가하세요.")
    st.stop()

BASE = "https://financialmodelingprep.com/api/v3"

def get_financial_data(ticker):
    try:
        # 기본 재무제표
        bs_url = f"{BASE}/balance-sheet-statement/{ticker}?limit=1&apikey={API_KEY}"
        cf_url = f"{BASE}/cash-flow-statement/{ticker}?limit=1&apikey={API_KEY}"
        is_url = f"{BASE}/income-statement/{ticker}?limit=1&apikey={API_KEY}"
        profile_url = f"{BASE}/profile/{ticker}?apikey={API_KEY}"

        bs = requests.get(bs_url).json()
        cf = requests.get(cf_url).json()
        is_ = requests.get(is_url).json()
        profile = requests.get(profile_url).json()

        if not bs or not cf or not is_:
            return None

        bs, cf, is_ = bs[0], cf[0], is_[0]
        total_debt = (bs.get("longTermDebt") or 0) + (bs.get("shortTermDebt") or 0)
        total_equity = bs.get("totalStockholdersEquity") or 0
        current_assets = bs.get("totalCurrentAssets") or 0
        current_liabilities = bs.get("totalCurrentLiabilities") or 0
        total_cash = bs.get("cashAndShortTermInvestments") or 0
        free_cf = cf.get("freeCashFlow") or cf.get("operatingCashFlow") or 0
        net_income = is_.get("netIncome") or 0

        # 비율 계산
        dte = round(total_debt / total_equity * 100, 2) if total_equity else None
        cr = round(current_assets / current_liabilities * 100, 2) if current_liabilities else None
        roe = round(net_income / total_equity * 100, 2) if total_equity and net_income else None

        total_cash_m = round(total_cash / 1_000_000, 2) if total_cash else None
        free_cf_m = round(free_cf / 1_000_000, 2) if free_cf else None

        runway_years = None
        if total_cash and free_cf:
            if free_cf < 0:
                runway_years = round(total_cash / abs(free_cf), 2)
            elif free_cf >= 0:
                runway_years = float("inf")

        return {
            "Ticker": ticker,
            "D/E(%)": dte,
            "CurrentRatio(%)": cr,
            "ROE(%)": roe,
            "Runway(Years)": runway_years,
            "TotalCash(M$)": total_cash_m,
            "FreeCashflow(M$)": free_cf_m,
            "LastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    except Exception as e:
        st.warning(f"⚠️ {ticker}: 오류 ({e})")
        return None

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
        data = get_financial_data(tkr)
        if data:
            results.append(data)
        progress_bar.progress(i / len(tickers))

    if results:
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
        st.error("❌ 데이터를 가져오지 못했습니다.")
else:
    st.info("왼쪽 사이드바에 티커를 입력하고 **[🚀 실행]**을 눌러주세요.")
