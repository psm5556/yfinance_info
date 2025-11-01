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
API_KEY = None
try:
    API_KEY = st.secrets["FMP_API_KEY"]
except Exception:
    import os
    API_KEY = os.environ.get("FMP_API_KEY")

if not API_KEY and not ticker:
    st.error("⚠️ FMP API 키가 설정되지 않았습니다.")
    st.write("**설정 방법:**")
    st.write("1. https://site.financialmodelingprep.com/developer/docs/ 에서 무료 가입")
    st.write("2. API 키 발급 (무료: 250 requests/day)")
    st.write("3. Streamlit Cloud → Settings → Secrets:")
    st.code('FMP_API_KEY = "your_api_key_here"', language="toml")

BASE_URL = "https://financialmodelingprep.com/api/v3"

@st.cache_data(ttl=300)  # 5분 캐시
def fmp_get_quote(symbol):
    """실시간 가격"""
    if not API_KEY:
        return {"error": "NO_API_KEY"}
    
    url = f"{BASE_URL}/quote/{symbol}?apikey={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        
        return data
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=3600)  # 1시간 캐시
def fmp_get_profile(symbol):
    """회사 프로필 (기본 정보)"""
    if not API_KEY:
        return {"error": "NO_API_KEY"}
    
    url = f"{BASE_URL}/profile/{symbol}?apikey={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        
        return data
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=3600)
def fmp_get_balance_sheet(symbol):
    """재무상태표"""
    if not API_KEY:
        return {"error": "NO_API_KEY"}
    
    url = f"{BASE_URL}/balance-sheet-statement/{symbol}?limit=1&apikey={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        
        return data
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=3600)
def fmp_get_financial_ratios(symbol):
    """재무 비율 (P/E, D/E, Current Ratio 등)"""
    if not API_KEY:
        return {"error": "NO_API_KEY"}
    
    url = f"{BASE_URL}/ratios/{symbol}?limit=1&apikey={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        
        return data
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=3600)
def fmp_get_key_metrics(symbol):
    """주요 지표 (Market Cap, P/E 등)"""
    if not API_KEY:
        return {"error": "NO_API_KEY"}
    
    url = f"{BASE_URL}/key-metrics/{symbol}?limit=1&apikey={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        
        return data
    except Exception as e:
        return {"error": str(e)}

def calculate_debt_to_equity_fmp(balance_sheet_data, ratios_data, show_debug=False):
    """부채비율 계산"""
    
    # 방법 1: Ratios API에서 직접 가져오기 (가장 정확)
    if ratios_data and "error" not in ratios_data:
        if show_debug:
            st.write("**Financial Ratios Data:**")
            relevant = {k: v for k, v in ratios_data.items() if 'debt' in k.lower() or 'equity' in k.lower()}
            st.json(relevant)
        
        # debtEquityRatio 필드
        if "debtEquityRatio" in ratios_data:
            ratio = ratios_data["debtEquityRatio"]
            if ratio is not None and ratio != "":
                try:
                    result = float(ratio)
                    if show_debug:
                        st.success(f"✅ D/E Ratio from ratios API: {result}")
                    return round(result, 2)
                except Exception:
                    pass
    
    # 방법 2: Balance Sheet에서 계산
    if balance_sheet_data and "error" not in balance_sheet_data:
        try:
            if show_debug:
                st.write("**Balance Sheet Data:**")
                relevant = {k: v for k, v in balance_sheet_data.items() if 'debt' in k.lower() or 'equity' in k.lower()}
                st.json(relevant)
            
            # Total Debt
            debt = None
            debt_keys = ["totalDebt", "totalLiabilities", "longTermDebt"]
            for key in debt_keys:
                if key in balance_sheet_data and balance_sheet_data[key] is not None:
                    try:
                        debt = float(balance_sheet_data[key])
                        if show_debug:
                            st.success(f"✓ Debt ({key}): {debt:,.0f}")
                        break
                    except Exception:
                        pass
            
            # Total Equity
            equity = None
            equity_keys = ["totalStockholdersEquity", "totalEquity"]
            for key in equity_keys:
                if key in balance_sheet_data and balance_sheet_data[key] is not None:
                    try:
                        equity = float(balance_sheet_data[key])
                        if show_debug:
                            st.success(f"✓ Equity ({key}): {equity:,.0f}")
                        break
                    except Exception:
                        pass
            
            if debt and equity and equity != 0:
                ratio = round(debt / equity, 2)
                if show_debug:
                    st.success(f"✅ Calculated D/E: {debt:,.0f} / {equity:,.0f} = {ratio}")
                return ratio
        except Exception as e:
            if show_debug:
                st.error(f"Calculation error: {e}")
    
    return None

