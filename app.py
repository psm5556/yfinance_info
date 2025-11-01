import streamlit as st
import yfinance as yf
import json

st.set_page_config(page_title="Finance API")

st.title("📡 Finance Data API (for Google Sheets)")

ticker = st.query_params.get("ticker", "")
field = st.query_params.get("field", "")

def get_data(ticker, field):
    t = yf.Ticker(ticker)
    info = t.info
    # 안전하게 key 체크
    if field in info:
        return info[field]
    elif field == "price":
        df = t.history(period="1d")
        return df["Close"].iloc[-1]
    else:
        return f"Field '{field}' not found"

if ticker and field:
    result = get_data(ticker, field)
    st.json({"ticker": ticker, "field": field, "value": result})
else:
    st.write("Use as: https://your-app.streamlit.app/?ticker=AAPL&field=debtToEquity")
