import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import time

# 페이지 설정
st.set_page_config(page_title="투자 포트폴리오 대시보드", layout="wide")

# -------------------------------------------------------
# 데이터 로드
# -------------------------------------------------------
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

# -------------------------------------------------------
# Finviz 캐시 최적화 적용
# -------------------------------------------------------
@st.cache_data(ttl=86400)
def get_finviz_metric_cached(ticker, metric_name):
    try:
        url = f"https://finviz.com/quote.ashx?t={ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table', {'class': 'snapshot-table2'})
        if not tables:
            return "-"
        for table in tables:
            for row in table.find_all('tr'):
                cells = row.find_all('td')
                for i in range(0, len(cells)-1, 2):
                    if cells[i].text.strip() == metric_name:
                        val = cells[i+1].text.strip().replace('%','').replace(',','')
                        try:
                            return float(val)
                        except:
                            return val
        return "-"
    except:
        return "-"

@st.cache_data(ttl=86400)
def get_finviz_data_cached(ticker, statement, item):
    try:
        map_ = {"IS": "IQ", "BS": "BQ", "CF": "CQ"}
        url = f"https://finviz.com/api/statement.ashx?t={ticker}&so=F&s={map_[statement]}"
        res = requests.get(url, timeout=10)
        data = res.json()
        if data and 'data' in data and item in data['data']:
            v = data['data'][item][0]
            return float(v) if v != '-' else None
        return None
    except:
        return None

# -------------------------------------------------------
# Yahoo Finance Chart API
# -------------------------------------------------------
@st.cache_data(ttl=3600)
def get_stock_data(ticker, start_date, end_date):
    try:
        start_ts = int(datetime.combine(start_date, datetime.min.time()).timestamp())
        end_ts = int(datetime.combine(end_date, datetime.max.time()).timestamp())
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        params = {'period1': start_ts, 'period2': end_ts, 'interval': '1d'}
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, params=params, headers=headers, timeout=20)
        if res.status_code != 200:
            return None
        data = res.json()
        result = data['chart']['result'][0]
        timestamps = result.get('timestamp', [])
        indicators = result['indicators']['quote'][0]
        df = pd.DataFrame({
            'Date': [datetime.fromtimestamp(t) for t in timestamps],
            'Close': indicators['close']
        }).dropna()
        df.set_index('Date', inplace=True)
        return df
    except:
        return None

