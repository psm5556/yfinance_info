import streamlit as st
import yfinance as yf
import pandas as pd
import time
import requests

st.set_page_config(page_title="Finance API")
st.title("📡 Finance Data API (for Google Sheets)")

ticker = st.query_params.get("ticker", "")
field = st.query_params.get("field", "")
debug = st.query_params.get("debug", "")

@st.cache_data(ttl=3600)
def get_all_financial_data(ticker_symbol):
    """여러 방법으로 데이터 가져오기"""
    result = {
        'balance_sheet': None,
        'quarterly_balance_sheet': None,
        'info': {},
        'price': None,
    }
    
    try:
        # 방법 1: User-Agent 헤더 추가하여 yfinance 사용
        import yfinance as yf
        
        # Ticker 객체 생성 시 세션 설정
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        t = yf.Ticker(ticker_symbol, session=session)
        
        # 1. 가격 - download 함수 사용 (더 안정적)
        try:
            df = yf.download(ticker_symbol, period="1d", progress=False, session=session)
            if not df.empty:
                result['price'] = float(df['Close'].iloc[-1])
        except Exception as e:
            pass
        
        # 2. 재무제표
        try:
            # get_balance_sheet() 메서드 사용
            bs = t.get_balance_sheet(freq='yearly')
            if bs is not None and not bs.empty:
                result['balance_sheet'] = bs
        except Exception:
            try:
                # 속성으로 접근
                bs = t.balance_sheet
                if bs is not None and not bs.empty:
                    result['balance_sheet'] = bs
            except Exception:
                pass
        
        try:
            bs = t.get_balance_sheet(freq='quarterly')
            if bs is not None and not bs.empty:
                result['quarterly_balance_sheet'] = bs
        except Exception:
            try:
                bs = t.quarterly_balance_sheet
                if bs is not None and not bs.empty:
                    result['quarterly_balance_sheet'] = bs
            except Exception:
                pass
        
        # 3. Info - 여러 방법 시도
        try:
            # get_info() 메서드
            info = t.get_info()
            if info and len(info) > 0:
                result['info'] = info
        except Exception:
            try:
                # info 속성
                info = t.info
                if info and len(info) > 0:
                    result['info'] = info
            except Exception:
                try:
                    # basic_info 시도
                    if hasattr(t, 'basic_info'):
                        info = t.basic_info
                        if info:
                            result['info'] = info
                except Exception:
                    pass
        
        # 4. fast_info 시도 (최신 yfinance)
        if not result['price']:
            try:
                if hasattr(t, 'fast_info'):
                    fast = t.fast_info
                    if hasattr(fast, 'last_price') and fast.last_price:
                        result['price'] = float(fast.last_price)
            except Exception:
                pass
        
        # 5. history로 가격 재시도
        if not result['price']:
            try:
                hist = t.history(period="1d")
                if not hist.empty:
                    result['price'] = float(hist['Close'].iloc[-1])
            except Exception:
                pass
        
        return result
        
    except Exception as e:
        return result

