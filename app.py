import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings

# 불필요한 경고 차단
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Medallion Fast Terminal", layout="wide")

# 1. 고속 데이터 로더
@st.cache_data(ttl=3600)
def get_stock_list():
    try:
        # 업종 정보와 함께 전체 종목 리스트 로드
        df = fdr.StockListing('KRX-DESC')
        return df[['Code', 'Name', 'Sector']].dropna(subset=['Sector'])
    except:
        return pd.DataFrame(columns=['Code', 'Name', 'Sector'])

# 2. 정밀 차트 분석 엔진
def draw_chart(code):
    try:
        # 데이터 로드 (최근 100일)
        df = fdr.DataReader(code).tail(100)
        
        # 볼린저 밴드 계산
        ma20 = df['Close'].rolling(window=20).mean()
        std20 = df['Close'].rolling(window=20).std()
        upper = ma20 + (std20 * 2)
        lower = ma20 - (std20 * 2)

        # 캔들스틱과 거래량 분리 레이아웃
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.05, row_heights=[0.7, 0.3])

        # 상단: 볼린저 밴드 + 캔들스틱
        fig.add_trace(go.Candlestick(
            x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close, 
            name='주가', increasing_line_color='#FF4B4B', decreasing_line_color='#007BFF'
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=df.index, y=upper, line=dict(color='rgba(255,0,0,0.2)'), name='상단'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=lower, line=dict(color='rgba(0,255,0,0.2)'), name='하단'), row=1, col=1)

        # 하단: 거래량 막대 (상승 빨강 / 하락 파랑)
        colors = ['#FF4B4B' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#007BFF' for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='거래량'), row=2, col=1)

        fig.update_layout(xaxis_rangeslider_visible=False, height=700, template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
    except:
        st.error("차트 데이터를 불러오는 데 실패했습니다. 종목을 다시 선택해 주세요.")

# --- 메인 UI ---
st.title("🏛️ Medallion Advanced Terminal")
df = get_stock_list()

if not df.empty:
    # 1. 종목 선택 및 업종 표시
    target_name = st.selectbox("분석할 종목을 검색하세요", df['Name'].tolist())
    
    if target_name:
        row = df[df['Name'] == target_name].iloc[0]
        st.info(f"📂 업종: {row['Sector']} | 종목코드: {row['Code']}")
        
        # 2. 즉시 차트 렌더링
        draw_chart(row['Code'])
else:
    st.warning("데이터 연결 대기 중... 잠시만 기다려 주세요.")
