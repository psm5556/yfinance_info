import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Finance API")
st.title("📡 Finance Data API (for Google Sheets)")

ticker = st.query_params.get("ticker", "")
field = st.query_params.get("field", "")
debug = st.query_params.get("debug", "")  # ?debug=true 추가 시 상세 정보 표시

def get_data(ticker, field, show_debug=False):
    try:
        t = yf.Ticker(ticker)
        
        # ------------------------------
        # ① 가격 (price)
        # ------------------------------
        if field == "price":
            try:
                df = t.history(period="1d")
                if df.empty:
                    return "N/A"
                return float(df["Close"].iloc[-1])
            except Exception as e:
                if show_debug:
                    st.error(f"Price error: {e}")
                return "N/A"
        
        # ------------------------------
        # ② 부채비율 (Debt to Equity)
        # ------------------------------
        if field == "debtToEquity":
            try:
                bs = t.balance_sheet
                
                if bs is None or bs.empty:
                    if show_debug:
                        st.error("Balance sheet is empty")
                    return "N/A"
                
                # 디버그 모드: 사용 가능한 모든 항목 출력
                if show_debug:
                    st.write("**Available Balance Sheet Items:**")
                    st.write(bs.index.tolist())
                    st.write("**Latest Balance Sheet:**")
                    st.dataframe(bs.iloc[:, 0])
                
                latest_col = bs.columns[0]
                
                # 부채 항목 찾기 (yfinance 최신 버전 기준)
                debt_candidates = [
                    "Total Debt",
                    "TotalDebt",
                    "Net Debt",
                    "NetDebt",
                    "Long Term Debt",
                    "LongTermDebt",
                    "Short Long Term Debt",
                    "Current Debt"
                ]
                
                # 자본 항목 찾기
                equity_candidates = [
                    "Stockholders Equity",
                    "StockholdersEquity",
                    "Total Equity Gross Minority Interest",
                    "TotalEquityGrossMinorityInterest",
                    "Common Stock Equity",
                    "CommonStockEquity",
                    "Tangible Book Value",
                    "TangibleBookValue"
                ]
                
                debt = None
                equity = None
                debt_found = None
                equity_found = None
                
                # 부채 찾기
                for name in debt_candidates:
                    if name in bs.index:
                        debt = bs.loc[name, latest_col]
                        debt_found = name
                        break
                
                # 자본 찾기
                for name in equity_candidates:
                    if name in bs.index:
                        equity = bs.loc[name, latest_col]
                        equity_found = name
                        break
                
                if show_debug:
                    st.write(f"**Debt found:** {debt_found} = {debt}")
                    st.write(f"**Equity found:** {equity_found} = {equity}")
                
                if debt is not None and equity is not None and equity != 0:
                    ratio = round(float(debt) / float(equity), 2)
                    return ratio
                else:
                    if show_debug:
                        st.warning("Could not find both debt and equity")
                    return "N/A"
                    
            except Exception as e:
                if show_debug:
                    st.error(f"Debt to Equity error: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                return "N/A"
        
        # ------------------------------
        # ③ 유동비율 (Current Ratio)
        # ------------------------------
        if field == "currentRatio":
            try:
                bs = t.balance_sheet
                
                if bs is None or bs.empty:
                    if show_debug:
                        st.error("Balance sheet is empty")
                    return "N/A"
                
                if show_debug:
                    st.write("**Available Balance Sheet Items:**")
                    st.write(bs.index.tolist())
                
                latest_col = bs.columns[0]
                
                ca_candidates = [
                    "Current Assets",
                    "CurrentAssets",
                    "Total Current Assets",
                    "TotalCurrentAssets"
                ]
                
                cl_candidates = [
                    "Current Liabilities",
                    "CurrentLiabilities",
                    "Total Current Liabilities",
                    "TotalCurrentLiabilities"
                ]
                
                ca = None
                cl = None
                ca_found = None
                cl_found = None
                
                for name in ca_candidates:
                    if name in bs.index:
                        ca = bs.loc[name, latest_col]
                        ca_found = name
                        break
                
                for name in cl_candidates:
                    if name in bs.index:
                        cl = bs.loc[name, latest_col]
                        cl_found = name
                        break
                
                if show_debug:
                    st.write(f"**Current Assets found:** {ca_found} = {ca}")
                    st.write(f"**Current Liabilities found:** {cl_found} = {cl}")
                
                if ca is not None and cl is not None and cl != 0:
                    ratio = round(float(ca) / float(cl), 2)
                    return ratio
                else:
                    if show_debug:
                        st.warning("Could not find both current assets and liabilities")
                    return "N/A"
                    
            except Exception as e:
                if show_debug:
                    st.error(f"Current Ratio error: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                return "N/A"
        
        # ------------------------------
        # ④ 기본 info 항목
        # ------------------------------
        try:
            info = t.info
            
            if show_debug:
                st.write("**Available info fields:**")
                st.write(list(info.keys()))
            
            if field in info:
                return info[field]
            else:
                if show_debug:
                    st.warning(f"Field '{field}' not found in info")
                return "N/A"
                
        except Exception as e:
            if show_debug:
                st.error(f"Info error: {e}")
            return "N/A"
            
    except Exception as e:
        if show_debug:
            st.error(f"General error: {e}")
            import traceback
            st.code(traceback.format_exc())
        return "N/A"


if ticker and field:
    show_debug = (debug.lower() == "true")
    result = get_data(ticker, field, show_debug)
    st.json({"ticker": ticker, "field": field, "value": result})
else:
    st.write("**사용법:**")
    st.code("?ticker=AAPL&field=debtToEquity")
    st.code("?ticker=AAPL&field=debtToEquity&debug=true  (디버그 모드)")
    st.write("")
    st.write("**지원 필드:**")
    st.write("- `price`: 현재 주가")
    st.write("- `debtToEquity`: 부채비율")
    st.write("- `currentRatio`: 유동비율")
    st.write("- 기타 yfinance info 필드 (예: `marketCap`, `trailingPE` 등)")
