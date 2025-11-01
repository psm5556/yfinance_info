import streamlit as st
import yfinance as yf
import json

st.set_page_config(page_title="Finance API")

st.title("📡 Finance Data API (for Google Sheets)")

ticker = st.query_params.get("ticker", "")
field = st.query_params.get("field", "")

import yfinance as yf
import pandas as pd

def get_data(ticker, field):
    t = yf.Ticker(ticker)

    # 기본 정보 안전 조회
    try:
        info = t.get_info()
    except Exception:
        info = getattr(t, "fast_info", {})

    # ------------------------------
    # ① 가격 (price)
    # ------------------------------
    if field == "price":
        try:
            df = t.history(period="1d")
            return float(df["Close"].iloc[-1])
        except Exception:
            return "N/A"

    # ------------------------------
    # ② 부채비율 (Debt to Equity)
    # ------------------------------
    if field == "debtToEquity":
        try:
            bs = t.balance_sheet
            if bs is None or bs.empty:
                return "N/A"

            # 대표 컬럼 (가장 최근 연도)
            latest_col = bs.columns[0]

            # 다양한 항목명 케이스 대응
            debt_candidates = ["Total Debt", "Long Term Debt", "Total Liabilities"]
            equity_candidates = ["Total Stockholder Equity", "Total Shareholder Equity", "Stockholders Equity"]

            debt = next((bs.loc[name, latest_col] for name in debt_candidates if name in bs.index), None)
            equity = next((bs.loc[name, latest_col] for name in equity_candidates if name in bs.index), None)

            if debt and equity and equity != 0:
                return round(float(debt) / float(equity), 2)
            else:
                return "N/A"
        except Exception:
            return "N/A"

    # ------------------------------
    # ③ 유동비율 (Current Ratio)
    # ------------------------------
    if field == "currentRatio":
        try:
            bs = t.balance_sheet
            if bs is None or bs.empty:
                return "N/A"

            latest_col = bs.columns[0]
            ca_candidates = ["Total Current Assets", "Current Assets"]
            cl_candidates = ["Total Current Liabilities", "Current Liabilities"]

            ca = next((bs.loc[name, latest_col] for name in ca_candidates if name in bs.index), None)
            cl = next((bs.loc[name, latest_col] for name in cl_candidates if name in bs.index), None)

            if ca and cl and cl != 0:
                return round(float(ca) / float(cl), 2)
            else:
                return "N/A"
        except Exception:
            return "N/A"

    # ------------------------------
    # ④ 기본 info / fast_info 항목
    # ------------------------------
    try:
        if field in info:
            return info[field]
        elif hasattr(t, "fast_info") and field in t.fast_info:
            return t.fast_info[field]
        else:
            return "N/A"
    except Exception:
        return "N/A"




if ticker and field:
    result = get_data(ticker, field)
    st.json({"ticker": ticker, "field": field, "value": result})
else:
    st.write("Use as: https://yfinanceinfo-n9gbqx6wbjrerkqvucghhl.streamlit.app/?ticker=AAPL&field=debtToEquity")
