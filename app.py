import requests
import pandas as pd
import streamlit as st
from datetime import datetime
import time

# ====================== 기본 설정 ======================
st.set_page_config(page_title="📊 FMP 재무비율 조회기", layout="wide")
st.title("📊 기업 재무비율 조회기 — Financial Modeling Prep (FMP API)")
st.caption("티커를 입력하면 FMP API에서 부채비율·유동비율·ROE(%)를 자동 계산합니다.")

# ====================== 함수 정의 ======================
def get_fmp_json(endpoint: str, symbol: str, api_key: str):
    """FMP API JSON 데이터 가져오기"""
    try:
        url = f"https://financialmodelingprep.com/api/v3/{endpoint}/{symbol}?limit=1&apikey={api_key}"
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0]
        return None
    except Exception as e:
        st.write(f"⚠️ API 요청 오류: {e}")
        return None


def get_debt_to_equity(symbol, api_key):
    """부채비율 (총부채 / 자기자본 × 100%)"""
    data = get_fmp_json("balance-sheet-statement", symbol, api_key)
    if not data:
        return "N/A"
    try:
        total_debt = float(data.get("totalLiabilities", 0))
        equity = float(data.get("totalStockholdersEquity", 0))
        if equity != 0:
            return round((total_debt / equity) * 100, 2)
    except Exception:
        pass
    return "N/A"


def get_current_ratio(symbol, api_key):
    """유동비율 (유동자산 / 유동부채 × 100%)"""
    data = get_fmp_json("balance-sheet-statement", symbol, api_key)
    if not data:
        return "N/A"
    try:
        current_assets = float(data.get("totalCurrentAssets", 0))
        current_liabilities = float(data.get("totalCurrentLiabilities", 0))
        if current_liabilities != 0:
            return round((current_assets / current_liabilities) * 100, 2)
    except Exception:
        pass
    return "N/A"


def get_roe(symbol, api_key):
    """ROE (순이익 / 자기자본 × 100%)"""
    income_data = get_fmp_json("income-statement", symbol, api_key)
    balance_data = get_fmp_json("balance-sheet-statement", symbol, api_key)
    if not income_data or not balance_data:
        return "N/A"
    try:
        net_income = float(income_data.get("netIncome", 0))
        equity = float(balance_data.get("totalStockholdersEquity", 0))
        if equity != 0:
            return round((net_income / equity) * 100, 2)
    except Exception:
        pass
    return "N/A"

# ====================== UI ======================
st.subheader("🔑 FMP API 키 입력")
api_key = st.text_input("https://financialmodelingprep.com 에서 무료 API 키를 발급받아 입력하세요.", type="password")

st.subheader("📋 티커 목록 입력 (줄바꿈 또는 쉼표로 구분)")
ticker_input = st.text_area("예시: AAPL, MSFT, NVDA, AMZN, LMT", height=150)

if st.button("📈 재무비율 조회"):
    if not api_key:
        st.error("API Key를 입력해주세요.")
    else:
        tickers = [t.strip().upper() for t in ticker_input.replace("\n", ",").split(",") if t.strip()]
        if not tickers:
            st.warning("티커를 입력해주세요.")
        else:
            st.info(f"{len(tickers)}개 티커 분석 중... 잠시만 기다려주세요.")
            results = []
            progress = st.progress(0)

            for i, ticker in enumerate(tickers):
                dte = get_debt_to_equity(ticker, api_key)
                cr = get_current_ratio(ticker, api_key)
                roe = get_roe(ticker, api_key)
                results.append({
                    "ticker": ticker,
                    "debtToEquity(%)": dte,
                    "currentRatio(%)": cr,
                    "ROE(%)": roe,
                    "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                progress.progress((i + 1) / len(tickers))
                time.sleep(0.3)

            df = pd.DataFrame(results)
            st.success("✅ 완료! 아래에서 결과를 확인하세요.")
            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📤 결과 CSV 다운로드", csv, "financial_ratios_result.csv", "text/csv")
