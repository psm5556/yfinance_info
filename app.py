import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

st.set_page_config(page_title="Finance API")
st.title("📡 Finance Data API (for Google Sheets)")

ticker = st.query_params.get("ticker", "")
field = st.query_params.get("field", "")
debug = st.query_params.get("debug", "")

def create_session():
    """안정적인 세션 생성"""
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    session = requests.Session()
    
    # 재시도 전략
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # User-Agent 설정
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    })
    
    return session

@st.cache_data(ttl=300)  # 5분 캐시
def get_ticker_price(symbol, max_retries=3):
    """가격 가져오기"""
    session = create_session()
    
    for attempt in range(max_retries):
        try:
            # 방법 1: download 사용
            df = yf.download(
                symbol,
                period="2d",
                progress=False,
                session=session,
                threads=False
            )
            
            if not df.empty and 'Close' in df.columns:
                price = float(df['Close'].iloc[-1])
                if price > 0:
                    return {"price": price, "source": "download"}
        except Exception:
            pass
        
        try:
            # 방법 2: Ticker.history
            ticker = yf.Ticker(symbol, session=session)
            hist = ticker.history(period="2d")
            
            if not hist.empty and 'Close' in hist.columns:
                price = float(hist['Close'].iloc[-1])
                if price > 0:
                    return {"price": price, "source": "history"}
        except Exception:
            pass
        
        try:
            # 방법 3: fast_info
            ticker = yf.Ticker(symbol, session=session)
            if hasattr(ticker, 'fast_info'):
                if hasattr(ticker.fast_info, 'last_price'):
                    price = ticker.fast_info.last_price
                    if price and price > 0:
                        return {"price": float(price), "source": "fast_info"}
        except Exception:
            pass
        
        # 재시도 전 대기
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    
    return None

@st.cache_data(ttl=3600)  # 1시간 캐시
def get_ticker_info(symbol, max_retries=3):
    """회사 정보 가져오기"""
    session = create_session()
    
    for attempt in range(max_retries):
        try:
            ticker = yf.Ticker(symbol, session=session)
            info = ticker.info
            
            if info and len(info) > 0:
                return info
        except Exception:
            pass
        
        # 재시도 전 대기
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    
    return {}

@st.cache_data(ttl=3600)
def get_balance_sheet(symbol, quarterly=False, max_retries=3):
    """재무상태표 가져오기"""
    session = create_session()
    
    for attempt in range(max_retries):
        try:
            ticker = yf.Ticker(symbol, session=session)
            
            if quarterly:
                bs = ticker.quarterly_balance_sheet
            else:
                bs = ticker.balance_sheet
            
            if bs is not None and not bs.empty:
                return bs
        except Exception:
            pass
        
        # 재시도 전 대기
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    
    return None

def calculate_debt_to_equity(info, balance_sheet, show_debug=False):
    """부채비율 계산"""
    
    # 방법 1: info에서 직접 가져오기
    if info:
        if show_debug:
            debt_equity_keys = {k: v for k, v in info.items() if 'debt' in k.lower() or 'equity' in k.lower()}
            if debt_equity_keys:
                st.write("**Info - Debt/Equity keys:**")
                st.json(debt_equity_keys)
        
        # totalDebt와 totalStockholderEquity로 계산
        total_debt = info.get('totalDebt')
        total_equity = info.get('totalStockholderEquity')
        
        if total_debt and total_equity and total_equity != 0:
            ratio = round(float(total_debt) / float(total_equity), 2)
            if show_debug:
                st.success(f"✅ From info: {total_debt:,} / {total_equity:,} = {ratio}")
            return ratio
    
    # 방법 2: Balance Sheet에서 계산
    if balance_sheet is not None and not balance_sheet.empty:
        try:
            if show_debug:
                st.write("**Balance Sheet Items:**")
                st.write(balance_sheet.index.tolist())
            
            latest_col = balance_sheet.columns[0]
            
            # Debt 찾기
            debt = None
            debt_patterns = ['total debt', 'debt', 'liabilities']
            for pattern in debt_patterns:
                matching = [idx for idx in balance_sheet.index if pattern in str(idx).lower()]
                if matching:
                    for match in matching:
                        val = balance_sheet.loc[match, latest_col]
                        if pd.notna(val) and val != 0:
                            debt = float(val)
                            if show_debug:
                                st.success(f"✓ Debt: {match} = {debt:,.0f}")
                            break
                if debt:
                    break
            
            # Equity 찾기
            equity = None
            equity_patterns = ['stockholder', 'equity', 'shareholder']
            for pattern in equity_patterns:
                matching = [idx for idx in balance_sheet.index if pattern in str(idx).lower()]
                if matching:
                    for match in matching:
                        val = balance_sheet.loc[match, latest_col]
                        if pd.notna(val) and val != 0:
                            equity = float(val)
                            if show_debug:
                                st.success(f"✓ Equity: {match} = {equity:,.0f}")
                            break
                if equity:
                    break
            
            if debt and equity and equity != 0:
                ratio = round(debt / equity, 2)
                if show_debug:
                    st.success(f"✅ Calculated: {debt:,.0f} / {equity:,.0f} = {ratio}")
                return ratio
                
        except Exception as e:
            if show_debug:
                st.error(f"Calculation error: {e}")
    
    return None

