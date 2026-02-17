import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Medallion Pro Terminal", layout="wide")

@st.cache_data
def load_stock_info():
    try:
        df = fdr.StockListing('KRX')
        if 'Sector' not in df.columns: df['Sector'] = '일반 업종'
        return df[['Code', 'Name', 'Market', 'Sector']]
    except:
        return pd.DataFrame(columns=['Code', 'Name', 'Market', 'Sector'])

# 1. 고속 스캐너 (스캔 범위 확대)
@st.cache_data(ttl=3600)
def get_medallion_picks(stock_df):
    if stock_df.empty: return pd.DataFrame()
    # 스캔 범위를 150개로 확대하여 추천 종목 수 확보
    sample_list = stock_df.sample(n=min(150, len(stock_df)))
    picks = []
    
    for _, row in sample_list.iterrows():
        try:
            df = fdr.DataReader(row['Code']).tail(30)
            if len(df) < 20: continue
            
            curr_p = int(df['Close'].iloc[-1])
            if curr_p < 2000: continue # 2,000원 필터 유지
            
            ma = df['Close'].mean()
            std = df['Close'].std()
            z_score = (curr_p - ma) / std if std > 0 else 0
            
            # 통계적 저점 구간 진입 종목 추출
            if z_score < -1.0: 
                picks.append({
                    '종목명': row['Name'], '섹터': row['Sector'],
                    '현재금액': f"{curr_p:,}원", '신뢰도': round(abs(z_score)*35, 1)
                })
        except: continue
    return pd.DataFrame(picks)

# --- 메인 화면 ---
stock_info = load_stock_info()
st.title("🏛️ Medallion Pro Terminal")
st.caption("시스템 상태: 정밀 시각화 모드 가동 중 | 가용 현금: 3,000,000원")

# 섹션 1: 추천 종목 (가로 스크롤형 카드 레이아웃)
if st.button("🚀 실시간 시장 전수 스캔 시작"):
    with st.spinner('시장의 모든 기회를 분석하는 중...'):
        recomm = get_medallion_picks(stock_info)
        if not recomm.empty:
            # 최대 10개까지 표시
            display_df = recomm.head(10)
            cols = st.columns(5) # 한 줄에 5개씩 배치
            for i, (_, row) in enumerate(display_df.iterrows()):
                with cols[i % 5]:
                    st.success(f"**{row['종목명']}**")
                    st.caption(f"📂 {row['섹터']}")
                    st.metric("현재가", row['현재금액'])
                    st.progress(min(row['신뢰도']/100, 1.0), text=f"신뢰도 {row['신뢰도']}%")
        else:
            st.info("현재 분석 기준에 맞는 종목이 없습니다.")

st.divider()

# 섹션 2: HTS급 정밀 분석 차트
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("📊 종목 정밀 분석 (캔들스틱 & 거래량)")
    target_name = st.selectbox("분석할 종목을 선택하거나 입력하세요", stock_info['Name'].tolist())
    
    if target_name:
        try:
            target_code = stock_info[stock_info['Name'] == target_name]['Code'].values[0]
            df = fdr.DataReader(target_code).tail(100)
            
            # 지표 계산 (볼린저 밴드)
            ma = df['Close'].rolling(20).mean()
            std = df['Close'].rolling(20).std()
            upper, lower = ma + (std * 2), ma - (std * 2)
            
            # 서브플롯: 위(캔들), 아래(거래량)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.03, row_heights=[0.7, 0.3])
            
            # 1. 캔들스틱 차트
            fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close, name='주가'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=upper, line=dict(color='rgba(255,0,0,0.3)'), name='상단'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=lower, line=dict(color='rgba(0,255,0,0.3)'), name='하단'), row=1, col=1)
            
            # 2. 막대형 거래량 (상승/하락 색상)
            colors = ['#ff4b4b' if df.Close[i] >= df.Open[i] else '#007bff' for i in range(len(df))]
            fig.add_trace(go.Bar(x=df.index, y=df.Volume, marker_color=colors, name='거래량'), row=2, col=1)
            
            # 디자인 스타일링
            fig.update_layout(xaxis_rangeslider_visible=False, height=700, template='plotly_dark', margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        except: st.error("차트 데이터를 불러올 수 없습니다.")

with col2:
    st.subheader("🏢 My Portfolio")
    my_stocks = ["이오테크닉스", "리노공업", "다원시스", "테크윙", "크래프톤", "꿈비", "샌즈랩", "삼양컴텍"]
    st.table(pd.DataFrame({"종목명": my_stocks}))
