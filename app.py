import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Finance API")
st.title("📡 Finance Data API (for Google Sheets)")

ticker = st.query_params.get("ticker", "")
field = st.query_params.get("field", "")
debug = st.query_params.get("debug", "")

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
        # ② 부채비율 (Debt to Equity) - info에서 직접 가져오기
        # ------------------------------
        if field == "debtToEquity":
            try:
                info = t.info
                
                if show_debug:
                    st.write("**Trying to get debtToEquity from info...**")
                
                # 방법 1: info에서 직접 debtToEquity 가져오기
                if 'debtToEquity' in info and info['debtToEquity'] is not None:
                    return float(info['debtToEquity']) / 100  # 종종 퍼센트로 저장됨
                
                # 방법 2: totalDebt와 totalStockholderEquity로 계산
                total_debt = info.get('totalDebt', None)
                stockholder_equity = info.get('totalStockholderEquity', None)
                
                if show_debug:
                    st.write(f"Total Debt: {total_debt}")
                    st.write(f"Stockholder Equity: {stockholder_equity}")
                
                if total_debt and stockholder_equity and stockholder_equity != 0:
                    return round(float(total_debt) / float(stockholder_equity), 2)
                
                # 방법 3: 재무제표에서 가져오기 (quarterly 포함)
                try:
                    # 연간 재무제표 시도
                    bs = t.balance_sheet
                    if bs is None or bs.empty:
                        # 분기 재무제표 시도
                        bs = t.quarterly_balance_sheet
                    
                    if bs is not None and not bs.empty:
                        if show_debug:
                            st.write("**Balance Sheet Items:**")
                            st.write(bs.index.tolist())
                        
                        latest_col = bs.columns[0]
                        
                        # 다양한 항목명 시도
                        debt = None
                        equity = None
                        
                        for d in ["Total Debt", "TotalDebt", "Net Debt", "Long Term Debt"]:
                            if d in bs.index:
                                debt = bs.loc[d, latest_col]
                                break
                        
                        for e in ["Stockholders Equity", "StockholdersEquity", 
                                  "Total Equity Gross Minority Interest", "Common Stock Equity"]:
                            if e in bs.index:
                                equity = bs.loc[e, latest_col]
                                break
                        
                        if debt is not None and equity is not None and equity != 0:
                            return round(float(debt) / float(equity), 2)
                except Exception as bs_error:
                    if show_debug:
                        st.warning(f"Balance sheet error: {bs_error}")
                
                return "N/A"
                    
            except Exception as e:
                if show_debug:
                    st.error(f"Debt to Equity error: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                return "N/A"
        
        # ------------------------------
        # ③ 유동비율 (Current Ratio) - info에서 직접 가져오기
        # ------------------------------
        if field == "currentRatio":
            try:
                info = t.info
                
                if show_debug:
                    st.write("**Trying to get currentRatio from info...**")
                
                # 방법 1: info에서 직접 currentRatio 가져오기
                if 'currentRatio' in info and info['currentRatio'] is not None:
                    return float(info['currentRatio'])
                
                # 방법 2: 재무제표에서 계산
                try:
                    bs = t.balance_sheet
                    if bs is None or bs.empty:
                        bs = t.quarterly_balance_sheet
                    
                    if bs is not None and not bs.empty:
                        if show_debug:
                            st.write("**Balance Sheet Items:**")
                            st.write(bs.index.tolist())
                        
                        latest_col = bs.columns[0]
                        
                        ca = None
                        cl = None
                        
                        for c in ["Current Assets", "CurrentAssets", "Total Current Assets"]:
                            if c in bs.index:
                                ca = bs.loc[c, latest_col]
                                break
                        
                        for c in ["Current Liabilities", "CurrentLiabilities", "Total Current Liabilities"]:
                            if c in bs.index:
                                cl = bs.loc[c, latest_col]
                                break
                        
                        if ca is not None and cl is not None and cl != 0:
                            return round(float(ca) / float(cl), 2)
                except Exception as bs_error:
                    if show_debug:
                        st.warning(f"Balance sheet error: {bs_error}")
                
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
                st.write("**Sample info fields:**")
                sample_keys = list(info.keys())[:20]
                st.write(sample_keys)
            
            if field in info and info[field] is not None:
                return info[field]
            else:
                if show_debug:
                    st.warning(f"Field '{field}' not found or is None in info")
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
    st.write("- 기타 yfinance info 필드")
    st.write("")
    st.write("**info에서 직접 가져올 수 있는 재무 필드 예시:**")
    st.write("- `totalDebt`, `totalStockholderEquity`, `totalCash`")
    st.write("- `totalRevenue`, `ebitda`, `netIncomeToCommon`")
    st.write("- `marketCap`, `enterpriseValue`, `profitMargins`")
