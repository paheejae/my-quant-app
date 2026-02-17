import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Medallion Final Fix", layout="wide")

# 1. 업종 정보 포함 데이터 로드
@st.cache_data
def load_data():
    try:
        df = fdr.StockListing('KRX')
        # 섹터 정보가 없는 종목을 위한 방어 코드
        df['Sector'] = df['Sector'].fillna('기타 산업')
        return df
    except:
        return pd.DataFrame(columns=['Code', 'Name', 'Sector'])

# 2. 차트 그리기 함수 (네이버 엔진 사용으로 안정성 확보)
def draw_chart(ticker):
    try:
        # 'naver' 엔진을 사용하여 KRX 서버 접속 문제를 우회
        df = fdr.DataReader(ticker, exchange='naver').tail(100)
        
        if df.empty:
            st.warning("현재 종목 데이터를 찾을 수 없습니다.")
            return

        # 볼린저 밴드 계산
        ma20 = df['Close'].rolling(20).mean()
        std20 = df['Close'].rolling(20).std()
        upper, lower = ma20 + (std20 * 2), ma20 - (std20 * 2)

        # 캔들과 거래량 분리 레이아웃
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.05, row_heights=[0.7, 0.3])

        # 상단: 캔들스틱 + 볼린저 밴드
        fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close, name='주가'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=upper, line=dict(color='rgba(255,0,0,0.2)'), name='상단'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=lower, line=dict(color='rgba(0,255,0,0.2)'), name='하단'), row=1, col=1)

        # 하단: 거래량 막대 (상승 빨강 / 하락 파랑)
        colors = ['red' if df.Close[i] >= df.Open[i] else 'blue' for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index, y=df.Volume, marker_color=colors, name='거래량'), row=2, col=1)

        fig.update_layout(xaxis_rangeslider_visible=False, height=600, template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"차트 엔진 가동 실패: {e}")

# --- 실행 화면 ---
data = load_data()
st.title("🏛️ Medallion Quant Final")
st.caption("차트 엔진: Naver Financial API 연결 중 | 가용 현금: 3,000,000원")

# 보유 종목 리스트
my_stocks = ["이오테크닉스", "리노공업", "다원시스", "테크윙", "크래프톤", "꿈비", "샌즈랩", "삼양컴텍"]

col1, col2 = st.columns([3, 1])
with col1:
    target = st.selectbox("종목 선택", data['Name'].tolist())
    if target:
        code = data[data['Name'] == target]['Code'].values[0]
        draw_chart(code)

with col2:
    st.subheader("📂 My Portfolio")
    st.table(pd.DataFrame({"종목": my_stocks}))
