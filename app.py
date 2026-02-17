import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Medallion Final", layout="wide")

# 1. 초고속 종목 로더 (네이버 엔진 고정)
@st.cache_data(ttl=3600)
def load_fast_data():
    try:
        # KOSPI, KOSDAQ 종목만 빠르게 가져오기
        df = fdr.StockListing('KRX-DESC') # 상세 설명 포함 모드
        return df[['Code', 'Name', 'Sector']].dropna(subset=['Sector'])
    except:
        # 비상용 기본 리스트
        return pd.DataFrame([["005930", "삼성전자", "반도체"], ["000660", "SK하이닉스", "반도체"]], 
                            columns=['Code', 'Name', 'Sector'])

# 2. 정밀 차트 엔진
def draw_professional_chart(name, code):
    try:
        # exchange='naver'를 명시하여 해외 서버 호출 차단
        df = fdr.DataReader(code, exchange='naver').tail(100)
        
        ma20 = df['Close'].rolling(20).mean()
        std20 = df['Close'].rolling(20).std()
        upper, lower = ma20 + (std20 * 2), ma20 - (std20 * 2)

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.05, row_heights=[0.7, 0.3])

        # 캔들스틱 + 볼린저 밴드         fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close, name='주가'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=upper, line=dict(color='rgba(255,0,0,0.2)'), name='상단'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=lower, line=dict(color='rgba(0,255,0,0.2)'), name='하단'), row=1, col=1)

        # 거래량 막대         colors = ['red' if df.Close[i] >= df.Open[i] else 'blue' for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index, y=df.Volume, marker_color=colors, name='거래량'), row=2, col=1)

        fig.update_layout(xaxis_rangeslider_visible=False, height=600, template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
    except:
        st.error("차트 데이터를 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.")

# --- 화면 구성 ---
st.title("🏛️ Medallion Quant Final")
df = load_fast_data()

col1, col2 = st.columns([3, 1])
with col1:
    target = st.selectbox("종목을 선택하세요", df['Name'].tolist())
    if target:
        row = df[df['Name'] == target].iloc[0]
        st.caption(f"📂 업종: {row['Sector']} | 종목코드: {row['Code']}")
        draw_professional_chart(target, row['Code'])

with col2:
    st.subheader("📂 My Portfolio")
    my_stocks = ["이오테크닉스", "리노공업", "다원시스", "테크윙", "크래프톤", "꿈비", "샌즈랩", "삼양컴텍"]
    st.table(pd.DataFrame({"보유종목": my_stocks}))
