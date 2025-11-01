import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

st.set_page_config(page_title="Finance API")
st.title("📡 Finance Data API (for Google Sheets)")

ticker = st.query_params.get("ticker", "")
field = st.query_params.get("field", "")
debug = st.query_params.get("debug", "")

# API 키 가져오기
API_KEY = None
try:
    API_KEY = st.secrets["ALPHA_VANTAGE_API_KEY"]
except Exception as e:
    # 로컬 테스트용 - 환경변수에서도 시도
    import os
    API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY")

if not API_KEY and not ticker:
    st.error("⚠️ Alpha Vantage API 키가 설정되지 않았습니다.")
    st.write("**설정 방법:**")
    st.write("1. https://www.alphavantage.co/support/#api-key 에서 무료 API 키 발급")
    st.write("2. Streamlit Cloud → Settings → Secrets에 다음 추가:")
    st.code('ALPHA_VANTAGE_API_KEY = "your_api_key_here"', language="toml")
    st.write("3. 로컬 개발 시: `.streamlit/secrets.toml` 파일 생성")

@st.cache_data(ttl=300)  # 5분 캐시
def get_alpha_vantage_quote(symbol):
    """실시간 가격 정보"""
    if not API_KEY:
        return {"error": "NO_API_KEY", "message": "API key not configured"}
    
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        return data
    except requests.exceptions.Timeout:
        return {"error": "TIMEOUT", "message": "Request timeout"}
    except requests.exceptions.RequestException as e:
        return {"error": "REQUEST_ERROR", "message": str(e)}
    except json.JSONDecodeError:
        return {"error": "JSON_ERROR", "message": "Invalid JSON response"}
    except Exception as e:
        return {"error": "UNKNOWN", "message": str(e)}

@st.cache_data(ttl=3600)  # 1시간 캐시
def get_alpha_vantage_overview(symbol):
    """회사 개요 데이터 (재무 지표 포함)"""
    if not API_KEY:
        return {"error": "NO_API_KEY", "message": "API key not configured"}
    
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={API_KEY}"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        return data
    except Exception as e:
        return {"error": "REQUEST_FAILED", "message": str(e)}

@st.cache_data(ttl=3600)
def get_alpha_vantage_balance_sheet(symbol):
    """재무상태표 (Balance Sheet)"""
    if not API_KEY:
        return {"error": "NO_API_KEY", "message": "API key not configured"}
    
    url = f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={symbol}&apikey={API_KEY}"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        return data
    except Exception as e:
        return {"error": "REQUEST_FAILED", "message": str(e)}

def calculate_debt_to_equity(overview_data, balance_sheet_data, show_debug=False):
    """부채비율 계산"""
    
    # Balance Sheet에서 계산
    if balance_sheet_data and "error" not in balance_sheet_data:
        try:
            if show_debug:
                st.write("**Balance Sheet Response:**")
                st.json(balance_sheet_data)
            
            # annualReports 또는 quarterlyReports 확인
            reports = balance_sheet_data.get("annualReports") or balance_sheet_data.get("quarterlyReports")
            
            if reports and len(reports) > 0:
                latest_report = reports[0]
                
                if show_debug:
                    st.write("**Latest Report:**")
                    st.json(latest_report)
                
                # Total Debt 찾기
                debt = None
                debt_keys = ["shortLongTermDebtTotal", "longTermDebt", "totalLiabilities"]
                for key in debt_keys:
                    if key in latest_report and latest_report[key] not in [None, "None", ""]:
                        try:
                            debt = float(latest_report[key])
                            if show_debug:
                                st.success(f"✓ Found debt ({key}): {debt:,.0f}")
                            break
                        except Exception:
                            pass
                
                # Total Equity 찾기
                equity = None
                equity_keys = ["totalShareholderEquity", "commonStockSharesOutstanding"]
                for key in equity_keys:
                    if key in latest_report and latest_report[key] not in [None, "None", ""]:
                        try:
                            equity = float(latest_report[key])
                            if show_debug:
                                st.success(f"✓ Found equity ({key}): {equity:,.0f}")
                            break
                        except Exception:
                            pass
                
                if debt and equity and equity != 0:
                    ratio = round(debt / equity, 2)
                    if show_debug:
                        st.success(f"✅ D/E Ratio: {debt:,.0f} / {equity:,.0f} = {ratio}")
                    return ratio
                else:
                    if show_debug:
                        st.warning(f"Missing data - Debt: {debt}, Equity: {equity}")
                        
        except Exception as e:
            if show_debug:
                st.error(f"Calculation error: {e}")
                import traceback
                st.code(traceback.format_exc())
    
    return None

