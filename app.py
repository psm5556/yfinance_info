import streamlit as st
import yfinance as yf
import pandas as pd
import time

st.set_page_config(page_title="Finance API")
st.title("📡 Finance Data API (for Google Sheets)")

ticker = st.query_params.get("ticker", "")
field = st.query_params.get("field", "")
debug = st.query_params.get("debug", "")

def get_ticker_with_retry(ticker_symbol, max_retries=3, show_debug=False):
    """재시도 로직이 있는 Ticker 객체 생성"""
    for attempt in range(max_retries):
        try:
            if show_debug and attempt > 0:
                st.info(f"Retry attempt {attempt + 1}/{max_retries}")
            
            t = yf.Ticker(ticker_symbol)
            
            # 데이터가 실제로 로드되는지 테스트
            _ = t.history(period="1d")
            
            return t
        except Exception as e:
            if show_debug:
                st.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 지수 백오프
            else:
                if show_debug:
                    st.error(f"All {max_retries} attempts failed")
                return None
    return None

@st.cache_data(ttl=3600)
def get_all_financial_data(ticker_symbol):
    """모든 재무 데이터를 한 번에 가져오기"""
    result = {
        'balance_sheet': None,
        'quarterly_balance_sheet': None,
        'financials': None,
        'info': {},
        'price': None,
        'history': None
    }
    
    try:
        # 세션 설정으로 더 안정적인 요청
        t = yf.Ticker(ticker_symbol)
        
        # 1. 가격 정보 (가장 안정적)
        try:
            hist = t.history(period="5d")
            if not hist.empty:
                result['history'] = hist
                result['price'] = float(hist['Close'].iloc[-1])
        except Exception as e:
            pass
        
        # 2. 재무제표
        try:
            bs = t.balance_sheet
            if bs is not None and not bs.empty:
                result['balance_sheet'] = bs
        except Exception:
            pass
        
        try:
            qbs = t.quarterly_balance_sheet
            if qbs is not None and not qbs.empty:
                result['quarterly_balance_sheet'] = qbs
        except Exception:
            pass
        
        try:
            fin = t.financials
            if fin is not None and not fin.empty:
                result['financials'] = fin
        except Exception:
            pass
        
        # 3. Info (가장 불안정)
        try:
            info = t.info
            if info and len(info) > 0:
                result['info'] = info
        except Exception:
            # info 실패 시 기본 정보만 가져오기
            try:
                result['info'] = {
                    'symbol': ticker_symbol,
                    'shortName': t.info.get('shortName', ticker_symbol) if hasattr(t, 'info') else ticker_symbol
                }
            except:
                result['info'] = {'symbol': ticker_symbol}
        
        return result
        
    except Exception as e:
        return result

