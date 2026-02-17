import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 페이지 설정
st.set_page_config(page_title="Medallion Final Terminal", layout="wide")

@st.cache_data
def load_market_data():
    try:
        # 상장 종목 리스트 로드
        df = fdr.StockListing('KRX')
        # 섹터 정보가 없는 경우를 대비한 방어 로직
        sector_col = 'Sector' if 'Sector' in df.columns else ('Industry' if 'Industry' in df.columns else None)
        df['Target_Sector'] = df[sector_col].fillna('일반 산업') if sector_col else '일반 산업'
        return df[['Code', 'Name', 'Target_Sector']]
    except:
        return pd.DataFrame(columns=['Code', 'Name', 'Target_Sector'])

# 2. 고속 추천 로직 (안정성 강화)
@st.cache_data(ttl=3600)
def get_recommendations(stock_df):
    if stock_df.empty: return pd.DataFrame()
    sample = stock_df.sample(n=min(100, len(stock_df)))
    picks = []
    
    for _, row in sample.iterrows():
        try:
            # Naver 엔진을 사용하여 데이터 안정성 확보
            df = fdr.DataReader(row['Code'], exchange='naver').tail(30)
            if len(df) < 20: continue
            
            curr_p = int(df['Close'].iloc[-1])
            if curr_p < 2000: continue # 2,000원 필터
            
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            z_score = (curr_p - ma20) / std20 if std20 > 0 else 0
            
            if z_score < -1.1:
                picks.append({
                    '종목명': row['Name'], '코드': row['Code'],
                    '섹터': row['Target_Sector'], '현재가': f"{curr_p:,}원",
                    '설명': f"{row['Target_Sector']} 관련주로 현재 통계적 과매도 구간입니다.",
                    '신뢰도': round(abs(z_score)*35, 1)
                })
        except: continue
    return pd.DataFrame(picks).head(8)

# --- UI 레이아웃 ---
market_data = load_market_data()
st.title("🏛️ Medallion Ultimate Terminal")
st.caption("시스템 상태: Naver 데이터 엔진 기반 안정화 모드 가동 중")

# 섹션 1: 추천 종목 카드
if st.button("🚀 실시간 시장 전수 스캔"):
    with st.spinner('거래소 데이터를 정밀 분석 중...'):
        recomm = get_recommendations(market_data)
        if not recomm.empty:
            for i in range(0, len(recomm), 4):
                cols = st.columns(4)
                for j, (idx, row) in enumerate(recomm.iloc[i:i+4].iterrows()):
                    with cols[j]:
                        st.success(f"**{row['종목명']}**")
                        st.caption(f"📂 {row['섹터']}")
                        st.metric("현재가", row['현재가'])
                        with st.expander("📝 상세 분석"):
                            st.write(row['설명'])
                        st.progress(min(row['신뢰도']/100, 1.0))
        else:
            st.info("조건에 맞는 종목이 없습니다. 다시 시도해 주세요.")

st.divider()

# 섹션 2: HTS급 정밀 차트 (캔들스틱 + 볼린저 + 막대 거래량)
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("📊 정밀 기술적 분석 차트")
    target_name = st.selectbox("분석할 종목 선택", market_data['Name'].tolist() if not market_data.empty else ["삼성전자"])
    
    if target_name:
        try:
            target_code = market_data[market_data['Name'] == target_name]['Code'].values[0]
            # 차트 데이터 로드 (Naver 엔진)
            df = fdr.DataReader(target_code, exchange='naver').tail(100)
            
            # 지표 계산
            ma20 = df['Close'].rolling(20).mean()
            std20 = df['Close'].rolling(20).std()
            upper, lower = ma20 + (std20 * 2), ma20 - (std20 * 2)
            
            # 레이아웃 분리: 상단(70%) 주가, 하단(30%) 거래량
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.03, row_heights=[0.7, 0.3])
            
            # 1. 캔들스틱 & 볼린저 밴드
            fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close, name='주가'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=upper, line=dict(color='rgba(255, 0, 0, 0.3)'), name='상단밴드'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=lower, line=dict(color='rgba(0, 255, 0, 0.3)'), name='하단밴드'), row=1, col=1)
            
            # 2. 막대형 거래량 (상승/하락 색상 구분)
            colors = ['#ff4b4b' if df.Close[i] >= df.Open[i] else '#007bff' for i in range(len(df))]
            fig.add_trace(go.Bar(x=df.index, y=df.Volume, marker_color=colors, name='거래량'), row=2, col=1)
            
            fig.update_layout(xaxis_rangeslider_visible=False, height=700, template='plotly_dark', margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"차트를 불러올 수 없습니다. 다시 시도해 주세요. (에러: {e})")

with col2:
    st.subheader("📂 내 포트폴리오")
    my_stocks = ["이오테크닉스", "리노공업", "다원시스", "테크윙", "크래프톤", "꿈비", "샌즈랩", "삼양컴텍"]
    st.table(pd.DataFrame({"보유종목": my_stocks}))
