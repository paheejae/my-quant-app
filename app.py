import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings

warnings.filterwarnings('ignore')

st.set_page_config(page_title="Medallion Auto-Picker", layout="wide")

# 1. 시장 데이터 로드 (업종 정보 포함)
@st.cache_data(ttl=3600)
def load_all_market_data():
    try:
        df = fdr.StockListing('KRX-DESC')
        return df[['Code', 'Name', 'Sector']].dropna(subset=['Sector'])
    except:
        return pd.DataFrame(columns=['Code', 'Name', 'Sector'])

# 2. 메달리온 알고리즘 (추천 종목 스캔)
def get_medallion_picks(stock_df):
    sample_size = 120 # 한 번에 스캔할 종목 수
    sample_list = stock_df.sample(n=min(sample_size, len(stock_df)))
    picks = []
    
    with st.spinner('시장의 기회를 포착하는 중...'):
        for _, row in sample_list.iterrows():
            try:
                # 네이버 엔진으로 빠르게 20일치 데이터 확인
                df = fdr.DataReader(row['Code']).tail(25)
                if len(df) < 20: continue
                
                curr_p = int(df['Close'].iloc[-1])
                if curr_p < 2000: continue # 2,000원 이하 필터링
                
                # 볼린저 밴드 하단 이탈 여부 계산
                ma20 = df['Close'].rolling(20).mean().iloc[-1]
                std20 = df['Close'].rolling(20).std().iloc[-1]
                lower_band = ma20 - (std20 * 2)
                
                # 현재가가 하단 밴드 근처(또는 아래)일 때 추천
                if curr_p <= lower_band * 1.02: # 하단 밴드 2% 이격 이내
                    picks.append({
                        '종목명': row['Name'], '코드': row['Code'],
                        '섹터': row['Sector'], '현재가': f"{curr_p:,}원",
                        '상태': "바닥권 진입 (매수 고려)"
                    })
            except: continue
    return pd.DataFrame(picks).head(10)

# 3. 차트 렌더링 엔진
def render_chart(code):
    df = fdr.DataReader(code).tail(120)
    ma20 = df['Close'].rolling(20).mean()
    std20 = df['Close'].rolling(20).std()
    upper, lower = ma20 + (std20 * 2), ma20 - (std20 * 2)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close, name='주가'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=upper, line=dict(color='rgba(255,0,0,0.2)'), name='상단'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=lower, line=dict(color='rgba(0,255,0,0.2)'), name='하단'), row=1, col=1)
    
    colors = ['#FF4B4B' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#007BFF' for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='거래량'), row=2, col=1)
    fig.update_layout(xaxis_rangeslider_visible=False, height=600, template='plotly_dark')
    st.plotly_chart(fig, use_container_width=True)

# --- 메인 화면 ---
st.title("🏛️ Medallion Ultimate Picker")
market_df = load_all_market_data()

# [중요] 추천 종목 스캔 섹션
st.subheader("🚀 오늘의 메달리온 추천 종목")
if st.button("실시간 시장 전수 스캔 (알고리즘 가동)"):
    recomm = get_medallion_picks(market_df)
    if not recomm.empty:
        cols = st.columns(min(len(recomm), 5))
        for idx, row in recomm.iterrows():
            with cols[idx % 5]:
                st.success(f"**{row['종목명']}**")
                st.caption(f"📂 {row['섹터']}")
                st.write(row['현재가'])
                st.info(row['상태'])
    else:
        st.warning("현재 바닥권에 진입한 우량 종목이 없습니다. 잠시 후 다시 시도하세요.")

st.divider()

# 종목 상세 분석 섹션
st.subheader("📊 종목 상세 차트 분석")
target_name = st.selectbox("리스트에서 종목을 선택하거나 검색하세요", market_df['Name'].tolist())
if target_name:
    target_code = market_df[market_df['Name'] == target_name]['Code'].values[0]
    render_chart(target_code)
