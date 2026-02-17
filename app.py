import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings

warnings.filterwarnings('ignore')

st.set_page_config(page_title="Medallion Final", layout="wide")

# 1. 세션 상태 저장소 (PC를 꺼도 클라우드에서는 유지됨)
if 'recomm_list' not in st.session_state:
    st.session_state.recomm_list = None

@st.cache_data(ttl=3600)
def load_market_data():
    try:
        df = fdr.StockListing('KRX-DESC')
        return df[['Code', 'Name', 'Sector']].dropna(subset=['Sector'])
    except:
        return pd.DataFrame(columns=['Code', 'Name', 'Sector'])

# 2. 짐 사이먼스 알고리즘 (빈 결과에 대한 방어 로직 추가)
def get_simons_picks(stock_df):
    sample_list = stock_df.sample(n=min(150, len(stock_df)))
    picks = []
    
    with st.spinner('시장의 비정상적 패턴을 추적 중...'):
        for _, row in sample_list.iterrows():
            try:
                # 데이터 로드
                df = fdr.DataReader(row['Code']).tail(35)
                if len(df) < 20: continue
                
                curr_p = int(df['Close'].iloc[-1])
                if curr_p < 2000: continue
                
                # 통계 점수 산출
                ma20 = df['Close'].rolling(20).mean().iloc[-1]
                std20 = df['Close'].rolling(20).std().iloc[-1]
                z_score = (curr_p - ma20) / std20 if std20 > 0 else 0
                
                # 사이먼스 점수 계산
                simons_score = 0
                if z_score < 0:
                    simons_score = min(100, round(abs(z_score) * 45))
                
                if simons_score >= 70: # 임계값 소폭 조정으로 추천 빈도 최적화
                    picks.append({
                        '종목명': row['Name'], '코드': row['Code'],
                        '섹터': row['Sector'], '현재가': f"{curr_p:,}원",
                        '시먼스_점수': simons_score,
                        '분석': f"표준편차 {abs(z_score):.2f}σ 이탈"
                    })
            except: continue
            
    # [핵심 수정] 결과가 없을 때 KeyError 방지
    if not picks:
        return pd.DataFrame()
    
    return pd.DataFrame(picks).sort_values(by='시먼스_점수', ascending=False).head(10)

# --- UI 레이아웃 ---
st.title("🏛️ Medallion Quant Final")
st.caption("가용 자산: 3,000,000원 | 짐 사이먼스 스코어 엔진 가동 중")

market_df = load_market_data()

# 추천 섹션
st.subheader("🚀 Medallion Top Picks (Jim Simons Model)")
if st.button("실시간 시장 패턴 스캔"):
    res = get_simons_picks(market_df)
    if not res.empty:
        st.session_state.recomm_list = res
    else:
        st.warning("현재 기준을 충족하는 종목이 없습니다. 다시 스캔해 보세요.")

# 고정된 추천 리스트 출력
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
                    <hr style="margin:8px 0; border:0.5px solid #333;">
                    <p style="font-size:13px; margin:0;">{row['현재가']}</p>
                    <p style="font-size:11px; color:#00FF00; margin:0;">{row['분석']}</p>
                </div>
                """, unsafe_allow_html=True)

st.divider()

# 차트 섹션
st.subheader("📊 정밀 기술적 분석 차트")
target_name = st.selectbox("종목 선택", market_df['Name'].tolist())
if target_name:
    code = market_df[market_df['Name'] == target_name]['Code'].values[0]
    try:
        df_chart = fdr.DataReader(code).tail(100)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart.Open, high=df_chart.High, low=df_chart.Low, close=df_chart.Close, name='주가'), row=1, col=1)
        
        colors = ['#FF4B4B' if df_chart['Close'].iloc[k] >= df_chart['Open'].iloc[k] else '#007BFF' for k in range(len(df_chart))]
        fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['Volume'], marker_color=colors, name='거래량'), row=2, col=1)
        
        fig.update_layout(xaxis_rangeslider_visible=False, height=600, template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
    except:
        st.error("데이터를 불러올 수 없습니다.")
