import streamlit as st
import yfinance as yf
import json

st.set_page_config(page_title="Finance API")

st.title("📡 Finance Data API (for Google Sheets)")

ticker = st.query_params.get("ticker", "")
field = st.query_params.get("field", "")

def get_data(ticker, field):
    t = yf.Ticker(ticker)

    # 1️⃣ 기본정보
    try:
        info = t.get_info()
    except Exception:
        info = t.fast_info

    # 2️⃣ price
    if field == "price":
        df = t.history(period="1d")
        return df["Close"].iloc[-1]

    # 3️⃣ debtToEquity 계산
    if field == "debtToEquity":
        bs = t.balance_sheet
        if 'Total Debt' in bs.index and 'Total Stockholder Equity' in bs.index:
            debt = bs.loc['Total Debt'].iloc[0]
            equity = bs.loc['Total Stockholder Equity'].iloc[0]
            return round(debt / equity, 2)
        else:
            return "N/A"

    # 4️⃣ currentRatio 계산
    if field == "currentRatio":
        bs = t.balance_sheet
        if 'Total Current Assets' in bs.index and 'Total Current Liabilities' in bs.index:
            ca = bs.loc['Total Current Assets'].iloc[0]
            cl = bs.loc['Total Current Liabilities'].iloc[0]
            return round(ca / cl, 2)
        else:
            return "N/A"

    # 5️⃣ 그 외 항목
    if field in info:
        return info[field]
    elif hasattr(t, "fast_info") and field in t.fast_info:
        return t.fast_info[field]

    return f"Field '{field}' not found"



if ticker and field:
    result = get_data(ticker, field)
    st.json({"ticker": ticker, "field": field, "value": result})
else:
    st.write("Use as: https://yfinanceinfo-n9gbqx6wbjrerkqvucghhl.streamlit.app/?ticker=AAPL&field=debtToEquity")
