import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 페이지 설정
st.set_page_config(page_title="투자 포트폴리오 대시보드", layout="wide")

# --------------------------
# 데이터 로드
# --------------------------
@st.cache_data
def load_portfolio_data():
    data = """팀,자산,섹터,기업명,티커
청팀,기회자산,우주경제,Rocket Lab,RKLB
청팀,기회자산,우주경제,Lockheed Martin,LMT
청팀,기회자산,우주경제,Raytheon Technologies Corporation,RTX
청팀,기회자산,우주경제,Boeing,BA
청팀,기회자산,우주경제,Northrop Grumman,NOC
청팀,기회자산,장수과학,CRISPR Therapeutics,CRSP
백팀,성장자산,AI,Palantir,PLTR
백팀,성장자산,AI,Salesforce,CRM
백팀,성장자산,데이터 인프라(로직반도체),NVIDIA,NVDA
백팀,성장자산,데이터 인프라(로직반도체),AMD,AMD"""
    from io import StringIO
    return pd.read_csv(StringIO(data))

# --------------------------
# Finviz 호출 함수 (캐시 적용)
# --------------------------
@st.cache_data(ttl=86400)
def get_finviz_metric(ticker, metric_name):
    try:
        url = f"https://finviz.com/quote.ashx?t={ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table', {'class': 'snapshot-table2'})
        if not tables:
            return "-"
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                for i in range(0, len(cells) - 1, 2):
                    if cells[i].text.strip() == metric_name:
                        value = cells[i + 1].text.strip().replace('%', '').replace(',', '')
                        try:
                            return float(value)
                        except:
                            return value
        return "-"
    except:
        return "-"

@st.cache_data(ttl=86400)
def get_finviz_data(ticker, statement, item):
    try:
        statement_map = {"IS": "IQ", "BS": "BQ", "CF": "CQ"}
        url = f"https://finviz.com/api/statement.ashx?t={ticker}&so=F&s={statement_map[statement]}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data and 'data' in data and item in data['data']:
            value = data['data'][item][0]
            return float(value) if value != '-' else None
        return None
    except:
        return None

# --------------------------
# Yahoo Finance 데이터
# --------------------------
@st.cache_data(ttl=3600)
def get_stock_data(ticker, start_date, end_date):
    try:
        import time
        start_ts = int(datetime.combine(start_date, datetime.min.time()).timestamp())
        end_ts = int(datetime.combine(end_date, datetime.max.time()).timestamp())
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        params = {'period1': start_ts, 'period2': end_ts, 'interval': '1d'}
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, params=params, headers=headers, timeout=20)
        if response.status_code != 200:
            return None
        data = response.json()['chart']['result'][0]
        timestamps = data['timestamp']
        indicators = data['indicators']['quote'][0]
        df = pd.DataFrame({
            'Date': [datetime.fromtimestamp(t) for t in timestamps],
            'Close': indicators['close']
        }).dropna()
        df.set_index('Date', inplace=True)
        return df
    except Exception as e:
        return None

# --------------------------
# 메인 앱
# --------------------------
def main():
    st.title("📊 투자 포트폴리오 대시보드")

    st.sidebar.header("⚙️ 설정")
    default_start = datetime(2025, 10, 1)
    default_end = datetime.now()

    start_date = st.sidebar.date_input("시작일", default_start)
    end_date = st.sidebar.date_input("종료일", default_end)
    analyze_button = st.sidebar.button("🔍 분석 시작", type="primary")

    portfolio_df = load_portfolio_data()
    tab1, tab2 = st.tabs(["📈 포트폴리오 분석", "📊 트렌드 분석"])

    # --------------------------
    # 포트폴리오 분석
    # --------------------------
    with tab1:
        if analyze_button:
            st.info("데이터 수집 중... 잠시만 기다려주세요.")
            results = []
            progress = st.progress(0)

            for idx, row in portfolio_df.iterrows():
                ticker = row['티커']
                progress.progress((idx + 1) / len(portfolio_df))

                df = get_stock_data(ticker, start_date, end_date)
                if df is None or df.empty:
                    continue

                base = df['Close'].iloc[0]
                current = df['Close'].iloc[-1]
                cum_return = ((df['Close'] / base) - 1) * 100

                debt_ratio = get_finviz_metric(ticker, "Debt/Eq")
                roe = get_finviz_metric(ticker, "ROE")
                total_cash = get_finviz_data(ticker, "BS", "Cash & Short Term Investments")
                fcf = get_finviz_data(ticker, "CF", "Free Cash Flow")
                runway = round(total_cash / abs(fcf), 1) if total_cash and fcf and fcf < 0 else "-"

                results.append({
                    '팀': row['팀'],
                    '섹터': row['섹터'],
                    '기업명': row['기업명'],
                    '티커': ticker,
                    '현재가': round(current, 2),
                    '누적수익률': round(cum_return.iloc[-1], 2),
                    'ROE': roe,
                    '부채비율': debt_ratio,
                    'Runway(년)': runway,
                    'cumulative_returns': cum_return
                })

            st.session_state['results'] = results
            st.session_state['result_df'] = pd.DataFrame(results)
            st.success("✅ 분석 완료!")

            df_display = st.session_state['result_df']
            st.dataframe(df_display, use_container_width=True)

    # --------------------------
    # 트렌드 분석
    # --------------------------
    with tab2:
        if 'result_df' in st.session_state:
            result_df = st.session_state['result_df']
            st.subheader("📊 팀별/섹터별 트렌드 분석")

            # 4️⃣ 청팀 vs 백팀 누적수익률 비교
            st.markdown("### 4️⃣ 청팀 vs 백팀 누적수익률 비교 (가중평균 포함)")

            team_returns = {}
            for team in result_df['팀'].unique():
                team_stocks = result_df[result_df['팀'] == team]
                all_returns = [r['cumulative_returns'] for _, r in team_stocks.iterrows() if r['cumulative_returns'] is not None]
                if all_returns:
                    combined = pd.concat(all_returns, axis=1)
                    # 종목 수 가중 평균 (동일 가중)
                    team_avg = combined.mean(axis=1)
                    team_returns[team] = team_avg

            if team_returns:
                total_stocks = sum(len(result_df[result_df['팀'] == t]) for t in team_returns.keys())
                weighted_averages = {}
                for team, data in team_returns.items():
                    weight = len(result_df[result_df['팀'] == team]) / total_stocks
                    weighted_averages[team] = data * weight

                # 합산 (전체 시장 가중평균)
                total_weighted = sum(weighted_averages.values())

                fig = go.Figure()
                for team, data in team_returns.items():
                    fig.add_trace(go.Scatter(x=data.index, y=data.values, mode='lines', name=f"{team} 평균"))
                fig.add_trace(go.Scatter(
                    x=total_weighted.index,
                    y=total_weighted.values,
                    mode='lines',
                    name="시장 전체 가중평균",
                    line=dict(width=3, dash="dot", color="black")
                ))

                fig.update_layout(
                    title="청팀 vs 백팀 누적수익률 비교 (가중 평균 반영)",
                    xaxis_title="날짜",
                    yaxis_title="누적수익률 (%)",
                    height=500,
                    hovermode='x unified',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                fig.add_hline(y=0, line_dash="dash", line_color="gray")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("먼저 '포트폴리오 분석' 탭에서 분석을 실행해주세요.")


if __name__ == "__main__":
    main()