def calculate_current_ratio(balance_sheet_data, show_debug=False):
    """유동비율 계산"""
    if not balance_sheet_data or "error" in balance_sheet_data:
        return None
    
    try:
        reports = balance_sheet_data.get("annualReports") or balance_sheet_data.get("quarterlyReports")
        
        if reports and len(reports) > 0:
            latest_report = reports[0]
            
            ca = latest_report.get("totalCurrentAssets")
            cl = latest_report.get("totalCurrentLiabilities")
            
            if ca and cl and ca not in ["None", None] and cl not in ["None", None]:
                ca = float(ca)
                cl = float(cl)
                
                if show_debug:
                    st.write(f"Current Assets: {ca:,.0f}")
                    st.write(f"Current Liabilities: {cl:,.0f}")
                
                if cl != 0:
                    return round(ca / cl, 2)
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
            st.write(f"**Fetching data for {ticker_symbol}...**")
            st.write(f"**Field: {field_name}**")
            st.write(f"**API Key: {'*' * (len(API_KEY) - 4) + API_KEY[-4:]}**")
        
        # ------------------------------
        # ① 가격 (price)
        # ------------------------------
        if field_name == "price":
            quote_data = get_alpha_vantage_quote(ticker_symbol)
            
            if show_debug:
                st.write("**Quote API Response:**")
                st.json(quote_data)
            
            # 에러 체크
            if "error" in quote_data:
                if show_debug:
                    st.error(f"API Error: {quote_data.get('message', 'Unknown error')}")
                return "N/A"
            
            # API 제한 체크
            if "Note" in quote_data:
                if show_debug:
                    st.warning("⚠️ API call frequency limit reached (5 calls/min, 500 calls/day)")
                return "API_LIMIT"
            
            # Invalid API key 체크
            if "Error Message" in quote_data:
                if show_debug:
                    st.error(f"❌ {quote_data['Error Message']}")
                return "INVALID_API_KEY"
            
            # Global Quote 데이터 추출
            if "Global Quote" in quote_data:
                global_quote = quote_data["Global Quote"]
                
                if show_debug:
                    st.write("**Global Quote:**")
                    st.json(global_quote)
                
                # 가격 필드들 확인
                price_keys = ["05. price", "price", "05price"]
                for key in price_keys:
                    if key in global_quote:
                        try:
                            price = float(global_quote[key])
                            if show_debug:
                                st.success(f"✅ Price found: ${price}")
                            return price
                        except Exception:
                            pass
            
            if show_debug:
                st.error("❌ Failed to extract price from response")
            return "N/A"
        
        # 나머지 필드는 overview 또는 balance sheet 필요
        overview_data = get_alpha_vantage_overview(ticker_symbol)
        
        if show_debug:
            st.write("**Overview API Response:**")
            if "error" in overview_data:
                st.error(f"Error: {overview_data.get('message')}")
            elif "Note" in overview_data:
                st.warning("API limit reached")
            else:
                st.json(dict(list(overview_data.items())[:10]))
        
        # ------------------------------
        # ② 부채비율 (debtToEquity)
        # ------------------------------
        if field_name == "debtToEquity":
            balance_sheet_data = get_alpha_vantage_balance_sheet(ticker_symbol)
            
            ratio = calculate_debt_to_equity(overview_data, balance_sheet_data, show_debug)
            
            if ratio:
                return ratio
            
            if show_debug:
                st.error("❌ Could not calculate D/E ratio")
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
                st.error("❌ Could not calculate current ratio")
            return "N/A"
        
        # ------------------------------
        # ④ Overview의 다른 필드들
        # ------------------------------
        if overview_data and "error" not in overview_data and "Note" not in overview_data:
            if show_debug:
                st.write("**Available overview fields:**")
                st.write(list(overview_data.keys()))
            
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
            
            alpha_field = field_mapping.get(field_name, field_name)
            
            if alpha_field in overview_data and overview_data[alpha_field] not in ["None", None, ""]:
                value = overview_data[alpha_field]
                try:
                    return float(value)
                except Exception:
                    return value
            
            if field_name in overview_data and overview_data[field_name] not in ["None", None, ""]:
                value = overview_data[field_name]
                try:
                    return float(value)
                except Exception:
                    return value
            
            if show_debug:
                st.warning(f"Field '{field_name}' (mapped to '{alpha_field}') not found")
        
        return "N/A"
        
    except Exception as e:
        if show_debug:
            st.error(f"Unexpected error: {e}")
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
        st.write("")
        st.write("**설정 방법:**")
        st.write("1. https://www.alphavantage.co/support/#api-key 에서 무료 API 키 발급 (이메일만 입력)")
        st.write("2. Streamlit Cloud → App 설정 → Secrets 탭")
        st.write("3. 다음 내용 추가:")
        st.code('ALPHA_VANTAGE_API_KEY = "YOUR_API_KEY_HERE"', language="toml")
        st.write("4. 로컬 개발 시: `.streamlit/secrets.toml` 파일 생성 후 동일 내용 추가")
    else:
        st.success(f"✓ API 키 설정됨: {'*' * (len(API_KEY) - 4) + API_KEY[-4:]}")
    
    st.write("")
    st.write("**테스트:**")
    st.code("?ticker=AAPL&field=price&debug=true")
    
    st.write("")
    st.write("**사용 예시:**")
    st.code("?ticker=AAPL&field=price")
    st.code("?ticker=AAPL&field=debtToEquity")
    st.code("?ticker=MSFT&field=marketCap")
    
    st.write("")
    st.write("**지원 필드:**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**가격/비율:**")
        st.write("- `price` - 현재 주가")
        st.write("- `debtToEquity` - 부채비율")
        st.write("- `currentRatio` - 유동비율")
        st.write("- `trailingPE` - PER")
        st.write("- `priceToBook` - PBR")
        
    with col2:
        st.write("**재무 지표:**")
        st.write("- `marketCap` - 시가총액")
        st.write("- `revenue` - 매출")
        st.write("- `ebitda` - EBITDA")
        st.write("- `eps` - 주당순이익")
        st.write("- `dividendYield` - 배당수익률")
    
    st.write("")
    st.info("💡 무료 API: 분당 5회, 일일 500회 제한 (캐싱으로 최적화)")
