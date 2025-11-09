import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import time

# 페이지 설정
st.set_page_config(page_title="투자 포트폴리오 대시보드", layout="wide")

# 데이터 로드
@st.cache_data
def load_portfolio_data():
    data = """팀,자산,섹터,기업명,티커
청팀,기회자산,우주경제,Rocket Lab,RKLB
청팀,기회자산,우주경제,Lockheed Martin,LMT
청팀,기회자산,우주경제,Raytheon Technologies Corporation,RTX
청팀,기회자산,우주경제,Boeing,BA
청팀,기회자산,우주경제,Northrop Grumman,NOC
청팀,기회자산,우주경제,AST SpaceMobile,ASTS
청팀,기회자산,우주경제,Virgin Galactic,SPCE
청팀,기회자산,우주경제,JOBY Aviation,JOBY
청팀,기회자산,우주경제,Archer Aviation,ACHR
청팀,기회자산,장수과학,Intellia Therapeutics,NTLA
청팀,기회자산,장수과학,CRISPR Therapeutics,CRSP
청팀,기회자산,장수과학,Recursion Pharmaceuticals,RXRX
청팀,기회자산,장수과학,UniQure,QURE
청팀,성장자산,장수과학,Tempus AI,TEM
청팀,성장자산,장수과학,HIMS&HERS,HIMS
청팀,기회자산,합성생물학,Ginkgo Bioworks,DNA
청팀,기회자산,합성생물학,Twist Bioscience,TWST
청팀,기회자산,합성생물학,10x Genomics,TXG
청팀,기회자산,합성생물학,Appsella Biologics,ABCL
청팀,기회자산,양자컴퓨터,IonQ,IONQ
청팀,기회자산,양자컴퓨터,D-Wave Quantum,QBTS
청팀,기회자산,양자컴퓨터,Rigetti Computing,RGTI
청팀,기회자산,양자컴퓨터,IBM,IBM
청팀,기회자산,양자컴퓨터,Quantum Computing,QUBT
청팀,기회자산,양자 암호,Arqit,ARQQ
청팀,기회자산,양자 암호,SEALSQ,LAES
청팀,기회자산,양자 암호,BTQ,BTQ
청팀,기회자산,BCI,ClearPoint Neuro,CLPT
청팀,기회자산,BCI,NeuroPace,NPCE
백팀,성장자산,AI,Palantir,PLTR
백팀,성장자산,AI,Salesforce,CRM
백팀,성장자산,AI,Super Micro Computer Inc.,SMCI
백팀,성장자산,AI,Figma Inc.,FIG
백팀,성장자산,AI,UiPath Inc.,PATH
백팀,성장자산,AI,Symbotic Inc.,SYM
백팀,성장자산,클라우드,Nebius Group,NBIS
백팀,성장자산,클라우드,IREN Limited,IREN
백팀,성장자산,클라우드,CoreWeave,CRWV
백팀,성장자산,미래에너지(수소/암모니아),Bloom Energy,BE
백팀,성장자산,미래에너지(수소/암모니아),Plug Power,PLUG
백팀,성장자산,미래에너지(수소/암모니아),Air Products,APD
백팀,성장자산,미래에너지(수소/암모니아),Linde,LIN
백팀,성장자산,미래에너지(수소/암모니아),CF Industries,CF
백팀,성장자산,미래에너지(수소/암모니아),Ballard Power Systems,BLDP
백팀,성장자산,미래에너지(수소/암모니아),FuelCell Energy,FCEL
백팀,성장자산,미래에너지(SMR),NuScale Power,SMR
백팀,성장자산,미래에너지(SMR),Oklo,OKLO
백팀,성장자산,미래에너지(SMR),BWX Technologies,BWXT
백팀,성장자산,미래에너지(SMR),Centrus Energy Corp.,LEU
백팀,성장자산,미래에너지(SMR),Uranium Energy,UEC
백팀,성장자산,미래에너지(SMR),Cameco (US-listed),CCJ
백팀,성장자산,미래에너지(전고체배터리),QuantumScape,QS
백팀,성장자산,미래에너지(전고체배터리),Solid Power,SLDP
백팀,성장자산,미래에너지(ESS),Fluence Energy,FLNC
백팀,성장자산,미래에너지(ESS),EnerSys,ENS
백팀,성장자산,미래에너지(ESS),Eos Energy Enterprises,EOSE
백팀,성장자산,미래에너지(ESS),Tesla (Energy),TSLA
백팀,성장자산,미래에너지(ESS),Enphase Energy,ENPH
백팀,성장자산,미래에너지(ESS),Eaton,ETN
백팀,성장자산,미래에너지(재생에너지),Duke Energy,DUK
백팀,성장자산,미래에너지(재생에너지),GE Vernova,GEV
백팀,성장자산,미래에너지(재생에너지),NextEra Energy,NEE
백팀,성장자산,미래에너지(재생에너지),Constellation Energy,CEG
백팀,성장자산,미래에너지(재생에너지),American Electric Power Company,AEP
백팀,성장자산,미래에너지(재생에너지),Vistra Energy,VST
백팀,성장자산,미래에너지(재생에너지),First Solar,FSLR
백팀,성장자산,전통에너지,Exxon Mobil,XOM
백팀,성장자산,전통에너지,Chevron,CVX
백팀,성장자산,전통에너지,Marathon Petroleum,MPC
백팀,성장자산,전통에너지,Shell plc,SHEL
백팀,성장자산,전통에너지,ConocoPhillips,COP
백팀,성장자산,전통에너지,Occidental Petroleum,OXY
백팀,성장자산,전통에너지,Devon Energy,DVN
백팀,성장자산,전통에너지,Valero Energy,VLO
백팀,성장자산,전통에너지,Southern Company,SO
백팀,성장자산,데이터 인프라(냉각),Vertiv,VRT
백팀,성장자산,데이터 인프라(냉각),Carrier Global,CARR
백팀,성장자산,데이터 인프라(냉각),Honeywell International,HON
백팀,성장자산,데이터 인프라(냉각),Johnson Controls,JCI
백팀,성장자산,데이터 인프라(네트워크),Arista Networks,ANET
백팀,성장자산,데이터 인프라(네트워크),Credo,CRDO
백팀,성장자산,데이터 인프라(네트워크),Astera Labs,ALAB
백팀,성장자산,데이터 인프라(네트워크),Marvell Technology,MRVL
백팀,성장자산,데이터 인프라(네트워크),Hewlett Packard Enterprise,HPE
백팀,성장자산,데이터 인프라(네트워크),Cisco,CSCO
백팀,성장자산,데이터 인프라(네트워크),Ciena,CIEN
백팀,성장자산,데이터 인프라(로직반도체),NVIDIA,NVDA
백팀,성장자산,데이터 인프라(로직반도체),Micron Technology,MU
백팀,성장자산,데이터 인프라(로직반도체),AMD,AMD
백팀,성장자산,데이터 인프라(로직반도체),Intel,INTC
백팀,성장자산,데이터 인프라(로직반도체),Broadcom,AVGO
백팀,성장자산,데이터 인프라(로직반도체),TSMC,TSM
백팀,성장자산,데이터 인프라(로직반도체),Lam Research,LRCX
백팀,성장자산,데이터 인프라(로직반도체),On Semiconductor,ON
백팀,성장자산,데이터 인프라(로직반도체),Synopsys,SNPS
백팀,성장자산,데이터 인프라(하이퍼스케일),Amazon (AWS),AMZN
백팀,성장자산,데이터 인프라(하이퍼스케일),Microsoft (Azure),MSFT
백팀,성장자산,데이터 인프라(하이퍼스케일),Alphabet (GCP),GOOGL
백팀,성장자산,데이터 인프라(하이퍼스케일),Meta Platforms,META
백팀,성장자산,데이터 인프라(하이퍼스케일),Apple,AAPL
백팀,성장자산,데이터 인프라(하이퍼스케일),Oracle Cloud,ORCL
백팀,성장자산,데이터 인프라(하이퍼스케일),Pure Storage,PSTG
백팀,성장자산,데이터 인프라(리츠),Equinix,EQIX
백팀,성장자산,데이터 인프라(리츠),Digital Realty,DLR
백팀,성장자산,데이터 인프라(리츠),CyrusOne,CONE
백팀,성장자산,데이터 인프라(리츠),Continental Building Co.,CONL
백팀,성장자산,사이버보안,Palo Alto Networks,PANW
백팀,성장자산,사이버보안,CrowdStrike,CRWD
백팀,성장자산,사이버보안,Zscaler,ZS
백팀,성장자산,필수소비재,Kenvue Inc.,KVUE
백팀,성장자산,필수소비재,Procter & Gamble,PG
백팀,성장자산,필수소비재,Coca-Cola,KO
백팀,성장자산,필수소비재,PepsiCo,PEP
백팀,성장자산,필수소비재,Walmart,WMT
백팀,성장자산,필수소비재,Costco,COST
백팀,성장자산,필수소비재,Colgate-Palmolive,CL
백팀,성장자산,필수소비재,Kimberly-Clark,KMB
백팀,성장자산,필수소비재,Target Corporation,TGT
백팀,성장자산,필수소비재,Philip Morris Intl,PM
백팀,성장자산,필수소비재,Unilever PLC,UL
백팀,성장자산,필수소비재,Altria Group Inc,MO
백팀,성장자산,필수소비재,3M Company,MMM
백팀,성장자산,결재시스템,Visa,V
백팀,성장자산,결재시스템,Mastercard,MA
백팀,성장자산,결재시스템,American Express,AXP
백팀,성장자산,결재시스템,PayPal,PYPL
백팀,성장자산,결재시스템,Block,SQ
백팀,성장자산,스테이블코인/핀테크,Coinbase,COIN
백팀,성장자산,스테이블코인/핀테크,SoFi Technologies,SOFI
백팀,성장자산,스테이블코인/핀테크,Robinhood,HOOD
백팀,성장자산,스테이블코인/핀테크,Circle,CRCL
백팀,성장자산,스테이블코인/핀테크,Block,SQ
백팀,성장자산,스테이블코인/핀테크,MicroStrategy,MSTR
백팀,성장자산,스테이블코인/핀테크,Bitmine Immersion Technologies,BMNR
백팀,성장자산,스테이블코인/핀테크,Toast Inc.,TOST
백팀,성장자산,스테이블코인/핀테크,Affirm Holdings Inc.,AFRM
백팀,성장자산,스테이블코인/핀테크,Global Payments Inc.,GPN
백팀,성장자산,스테이블코인/핀테크,Zillow Group Inc.,Z
백팀,성장자산,금융/자산운용,BlackRock,BLK
백팀,성장자산,금융/자산운용,JPMorgan Chase,JPM
백팀,성장자산,금융/자산운용,Morgan Stanley,MS
백팀,성장자산,금융/자산운용,Goldman Sachs,GS
백팀,성장자산,금융/자산운용,Bank of America,BAC
백팀,성장자산,금융/자산운용,Citi Group,C
백팀,성장자산,금융/자산운용,HSBC Holdings,HSBC
백팀,성장자산,금융/자산운용,Blackstone Inc.,BX
백팀,성장자산,금융/자산운용,CME Group Inc.,CME
백팀,성장자산,금융/자산운용,Bank of New York Mellon,BK
백팀,성장자산,명품소비재,Ferrari N.V.,RACE
백팀,성장자산,명품소비재,Williams-Sonoma Inc.,WSM
백팀,성장자산,명품소비재,Tapestry,TPR
백팀,성장자산,명품소비재,Estée Lauder,EL
백팀,성장자산,명품소비재,Lululemon Athletica,LULU
백팀,성장자산,명품소비재,Cullen/Frost Bankers,CFR
백팀,성장자산,명품소비재,Old Republic Intl,ORI
백팀,성장자산,명품소비재,LVMH Moët Hennessy Louis Vuitton,MC
백팀,성장자산,명품소비재,Brunswick Corporation,BC
백팀,성장자산,명품소비재,LVMH Moët Hennessy Louis Vuitton,LVMUY
백팀,성장자산,명품소비재,Ralph Lauren,RL
백팀,성장자산,명품소비재,Capri Holdings,CPRI
백팀,성장자산,명품소비재,Canada Goose,GOOS
백팀,성장자산,헬스케어,UnitedHealth,UNH
백팀,성장자산,헬스케어,Natera,NTRA
백팀,성장자산,헬스케어,Johnson & Johnson,JNJ
백팀,성장자산,헬스케어,Thermo Fisher,TMO
백팀,성장자산,헬스케어,Abbott Labs,ABT
백팀,성장자산,헬스케어,Intuitive Surgical,ISRG
백팀,성장자산,헬스케어,Pfizer,PFE
백팀,성장자산,헬스케어,Merck & Co.,MRK
백팀,성장자산,헬스케어,Moderna,MRNA
백팀,성장자산,헬스케어,Eli Lilly,LLY
백팀,성장자산,물&식량,Xylem,XYL
백팀,성장자산,물&식량,Ecolab,ECL
백팀,성장자산,물&식량,American Water Works,AWK
백팀,성장자산,물&식량,DuPont,DD
백팀,성장자산,물&식량,Nestlé,NSRGY"""
    
    from io import StringIO
    df = pd.read_csv(StringIO(data))
    return df

