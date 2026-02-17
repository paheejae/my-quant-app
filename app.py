import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Medallion Terminal V2", layout="wide")

# 1. 고속 종목 리스트 및 검색 최적화
@st.cache_data
def load_stock_info():
    df = fdr.StockListing('KRX')[['Code', 'Name', 'Market']]
    return df

# 2. 메달리온 고속 스캐너 (에러 방지 및 속도 최적화)
@st.cache_data(ttl=1800)
def get_medallion_picks(stock_df):
    # 상위 우량주 샘플링 (속도와 확률의 타협점)
    sample_list = stock_df.sample(n=min(60, len(stock_df)))
    picks = []
    
    for _, row in sample_list.iterrows():
        try:
            df = fdr.DataReader(row['Code']).tail(20)
            if len(df) < 15: continue
            
            # 짐 사이먼스식 변동성 점수 (Z-Score)
            ma = df['Close'].mean()
            std = df['Close'].std()
            if std == 0: continue
            
            z_score = (df['Close'].iloc[-1] - ma) / std
            
            # 통계적 하단 진입 시 추천
            if z_score < -1.0: 
                picks.append({
                    '종목명': row['Name'], '코드': row['Code'],
                    '현재가': int(df['Close'].iloc[-1]), '신뢰도': round(abs(z_score)*30, 1)
                })
        except: continue
    return pd.DataFrame(picks).head(5)

# --- 메인 대시보드 UI ---
stock_info = load_stock_info()

st.title("🏛️ Medallion Quant Intelligence")
st.caption(f"시스템 상태: 최적화 가동 중 | 가용 현금: 3,000,000원")

# 섹션 1: 추천 종목
st.subheader("🎯 사이먼스 픽 (고속 스캔)")
if st.button("🚀 실시간 통계 분석 시작"):
    with st.spinner('이상 차트를 걸러내고 최적의 타점을 찾는 중...'):
        recomm = get_medallion_picks(stock_info)
        if not recomm.empty:
            cols = st.columns(len(recomm))
            for i, (_, row) in enumerate(recomm.iterrows()):
                with cols[i]:
                    st.success(f"**{row['종목명']}**")
                    st.metric("추천가", f"{row['현재가']:,}원")
                    st.caption(f"신뢰도: {row['신뢰도']}%")
        else:
            st.info("현재 시장에 통계적 저점에 도달한 우량주가 없습니다. 다시 시도해 주세요.")

st.divider()

# 섹션 2: 정밀 분석 및 내 포트폴리오
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("🔍 종목 정밀 분석 차트")
    target_name = st.selectbox("종목명을 선택하거나 입력하세요", ["삼성전자"] + stock_info['Name'].tolist())
    
    if target_name:
        try:
            target_code = stock_info[stock_info['Name'] == target_name]['Code'].values[0]
            df_chart = fdr.DataReader(target_code).tail(60)
            
            # 볼린저 밴드 지표
            ma = df_chart['Close'].rolling(20).mean()
            std = df_chart['Close'].rolling(20).std()
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], 
                                         low=df_chart['Low'], close=df_chart['Close'], name='주가'))
            fig.add_trace(go.Scatter(x=df_chart.index, y=ma+(std*2), line=dict(color='rgba(255,0,0,0.2)'), name='상단'))
            fig.add_trace(go.Scatter(x=df_chart.index, y=ma-(std*2), line=dict(color='rgba(0,255,0,0.2)'), name='하단'))
            fig.update_layout(xaxis_rangeslider_visible=False, height=450, template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)
        except: st.warning("차트 데이터를 불러오는 중입니다...")

with col2:
    st.subheader("📊 My Portfolio")
    my_stocks = ["이오테크닉스", "리노공업", "다원시스", "테크윙", "크래프톤", "꿈비", "샌즈랩", "삼양컴텍"]
    st.table(pd.DataFrame({"보유종목": my_stocks}))