def calculate_current_ratio_fmp(balance_sheet_data, ratios_data, show_debug=False):
    """유동비율 계산"""
    
    # 방법 1: Ratios API에서 직접 가져오기
    if ratios_data and "error" not in ratios_data:
        if "currentRatio" in ratios_data:
            ratio = ratios_data["currentRatio"]
            if ratio is not None and ratio != "":
                try:
                    result = float(ratio)
                    if show_debug:
                        st.success(f"✅ Current Ratio from ratios API: {result}")
                    return round(result, 2)
                except Exception:
                    pass
    
    # 방법 2: Balance Sheet에서 계산
    if balance_sheet_data and "error" not in balance_sheet_data:
        try:
            ca = balance_sheet_data.get("totalCurrentAssets")
            cl = balance_sheet_data.get("totalCurrentLiabilities")
            
            if ca and cl and ca is not None and cl is not None:
                ca = float(ca)
                cl = float(cl)
                
                if show_debug:
                    st.write(f"Current Assets: {ca:,.0f}")
                    st.write(f"Current Liabilities: {cl:,.0f}")
                
                if cl != 0:
                    ratio = round(ca / cl, 2)
                    if show_debug:
                        st.success(f"✅ Calculated Current Ratio: {ratio}")
                    return ratio
        except Exception as e:
            if show_debug:
                st.error(f"Error: {e}")
    
    return None

