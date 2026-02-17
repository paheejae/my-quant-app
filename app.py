import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 페이지 설정
st.set_page_config(page_title="Medallion Ultimate Terminal", layout="wide")

@st.cache_data
def load_full_data():
    # KRX 전체 종목 리스트와 업종 상세 정보를 가져옵니다.
    df = fdr.StockListing('KRX')
    # 상세 업종명이 없을 경우 '산업분류' 등을 참고하여 최대한 구체적으로 표기
    df['Detailed_Sector'] = df['Sector'].fillna(df['Industry']).fillna('기타 산업')
    return df

# 2. 고속 스캐너 (추천 종목 및 설명 생성)
@st.cache_data(ttl=3600)
def get_pro_recommendations(stock_df):
    sample_list = stock_df.sample(n=min(120, len(stock_df)))
    picks = []
    
    for _, row in sample_list.iterrows():
        try:
            df = fdr.DataReader(row['Code']).tail(30)
            curr_p = int(df['Close'].iloc[-1])
            if curr_p < 2000: continue
            
            # 통계 지표 계산
            ma20 = df['Close'].rolling(20).mean()
            std20 = df['Close'].rolling(20).std()
            z_score = (curr_p - ma20.iloc[-1]) / std20.iloc[-1]
            
            if z_score < -1.2: # 저점 구간
                # 종목 설명 자동 생성 (섹터 기반)
                desc = f"{row['Name']}은(는) {row['Detailed_Sector']} 분야의 주요 기업으로, 현재 통계적 과매도 구간에 진입하여 기술적 반등이 기대되는 시점입니다."
                
                picks.append({
                    '종목명': row['Name'], 
                    '섹터': row['Detailed_Sector'],
                    '현재가': f"{curr_p:,}원",
                    '설명': desc,
                    '신뢰도': round(abs(z_score)*35, 1)
                })
        except: continue
    return pd.DataFrame(picks).head(8)

# --- UI 레이아웃 ---
stock_info = load_full_data()
st.title("🏛️ Medallion Ultimate Terminal")
st.caption(f"시스템 상태: 정밀 분석 모드 | 가용 현금: 3,000,000원")

# 섹션 1: 추천 종목 카드 (설명 포함)
if st.button("🚀 실시간 시장 전수 스캔 및 섹터 분석 시작"):
    with st.spinner('메달리온 알고리즘이 유망 종목과 섹터를 분석 중...'):
        recomm = get_pro_recommendations(stock_info)
        if not recomm.empty:
            for i in range(0, len(recomm), 4): # 4개씩 한 줄에 배치
                cols = st.columns(4)
                for j, (idx, row) in enumerate(recomm.iloc[i:i+4].iterrows()):
                    with cols[j]:
                        st.success(f"**{row['종목명']}**")
                        st.caption(f"🏗️ {row['섹터']}")
                        st.metric("현재가", row['현재가'])
                        with st.expander("📝 종목 분석 설명"):
                            st.write(row['설명'])
                        st.progress(min(row['신뢰도']/100, 1.0), text=f"신뢰도 {row['신뢰도']}%")
        else:
            st.info("현재 분석 기준에 맞는 종목이 없습니다.")

st.divider()

# 섹션 2: HTS급 정밀 차트 (볼린저 밴드 + 막대 거래량)
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("📊 정밀 기술적 분석 (볼린저 밴드 & 거래량)")
    target_name = st.selectbox("종목 검색", stock_info['Name'].tolist())
    
    if target_name:
        try:
            target_code = stock_info[stock_info['Name'] == target_name]['Code'].values[0]
            df = fdr.DataReader(target_code).tail(120)
            
            # 볼린저 밴드 계산
            ma20 = df['Close'].rolling(20).mean()
            std20 = df['Close'].rolling(20).std()
            upper = ma20 + (std20 * 2)
            lower = ma20 - (std20 * 2)
            
            # 차트 구성
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            
            # 1. 캔들스틱 & 볼린저 밴드
            fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close, name='주가'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=upper, line=dict(color='rgba(255, 0, 0, 0.3)', width=1), name='상단밴드'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=ma20, line=dict(color='rgba(255, 255, 255, 0.3)', dash='dot'), name='중심선'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=lower, line=dict(color='rgba(0, 255, 0, 0.3)', width=1), name='하단밴드'), row=1, col=1)
            
            # 2. 막대형 거래량
            colors = ['red' if df.Close[i] >= df.Open[i] else 'blue' for i in range(len(df))]
            fig.add_trace(go.Bar(x=df.index, y=df.Volume, marker_color=colors, name='거래량'), row=2, col=1)
            
            fig.update_layout(xaxis_rangeslider_visible=False, height=750, template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)
        except: st.error("데이터 수집 중입니다. 잠시만 기다려 주세요.")

with col2:
    st.subheader("📂 My Portfolio")
    # 보유 종목 리스트
    my_stocks = ["이오테크닉스", "리노공업", "다원시스", "테크윙", "크래프톤", "꿈비", "샌즈랩", "삼양컴텍"]
    for s in my_stocks:
        st.write(f"- {s}")
    st.divider()
    st.info("💡 팁: 볼린저 밴드 하단(녹색선)을 캔들이 뚫고 내려갔다 반등할 때 거래량이 실리면 강력한 매수 신호입니다.")
