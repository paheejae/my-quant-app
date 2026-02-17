import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 페이지 설정
st.set_page_config(page_title="Medallion Advanced Terminal", layout="wide")

@st.cache_data
def load_stock_info():
    return fdr.StockListing('KRX')[['Code', 'Name', 'Market']]

# 2. 고속 추천 로직 (현재가 및 필터 강화)
@st.cache_data(ttl=3600)
def get_medallion_picks(stock_df):
    sample_list = stock_df.sample(n=min(60, len(stock_df)))
    picks = []
    
    for _, row in sample_list.iterrows():
        try:
            df = fdr.DataReader(row['Code']).tail(30)
            if len(df) < 20: continue
            
            curr_price = int(df['Close'].iloc[-1])
            # 2,000원 미만 종목 제외
            if curr_price < 2000: continue 
            
            ma = df['Close'].mean()
            std = df['Close'].std()
            if std == 0: continue
            
            z_score = (curr_price - ma) / std
            
            # 통계적 저점 (Z-Score -1.2 이하)
            if z_score < -1.2:
                picks.append({
                    '종목명': row['Name'], 
                    '코드': row['Code'], 
                    '현재가': curr_price, 
                    '현재금액': f"{curr_price:,}원", # 화면 표시용 포맷팅
                    '신뢰도': round(abs(z_score)*35, 1)
                })
        except: continue
    return pd.DataFrame(picks).head(5)

# --- UI 레이아웃 ---
stock_info = load_stock_info()
st.title("🏛️ Medallion Quant Intelligence")
st.caption("시스템 상태: 2,000원 필터 및 실시간 금액 표기 활성")

# 섹션 1: 추천 종목 (현재금액 강조)
if st.button("🚀 실시간 통계 분석 시작"):
    with st.spinner('이상 차트를 걸러내고 우량 종목의 현재가를 불러오는 중...'):
        recomm = get_medallion_picks(stock_info)
        if not recomm.empty:
            cols = st.columns(len(recomm))
            for i, (_, row) in enumerate(recomm.iterrows()):
                with cols[i]:
                    st.success(f"**{row['종목명']}**")
                    # 현재금액을 가장 큰 글씨로 강조
                    st.metric(label="현재 금액", value=row['현재금액'])
                    st.caption(f"통계적 신뢰도: {row['신뢰도']}%")
        else:
            st.info("현재 분석 기준에 맞는 종목이 없습니다.")

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
            
            ma = df['Close'].rolling(20).mean()
            std = df['Close'].rolling(20).std()
            upper = ma + (std * 2)
            lower = ma - (std * 2)
            
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            
            # 1층: 캔들스틱 및 볼린저 밴드
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='주가'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=upper, line=dict(color='rgba(255,0,0,0.3)'), name='상단밴드'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=lower, line=dict(color='rgba(0,255,0,0.3)'), name='하단밴드'), row=1, col=1)
            
            # 2층: 거래량 (색상 구분: 전일 대비가 아닌 당일 시가 대비)
            bar_colors = ['red' if df.Close[i] >= df.Open[i] else 'blue' for i in range(len(df))]
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=bar_colors, name='거래량'), row=2, col=1)
            
            fig.update_layout(xaxis_rangeslider_visible=False, height=600, template='plotly_dark', margin=dict(t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)
        except: st.warning("데이터 로딩 중...")

with col2:
    st.subheader("📊 My Portfolio")
    my_stocks = ["이오테크닉스", "리노공업", "다원시스", "테크윙", "크래프톤", "꿈비", "샌즈랩", "삼양컴텍"]
    st.table(pd.DataFrame({"보유종목": my_stocks}))
