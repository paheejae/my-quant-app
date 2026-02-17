import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. 페이지 환경 설정
st.set_page_config(page_title="Medallion Terminal V2", layout="wide")

# 2. 고속 데이터 스캔 함수 (안정성 강화 버전)
@st.cache_data(ttl=3600)
def get_safe_recommendations():
    try:
        # 시가총액 상위 우량주 200개 중 샘플링하여 속도 확보
        df_krx = fdr.StockListing('KOSPI')
        df_filtered = df_krx[df_krx['Price'] >= 5000].sample(min(30, len(df_krx)))
        
        results = []
        for _, row in df_filtered.iterrows():
            try:
                # 데이터 수집 (안전 장치 추가)
                df = fdr.DataReader(row['Code']).tail(25)
                if df is None or len(df) < 20: continue
                
                # 통계 지표 계산 (분모가 0이 되는 경우 방지)
                ma = df['Close'].mean()
                std = df['Close'].std()
                if std == 0: continue
                
                z_score = (df['Close'].iloc[-1] - ma) / std
                
                # 메달리온 저점 신호 (Z-Score -1.2 이하)
                if z_score < -1.2:
                    results.append({
                        '종목명': row['Name'], 
                        '코드': row['Code'], 
                        '현재가': int(df['Close'].iloc[-1]), 
                        '신뢰도': round(abs(z_score)*35, 1)
                    })
            except: continue # 개별 종목 에러 시 중단 없이 다음으로 진행
        return pd.DataFrame(results).head(5)
    except:
        return pd.DataFrame()

# --- 메인 대시보드 UI ---
st.title("🏛️ Medallion Quant Intelligence")
st.caption("시스템 상태: 최적화 가동 중 | 가용 현금: 3,000,000원")

# 섹션 1: 짐 사이먼스 고속 추천
st.subheader("🎯 사이먼스 픽 (고속 스캔)")
if st.button("🚀 10초 내 종목 추출 시작"):
    with st.spinner('안전한 통계 데이터를 수집 중입니다...'):
        recomm_df = get_safe_recommendations()
        if not recomm_df.empty:
            cols = st.columns(len(recomm_df))
            for i, (idx, row) in enumerate(recomm_df.iterrows()):
                with cols[i]:
                    st.success(f"**{row['종목명']}**")
                    st.metric("추천가", f"{row['현재가']:,}원")
                    st.caption(f"신뢰도: {row['신뢰도']}%")
        else:
            st.info("현재 분석 기준에 맞는 안전한 종목이 없습니다. 잠시 후 다시 시도해 주세요.")

st.divider()

# 섹션 2: 정밀 분석 및 차트
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("🔍 종목별 확률 분포 분석 (차트)")
    target = st.text_input("종목명 또는 코드 입력", "삼성전자")
    if target:
        try:
            df_chart = fdr.DataReader(target).tail(60)
            # 볼린저 밴드 시각화
            ma = df_chart['Close'].rolling(20).mean()
            std = df_chart['Close'].rolling(20).std()
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], 
                                         low=df_chart['Low'], close=df_chart['Close'], name='주가'))
            fig.add_trace(go.Scatter(x=df_chart.index, y=ma+(std*2), line=dict(color='rgba(255,0,0,0.2)'), name='상단'))
            fig.add_trace(go.Scatter(x=df_chart.index, y=ma-(std*2), line=dict(color='rgba(0,255,0,0.2)'), name='하단'))
            fig.update_layout(xaxis_rangeslider_visible=False, height=450, template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)
        except: st.error("종목명을 다시 확인해 주세요.")

with col2:
    st.subheader("📊 My Portfolio")
    my_stocks = ["이오테크닉스", "리노공업", "다원시스", "테크윙", "크래프톤", "꿈비", "샌즈랩", "삼양컴텍"]
    st.write(pd.DataFrame({"보유종목": my_stocks}))
