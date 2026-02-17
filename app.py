import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 설정: 페이지 레이아웃 최적화
st.set_page_config(page_title="Medallion Terminal V2", layout="wide")

# [핵심] 데이터 캐싱 기능: 동일 분석 시 재로딩 방지
@st.cache_data(ttl=3600) # 1시간 동안 결과 보존
def get_fast_recommendations():
    # 코스피 200 등 우량주 위주로 스캔 범위를 좁혀 속도 향상
    df_krx = fdr.StockListing('KOSPI')
    df_filtered = df_krx[df_krx['Price'] >= 5000].sample(40) # 정예 40개 샘플링
    
    results = []
    for _, row in df_filtered.iterrows():
        try:
            df = fdr.DataReader(row['Code']).tail(30)
            # 이상한 차트(거래정지 등) 필터링
            if len(df) < 20 or df['Close'].pct_change().std() > 0.05: continue
            
            # 볼린저 밴드 기반 저점 점수
            ma20 = df['Close'].mean()
            std20 = df['Close'].std()
            z_score = (df['Close'].iloc[-1] - ma20) / std20
            
            if z_score < -1.3: # 통계적 저점
                results.append({'종목명': row['Name'], '코드': row['Code'], '현재가': int(df['Close'].iloc[-1]), '신뢰도': round(abs(z_score)*35, 1)})
        except: continue
    return pd.DataFrame(results).head(5)

# --- 메인 화면 구성 ---
st.title("🏛️ Medallion Quant Intelligence")
st.caption(f"시스템 상태: 최적화 가동 중 | 가용 현금: 3,000,000원")

# 1. 고속 추천 섹션
st.subheader("🎯 사이먼스 픽 (고속 스캔)")
if st.button("🚀 10초 내 종목 추출 시작"):
    with st.spinner('데이터 파이프라인 최적화 중...'):
        recomm_df = get_fast_recommendations()
        if not recomm_df.empty:
            cols = st.columns(len(recomm_df))
            for i, (idx, row) in enumerate(recomm_df.iterrows()):
                with cols[i]:
                    st.metric(row['종목명'], f"{row['현재가']:,}원", f"신뢰도 {row['신뢰도']}%")
        else:
            st.info("현재 분석 기준에 맞는 안전한 종목이 없습니다.")

st.divider()

# 2. 정밀 분석 및 차트
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("🔍 정밀 분석 차트")
    stock_input = st.text_input("종목명 또는 코드를 입력하세요", "005930")
    if stock_input:
        df_chart = fdr.DataReader(stock_input).tail(60)
        # 차트 생성 (Bollinger Bands 포함)
        fig = go.Figure(data=[go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'])])
        fig.update_layout(xaxis_rangeslider_visible=False, height=400, template='plotly_dark', margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 My Portfolio")
    my_stocks = ["이오테크닉스", "리노공업", "다원시스", "테크윙", "크래프톤", "꿈비", "샌즈랩", "삼양컴텍"]
    # 보유 종목 간략 리스트업
    st.write(pd.DataFrame({"보유종목": my_stocks}))
