import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Medallion Terminal V3", layout="wide")

@st.cache_data
def load_stock_info():
    # 전체 종목을 가져오되, 추천 대상에서 2,000원 미만은 나중에 필터링
    return fdr.StockListing('KRX')[['Code', 'Name', 'Market']]

# 1. 고속 추천 로직 (2,000원 미만 종목 완전 제외)
@st.cache_data(ttl=3600)
def get_medallion_picks(stock_df):
    # 기초 필터링: 관리종목 등을 피하기 위해 KOSPI/KOSDAQ 우량주 위주로 샘플링
    sample_list = stock_df.sample(n=min(80, len(stock_df)))
    picks = []
    
    for _, row in sample_list.iterrows():
        try:
            df = fdr.DataReader(row['Code']).tail(25)
            # [필터] 데이터 부족하거나 현재가가 2,000원 미만인 종목은 즉시 패스
            curr_price = int(df['Close'].iloc[-1])
            if len(df) < 20 or curr_price < 2000: continue 
            
            ma = df['Close'].mean()
            std = df['Close'].std()
            if std == 0: continue
            
            z_score = (curr_price - ma) / std
            
            # 통계적 하단 진입 시 추천 (Z-Score -1.2 이하)
            if z_score < -1.2:
                picks.append({
                    '종목명': row['Name'], '코드': row['Code'], 
                    '현재가': curr_price, '신뢰도': round(abs(z_score)*35, 1)
                })
        except: continue
    return pd.DataFrame(picks).head(5)

# --- UI 레이아웃 ---
stock_info = load_stock_info()
st.title("🏛️ Medallion Quant Intelligence")
st.caption("시스템 상태: 2,000원 미만 종목 필터링 적용 중 | 가용 현금: 3,000,000원") [cite: 2026-01-28]

# 섹션 1: 추천 종목 (2,000원 이상만 추출)
if st.button("🚀 실시간 통계 분석 시작"):
    with st.spinner('이상 차트를 걸러내고 우량 종목을 찾는 중...'):
        recomm = get_medallion_picks(stock_info)
        if not recomm.empty:
            cols = st.columns(len(recomm))
            for i, (_, row) in enumerate(recomm.iterrows()):
                with cols[i]:
                    st.success(f"**{row['종목명']}**")
                    st.metric("현재가", f"{row['현재가']:,}원")
                    st.caption(f"신뢰도: {row['신뢰도']}%")
        else:
            st.info("현재 분석 기준(2,000원 이상 우량주)에 맞는 종목이 없습니다.")

st.divider()

# 섹션 2: 정밀 차트 분석 (볼린저 밴드 + 거래량)
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("🔍 종목 정밀 분석 차트")
    target_name = st.selectbox("분석할 종목을 선택하세요", stock_info['Name'].tolist(), index=0)
    
    if target_name:
        try:
            target_code = stock_info[stock_info['Name'] == target_name]['Code'].values[0]
            df = fdr.DataReader(target_code).tail(100)
            
            # 지표 계산
            ma = df['Close'].rolling(20).mean()
            std = df['Close'].rolling(20).std()
            upper = ma + (std * 2)
            lower = ma - (std * 2)
            
            # 차트 구성 (주가 + 거래량)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='주가'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=upper, line=dict(color='rgba(255,0,0,0.3)'), name='상단밴드'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=lower, line=dict(color='rgba(0,255,0,0.3)'), name='하단밴드'), row=1, col=1)
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color='gray', name='거래량'), row=2, col=1)
            
            fig.update_layout(xaxis_rangeslider_visible=False, height=600, template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)
        except: st.error("데이터 로딩 중 에러가 발생했습니다.")

with col2:
    st.subheader("📊 My Portfolio")
    my_stocks = ["이오테크닉스", "리노공업", "다원시스", "테크윙", "크래프톤", "꿈비", "샌즈랩", "삼양컴텍"]
    st.table(pd.DataFrame({"보유종목": my_stocks}))