def get_data(ticker, field, show_debug=False):
    try:
        if show_debug:
            st.write(f"**Fetching data for {ticker}...**")
            st.write(f"yfinance version: {yf.__version__}")
        
        # 모든 데이터 가져오기
        data = get_all_financial_data(ticker)
        
        if show_debug:
            st.write("**Data retrieval status:**")
            st.write(f"- Price: {'✓ ' + str(data['price']) if data['price'] else '✗'}")
            st.write(f"- Balance Sheet: {'✓ (shape: ' + str(data['balance_sheet'].shape) + ')' if data['balance_sheet'] is not None else '✗'}")
            st.write(f"- Quarterly BS: {'✓ (shape: ' + str(data['quarterly_balance_sheet'].shape) + ')' if data['quarterly_balance_sheet'] is not None else '✗'}")
            st.write(f"- Info keys: {len(data['info'])}")
            
            if data['info']:
                st.write("**Info sample:**")
                sample = dict(list(data['info'].items())[:10])
                st.json(sample)
        
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
                # 재무제표에서 계산
                bs = data['balance_sheet'] if data['balance_sheet'] is not None else data['quarterly_balance_sheet']
                
                if bs is not None and not bs.empty:
                    if show_debug:
                        st.write("**✓ Balance Sheet Available**")
                        st.write(f"Columns: {bs.columns.tolist()}")
                        st.write(f"Index ({len(bs.index)} items):")
                        st.write(bs.index.tolist())
                        st.write("**Full balance sheet:**")
                        st.dataframe(bs)
                    
                    latest_col = bs.columns[0]
                    
                    # 부채 찾기 - 문자열 검색
                    debt = None
                    debt_items = [idx for idx in bs.index if 'debt' in str(idx).lower()]
                    
                    if show_debug:
                        st.write(f"**Debt-related items:** {debt_items}")
                        if debt_items:
                            for item in debt_items:
                                st.write(f"  - {item}: {bs.loc[item, latest_col]}")
                    
                    # Total Debt 우선
                    for item in debt_items:
                        if 'total' in str(item).lower():
                            val = bs.loc[item, latest_col]
                            if pd.notna(val) and val != 0:
                                debt = float(val)
                                if show_debug:
                                    st.success(f"✓ Using: {item} = {debt:,.0f}")
                                break
                    
                    # 없으면 첫 번째 debt 항목
                    if debt is None and debt_items:
                        val = bs.loc[debt_items[0], latest_col]
                        if pd.notna(val):
                            debt = float(val)
                            if show_debug:
                                st.info(f"Using: {debt_items[0]} = {debt:,.0f}")
                    
                    # 자본 찾기
                    equity = None
                    equity_items = [idx for idx in bs.index if 'equity' in str(idx).lower() or 'stockholder' in str(idx).lower()]
                    
                    if show_debug:
                        st.write(f"**Equity-related items:** {equity_items}")
                        if equity_items:
                            for item in equity_items:
                                st.write(f"  - {item}: {bs.loc[item, latest_col]}")
                    
                    for item in equity_items:
                        val = bs.loc[item, latest_col]
                        if pd.notna(val) and val != 0:
                            equity = float(val)
                            if show_debug:
                                st.success(f"✓ Using: {item} = {equity:,.0f}")
                            break
                    
                    if debt is not None and equity is not None and equity != 0:
                        ratio = round(debt / equity, 2)
                        if show_debug:
                            st.success(f"✅ D/E Ratio: {debt:,.0f} / {equity:,.0f} = {ratio}")
                        return ratio
                    else:
                        if show_debug:
                            st.warning(f"Incomplete data: debt={debt}, equity={equity}")
                else:
                    if show_debug:
                        st.error("Balance sheet is empty")
                
                # info에서 시도
                info = data['info']
                if info:
                    if show_debug:
                        st.write("**Checking info dictionary...**")
                        relevant = {k: v for k, v in info.items() if 'debt' in k.lower() or 'equity' in k.lower()}
                        if relevant:
                            st.json(relevant)
                        else:
                            st.write("No debt/equity keys in info")
                    
                    if 'debtToEquity' in info and info['debtToEquity']:
                        val = float(info['debtToEquity'])
                        result = round(val / 100, 2) if val > 100 else round(val, 2)
                        if show_debug:
                            st.success(f"✓ From info['debtToEquity']: {result}")
                        return result
                    
                    total_debt = info.get('totalDebt') or info.get('longTermDebt')
                    equity = info.get('totalStockholderEquity') or info.get('stockholdersEquity')
                    
                    if show_debug:
                        st.write(f"totalDebt: {total_debt}")
                        st.write(f"stockholderEquity: {equity}")
                    
                    if total_debt and equity and equity != 0:
                        result = round(float(total_debt) / float(equity), 2)
                        if show_debug:
                            st.success(f"✓ Calculated from info: {result}")
                        return result
                
                if show_debug:
                    st.error("❌ Could not calculate D/E ratio from any source")
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
                    
                    ca_items = [idx for idx in bs.index if 'current asset' in str(idx).lower()]
                    cl_items = [idx for idx in bs.index if 'current liab' in str(idx).lower()]
                    
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
                st.write(list(info.keys())[:50])
        
        if info and field in info and info[field] is not None:
            return info[field]
        
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
    st.write("**📌 Finance Data API for Google Sheets**")
    st.write("")
    st.write("**사용법:**")
    st.code("?ticker=AAPL&field=price")
    st.code("?ticker=AAPL&field=debtToEquity")
    st.code("?ticker=MSFT&field=marketCap")
    st.write("")
    st.write("**디버그 모드:**")
    st.code("?ticker=AAPL&field=debtToEquity&debug=true")
    st.write("")
    st.write("**지원 필드:**")
    st.write("- `price`: 현재 주가")
    st.write("- `debtToEquity`: 부채비율")
    st.write("- `currentRatio`: 유동비율")
    st.write("- `marketCap`, `trailingPE`, `profitMargins` 등")
    st.write("")
    st.info("💡 yfinance는 Yahoo Finance API를 사용하므로 일시적으로 데이터를 가져오지 못할 수 있습니다.")