def get_data(ticker_symbol, field_name, show_debug=False):
    """데이터 조회 메인 함수"""
    
    if not API_KEY:
        if show_debug:
            st.error("❌ API key not configured")
        return "NO_API_KEY"
    
    try:
        if show_debug:
            st.write(f"**Fetching {ticker_symbol} - {field_name}**")
        
        # ------------------------------
        # ① 가격 (price)
        # ------------------------------
        if field_name == "price":
            quote_data = fmp_get_quote(ticker_symbol)
            
            if show_debug:
                st.write("**Quote Data:**")
                st.json(quote_data)
            
            if "error" in quote_data:
                if show_debug:
                    st.error(f"Error: {quote_data['error']}")
                return "N/A"
            
            # API 제한 체크
            if "Error Message" in quote_data:
                if show_debug:
                    st.error(f"API Error: {quote_data['Error Message']}")
                return "API_ERROR"
            
            # 가격 추출
            price_keys = ["price", "previousClose"]
            for key in price_keys:
                if key in quote_data and quote_data[key] is not None:
                    try:
                        price = float(quote_data[key])
                        if show_debug:
                            st.success(f"✅ Price ({key}): ${price}")
                        return price
                    except Exception:
                        pass
            
            if show_debug:
                st.error("Failed to extract price")
            return "N/A"
        
        # ------------------------------
        # ② 부채비율 (debtToEquity)
        # ------------------------------
        if field_name == "debtToEquity":
            ratios_data = fmp_get_financial_ratios(ticker_symbol)
            balance_sheet_data = fmp_get_balance_sheet(ticker_symbol)
            
            ratio = calculate_debt_to_equity_fmp(balance_sheet_data, ratios_data, show_debug)
            
            if ratio is not None:
                return ratio
            
            if show_debug:
                st.error("❌ Could not calculate D/E ratio")
            return "N/A"
        
        # ------------------------------
        # ③ 유동비율 (currentRatio)
        # ------------------------------
        if field_name == "currentRatio":
            ratios_data = fmp_get_financial_ratios(ticker_symbol)
            balance_sheet_data = fmp_get_balance_sheet(ticker_symbol)
            
            ratio = calculate_current_ratio_fmp(balance_sheet_data, ratios_data, show_debug)
            
            if ratio is not None:
                return ratio
            
            if show_debug:
                st.error("❌ Could not calculate current ratio")
            return "N/A"
        
        # ------------------------------
        # ④ 기타 필드들
        # ------------------------------
        
        # Profile, Key Metrics, Ratios에서 찾기
        profile_data = fmp_get_profile(ticker_symbol)
        key_metrics_data = fmp_get_key_metrics(ticker_symbol)
        ratios_data = fmp_get_financial_ratios(ticker_symbol)
        
        if show_debug:
            st.write("**Available data sources:**")
            st.write(f"- Profile: {'✓' if 'error' not in profile_data else '✗'}")
            st.write(f"- Key Metrics: {'✓' if 'error' not in key_metrics_data else '✗'}")
            st.write(f"- Ratios: {'✓' if 'error' not in ratios_data else '✗'}")
        
        # 필드 매핑
        field_mapping = {
            "marketCap": ("mktCap", "profile"),  # (필드명, 소스)
            "trailingPE": ("peRatio", "ratios"),
            "forwardPE": ("forwardPE", "profile"),
            "priceToBook": ("priceToBookRatio", "ratios"),
            "dividendYield": ("dividendYield", "profile"),
            "beta": ("beta", "profile"),
            "eps": ("eps", "profile"),
            "revenue": ("revenue", "key_metrics"),
            "volume": ("volume", "profile"),
        }
        
        # 매핑된 필드 확인
        if field_name in field_mapping:
            mapped_field, source = field_mapping[field_name]
            
            if source == "profile" and "error" not in profile_data:
                if mapped_field in profile_data and profile_data[mapped_field] is not None:
                    value = profile_data[mapped_field]
                    if show_debug:
                        st.success(f"✅ Found in profile: {mapped_field} = {value}")
                    try:
                        return float(value)
                    except Exception:
                        return value
            
            elif source == "key_metrics" and "error" not in key_metrics_data:
                if mapped_field in key_metrics_data and key_metrics_data[mapped_field] is not None:
                    value = key_metrics_data[mapped_field]
                    if show_debug:
                        st.success(f"✅ Found in key_metrics: {mapped_field} = {value}")
                    try:
                        return float(value)
                    except Exception:
                        return value
            
            elif source == "ratios" and "error" not in ratios_data:
                if mapped_field in ratios_data and ratios_data[mapped_field] is not None:
                    value = ratios_data[mapped_field]
                    if show_debug:
                        st.success(f"✅ Found in ratios: {mapped_field} = {value}")
                    try:
                        return float(value)
                    except Exception:
                        return value
        
        # 원본 필드명으로도 검색
        for data_source, data in [("profile", profile_data), ("key_metrics", key_metrics_data), ("ratios", ratios_data)]:
            if "error" not in data and field_name in data and data[field_name] is not None:
                value = data[field_name]
                if show_debug:
                    st.success(f"✅ Found in {data_source}: {field_name} = {value}")
                try:
                    return float(value)
                except Exception:
                    return value
        
        if show_debug:
            st.write("**Available fields in profile:**")
            if "error" not in profile_data:
                st.write(list(profile_data.keys())[:20])
            st.write("**Available fields in key_metrics:**")
            if "error" not in key_metrics_data:
                st.write(list(key_metrics_data.keys())[:20])
            st.write("**Available fields in ratios:**")
            if "error" not in ratios_data:
                st.write(list(ratios_data.keys())[:20])
            st.warning(f"Field '{field_name}' not found")
        
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
    st.write("**📊 Finance Data API - Financial Modeling Prep**")
    st.write("")
    
    if not API_KEY:
        st.error("⚠️ FMP API 키가 설정되지 않았습니다!")
        st.write("")
        st.write("**설정 방법:**")
        st.write("1. https://site.financialmodelingprep.com/developer/docs/ 접속")
        st.write("2. 무료 가입 (이메일만 입력)")
        st.write("3. Dashboard에서 API 키 복사")
        st.write("4. Streamlit Cloud → App 설정 → Secrets:")
        st.code('FMP_API_KEY = "YOUR_API_KEY_HERE"', language="toml")
    else:
        st.success(f"✓ API 키 설정됨: ...{API_KEY[-8:]}")
    
    st.write("")
    st.write("**테스트:**")
    st.code("?ticker=AAPL&field=price&debug=true")
    
    st.write("")
    st.write("**사용 예시:**")
    st.code("?ticker=AAPL&field=price")
    st.code("?ticker=AAPL&field=debtToEquity")
    st.code("?ticker=MSFT&field=marketCap")
    st.code("?ticker=GOOGL&field=trailingPE")
    
    st.write("")
    st.write("**지원 필드:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**가격/거래:**")
        st.write("- `price` - 현재 주가")
        st.write("- `volume` - 거래량")
        st.write("- `beta` - 베타")
        
    with col2:
        st.write("**비율:**")
        st.write("- `debtToEquity` - 부채비율")
        st.write("- `currentRatio` - 유동비율")
        st.write("- `trailingPE` - PER")
        st.write("- `priceToBook` - PBR")
        
    with col3:
        st.write("**재무:**")
        st.write("- `marketCap` - 시가총액")
        st.write("- `revenue` - 매출")
        st.write("- `eps` - 주당순이익")
        st.write("- `dividendYield` - 배당률")
    
    st.write("")
    st.info("💡 무료 플랜: 250 requests/day (캐싱으로 최적화)")
    
    st.write("")
    st.write("**FMP 장점:**")
    st.write("✅ Alpha Vantage보다 많은 무료 호출 (250 vs 25)")
    st.write("✅ 재무 비율이 이미 계산되어 있음 (D/E, Current Ratio 등)")
    st.write("✅ 안정적인 API")
    st.write("✅ 실시간 데이터")
