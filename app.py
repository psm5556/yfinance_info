import streamlit as st
import yfinance as yf
import pandas as pd
import time

st.set_page_config(page_title="Finance API")
st.title("📡 Finance Data API (for Google Sheets)")

ticker = st.query_params.get("ticker", "")
field = st.query_params.get("field", "")
debug = st.query_params.get("debug", "")

@st.cache_data(ttl=3600)
def get_balance_sheet_data(ticker_symbol, quarterly=False):
    """재무제표 데이터를 DataFrame으로 캐싱"""
    try:
        t = yf.Ticker(ticker_symbol)
        if quarterly:
            bs = t.quarterly_balance_sheet
        else:
            bs = t.balance_sheet
        
        if bs is not None and not bs.empty:
            return bs
        return None
    except Exception:
        return None

@st.cache_data(ttl=3600)
def get_financials_data(ticker_symbol):
    """손익계산서 데이터 캐싱"""
    try:
        t = yf.Ticker(ticker_symbol)
        return t.financials
    except Exception:
        return None

@st.cache_data(ttl=3600)
def get_info_data(ticker_symbol):
    """info 데이터를 dict로 캐싱"""
    try:
        t = yf.Ticker(ticker_symbol)
        return t.info
    except Exception:
        return {}

@st.cache_data(ttl=300)
def get_price_data(ticker_symbol):
    """가격 데이터 캐싱"""
    try:
        t = yf.Ticker(ticker_symbol)
        
        # fast_info 시도
        if hasattr(t, 'fast_info') and hasattr(t.fast_info, 'last_price'):
            price = t.fast_info.last_price
            if price and price > 0:
                return float(price)
        
        # history 시도
        df = t.history(period="1d")
        if not df.empty:
            return float(df["Close"].iloc[-1])
        
        return None
    except Exception:
        return None

