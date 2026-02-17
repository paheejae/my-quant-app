import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings

warnings.filterwarnings('ignore')

# 페이지 설정
st.set_page_config(page_title="Medallion Persistent Terminal", layout="wide")

# 1. 세션 상태 초기화 (추천 리스트를 저장할 공간 생성)
if 'recomm_list' not in st.session_state:
    st.session_state.recomm_list = None

@st.cache_data(ttl=3600)
def load_market_data():
    try:
        df = fdr.StockListing('KRX-DESC')
        return df[['Code', 'Name', 'Sector']].dropna(subset=['Sector'])
    except:
        return pd.DataFrame(columns=['Code', 'Name', 'Sector'])

# 2. 짐 사이먼스 스코어 알고리즘
def get_simons_picks(stock_df):
    sample_list = stock_df.sample(n=min(120, len(stock_df)))
    picks = []
    
    with st.spinner('짐 사이먼스 알고리즘 가동 중... 시장의 패턴을 분석합니다.'):
        for _, row in sample_list.iterrows():
            try:
                df = fdr.DataReader(row['Code']).tail(40)
                if len(df) < 25: continue
                
                curr_p = int(df['Close'].iloc[-1])
                if curr_p < 2000: continue
                
                ma20 = df['Close'].rolling(20).mean().iloc[-1]
                std20 = df['Close'].rolling(20).std().iloc[-1]
                z_score = (curr_p - ma20) / std20 if std20 > 0 else 0
                
                simons_score = 0
                if z_score < 0:
                    simons_score = min(100, round(abs(z_score) * 40)) 
                
                if simons_score >= 75:
                    picks.append({
                        '종목명': row['Name'], '코드': row['Code'],
                        '섹터': row['Sector'], '현재가': f"{curr_p:,}원",
                        '시먼스_점수': simons_score,
                        '분석': f"과매도 {abs(z_score):.2f}σ"
                    })
            except: continue
    
    res = pd.DataFrame(picks).sort_values(by='시먼스_점수', ascending=False).head(10)
    return res

# --- 메인 레이아웃 ---
st.title("🏛️ Medallion Quant Final")
st.caption("가용 자산: 3,000,000원 | 데이터 상태: 영구 유지 및 짐 사이먼스 모델 적용")

market_df = load_market_data()

# 섹션 1: 추천 종목 (상태 유지 기능 적용)
st.subheader("🚀 Medallion Top Picks (By Jim Simons Model)")

# 스캔 버튼
if st.button("실시간 패턴 스캔 및 스코어 고정"):
    # 결과를 세션 상태에 저장하여 초기화 방지
    st.session_state.recomm_list = get_simons_picks(market_df)

# 세션 상태에 데이터가 있으면 화면에 표시 (다른 조작 시에도 유지됨)
if st.session_state.recomm_list is not None:
    recomm = st.session_state.recomm_list
    for i in range(0, len(recomm), 5):
        cols = st.columns(5)
        for j, (idx, row) in enumerate(recomm.iloc[i:i+5].iterrows()):
            with cols[j]:
                st.markdown(f"""
                <div style="border:1px solid #4a4a4a; border-radius:10px; padding:15px; background-color:#1e1e1e; height:180px">
                    <h3 style="color:#FF4B4B; margin:0;">{row['시먼스_점수']}점</h3>
                    <p style="font-size:16px; font-weight:bold; margin:5px 0;">{row['종목명']}</p>
                    <p style="font-size:11px; color:#888;">{row['섹터']}</p>
                    <hr style="margin:8px 0; border:0.5px solid #333;">
                    <p style="font-size:13px; margin:0;">{row['현재가']}</p>
                    <p style="font-size:11px; color:#00FF00; margin:0;">{row['분석']}</p>
                </div>
                """, unsafe_allow_html=True)
else:
    st.info("위 버튼을 눌러 추천 종목을 불러오세요. 한 번 불러오면 초기화되지 않습니다.")

st.divider()

# 섹션 2: 정밀 차트 분석 (추천주를 봐도 상단 리스트는 유지됨)
st.subheader("📊 정밀 기술적 분석")
target_name = st.selectbox("분석할 종목을 검색하거나 선택하세요", market_df['Name'].tolist())

if target_name:
    code = market_df[market_df['Name'] == target_name]['Code'].values[0]
    df = fdr.DataReader(code).tail(120)
    
    ma20 = df['Close'].rolling(20).mean()
    std20 = df['Close'].rolling(20).std()
    upper, lower = ma20 + (std20 * 2), ma20 - (std20 * 2)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
    
    # 캔들스틱 및 볼린저 밴드
    fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close, name='주가'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=upper, line=dict(color='rgba(255,0,0,0.2)', width=1), name='상단'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=lower, line=dict(color='rgba(0,255,0,0.2)', width=1), name='하단'), row=1, col=1)
    
    # 거래량
    colors = ['#FF4B4B' if df['Close'].iloc[k] >= df['Open'].iloc[k] else '#007BFF' for k in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='거래량'), row=2, col=1)
    
    fig.update_layout(xaxis_rangeslider_visible=False, height=650, template='plotly_dark')
    st.plotly_chart(fig, use_container_width=True)
