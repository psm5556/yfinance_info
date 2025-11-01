import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Finance API")
st.title("📡 Finance Data API (for Google Sheets)")

ticker = st.query_params.get("ticker", "")
field = st.query_params.get("field", "")
debug = st.query_params.get("debug", "")

# API 키 가져오기
try:
    API_KEY = st.secrets["ALPHA_VANTAGE_API_KEY"]
except Exception:
    API_KEY = None
    st.error("⚠️ Alpha Vantage API 키가 설정되지 않았습니다. Streamlit Secrets에 ALPHA_VANTAGE_API_KEY를 추가하세요.")

@st.cache_data(ttl=3600)  # 1시간 캐시
def get_alpha_vantage_overview(symbol):
    """회사 개요 데이터 (재무 지표 포함)"""
    if not API_KEY:
        return None
    
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # API 제한 체크
        if "Note" in data:
            return {"error": "API_LIMIT", "message": "API call frequency limit reached"}
        
        if "Error Message" in data:
            return {"error": "INVALID_SYMBOL", "message": "Invalid symbol"}
        
        if data and len(data) > 0:
            return data
        
        return None
    except Exception as e:
        return {"error": "REQUEST_FAILED", "message": str(e)}

@st.cache_data(ttl=300)  # 5분 캐시
def get_alpha_vantage_quote(symbol):
    """실시간 가격 정보"""
    if not API_KEY:
        return None
    
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "Note" in data:
            return {"error": "API_LIMIT"}
        
        if "Global Quote" in data and data["Global Quote"]:
            return data["Global Quote"]
        
        return None
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=3600)
def get_alpha_vantage_balance_sheet(symbol):
    """재무상태표 (Balance Sheet)"""
    if not API_KEY:
        return None
    
    url = f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={symbol}&apikey={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "Note" in data:
            return {"error": "API_LIMIT"}
        
        if "annualReports" in data and data["annualReports"]:
            return data["annualReports"][0]  # 최신 연간 보고서
        
        if "quarterlyReports" in data and data["quarterlyReports"]:
            return data["quarterlyReports"][0]  # 최신 분기 보고서
        
        return None
    except Exception as e:
        return {"error": str(e)}

def calculate_debt_to_equity(overview_data, balance_sheet_data, show_debug=False):
    """부채비율 계산"""
    
    # 방법 1: Overview에서 직접 가져오기
    if overview_data and "BookValue" in overview_data:
        try:
            # Overview에는 직접적인 D/E ratio는 없지만 계산 가능
            if show_debug:
                st.write("**Overview data available:**")
                relevant = {k: v for k, v in overview_data.items() if any(x in k for x in ['Debt', 'Equity', 'Book'])}
                st.json(relevant)
        except Exception:
            pass
    
    # 방법 2: Balance Sheet에서 계산
    if balance_sheet_data and "error" not in balance_sheet_data:
        try:
            if show_debug:
                st.write("**Balance Sheet data:**")
                st.json(balance_sheet_data)
            
            # Total Debt 찾기
            debt = None
            if "shortLongTermDebtTotal" in balance_sheet_data:
                debt = float(balance_sheet_data["shortLongTermDebtTotal"])
            elif "longTermDebt" in balance_sheet_data:
                debt = float(balance_sheet_data["longTermDebt"])
            elif "totalLiabilities" in balance_sheet_data:
                debt = float(balance_sheet_data["totalLiabilities"])
            
            # Total Equity 찾기
            equity = None
            if "totalShareholderEquity" in balance_sheet_data:
                equity = float(balance_sheet_data["totalShareholderEquity"])
            elif "commonStockSharesOutstanding" in balance_sheet_data and "bookValue" in overview_data:
                try:
                    shares = float(balance_sheet_data["commonStockSharesOutstanding"])
                    book_value = float(overview_data["BookValue"])
                    equity = shares * book_value
                except Exception:
                    pass
            
            if show_debug:
                st.write(f"**Calculated values:**")
                st.write(f"- Debt: {debt}")
                st.write(f"- Equity: {equity}")
            
            if debt and equity and equity != 0:
                ratio = round(debt / equity, 2)
                if show_debug:
                    st.success(f"✓ D/E Ratio: {ratio}")
                return ratio
                
        except Exception as e:
            if show_debug:
                st.error(f"Calculation error: {e}")
    
    return None

def calculate_current_ratio(balance_sheet_data, show_debug=False):
    """유동비율 계산"""
    if not balance_sheet_data or "error" in balance_sheet_data:
        return None
    
    try:
        ca = float(balance_sheet_data.get("totalCurrentAssets", 0))
        cl = float(balance_sheet_data.get("totalCurrentLiabilities", 0))
        
        if show_debug:
            st.write(f"Current Assets: {ca:,.0f}")
            st.write(f"Current Liabilities: {cl:,.0f}")
        
        if ca and cl and cl != 0:
            return round(ca / cl, 2)
    except Exception as e:
        if show_debug:
            st.error(f"Error: {e}")
    
    return None

def get_data(ticker_symbol, field_name, show_debug=False):
    """데이터 조회 메인 함수"""
    
    if not API_KEY:
        return "NO_API_KEY"
    
    try:
        if show_debug:
            st.write(f"**Fetching data for {ticker_symbol}...**")
        
        # ------------------------------
        # ① 가격 (price)
        # ------------------------------
        if field_name == "price":
            quote_data = get_alpha_vantage_quote(ticker_symbol)
            
            if show_debug:
                st.write("**Quote data:**")
                st.json(quote_data)
            
            if quote_data and "error" not in quote_data:
                if "05. price" in quote_data:
                    return float(quote_data["05. price"])
            
            if show_debug:
                st.error("Failed to get price")
            return "N/A"
        
        # 나머지 필드는 overview와 balance sheet 필요
        overview_data = get_alpha_vantage_overview(ticker_symbol)
        
        if overview_data and "error" in overview_data:
            if show_debug:
                st.error(f"Overview error: {overview_data.get('message', 'Unknown error')}")
            return "N/A"
        
        # ------------------------------
        # ② 부채비율 (debtToEquity)
        # ------------------------------
        if field_name == "debtToEquity":
            balance_sheet_data = get_alpha_vantage_balance_sheet(ticker_symbol)
            
            if balance_sheet_data and "error" in balance_sheet_data:
                if show_debug:
                    st.warning(f"Balance sheet error: {balance_sheet_data.get('error')}")
            
            ratio = calculate_debt_to_equity(overview_data, balance_sheet_data, show_debug)
            
            if ratio:
                return ratio
            
            if show_debug:
                st.error("Could not calculate D/E ratio")
            return "N/A"
        
        # ------------------------------
        # ③ 유동비율 (currentRatio)
        # ------------------------------
        if field_name == "currentRatio":
            balance_sheet_data = get_alpha_vantage_balance_sheet(ticker_symbol)
            
            ratio = calculate_current_ratio(balance_sheet_data, show_debug)
            
            if ratio:
                return ratio
            
            if show_debug:
                st.error("Could not calculate current ratio")
            return "N/A"
        
        # ------------------------------
        # ④ Overview의 다른 필드들
        # ------------------------------
        if overview_data:
            if show_debug:
                st.write("**Available overview fields:**")
                st.write(list(overview_data.keys())[:30])
            
            # 필드명 매핑
            field_mapping = {
                "marketCap": "MarketCapitalization",
                "trailingPE": "PERatio",
                "forwardPE": "ForwardPE",
                "priceToBook": "PriceToBookRatio",
                "dividendYield": "DividendYield",
                "profitMargins": "ProfitMargin",
                "beta": "Beta",
                "eps": "EPS",
                "revenue": "RevenueTTM",
                "grossProfit": "GrossProfitTTM",
                "ebitda": "EBITDA",
                "52WeekHigh": "52WeekHigh",
                "52WeekLow": "52WeekLow",
            }
            
            # 매핑된 필드명 확인
            alpha_field = field_mapping.get(field_name, field_name)
            
            if alpha_field in overview_data and overview_data[alpha_field] != "None":
                value = overview_data[alpha_field]
                
                # 숫자 변환 시도
                try:
                    return float(value)
                except Exception:
                    return value
            
            # 원래 필드명으로도 시도
            if field_name in overview_data and overview_data[field_name] != "None":
                value = overview_data[field_name]
                try:
                    return float(value)
                except Exception:
                    return value
            
            if show_debug:
                st.warning(f"Field '{field_name}' not found in overview data")
        
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
    st.write("**📊 Finance Data API - Alpha Vantage**")
    st.write("")
    
    if not API_KEY:
        st.error("⚠️ API 키가 설정되지 않았습니다!")
        st.write("1. https://www.alphavantage.co/support/#api-key 에서 무료 API 키 발급")
        st.write("2. Streamlit Cloud의 Secrets에 추가:")
        st.code('ALPHA_VANTAGE_API_KEY = "your_api_key_here"')
    else:
        st.success("✓ API 키가 설정되어 있습니다")
    
    st.write("")
    st.write("**사용법:**")
    st.code("?ticker=AAPL&field=price")
    st.code("?ticker=AAPL&field=debtToEquity")
    st.code("?ticker=MSFT&field=marketCap")
    st.code("?ticker=GOOGL&field=trailingPE&debug=true")
    
    st.write("")
    st.write("**지원 필드:**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**가격/비율:**")
        st.write("- `price`: 현재 주가")
        st.write("- `debtToEquity`: 부채비율")
        st.write("- `currentRatio`: 유동비율")
        st.write("- `trailingPE`: PER")
        st.write("- `priceToBook`: PBR")
        
    with col2:
        st.write("**재무 지표:**")
        st.write("- `marketCap`: 시가총액")
        st.write("- `revenue`: 매출")
        st.write("- `ebitda`: EBITDA")
        st.write("- `eps`: 주당순이익")
        st.write("- `dividendYield`: 배당수익률")
    
    st.write("")
    st.info("💡 무료 API는 분당 5회, 일일 500회 제한이 있습니다. 캐싱으로 최적화되어 있습니다.")