# -------------------------------------------------------
# 메인 앱
# -------------------------------------------------------
def main():
    st.title("📊 투자 포트폴리오 대시보드")

    st.sidebar.header("⚙️ 설정")
    start_date = st.sidebar.date_input("시작일", datetime(2025,10,1))
    end_date = st.sidebar.date_input("종료일", datetime.now())
    analyze = st.sidebar.button("🔍 분석 시작", type="primary")

    df_port = load_portfolio_data()
    tab1, tab2 = st.tabs(["📈 포트폴리오 분석", "📊 트렌드 분석"])

    # ---------------- 포트폴리오 분석 ----------------
    with tab1:
        if analyze:
            st.info("데이터를 수집 중입니다. 잠시만 기다려주세요.")
            results = []
            prog = st.progress(0)

            for i, row in df_port.iterrows():
                ticker = row['티커']
                prog.progress((i+1)/len(df_port))
                data = get_stock_data(ticker, start_date, end_date)
                if data is None or data.empty:
                    continue
                base, curr = data['Close'].iloc[0], data['Close'].iloc[-1]
                highest = data['Close'].max()
                cum = ((data['Close']/base)-1)*100
                debt = get_finviz_metric_cached(ticker, "Debt/Eq")
                curr_ratio = get_finviz_metric_cached(ticker, "Current Ratio")
                roe = get_finviz_metric_cached(ticker, "ROE")
                cash = get_finviz_data_cached(ticker, "BS", "Cash & Short Term Investments")
                fcf = get_finviz_data_cached(ticker, "CF", "Free Cash Flow")
                runway = round(cash/abs(fcf),1) if cash and fcf and fcf<0 else "-"
                results.append({
                    '팀':row['팀'],'섹터':row['섹터'],'기업명':row['기업명'],'티커':ticker,
                    '기준가':round(base,2),'현재가':round(curr,2),'최고가':round(highest,2),
                    '누적수익률(기준가)':round(((curr-base)/base)*100,2),
                    '누적수익률(최고가)':round(((curr-highest)/highest)*100,2),
                    'ROE':roe,'부채비율':debt,'유동비율':curr_ratio,
                    'Runway(년)':runway,'Total Cash(M$)':cash,'FCF(M$)':fcf,
                    'price_data':data,'cumulative_returns':cum
                })
            st.session_state['result_df'] = pd.DataFrame(results)
            st.success("✅ 분석 완료!")

            st.subheader("📋 포트폴리오 결과 요약")
            disp = st.session_state['result_df'].copy()
            st.dataframe(disp,use_container_width=True)

    # ---------------- 트렌드 분석 ----------------
    with tab2:
        if 'result_df' not in st.session_state:
            st.info("먼저 '포트폴리오 분석' 탭에서 분석을 실행해주세요.")
            return

        result_df = st.session_state['result_df']
        st.subheader("📊 트렌드 분석")

        # 팀별 평균 변동률 트렌드
        st.markdown("### 1️⃣ 팀별 평균 변동률 트렌드")
        team_data = {}
        for team in result_df['팀'].unique():
            changes = []
            for _, row in result_df[result_df['팀']==team].iterrows():
                if row['cumulative_returns'] is not None:
                    changes.append(row['cumulative_returns'].pct_change().dropna()*100)
            if changes:
                combined = pd.concat(changes,axis=1).mean(axis=1)
                team_data[team]=combined
        if team_data:
            fig_team = go.Figure()
            for t,d in team_data.items():
                fig_team.add_trace(go.Scatter(x=d.index,y=d.values,mode='lines',name=t))
            fig_team.update_layout(title="팀별 평균 변동률",height=400)
            st.plotly_chart(fig_team,use_container_width=True)

        # 섹터별 평균 변동률
        st.markdown("### 2️⃣ 섹터별 평균 변동률 트렌드")
        sector_data={}
        for s in result_df['섹터'].unique():
            arr=[]
            for _,r in result_df[result_df['섹터']==s].iterrows():
                if r['cumulative_returns'] is not None:
                    arr.append(r['cumulative_returns'].pct_change().dropna()*100)
            if arr:
                sector_data[s]=pd.concat(arr,axis=1).mean(axis=1)
        if sector_data:
            fig_sector=go.Figure()
            for s,d in sector_data.items():
                fig_sector.add_trace(go.Scatter(x=d.index,y=d.values,mode='lines',name=s))
            fig_sector.update_layout(title="섹터별 평균 변동률",height=400)
            st.plotly_chart(fig_sector,use_container_width=True)

        # 섹터별 개별 종목 변동률
        st.markdown("### 3️⃣ 섹터별 개별 종목 변동률")
        for sector in result_df['섹터'].unique():
            with st.expander(f"📂 {sector}"):
                sector_df = result_df[result_df['섹터']==sector]
                n=len(sector_df)
                rows=(n+2)//3
                fig=make_subplots(rows=rows,cols=3,
                    subplot_titles=[f"{r['티커']}" for _,r in sector_df.iterrows()],
                    vertical_spacing=0.1,horizontal_spacing=0.05)
                for idx,(_,r) in enumerate(sector_df.iterrows()):
                    if r['cumulative_returns'] is not None:
                        ch=r['cumulative_returns'].pct_change().dropna()*100
                        row,col=(idx//3)+1,(idx%3)+1
                        fig.add_trace(go.Bar(x=ch.index,y=ch.values,showlegend=False),row=row,col=col)
                fig.update_layout(height=300*rows,title=f"{sector} 섹터 변동률")
                st.plotly_chart(fig,use_container_width=True)

        # ✅ 청팀 vs 백팀 누적수익률 비교 (가중평균 포함)
        st.markdown("### 4️⃣ 청팀 vs 백팀 누적수익률 비교 (가중평균 포함)")
        team_returns={}
        for team in result_df['팀'].unique():
            team_stocks=result_df[result_df['팀']==team]
            arr=[]
            for _,r in team_stocks.iterrows():
                if r['cumulative_returns'] is not None:
                    arr.append(r['cumulative_returns'].dropna())
            if arr:
                team_returns[team]=pd.concat(arr,axis=1).mean(axis=1)

        if team_returns:
            total=sum(len(result_df[result_df['팀']==t]) for t in team_returns.keys())
            weighted={}
            for t,d in team_returns.items():
                w=len(result_df[result_df['팀']==t])/total
                weighted[t]=d*w
            total_weighted=sum(weighted.values())

            fig=go.Figure()
            for t,d in team_returns.items():
                fig.add_trace(go.Scatter(x=d.index,y=d.values,mode='lines',name=f"{t} 평균"))
            fig.add_trace(go.Scatter(x=total_weighted.index,y=total_weighted.values,
                                     mode='lines',name="시장 전체 가중평균",
                                     line=dict(width=3,dash='dot',color='black')))
            fig.update_layout(title="청팀 vs 백팀 누적수익률 비교 (가중평균 포함)",
                              height=500,hovermode='x unified')
            fig.add_hline(y=0,line_dash="dash",line_color="gray")
            st.plotly_chart(fig,use_container_width=True)

if __name__=="__main__":
    main()
