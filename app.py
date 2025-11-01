import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Finance API")
st.title("📡 Finance Data API (for Google Sheets)")

ticker = st.query_params.get("ticker", "")
field = st.query_params.get("field", "")

def get_data(ticker, field):
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
                st.error(f"Price error: {e}")
                return "N/A"
        
        # ------------------------------
        # ② 부채비율 (Debt to Equity)
        # ------------------------------
        if field == "debtToEquity":
            try:
                # quarterly=False로 연간 재무제표 가져오기
                bs = t.balance_sheet
                
                if bs is None or bs.empty:
                    return "N/A"
                
                # 가장 최근 컬럼
                latest_col = bs.columns[0]
                
                # 부채 항목 찾기
                debt_candidates = [
                    "Total Debt",
                    "Long Term Debt", 
                    "Net Debt",
                    "Total Liabilities Net Minority Interest"
                ]
                
                # 자본 항목 찾기
                equity_candidates = [
                    "Stockholders Equity",
                    "Total Equity Gross Minority Interest",
                    "Common Stock Equity"
                ]
                
                debt = None
                equity = None
                
                # 부채 찾기
                for name in debt_candidates:
                    if name in bs.index:
                        debt = bs.loc[name, latest_col]
                        break
                
                # 자본 찾기
                for name in equity_candidates:
                    if name in bs.index:
                        equity = bs.loc[name, latest_col]
                        break
                
                if debt is not None and equity is not None and equity != 0:
                    return round(float(debt) / float(equity), 2)
                else:
                    return "N/A"
                    
            except Exception as e:
                st.error(f"Debt to Equity error: {e}")
                return "N/A"
        
        # ------------------------------
        # ③ 유동비율 (Current Ratio)
        # ------------------------------
        if field == "currentRatio":
            try:
                bs = t.balance_sheet
                
                if bs is None or bs.empty:
                    return "N/A"
                
                latest_col = bs.columns[0]
                
                ca_candidates = [
                    "Current Assets",
                    "Total Current Assets"
                ]
                
                cl_candidates = [
                    "Current Liabilities",
                    "Total Current Liabilities"
                ]
                
                ca = None
                cl = None
                
                for name in ca_candidates:
                    if name in bs.index:
                        ca = bs.loc[name, latest_col]
                        break
                
                for name in cl_candidates:
                    if name in bs.index:
                        cl = bs.loc[name, latest_col]
                        break
                
                if ca is not None and cl is not None and cl != 0:
                    return round(float(ca) / float(cl), 2)
                else:
                    return "N/A"
                    
            except Exception as e:
                st.error(f"Current Ratio error: {e}")
                return "N/A"
        
        # ------------------------------
        # ④ 기본 info 항목
        # ------------------------------
        try:
            info = t.info
            
            if field in info:
                return info[field]
            else:
                return "N/A"
                
        except Exception as e:
            st.error(f"Info error: {e}")
            return "N/A"
            
    except Exception as e:
        st.error(f"General error: {e}")
        return "N/A"


if ticker and field:
    result = get_data(ticker, field)
    st.json({"ticker": ticker, "field": field, "value": result})
else:
    st.write("**사용법:**")
    st.code("?ticker=AAPL&field=debtToEquity")
    st.write("**지원 필드:**")
    st.write("- `price`: 현재 주가")
    st.write("- `debtToEquity`: 부채비율")
    st.write("- `currentRatio`: 유동비율")
    st.write("- 기타 yfinance info 필드 (예: `marketCap`, `trailingPE` 등)")
```

## 주요 개선사항:

1. **중복 import 제거**: `yfinance`와 `pandas`를 한 번만 import
2. **get_info() 대신 info 사용**: `t.info`로 직접 접근 (더 안정적)
3. **에러 메시지 추가**: 디버깅을 위해 `st.error()`로 에러 표시
4. **재무제표 항목명 업데이트**: yfinance의 최신 항목명으로 수정
5. **None 체크 강화**: `is not None`으로 명시적 체크
6. **빈 데이터프레임 체크**: `df.empty` 확인 추가
7. **사용 안내 개선**: 파라미터 없을 때 명확한 안내 메시지

## 테스트 방법:
```
?ticker=AAPL&field=price
?ticker=AAPL&field=debtToEquity
?ticker=AAPL&field=currentRatio
?ticker=AAPL&field=marketCap
