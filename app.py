import streamlit as st
import yfinance as yf
import json

st.set_page_config(page_title="Finance API")

st.title("📡 Finance Data API (for Google Sheets)")

ticker = st.query_params.get("ticker", "")
field = st.query_params.get("field", "")

def get_data(ticker, field):
    t = yf.Ticker(ticker)

    # 우선 안전하게 info 조회 시도
    try:
        info = t.get_info()
    except Exception:
        info = t.fast_info  # 빠르고 안정적
    
    if not info:
        return "No data"

    # 필드 처리
    if field in info:
        return info[field]
    elif field == "price":
        df = t.history(period="1d")
        return df["Close"].iloc[-1]
    elif field in t.fast_info:
        return t.fast_info[field]
    else:
        return f"Field '{field}' not found"


if ticker and field:
    result = get_data(ticker, field)
    st.json({"ticker": ticker, "field": field, "value": result})
else:
    st.write("Use as: https://yfinanceinfo-n9gbqx6wbjrerkqvucghhl.streamlit.app/?ticker=AAPL&field=debtToEquity")