def get_data(ticker, field, show_debug=False):
    try:
        # ------------------------------
        # ① 가격 (price)
        # ------------------------------
        if field == "price":
            price = get_price_data(ticker)
            if price is not None:
                return price
            
            if show_debug:
                st.error("Failed to get price data")
            return "N/A"
        
        # ------------------------------
        # ② 부채비율 (Debt to Equity)
        # ------------------------------
        if field == "debtToEquity":
            try:
                # 방법 1: 재무제표에서 계산
                bs = get_balance_sheet_data(ticker, quarterly=False)
                
                if bs is None:
                    if show_debug:
                        st.warning("Annual balance sheet is None, trying quarterly...")
                    bs = get_balance_sheet_data(ticker, quarterly=True)
                
                if bs is not None and not bs.empty:
                    if show_debug:
                        st.write("**✓ Balance Sheet Retrieved Successfully**")
                        st.write(f"Shape: {bs.shape}")
                        st.write(f"Columns (dates): {bs.columns.tolist()}")
                        st.write("**ALL Balance Sheet Items:**")
                        st.write(bs.index.tolist())
                        st.write("**Full Balance Sheet (latest column):**")
                        st.dataframe(bs.iloc[:, 0].to_frame())
                    
                    latest_col = bs.columns[0]
                    debt = None
                    equity = None
                    debt_key_found = None
                    equity_key_found = None
                    
                    # 부채 찾기 - 가능한 모든 변형
                    debt_keys = [
                        "Total Debt",
                        "TotalDebt",
                        "Net Debt",
                        "NetDebt",
                        "Long Term Debt",
                        "LongTermDebt",
                        "Short Long Term Debt Total",
                        "Long Term Debt And Capital Lease Obligation",
                        "Current Debt And Capital Lease Obligation",
                        "Total Liabilities Net Minority Interest",
                        "TotalLiabilitiesNetMinorityInterest"
                    ]
                    
                    if show_debug:
                        st.write("**Searching for Debt...**")
                    
                    for debt_key in debt_keys:
                        if debt_key in bs.index:
                            val = bs.loc[debt_key, latest_col]
                            if show_debug:
                                st.write(f"  - Checking '{debt_key}': {val}")
                            if pd.notna(val) and val != 0:
                                debt = float(val)
                                debt_key_found = debt_key
                                if show_debug:
                                    st.success(f"  ✓ FOUND Debt: {debt_key} = {debt:,.0f}")
                                break
                    
                    # 자본 찾기
                    equity_keys = [
                        "Stockholders Equity",
                        "StockholdersEquity",
                        "Total Equity Gross Minority Interest",
                        "TotalEquityGrossMinorityInterest",
                        "Common Stock Equity",
                        "CommonStockEquity",
                        "Stockholder Equity",
                        "StockholderEquity",
                        "Total Capitalization",
                        "Invested Capital",
                        "Tangible Book Value",
                        "Net Tangible Assets"
                    ]
                    
                    if show_debug:
                        st.write("**Searching for Equity...**")
                    
                    for equity_key in equity_keys:
                        if equity_key in bs.index:
                            val = bs.loc[equity_key, latest_col]
                            if show_debug:
                                st.write(f"  - Checking '{equity_key}': {val}")
                            if pd.notna(val) and val != 0:
                                equity = float(val)
                                equity_key_found = equity_key
                                if show_debug:
                                    st.success(f"  ✓ FOUND Equity: {equity_key} = {equity:,.0f}")
                                break
                    
                    if show_debug:
                        st.write("**Result:**")
                        st.write(f"Debt: {debt} (from '{debt_key_found}')")
                        st.write(f"Equity: {equity} (from '{equity_key_found}')")
                    
                    if debt is not None and equity is not None and equity != 0:
                        ratio = round(debt / equity, 2)
                        if show_debug:
                            st.success(f"✓✓✓ Calculated D/E Ratio: {ratio}")
                        return ratio
                    else:
                        if show_debug:
                            if debt is None:
                                st.error("❌ Could not find Debt")
                            if equity is None:
                                st.error("❌ Could not find Equity")
                else:
                    if show_debug:
                        st.error("❌ Balance sheet is None or empty")
                
                # 방법 2: info에서 가져오기
                if show_debug:
                    st.write("**Trying info dictionary...**")
                
                info = get_info_data(ticker)
                
                if info:
                    if show_debug:
                        debt_equity_keys = {k: v for k, v in info.items() if 'debt' in k.lower() or 'equity' in k.lower()}
                        st.write("**Debt/Equity related keys in info:**")
                        st.json(debt_equity_keys)
                    
                    # debtToEquity 직접 확인
                    if 'debtToEquity' in info and info['debtToEquity']:
                        value = float(info['debtToEquity'])
                        if value > 100:
                            return round(value / 100, 2)
                        return round(value, 2)
                    
                    # totalDebt와 stockholderEquity로 계산
                    total_debt = info.get('totalDebt') or info.get('longTermDebt')
                    equity = info.get('totalStockholderEquity') or info.get('stockholdersEquity')
                    
                    if show_debug:
                        st.write(f"totalDebt: {total_debt}")
                        st.write(f"totalStockholderEquity: {equity}")
                    
                    if total_debt and equity and equity != 0:
                        ratio = round(float(total_debt) / float(equity), 2)
                        if show_debug:
                            st.success(f"✓ Calculated from info: {ratio}")
                        return ratio
                else:
                    if show_debug:
                        st.error("❌ Info is empty")
                
                if show_debug:
                    st.error("❌ Could not calculate Debt to Equity ratio")
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
                bs = get_balance_sheet_data(ticker, quarterly=False)
                
                if bs is None:
                    bs = get_balance_sheet_data(ticker, quarterly=True)
                
                if bs is not None:
                    if show_debug:
                        st.write("**Balance Sheet Index:**")
                        st.write(bs.index.tolist())
                    
                    latest_col = bs.columns[0]
                    ca = None
                    cl = None
                    
                    ca_keys = ["Current Assets", "CurrentAssets", "Total Current Assets", "TotalCurrentAssets"]
                    cl_keys = ["Current Liabilities", "CurrentLiabilities", "Total Current Liabilities", "TotalCurrentLiabilities"]
                    
                    for ca_key in ca_keys:
                        if ca_key in bs.index:
                            val = bs.loc[ca_key, latest_col]
                            if pd.notna(val):
                                ca = float(val)
                                if show_debug:
                                    st.success(f"✓ Found current assets: {ca_key} = {ca:,.0f}")
                                break
                    
                    for cl_key in cl_keys:
                        if cl_key in bs.index:
                            val = bs.loc[cl_key, latest_col]
                            if pd.notna(val):
                                cl = float(val)
                                if show_debug:
                                    st.success(f"✓ Found current liabilities: {cl_key} = {cl:,.0f}")
                                break
                    
                    if ca is not None and cl is not None and cl != 0:
                        ratio = round(ca / cl, 2)
                        if show_debug:
                            st.success(f"✓ Calculated Current Ratio: {ratio}")
                        return ratio
                
                # info에서 가져오기
                info = get_info_data(ticker)
                if info and 'currentRatio' in info and info['currentRatio']:
                    return float(info['currentRatio'])
                
                if show_debug:
                    st.error("Could not calculate Current Ratio")
                return "N/A"
                    
            except Exception as e:
                if show_debug:
                    st.error(f"Current Ratio error: {e}")
                return "N/A"
        
        # ------------------------------
        # ④ 기본 info 항목
        # ------------------------------
        info = get_info_data(ticker)
        
        if show_debug and info:
            st.write("**Available info keys:**")
            st.write(list(info.keys()))
        
        if info and field in info and info[field] is not None:
            return info[field]
        
        if show_debug:
            st.warning(f"Field '{field}' not found in info")
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
    st.code("?ticker=AAPL&field=debtToEquity&debug=true")
    st.write("")
    st.write("**지원 필드:**")
    st.write("- `price`: 현재 주가")
    st.write("- `debtToEquity`: 부채비율")
    st.write("- `currentRatio`: 유동비율")
    st.write("- 기타 info 필드 (marketCap, trailingPE 등)")