def calculate_current_ratio(balance_sheet, show_debug=False):
    """유동비율 계산"""
    if balance_sheet is None or balance_sheet.empty:
        return None
    
    try:
        latest_col = balance_sheet.columns[0]
        
        # Current Assets
        ca = None
        ca_patterns = ['current asset']
        for pattern in ca_patterns:
            matching = [idx for idx in balance_sheet.index if pattern in str(idx).lower()]
            if matching:
                val = balance_sheet.loc[matching[0], latest_col]
                if pd.notna(val):
                    ca = float(val)
                    if show_debug:
                        st.success(f"✓ Current Assets: {ca:,.0f}")
                    break
        
        # Current Liabilities
        cl = None
        cl_patterns = ['current liab']
        for pattern in cl_patterns:
            matching = [idx for idx in balance_sheet.index if pattern in str(idx).lower()]
            if matching:
                val = balance_sheet.loc[matching[0], latest_col]
                if pd.notna(val):
                    cl = float(val)
                    if show_debug:
                        st.success(f"✓ Current Liabilities: {cl:,.0f}")
                    break
        
        if ca and cl and cl != 0:
            ratio = round(ca / cl, 2)
            if show_debug:
                st.success(f"✅ Current Ratio: {ratio}")
            return ratio
    except Exception as e:
        if show_debug:
            st.error(f"Error: {e}")
    
    return None

def get_data(ticker_symbol, field_name, show_debug=False):
    """메인 데이터 조회 함수"""
    
    try:
        if show_debug:
            st.write(f"**Fetching {ticker_symbol} - {field_name}**")
        
        # ------------------------------
        # ① 가격 (price)
        # ------------------------------
        if field_name == "price":
            price_data = get_ticker_price(ticker_symbol)
            
            if show_debug:
                st.write("**Price data:**")
                st.json(price_data)
            
            if price_data and "price" in price_data:
                return price_data["price"]
            
            if show_debug:
                st.error("❌ Failed to get price")
            return "N/A"
        
        # ------------------------------
        # ② 부채비율 (debtToEquity)
        # ------------------------------
        if field_name == "debtToEquity":
            info = get_ticker_info(ticker_symbol)
            balance_sheet = get_balance_sheet(ticker_symbol, quarterly=False)
            
            if not balance_sheet or balance_sheet.empty:
                if show_debug:
                    st.warning("Annual balance sheet empty, trying quarterly...")
                balance_sheet = get_balance_sheet(ticker_symbol, quarterly=True)
            
            ratio = calculate_debt_to_equity(info, balance_sheet, show_debug)
            
            if ratio is not None:
                return ratio
            
            if show_debug:
                st.error("❌ Could not calculate D/E ratio")
            return "N/A"
        
        # ------------------------------
        # ③ 유동비율 (currentRatio)
        # ------------------------------
        if field_name == "currentRatio":
            balance_sheet = get_balance_sheet(ticker_symbol, quarterly=False)
            
            if not balance_sheet or balance_sheet.empty:
                balance_sheet = get_balance_sheet(ticker_symbol, quarterly=True)
            
            ratio = calculate_current_ratio(balance_sheet, show_debug)
            
            if ratio is not None:
                return ratio
            
            if show_debug:
                st.error("❌ Could not calculate current ratio")
            return "N/A"
        
        # ------------------------------
        # ④ 기타 info 필드
        # ------------------------------
        info = get_ticker_info(ticker_symbol)
        
        if show_debug:
            st.write(f"**Info keys ({len(info)}):**")
            if info:
                st.write(list(info.keys())[:30])
        
        if info and field_name in info and info[field_name] is not None:
            value = info[field_name]
            if show_debug:
                st.success(f"✅ Found: {field_name} = {value}")
            return value
        
        if show_debug:
            st.warning(f"Field '{field_name}' not found in info")
        
        return "N/A"
        
    except Exception as e:
        if show_debug:
            st.error(f"Error: {e}")
            import traceback
            st.code(traceback.format_exc())
        return "N/A"


# 메인 실행
if ticker and field:
    show_debug = (debug.lower() == "true")
    result = get_data(ticker, field, show_debug)
    st.json({"ticker": ticker, "field": field, "value": result})
else:
    st.write("**📊 Finance Data API - yfinance**")
    st.write("")
    st.write("**특징:**")
    st.write("✅ 무료, API 키 불필요")
    st.write("✅ 실시간 가격 데이터")
    st.write("✅ 재무제표 데이터")
    st.write("✅ 안정적인 재시도 로직")
    st.write("")
    
    st.write("**테스트:**")
    st.code("?ticker=AAPL&field=price&debug=true")
    
    st.write("")
    st.write("**사용 예시:**")
    st.code("?ticker=AAPL&field=price")
    st.code("?ticker=AAPL&field=debtToEquity")
    st.code("?ticker=MSFT&field=currentRatio")
    st.code("?ticker=GOOGL&field=marketCap")
    
    st.write("")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**지원 필드:**")
        st.write("- `price` - 현재 주가")
        st.write("- `debtToEquity` - 부채비율")
        st.write("- `currentRatio` - 유동비율")
        
    with col2:
        st.write("**info 필드:**")
        st.write("- `marketCap` - 시가총액")
        st.write("- `trailingPE` - PER")
        st.write("- `dividendYield` - 배당률")
        st.write("- 기타 yfinance info 필드")
    
    st.write("")
    st.info("💡 API 키가 필요 없고 무료로 사용 가능합니다!")
