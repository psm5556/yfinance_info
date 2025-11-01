import streamlit as st
import yfinance as yf
import pandas as pd
import time

st.set_page_config(page_title="Finance API")
st.title("📡 Finance Data API (for Google Sheets)")

ticker = st.query_params.get("ticker", "")
field = st.query_params.get("field", "")
debug = st.query_params.get("debug", "")

@st.cache_data(ttl=3600)  # 1시간 캐시
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

@st.cache_data(ttl=3600)  # 1시간 캐시
def get_info_data(ticker_symbol):
    """info 데이터를 dict로 캐싱"""
    try:
        t = yf.Ticker(ticker_symbol)
        return t.info
    except Exception:
        return {}

@st.cache_data(ttl=300)  # 5분 캐시 (가격은 자주 변경됨)
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
                    bs = get_balance_sheet_data(ticker, quarterly=True)
                
                if bs is not None:
                    if show_debug:
                        st.write("**Balance Sheet Index:**")
                        st.write(bs.index.tolist())
                        st.write("**First few rows:**")
                        st.dataframe(bs.head())
                    
                    latest_col = bs.columns[0]
                    debt = None
                    equity = None
                    
                    # 부채 찾기 - 더 많은 변형 추가
                    debt_keys = [
                        "Total Debt",
                        "TotalDebt",
                        "Net Debt",
                        "NetDebt",
                        "Long Term Debt",
                        "LongTermDebt",
                        "Total Liabilities Net Minority Interest",
                        "TotalLiabilitiesNetMinorityInterest"
                    ]
                    
                    for debt_key in debt_keys:
                        if debt_key in bs.index:
                            val = bs.loc[debt_key, latest_col]
                            if pd.notna(val) and val != 0:
                                debt = float(val)
                                if show_debug:
                                    st.success(f"✓ Found debt: {debt_key} = {debt:,.0f}")
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
                        "Ordinary Shares Number"
                    ]
                    
                    for equity_key in equity_keys:
                        if equity_key in bs.index:
                            val = bs.loc[equity_key, latest_col]
                            if pd.notna(val) and val != 0:
                                equity = float(val)
                                if show_debug:
                                    st.success(f"✓ Found equity: {equity_key} = {equity:,.0f}")
                                break
                    
                    if debt is not None and equity is not None and equity != 0:
                        ratio = round(debt / equity, 2)
                        if show_debug:
                            st.success(f"✓ Calculated D/E Ratio: {ratio}")
                        return ratio
                    else:
                        if show_debug:
                            st.warning(f"Missing data - Debt: {debt}, Equity: {equity}")
                
                # 방법 2: info에서 가져오기
                info = get_info_data(ticker)
                
                if info and show_debug:
                    st.write("**Checking info...**")
                    debt_equity_keys = [k for k in info.keys() if 'debt' in k.lower() or 'equity' in k.lower()]
                    st.write(f"Debt/Equity related keys: {debt_equity_keys}")
                
                if info:
                    # debtToEquity 직접 확인
                    if 'debtToEquity' in info and info['debtToEquity']:
                        value = float(info['debtToEquity'])
                        if value > 100:
                            return round(value / 100, 2)
                        return round(value, 2)
                    
                    # totalDebt와 stockholderEquity로 계산
                    total_debt = info.get('totalDebt') or info.get('longTermDebt', 0)
                    equity = info.get('totalStockholderEquity') or info.get('stockholdersEquity', 0)
                    
                    if show_debug:
                        st.write(f"Info - totalDebt: {total_debt}, stockholderEquity: {equity}")
                    
                    if total_debt and equity and equity != 0:
                        return round(float(total_debt) / float(equity), 2)
                
                if show_debug:
                    st.error("Could not calculate Debt to Equity ratio")
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
            st.write("**Available info keys (first 50):**")
            st.write(list(info.keys())[:50])
        
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
    st.code("?ticker=AAPL&field=debtToEquity")
    st.code("?ticker=AAPL&field=price")
    st.code("?ticker=AAPL&field=marketCap")
    st.write("")
    st.write("**디버그 모드:**")
    st.code("?ticker=AAPL&field=debtToEquity&debug=true")
    st.write("")
    st.write("**지원 필드:**")
    st.write("- `price`: 현재 주가")
    st.write("- `debtToEquity`: 부채비율")
    st.write("- `currentRatio`: 유동비율")
    st.write("- `marketCap`: 시가총액")
    st.write("- `trailingPE`: PER")
    st.write("- `profitMargins`: 순이익률")
    st.write("- 기타 yfinance info 필드")
