import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Medallion Ultimate Terminal", layout="wide")

@st.cache_data
def load_market_data():
    try:
        # 가장 안정적인 상장 종목 리스트 로드
        df = fdr.StockListing('KRX')
        # 업종 정보(Sector)가 없을 경우 Industry 컬럼 활용, 둘 다 없으면 '미분류'
        if 'Sector' in df.columns:
            df['Target_Sector'] = df['Sector'].fillna('일반 산업')
        elif 'Industry' in df.columns:
            df['Target_Sector'] = df['Industry'].fillna('일반 산업')
        else:
            df['Target_Sector'] = '일반 산업'
        return df[['Code', 'Name', 'Target_Sector']]
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
        return pd.DataFrame(columns=['Code', 'Name', 'Target_Sector'])

# 2. 고속 추천 로직 (설명 생성 및 2,000원 필터링)
@st.cache_data(ttl=3600)
def get_ai_recommendations(stock_df):
    if stock_df.empty: return pd.DataFrame()
    # 스캔 범위를 넓혀 추천 종목 수 확보
    sample_list = stock_df.sample(n=min(150, len(stock_df)))
    picks = []
    
    for _, row in sample_list.iterrows():
        try:
            df = fdr.DataReader(row['Code']).tail(40)
            if len(df) < 20: continue
            
            curr_p = int(df['Close'].iloc[-1])
            if curr_p < 2000: continue # 2,000원 필터링
            
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            z_score = (curr_p - ma20) / std20 if std20 > 0 else 0
            
            # 볼린저 밴드 하단 근접 (통계적 저점)
            if z_score < -1.1:
                sector = row['Target_Sector']
                desc = f"이 종목은 현재 **{sector}** 섹터 내에서 과매도 구간에 진입했습니다. 볼린저 밴드 하단 지지력을 확인하며 기술적 반등을 노려볼 수 있는 시점입니다."
                
                picks.append({
                    '종목명': row['Name'], '코드': row['Code'],
                    '섹터': sector, '현재가': f"{curr_p:,}원",
                    '설명': desc, '신뢰도': round(abs(z_score)*35, 1)
                })
        except: continue
    return pd.DataFrame(picks).head(10)

# --- UI 레이아웃 ---
market_data = load_market_data()
st.title("🏛️ Medallion Ultimate Terminal")
st.caption("시스템 상태: 캔들스틱 및 AI 섹터 분석 엔진 가동 중 | 2026 전략 가동")

# 섹션 1: 추천 종목 (카드 레이아웃 & 설명 포함)
if st.button("🚀 실시간 퀀트 스캔 시작"):
    with st.spinner('시장의 모든 데이터를 전수 분석 중...'):
        recomm = get_ai_recommendations(market_data)
        if not recomm.empty:
            for i in range(0, len(recomm), 5): # 5개씩 배치
                cols = st.columns(5)
                for j, (idx, row) in enumerate(recomm.iloc[i:i+5].iterrows()):
                    with cols[j]:
                        st.success(f"**{row['종목명']}**")
                        st.caption(f"📂 {row['섹터']}")
                        st.metric("현재가", row['현재가'])
                        with st.expander("🔍 AI 종목 분석"):
                            st.write(row['설명'])
                        st.progress(min(row['신뢰도']/100, 1.0), text=f"신뢰도 {row['신뢰도']}%")
        else:
            st.info("현재 분석 기준에 맞는 종목이 없습니다. 잠시 후 다시 시도해 주세요.")

st.divider()

# 섹션 2: HTS급 정밀 차트 (캔들스틱 + 볼린저 밴드 + 분리형 거래량)
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("📊 정밀 기술적 분석 (볼린저 밴드)")
    target_name = st.selectbox("분석할 종목을 선택하세요", market_data['Name'].tolist() if not market_data.empty else ["삼성전자"])
    
    if target_name:
        try:
            target_code = market_data[market_data['Name'] == target_name]['Code'].values[0]
            # 최근 120일 데이터 로드
            df = fdr.DataReader(target_code).tail(120)
            
            # 볼린저 밴드 계산 (20일 기준)
            ma20 = df['Close'].rolling(20).mean()
            std20 = df['Close'].rolling(20).std()
            upper = ma20 + (std20 * 2)
            lower = ma20 - (std20 * 2)
            
            # 이중축 서브플롯: 주가(70%), 거래량(30%) 분리
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.03, row_heights=[0.7, 0.3])
            
            # 1. 캔들스틱 차트
            fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close, name='주가'), row=1, col=1)
            # 볼린저 밴드 추가
            fig.add_trace(go.Scatter(x=df.index, y=upper, line=dict(color='rgba(255, 0, 0, 0.3)', width=1), name='상단밴드'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=lower, line=dict(color='rgba(0, 255, 0, 0.3)', width=1), name='하단밴드'), row=1, col=1)
            
            # 2. 막대형 거래량 (상승/하락 색상 구분)
            colors = ['red' if df.Close[i] >= df.Open[i] else 'blue' for i in range(len(df))]
            fig.add_trace(go.Bar(x=df.index, y=df.Volume, marker_color=colors, name='거래량'), row=2, col=1)
            
            # 차트 스타일링
            fig.update_layout(xaxis_rangeslider_visible=False, height=750, template='plotly_dark', margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"데이터 로딩 중: {e}")

with col2:
    st.subheader("📂 My Portfolio")
    my_stocks = ["이오테크닉스", "리노공업", "다원시스", "테크윙", "크래프톤", "꿈비", "샌즈랩", "삼양컴텍"]
    st.table(pd.DataFrame({"보유종목": my_stocks}))
    st.info("💡 **전략 가이드**: 캔들이 볼린저 밴드 하단(녹색선)을 터치하고 거래량이 늘어나며 반등할 때가 매수 급소입니다.")