def get_data(ticker, field, show_debug=False):
    try:
        if show_debug:
            st.write(f"**Fetching data for {ticker}...**")
        
        # 모든 데이터 한 번에 가져오기
        data = get_all_financial_data(ticker)
        
        if show_debug:
            st.write("**Data retrieval status:**")
            st.write(f"- Price: {'✓' if data['price'] else '✗'}")
            st.write(f"- Balance Sheet: {'✓' if data['balance_sheet'] is not None else '✗'}")
            st.write(f"- Quarterly BS: {'✓' if data['quarterly_balance_sheet'] is not None else '✗'}")
            st.write(f"- Info: {'✓' if len(data['info']) > 1 else '✗'}")
        
        # ------------------------------
        # ① 가격 (price)
        # ------------------------------
        if field == "price":
            if data['price'] is not None:
                return data['price']
            
            if show_debug:
                st.error("Failed to get price data")
            return "N/A"
        
        # ------------------------------
        # ② 부채비율 (Debt to Equity)
        # ------------------------------
        if field == "debtToEquity":
            try:
                # 재무제표 우선
                bs = data['balance_sheet'] if data['balance_sheet'] is not None else data['quarterly_balance_sheet']
                
                if bs is not None and not bs.empty:
                    if show_debug:
                        st.write("**✓ Balance Sheet Available**")
                        st.write(f"Shape: {bs.shape}")
                        st.write("**All items:**")
                        st.write(bs.index.tolist())
                        st.write("**Sample data:**")
                        st.dataframe(bs.iloc[:10, :1])
                    
                    latest_col = bs.columns[0]
                    
                    # 부채 항목 모두 시도
                    debt = None
                    debt_items = bs.index[bs.index.str.contains('debt', case=False, na=False)].tolist()
                    
                    if show_debug:
                        st.write(f"**Found debt-related items:** {debt_items}")
                    
                    # 우선순위대로 검색
                    for item in debt_items:
                        val = bs.loc[item, latest_col]
                        if pd.notna(val) and val != 0:
                            # "Total Debt" 같은 항목 우선
                            if 'total' in item.lower():
                                debt = float(val)
                                if show_debug:
                                    st.success(f"✓ Debt: {item} = {debt:,.0f}")
                                break
                    
                    # 찾지 못했으면 아무 debt 항목이나
                    if debt is None and debt_items:
                        val = bs.loc[debt_items[0], latest_col]
                        if pd.notna(val):
                            debt = float(val)
                            if show_debug:
                                st.info(f"Using: {debt_items[0]} = {debt:,.0f}")
                    
                    # 자본 항목
                    equity = None
                    equity_items = bs.index[bs.index.str.contains('equity|stockholder', case=False, na=False)].tolist()
                    
                    if show_debug:
                        st.write(f"**Found equity-related items:** {equity_items}")
                    
                    for item in equity_items:
                        val = bs.loc[item, latest_col]
                        if pd.notna(val) and val != 0:
                            if 'stockholder' in item.lower() or 'equity' in item.lower():
                                equity = float(val)
                                if show_debug:
                                    st.success(f"✓ Equity: {item} = {equity:,.0f}")
                                break
                    
                    if equity is None and equity_items:
                        val = bs.loc[equity_items[0], latest_col]
                        if pd.notna(val):
                            equity = float(val)
                            if show_debug:
                                st.info(f"Using: {equity_items[0]} = {equity:,.0f}")
                    
                    if debt is not None and equity is not None and equity != 0:
                        ratio = round(debt / equity, 2)
                        if show_debug:
                            st.success(f"✓✓ D/E Ratio: {ratio}")
                        return ratio
                    else:
                        if show_debug:
                            st.warning(f"Missing: debt={debt}, equity={equity}")
                
                # info에서 시도
                info = data['info']
                if info and len(info) > 1:
                    if show_debug:
                        st.write("**Checking info...**")
                        relevant = {k: v for k, v in info.items() if 'debt' in k.lower() or 'equity' in k.lower()}
                        st.json(relevant)
                    
                    if 'debtToEquity' in info and info['debtToEquity']:
                        val = float(info['debtToEquity'])
                        return round(val / 100, 2) if val > 100 else round(val, 2)
                    
                    total_debt = info.get('totalDebt') or info.get('longTermDebt')
                    equity = info.get('totalStockholderEquity')
                    
                    if total_debt and equity and equity != 0:
                        return round(float(total_debt) / float(equity), 2)
                
                if show_debug:
                    st.error("❌ Could not calculate D/E ratio")
                return "N/A"
                
            except Exception as e:
                if show_debug:
                    st.error(f"Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                return "N/A"
        
        # ------------------------------
        # ③ 유동비율 (Current Ratio)
        # ------------------------------
        if field == "currentRatio":
            try:
                bs = data['balance_sheet'] if data['balance_sheet'] is not None else data['quarterly_balance_sheet']
                
                if bs is not None:
                    latest_col = bs.columns[0]
                    
                    ca_items = bs.index[bs.index.str.contains('current asset', case=False, na=False)].tolist()
                    cl_items = bs.index[bs.index.str.contains('current liab', case=False, na=False)].tolist()
                    
                    ca = None
                    cl = None
                    
                    if ca_items:
                        val = bs.loc[ca_items[0], latest_col]
                        if pd.notna(val):
                            ca = float(val)
                    
                    if cl_items:
                        val = bs.loc[cl_items[0], latest_col]
                        if pd.notna(val):
                            cl = float(val)
                    
                    if ca and cl and cl != 0:
                        return round(ca / cl, 2)
                
                info = data['info']
                if info and 'currentRatio' in info:
                    return float(info['currentRatio'])
                
                return "N/A"
            except Exception:
                return "N/A"
        
        # ------------------------------
        # ④ 기본 info 항목
        # ------------------------------
        info = data['info']
        
        if show_debug:
            st.write(f"**Info keys ({len(info)}):**")
            if len(info) > 0:
                st.write(list(info.keys())[:30])
        
        if info and field in info and info[field] is not None:
            return info[field]
        
        return "N/A"
            
    except Exception as e:
        if show_debug:
            st.error(f"General error: {e}")
        return "N/A"


if ticker and field:
    show_debug = (debug.lower() == "true")
    result = get_data(ticker, field, show_debug)
    st.json({"ticker": ticker, "field": field, "value": result})
else:
    st.write("**사용법:**")
    st.code("?ticker=AAPL&field=price")
    st.code("?ticker=AAPL&field=debtToEquity&debug=true")
    st.write("")
    st.write("**지원 필드:**")
    st.write("- `price`: 현재 주가")
    st.write("- `debtToEquity`: 부채비율")
    st.write("- `currentRatio`: 유동비율")
    st.write("- 기타 yfinance info 필드")
    st.write("")
    st.info("💡 데이터 로딩이 실패하면 debug=true를 추가하여 원인을 확인하세요")
