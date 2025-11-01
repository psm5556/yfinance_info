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
def get_ticker_data(ticker_symbol):
    """티커 데이터를 캐시하여 반복 요청 방지"""
    try:
        t = yf.Ticker(ticker_symbol)
        return t
    except Exception as e:
        return None

def safe_get_info(ticker_obj, show_debug=False):
    """안전하게 info 가져오기"""
    try:
        return ticker_obj.info
    except Exception as e1:
        if show_debug:
            st.warning(f"Failed to get info (attempt 1): {e1}")
        try:
            # 재시도
            time.sleep(1)
            return ticker_obj.info
        except Exception as e2:
            if show_debug:
                st.error(f"Failed to get info (attempt 2): {e2}")
            return {}

def safe_get_balance_sheet(ticker_obj, quarterly=False, show_debug=False):
    """안전하게 재무제표 가져오기"""
    try:
        if quarterly:
            bs = ticker_obj.quarterly_balance_sheet
        else:
            bs = ticker_obj.balance_sheet
        
        if bs is not None and not bs.empty:
            return bs
        return None
    except Exception as e:
        if show_debug:
            st.warning(f"Failed to get balance sheet: {e}")
        return None

def get_data(ticker, field, show_debug=False):
    try:
        t = get_ticker_data(ticker)
        if t is None:
            return "N/A"
        
        # ------------------------------
        # ① 가격 (price)
        # ------------------------------
        if field == "price":
            try:
                # fast_info 사용 (더 빠르고 안정적)
                if hasattr(t, 'fast_info') and hasattr(t.fast_info, 'last_price'):
                    price = t.fast_info.last_price
                    if price and price > 0:
                        return float(price)
                
                # history 사용
                df = t.history(period="1d")
                if not df.empty:
                    return float(df["Close"].iloc[-1])
                
                return "N/A"
            except Exception as e:
                if show_debug:
                    st.error(f"Price error: {e}")
                return "N/A"
        
        # ------------------------------
        # ② 부채비율 (Debt to Equity)
        # ------------------------------
        if field == "debtToEquity":
            try:
                # 방법 1: 재무제표에서 직접 계산 (가장 신뢰성 높음)
                bs = safe_get_balance_sheet(t, quarterly=False, show_debug=show_debug)
                
                if bs is None:
                    # 분기 재무제표 시도
                    bs = safe_get_balance_sheet(t, quarterly=True, show_debug=show_debug)
                
                if bs is not None:
                    if show_debug:
                        st.write("**Balance Sheet Index:**")
                        st.write(bs.index.tolist())
                    
                    latest_col = bs.columns[0]
                    debt = None
                    equity = None
                    
                    # 부채 찾기
                    for debt_key in ["Total Debt", "TotalDebt", "Net Debt", "NetDebt"]:
                        if debt_key in bs.index:
                            val = bs.loc[debt_key, latest_col]
                            if pd.notna(val):
                                debt = float(val)
                                if show_debug:
                                    st.write(f"Found debt: {debt_key} = {debt}")
                                break
                    
                    # 자본 찾기
                    for equity_key in ["Stockholders Equity", "StockholdersEquity", 
                                       "Total Equity Gross Minority Interest", 
                                       "Common Stock Equity", "CommonStockEquity"]:
                        if equity_key in bs.index:
                            val = bs.loc[equity_key, latest_col]
                            if pd.notna(val):
                                equity = float(val)
                                if show_debug:
                                    st.write(f"Found equity: {equity_key} = {equity}")
                                break
                    
                    if debt is not None and equity is not None and equity != 0:
                        ratio = round(debt / equity, 2)
                        return ratio
                
                # 방법 2: info에서 가져오기
                info = safe_get_info(t, show_debug)
                
                if info:
                    if show_debug:
                        st.write("**Checking info for debt/equity...**")
                        relevant_keys = [k for k in info.keys() if 'debt' in k.lower() or 'equity' in k.lower()]
                        st.write(f"Relevant keys: {relevant_keys}")
                    
                    # debtToEquity 직접 확인
                    if 'debtToEquity' in info and info['debtToEquity']:
                        value = float(info['debtToEquity'])
                        # 100 이상이면 퍼센트일 가능성
                        if value > 100:
                            return round(value / 100, 2)
                        return round(value, 2)
                    
                    # totalDebt와 stockholderEquity로 계산
                    total_debt = info.get('totalDebt') or info.get('longTermDebt')
                    equity = info.get('totalStockholderEquity') or info.get('stockholdersEquity')
                    
                    if show_debug:
                        st.write(f"totalDebt: {total_debt}, stockholderEquity: {equity}")
                    
                    if total_debt and equity and equity != 0:
                        return round(float(total_debt) / float(equity), 2)
                
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
                # 재무제표에서 계산
                bs = safe_get_balance_sheet(t, quarterly=False, show_debug=show_debug)
                
                if bs is None:
                    bs = safe_get_balance_sheet(t, quarterly=True, show_debug=show_debug)
                
                if bs is not None:
                    if show_debug:
                        st.write("**Balance Sheet Index:**")
                        st.write(bs.index.tolist())
                    
                    latest_col = bs.columns[0]
                    ca = None
                    cl = None
                    
                    for ca_key in ["Current Assets", "CurrentAssets"]:
                        if ca_key in bs.index:
                            val = bs.loc[ca_key, latest_col]
                            if pd.notna(val):
                                ca = float(val)
                                break
                    
                    for cl_key in ["Current Liabilities", "CurrentLiabilities"]:
                        if cl_key in bs.index:
                            val = bs.loc[cl_key, latest_col]
                            if pd.notna(val):
                                cl = float(val)
                                break
                    
                    if ca is not None and cl is not None and cl != 0:
                        return round(ca / cl, 2)
                
                # info에서 가져오기
                info = safe_get_info(t, show_debug)
                if info and 'currentRatio' in info and info['currentRatio']:
                    return float(info['currentRatio'])
                
                return "N/A"
                    
            except Exception as e:
                if show_debug:
                    st.error(f"Current Ratio error: {e}")
                return "N/A"
        
        # ------------------------------
        # ④ 기본 info 항목
        # ------------------------------
        try:
            info = safe_get_info(t, show_debug)
            
            if show_debug and info:
                st.write("**Available info keys (sample):**")
                st.write(list(info.keys())[:30])
            
            if info and field in info and info[field] is not None:
                return info[field]
            
            return "N/A"
                
        except Exception as e:
            if show_debug:
                st.error(f"Info field error: {e}")
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
    st.write("- 기타 yfinance info 필드")