# Finviz 데이터 가져오기
@st.cache_data(ttl=86400)
def get_finviz_metric(ticker, metric_name):
    try:
        url = f"https://finviz.com/quote.ashx?t={ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=100)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        tables = soup.find_all('table', {'class': 'snapshot-table2'})
        if not tables:
            return "-"
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                for i in range(0, len(cells)-1, 2):
                    if cells[i].text.strip() == metric_name:
                        value = cells[i+1].text.strip()
                        if value == '-':
                            return "-"
                        # % 제거하고 숫자로 변환
                        value = value.replace('%', '').replace(',', '')
                        try:
                            return float(value)
                        except:
                            return value
        return "-"
    except Exception as e:
        return "-"

# Finviz API 데이터 가져오기
@st.cache_data(ttl=86400)
def get_finviz_data(ticker, statement, item):
    try:
        statement_map = {"IS": "IQ", "BS": "BQ", "CF": "CQ"}
        url = f"https://finviz.com/api/statement.ashx?t={ticker}&so=F&s={statement_map[statement]}"
        response = requests.get(url, timeout=100)
        data = response.json()
        
        if data and 'data' in data and item in data['data']:
            value = data['data'][item][0]
            return float(value) if value != '-' else None
        return None
    except:
        return None

# 주가 데이터 가져오기 (Yahoo Finance Chart API - Google Apps Script 방식)
@st.cache_data(ttl=3600)
def get_stock_data(ticker, start_date, end_date):
    """Yahoo Finance Chart API를 통해 주가 데이터 가져오기 (Google Apps Script 방식과 동일)"""
    
    # 날짜를 datetime 객체로 변환
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        # date 객체를 datetime으로 변환
        start_date = datetime.combine(start_date, datetime.min.time())
    
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        # date 객체를 datetime으로 변환
        end_date = datetime.combine(end_date, datetime.min.time())
    
    try:
        # UTC 자정 기준으로 타임스탬프 생성
        start_timestamp = int(start_date.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        end_timestamp = int(end_date.replace(hour=23, minute=59, second=59, microsecond=999000).timestamp())
        
        # Yahoo Finance Chart API URL
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        params = {
            'period1': start_timestamp,
            'period2': end_timestamp,
            'interval': '1d'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print(f"HTTP {response.status_code} for {ticker}")
            return None
        
        data = response.json()
        
        # 데이터 구조 검증
        if not data.get('chart') or not data['chart'].get('result') or len(data['chart']['result']) == 0:
            print(f"Invalid API response for {ticker}")
            return None
        
        result = data['chart']['result'][0]
        
        # timestamp와 indicators 추출
        timestamps = result.get('timestamp', [])
        if not timestamps:
            print(f"No timestamps for {ticker}")
            return None
        
        indicators_list = result.get('indicators', {}).get('quote', [])
        if not indicators_list or len(indicators_list) == 0:
            print(f"No indicators for {ticker}")
            return None
        
        indicators = indicators_list[0]
        
        # 데이터 추출
        opens = indicators.get('open', [])
        highs = indicators.get('high', [])
        lows = indicators.get('low', [])
        closes = indicators.get('close', [])
        volumes = indicators.get('volume', [])
        
        # 데이터프레임 생성 (null 값 필터링)
        data_list = []
        for i in range(len(timestamps)):
            # null 체크
            if (closes[i] is not None and 
                opens[i] is not None and 
                highs[i] is not None and 
                lows[i] is not None):
                
                date = datetime.fromtimestamp(timestamps[i])
                
                data_list.append({
                    'Date': date,
                    'Open': float(opens[i]),
                    'High': float(highs[i]),
                    'Low': float(lows[i]),
                    'Close': float(closes[i]),
                    'Volume': int(volumes[i]) if volumes[i] is not None else 0
                })
        
        if not data_list:
            print(f"No valid data for {ticker}")
            return None
        
        # 데이터프레임 생성
        df = pd.DataFrame(data_list)
        df = df.set_index('Date')
        df = df.sort_index()
        
        return df
        
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

# 미니 차트 생성
def create_mini_chart(data, chart_type='line'):
    if data is None or len(data) == 0:
        return None
    
    fig = go.Figure()
    
    if chart_type == 'line':
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Close'],
            mode='lines',
            line=dict(width=1, color='#1f77b4'),
            showlegend=False
        ))
    elif chart_type == 'bar':
        colors = ['green' if x >= 0 else 'red' for x in data]
        fig.add_trace(go.Bar(
            x=list(range(len(data))),
            y=data,
            marker_color=colors,
            showlegend=False
        ))
    
    fig.update_layout(
        height=50,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

# 메인 앱
def main():
    st.title("📊 투자 포트폴리오 대시보드")
    
    # 사이드바
    st.sidebar.header("⚙️ 설정")
    
    # 기본 날짜 설정
    default_start = datetime(2025, 10, 9)
    default_end = datetime.now()
    
    start_date = st.sidebar.date_input("시작일", default_start)
    end_date = st.sidebar.date_input("종료일", default_end)
    
    # Y축 범위 설정
    st.sidebar.subheader("차트 Y축 범위")
    change_y_min = st.sidebar.number_input("변동율 Y축 최소값", value=-10)
    change_y_max = st.sidebar.number_input("변동율 Y축 최대값", value=10)
    return_y_min = st.sidebar.number_input("누적수익율 Y축 최소값", value=-50)
    return_y_max = st.sidebar.number_input("누적수익율 Y축 최대값", value=50)
    
    analyze_button = st.sidebar.button("🔍 분석 시작", type="primary", use_container_width=True)
    
    # 포트폴리오 데이터 로드
    portfolio_df = load_portfolio_data()
    
    # 탭 생성
    tab1, tab2 = st.tabs(["📈 포트폴리오 분석", "📊 트렌드 분석"])
    
    with tab1:
        if analyze_button:
            st.info("데이터를 가져오는 중... 시간이 걸릴 수 있습니다.")
            
            # 결과 데이터프레임 생성
            results = []
            progress_bar = st.progress(0)
            
            for idx, row in portfolio_df.iterrows():
                ticker = row['티커']
                
                # 진행률 업데이트
                progress_bar.progress((idx + 1) / len(portfolio_df))
                
                # 주가 데이터 가져오기
                stock_data = get_stock_data(ticker, start_date, end_date)
                
                if stock_data is not None and len(stock_data) > 0:
                    # 기본 계산
                    base_price = stock_data['Close'].iloc[0]
                    current_price = stock_data['Close'].iloc[-1]
                    highest_price = stock_data['Close'].max()
                    
                    # 수익률 계산
                    return_from_base = ((current_price - base_price) / base_price) * 100
                    return_from_high = ((current_price - highest_price) / highest_price) * 100
                    
                    # 일일 수익
                    if len(stock_data) > 1:
                        daily_return = current_price - stock_data['Close'].iloc[-2]
                        daily_return_pct = ((current_price - stock_data['Close'].iloc[-2]) / stock_data['Close'].iloc[-2]) * 100
                    else:
                        daily_return = 0
                        daily_return_pct = 0
                    
                    # 변동률 계산 (일별)
                    daily_changes = stock_data['Close'].pct_change() * 100
                    
                    # 누적 수익률 (기준가 대비)
                    cumulative_returns = ((stock_data['Close'] / base_price) - 1) * 100
                    
                    # Finviz 메트릭
                    debt_ratio = get_finviz_metric(ticker, "Debt/Eq")
                    current_ratio = get_finviz_metric(ticker, "Current Ratio")
                    roe = get_finviz_metric(ticker, "ROE")
                    
                    # Finviz API 데이터
                    total_cash = get_finviz_data(ticker, "BS", "Cash & Short Term Investments")
                    free_cash_flow = get_finviz_data(ticker, "CF", "Free Cash Flow")
                    
                    # Runway 계산 (간단 버전)
                    runway = "-"
                    if total_cash and free_cash_flow and free_cash_flow < 0:
                        runway = round(total_cash / abs(free_cash_flow), 1)
                    
                    results.append({
                        '팀': row['팀'],
                        '자산': row['자산'],
                        '섹터': row['섹터'],
                        '기업명': row['기업명'],
                        '티커': ticker,
                        '기준가': round(base_price, 2),
                        '최고가': round(highest_price, 2),
                        '현재가': round(current_price, 2),
                        '누적수익률(기준가)': round(return_from_base, 2),
                        '누적수익률(최고가)': round(return_from_high, 2),
                        '일일수익': round(daily_return, 2),
                        '일일수익률': round(daily_return_pct, 2),
                        '부채비율': debt_ratio if debt_ratio != "-" else "-",
                        '유동비율': current_ratio if current_ratio != "-" else "-",
                        'ROE': roe if roe != "-" else "-",
                        'Runway(년)': runway,
                        'Total Cash(M$)': round(total_cash, 2) if total_cash else "-",
                        'FCF(M$)': round(free_cash_flow, 2) if free_cash_flow else "-",
                        'price_data': stock_data,
                        'daily_changes': daily_changes[1:],
                        'cumulative_returns': cumulative_returns
                    })
                else:
                    # 데이터가 없는 경우
                    results.append({
                        '팀': row['팀'],
                        '자산': row['자산'],
                        '섹터': row['섹터'],
                        '기업명': row['기업명'],
                        '티커': ticker,
                        '기준가': "-",
                        '최고가': "-",
                        '현재가': "-",
                        '누적수익률(기준가)': "-",
                        '누적수익률(최고가)': "-",
                        '일일수익': "-",
                        '일일수익률': "-",
                        '부채비율': "-",
                        '유동비율': "-",
                        'ROE': "-",
                        'Runway(년)': "-",
                        'Total Cash(M$)': "-",
                        'FCF(M$)': "-",
                        'price_data': None,
                        'daily_changes': None,
                        'cumulative_returns': None
                    })
            
            progress_bar.empty()
            st.success("✅ 분석 완료!")
            
            # 결과 표시
            st.subheader("포트폴리오 상세 분석")
            
            # 데이터프레임으로 변환
            result_df = pd.DataFrame(results)
            
            # 컬럼 구성
            display_columns = ['팀', '자산', '섹터', '기업명', '티커', '기준가', '최고가', '현재가',
                             '누적수익률(기준가)', '누적수익률(최고가)', '일일수익', '일일수익률',
                             '부채비율', '유동비율', 'ROE', 'Runway(년)', 'Total Cash(M$)', 'FCF(M$)']
            
            # 스타일링 함수
            def highlight_returns(val):
                if isinstance(val, (int, float)):
                    color = 'green' if val >= 0 else 'red'
                    return f'color: {color}'
                return ''
            
            # 표시용 데이터프레임
            display_df = result_df[display_columns].copy()
            
            st.dataframe(
                display_df.style.applymap(
                    highlight_returns,
                    subset=['누적수익률(기준가)', '누적수익률(최고가)', '일일수익', '일일수익률']
                ),
                use_container_width=True,
                height=600
            )
            
            # 차트 섹션
            st.subheader("📈 개별 종목 차트")
            
            # 종목 선택
            selected_ticker = st.selectbox(
                "종목 선택",
                result_df['티커'].tolist(),
                format_func=lambda x: f"{x} - {result_df[result_df['티커']==x]['기업명'].iloc[0]}"
            )
            
            selected_data = result_df[result_df['티커'] == selected_ticker].iloc[0]
            
            if selected_data['price_data'] is not None:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("현재가", f"${selected_data['현재가']}", 
                             f"{selected_data['일일수익률']}%")
                
                with col2:
                    st.metric("누적수익률 (기준가)", 
                             f"{selected_data['누적수익률(기준가)']}%")
                
                with col3:
                    st.metric("누적수익률 (최고가)", 
                             f"{selected_data['누적수익률(최고가)']}%")
                
                # 주가 트렌드
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=selected_data['price_data'].index,
                    y=selected_data['price_data']['Close'],
                    mode='lines',
                    name='주가',
                    line=dict(color='#1f77b4', width=2)
                ))
                fig_price.update_layout(
                    title="주가 트렌드",
                    xaxis_title="날짜",
                    yaxis_title="가격 ($)",
                    height=400,
                    hovermode='x unified'
                )
                st.plotly_chart(fig_price, use_container_width=True)
                
                # 변동률과 누적수익률 차트
                col1, col2 = st.columns(2)
                
                with col1:
                    if selected_data['daily_changes'] is not None:
                        changes = selected_data['daily_changes'].dropna()
                        colors = ['green' if x >= 0 else 'red' for x in changes]
                        
                        fig_change = go.Figure()
                        fig_change.add_trace(go.Bar(
                            x=changes.index,
                            y=changes.values,
                            marker_color=colors,
                            name='일일 변동률'
                        ))
                        fig_change.update_layout(
                            title="변동률 트렌드",
                            xaxis_title="날짜",
                            yaxis_title="변동률 (%)",
                            yaxis=dict(range=[change_y_min, change_y_max]),
                            height=400,
                            showlegend=False
                        )
                        fig_change.add_hline(y=0, line_dash="dash", line_color="gray")
                        st.plotly_chart(fig_change, use_container_width=True)
                
                with col2:
                    if selected_data['cumulative_returns'] is not None:
                        returns = selected_data['cumulative_returns'].dropna()
                        colors = ['green' if x >= 0 else 'red' for x in returns]
                        
                        fig_return = go.Figure()
                        fig_return.add_trace(go.Bar(
                            x=returns.index,
                            y=returns.values,
                            marker_color=colors,
                            name='누적 수익률'
                        ))
                        fig_return.update_layout(
                            title="누적 수익률 트렌드",
                            xaxis_title="날짜",
                            yaxis_title="누적 수익률 (%)",
                            yaxis=dict(range=[return_y_min, return_y_max]),
                            height=400,
                            showlegend=False
                        )
                        fig_return.add_hline(y=0, line_dash="dash", line_color="gray")
                        st.plotly_chart(fig_return, use_container_width=True)
            
            # 세션 상태에 저장
            st.session_state['results'] = results
            st.session_state['result_df'] = result_df
    
    with tab2:
        if 'results' in st.session_state:
            results = st.session_state['results']
            result_df = st.session_state['result_df']
            
            st.subheader("📊 트렌드 분석")

            # ✅ 4️⃣ 청팀 vs 백팀 누적수익률 비교 (가중평균 포함)
            st.markdown("### 1️⃣ 청팀 vs 백팀 누적수익률 비교 (가중평균 포함)")
            team_returns={}
            for team in result_df['팀'].unique():
                stocks=result_df[result_df['팀']==team]
                arr=[r['cumulative_returns'].dropna() for _,r in stocks.iterrows() if r['cumulative_returns'] is not None]
                if arr:
                    team_returns[team]=pd.concat(arr,axis=1).mean(axis=1)
            if team_returns:
                total=sum(len(result_df[result_df['팀']==t]) for t in team_returns.keys())
                weighted={t:d*(len(result_df[result_df['팀']==t])/total) for t,d in team_returns.items()}
                total_weighted=sum(weighted.values())
    
                fig=go.Figure()
                for t,d in team_returns.items():
                    fig.add_trace(go.Scatter(x=d.index,y=d.values,mode='lines',name=f"{t} 평균"))
                fig.add_trace(go.Scatter(x=total_weighted.index,y=total_weighted.values,
                                         mode='lines',name="시장 전체 가중평균",
                                         line=dict(width=3,dash='dot',color='black')))
                fig.update_layout(title="청팀 vs 백팀 누적수익률 비교 (가중평균 포함)",
                                  height=500,hovermode='x unified',
                                  legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                                 )
                fig.add_hline(y=0,line_dash="dash",line_color="gray")
                st.plotly_chart(fig,use_container_width=True)
            
            # 차트 2: 팀별 평균 변동률 트렌드
            st.markdown("### 2️⃣ 팀별 평균 변동률 트렌드")
            
            team_data = {}
            for team in result_df['팀'].unique():
                team_stocks = result_df[result_df['팀'] == team]
                all_changes = []
                
                for idx, row in team_stocks.iterrows():
                    if row['daily_changes'] is not None: #cumulative_returns, daily_changes
                        all_changes.append(row['daily_changes'].dropna())
                
                if all_changes:
                    # 모든 날짜의 평균 계산
                    combined = pd.concat(all_changes, axis=1)
                    team_avg = combined.mean(axis=1)
                    team_data[team] = team_avg
            
            if team_data:
                fig_team = go.Figure()
                for team, data in team_data.items():
                    fig_team.add_trace(go.Scatter(
                        x=data.index,
                        y=data.values,
                        mode='lines',
                        name=team,
                        line=dict(width=2)
                    ))
                
                fig_team.update_layout(
                    title="팀별 평균 변동률 비교",
                    xaxis_title="날짜",
                    yaxis_title="평균 변동률 (%)",
                    height=500,
                    hovermode='x unified',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                fig_team.add_hline(y=0, line_dash="dash", line_color="gray")
                st.plotly_chart(fig_team, use_container_width=True)
            
            # 차트 3: 섹터별 평균 누적변동률 트렌드
            st.markdown("### 3️⃣ 섹터별 평균 누적변동률 트렌드")
            
            sector_data = {}
            for sector in result_df['섹터'].unique():
                sector_stocks = result_df[result_df['섹터'] == sector]
                all_changes = []
                
                for idx, row in sector_stocks.iterrows():
                    if row['cumulative_returns'] is not None:  #cumulative_returns, daily_changes
                        all_changes.append(row['daily_changes'].dropna())
                
                if all_changes:
                    combined = pd.concat(all_changes, axis=1)
                    sector_avg = combined.mean(axis=1)
                    sector_data[sector] = sector_avg
            
            if sector_data:
                fig_sector = go.Figure()
                for sector, data in sector_data.items():
                    fig_sector.add_trace(go.Scatter(
                        x=data.index,
                        y=data.values,
                        mode='lines',
                        name=sector,
                        line=dict(width=2)
                    ))
                
                fig_sector.update_layout(
                    title="섹터별 평균 변동률 비교",
                    xaxis_title="날짜",
                    yaxis_title="평균 변동률 (%)",
                    height=500,
                    hovermode='x unified',
                    legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
                )
                fig_sector.add_hline(y=0, line_dash="dash", line_color="gray")
                st.plotly_chart(fig_sector, use_container_width=True)
            
            # 차트 4: 섹터별 개별 종목 누적변동률 (서브플롯)
            st.markdown("### 4️⃣ 섹터별 개별 종목 누적변동률")
            
            sectors = result_df['섹터'].unique()
            
            for sector in sectors:
                with st.expander(f"📂 {sector}"):
                    sector_stocks = result_df[result_df['섹터'] == sector]
                    
                    # 서브플롯 생성
                    n_stocks = len(sector_stocks)
                    if n_stocks == 0:
                        continue
                    
                    cols = 5  # ✅ 5열로 변경
                    rows = (n_stocks + cols - 1) // cols  # 행 자동 계산
                    
                    fig = make_subplots(
                        rows=rows,
                        cols=cols,
                        subplot_titles=[f"{row['티커']}" for _, row in sector_stocks.iterrows()],
                        vertical_spacing=0.1,
                        horizontal_spacing=0.03
                    )
                    
                    for idx, (_, row) in enumerate(sector_stocks.iterrows()):
                        if row['cumulative_returns'] is not None:
                            changes = row['cumulative_returns'].dropna()
                            colors = ['green' if x >= 0 else 'red' for x in changes]
                            
                            row_num = (idx // cols) + 1
                            col_num = (idx % cols) + 1
                            
                            fig.add_trace(
                                go.Bar(
                                    x=changes.index,
                                    y=changes.values,
                                    marker_color=colors,
                                    showlegend=False,
                                    name=row['티커'],
                                ),
                                row=row_num,
                                col=col_num
                            )
                            fig.update_yaxes(range=[return_y_min, return_y_max])
                    
                    fig.update_layout(
                        height=300 * rows,
                        title_text=f"{sector} 섹터 누적변동률",
                        showlegend=False,
                    )
                    
                    # 모든 서브플롯에 0선 추가
                    for i in range(1, rows + 1):
                        for j in range(1, cols + 1):
                            fig.add_hline(
                                y=0,
                                line_dash="dash",
                                line_color="gray",
                                row=i,
                                col=j
                            )
                    
                    st.plotly_chart(fig, use_container_width=True)

            
        else:
            st.info("먼저 '포트폴리오 분석' 탭에서 분석을 실행해주세요.")

if __name__ == "__main__":
    main()
