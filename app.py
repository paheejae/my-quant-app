import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# 1. 환경 설정
st.set_page_config(page_title="Medallion Terminal", layout="wide")

# 2. 데이터 엔진 (필터링 로직 포함)
@st.cache_data
def get_stock_list():
    df = fdr.StockListing('KRX')
    # 이상한 차트 제거 1단계: 동전주 및 관리종목 제외
    return df[(df['Price'] >= 2000) & (df['Market'].isin(['KOSPI', 'KOSDAQ']))]

@st.cache_data
def get_recommendations(df_list):
    candidates = []
    # 속도를 위해 무작위 100개 추출 분석
    sample = df_list.sample(100)
    for _, row in sample.iterrows():
        try:
            df = fdr.DataReader(row['Code']).tail(40)
            if len(df) < 30: continue
            
            # 이상한 차트 제거 2단계: 변동성(Noise) 체크
            daily_ret = df['Close'].pct_change().dropna()
            if daily_ret.std() > 0.06: continue # 급등락주 제거
            
            # 통계 지표: 볼린저 밴드 역추세 전략
            ma = df['Close'].rolling(20).mean()
            std = df['Close'].rolling(20).std()
            z_score = (df['Close'].iloc[-1] - ma.iloc[-1]) / std.iloc[-1]
            
            if z_score < -1.5: # 하단 밴드 근접 (과매도)
                candidates.append({
                    '종목명': row['Name'], '코드': row['Code'], 
                    '현재가': int(df['Close'].iloc[-1]), '신뢰도': round(abs(z_score)*30, 1)
                })
        except: continue
    return pd.DataFrame(candidates).sort_values('신뢰도', ascending=False).head(5)

# --- UI 레이아웃 ---
st.title("🏛️ Medallion Quant Intelligence Terminal")
st.caption(f"접속 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 가용 현금: 3,000,000원")

# 섹션 1: 짐 사이먼스 추천 스캐너
st.subheader("🎯 오늘의 사이먼스 픽 (통계적 저점 종목)")
if st.button("🚀 전체 시장 스캔 시작"):
    with st.spinner('메달리온 알고리즘이 이상 차트를 걸러내는 중...'):
        stocks = get_stock_list()
        recomm = get_recommendations(stocks)
        if not recomm.empty:
            cols = st.columns(5)
            for i, (idx, row) in enumerate(recomm.iterrows()):
                with cols[i]:
                    st.success(f"**{row['종목명']}**")
                    st.metric("추천가", f"{row['현재가']:,}원")
                    st.caption(f"통계적 신뢰도: {row['신뢰도']}%")
        else:
            st.info("현재 분석 기준에 부합하는 안전한 종목이 없습니다.")

st.divider()

# 섹션 2: 정밀 분석 및 차트
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🔍 종목 정밀 진단")
    all_stocks = get_stock_list()
    search_name = st.selectbox("분석할 종목을 선택하세요", [""] + all_stocks['Name'].tolist())
    
    if search_name:
        code = all_stocks[all_stocks['Name'] == search_name]['Code'].values[0]
        df_chart = fdr.DataReader(code).tail(60)
        
        # 지표 계산
        ma = df_chart['Close'].rolling(20).mean()
        std = df_chart['Close'].rolling(20).std()
        upper = ma + (std * 2)
        lower = ma - (std * 2)
        
        # Plotly 차트
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], 
                                     low=df_chart['Low'], close=df_chart['Close'], name='Price'))
        fig.add_trace(go.Scatter(x=df_chart.index, y=upper, line=dict(color='rgba(255,0,0,0.2)'), name='상단밴드'))
        fig.add_trace(go.Scatter(x=df_chart.index, y=lower, line=dict(color='rgba(0,255,0,0.2)'), name='하단밴드'))
        fig.update_layout(xaxis_rangeslider_visible=False, height=450, template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 My Portfolio")
    # 보유 종목 리스트 (사용자 정보 기반)
    my_stocks = ["이오테크닉스", "리노공업", "다원시스", "테크윙", "크래프톤", "꿈비", "샌즈랩", "삼양컴텍"]
    
    res = []
    for s
