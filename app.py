import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 페이지 설정 및 다크 테마
st.set_page_config(page_title="Medallion Final V8", layout="wide")

@st.cache_data
def load_pro_data():
    try:
        df = fdr.StockListing('KRX')
        # 섹터 정보 추출 (방어적 로직)
        if 'Sector' in df.columns:
            df['Display_Sector'] = df['Sector'].fillna('일반 산업')
        elif 'Industry' in df.columns:
            df['Display_Sector'] = df['Industry'].fillna('일반 산업')
        else:
            df['Display_Sector'] = '코스피/코스닥 상장사'
        return df[['Code', 'Name', 'Display_Sector']]
    except:
        return pd.DataFrame(columns=['Code', 'Name', 'Display_Sector'])

# 2. 고속 퀀트 스캐너 (추천 종목 + AI 설명)
@st.cache_data(ttl=3600)
def get_picks(stock_df):
    if stock_df.empty: return pd.DataFrame()
    sample = stock_df.sample(n=min(100, len(stock_df)))
    picks = []
    
    for _, row in sample.iterrows():
        try:
            df = fdr.DataReader(row['Code']).tail(40)
            if len(df) < 20: continue
            curr_p = int(df['Close'].iloc[-1])
            if curr_p < 2000: continue # 2,000원 이하 제외
            
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            z_score = (curr_p - ma20) / std20 if std20 > 0 else 0
            
            if z_score < -1.1:
                sector = row['Display_Sector']
                picks.append({
                    '종목명': row['Name'], '섹터': sector,
                    '현재가': f"{curr_p:,}원",
                    '설명': f"본 종목은 **{sector}** 관련주로, 현재 통계적 과매도 구간(Z-Score {z_score:.2f})에 진입하여 기술적 반등 가능성이 높습니다.",
                    '신뢰도': round(abs(z_score)*35, 1)
                })
        except: continue
    return pd.DataFrame(picks).head(10)

# --- 레이아웃 시작 ---
market_df = load_pro_data()
st.title("🏛️ Medallion Quant Final Terminal")
st.caption("시스템 상태: 정밀 캔들스틱 및 섹터 엔진 최적화 완료 | 가용 현금: 3,000,000원")

# 섹션 1: 추천 종목 카드
if st.button("🚀 실시간 시장 전수 분석"):
    with st.spinner('메달리온 알고리즘 가동 중...'):
        recomm = get_picks(market_df)
        if not recomm.empty:
            for i in range(0, len(recomm), 5):
                cols = st.columns(5)
                for j, (idx, row) in enumerate(recomm.iloc[i:i+5].iterrows()):
                    with cols[j]:
                        st.success(f"**{row['종목명']}**")
                        st.caption(f"📂 {row['섹터']}")
                        st.metric("현재가", row['현재가'])
                        with st.expander("📝 AI 분석 리포트"):
                            st.write(row['설명'])
                        st.progress(min(row['신뢰도']/100, 1.0))
        else:
            st.info("현재 기준에 부합하는 안정적인 종목이 없습니다.")

st.divider()

# 섹션 2: HTS급 정밀 차트 (캔들스틱 + 볼린저 + 분리형 거래량)
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("📊 정밀 기술적 분석 차트")
    target_name = st.selectbox("분석할 종목 선택", market_df['Name'].tolist() if not market_df.empty else ["삼성전자"])
    
    if target_name:
        try:
            target_code = market_df[market_df['Name'] == target_name]['Code'].values[0]
            df = fdr.DataReader(target_code).tail(120)
            
            # 지표 계산
            ma20 = df['Close'].rolling(20).mean()
            std20 = df['Close'].rolling(20).std()
            upper, lower = ma20 + (std20 * 2), ma20 - (std20 * 2)
            
            # 차트 분리 (주가 70%, 거래량 30%)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            
            # 1. 캔들스틱 & 볼린저 밴드
            fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close, name='주가'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=upper, line=dict(color='rgba(255, 0, 0, 0.2)'), name='상단'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=lower, line=dict(color='rgba(0, 255, 0, 0.2)'), name='하단'), row=1, col=1)
            
            # 2. 막대형 거래량 (상승 빨강 / 하락 파랑)
            v_colors = ['red' if df.Close[i] >= df.Open[i] else 'blue' for i in range(len(df))]
            fig.add_trace(go.Bar(x=df.index, y=df.Volume, marker_color=v_colors, name='거래량'), row=2, col=1)
            
            fig.update_layout(xaxis_rangeslider_visible=False, height=700, template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)
        except: st.error("차트 데이터를 불러올 수 없습니다.")

with col2:
    st.subheader("📂 My Portfolio")
    my_stocks = ["이오테크닉스", "리노공업", "다원시스", "테크윙", "크래프톤", "꿈비", "샌즈랩", "삼양컴텍"]
    st.table(pd.DataFrame({"보유종목": my_stocks}))
