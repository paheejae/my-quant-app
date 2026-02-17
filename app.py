import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 페이지 설정
st.set_page_config(page_title="Medallion Advanced Terminal", layout="wide")

@st.cache_data
def load_stock_info():
    # 섹터(Sector) 정보를 포함하여 로드
    return fdr.StockListing('KRX')[['Code', 'Name', 'Market', 'Sector']]

# 2. 고속 추천 로직 (섹터 정보 포함)
@st.cache_data(ttl=3600)
def get_medallion_picks(stock_df):
    sample_list = stock_df.sample(n=min(60, len(stock_df)))
    picks = []
    
    for _, row in sample_list.iterrows():
        try:
            df = fdr.DataReader(row['Code']).tail(30)
            if len(df) < 20: continue
            
            curr_price = int(df['Close'].iloc[-1])
            if curr_price < 2000: continue 
            
            ma = df['Close'].mean()
            std = df['Close'].std()
            if std == 0: continue
            
            z_score = (curr_price - ma) / std
            
            if z_score < -1.2:
                picks.append({
                    '종목명': row['Name'], 
                    '코드': row['Code'], 
                    '섹터': row['Sector'] if pd.notna(row['Sector']) else "기타",
                    '현재가': curr_price, 
                    '현재금액': f"{curr_price:,}원",
                    '신뢰도': round(abs(z_score)*35, 1)
                })
        except: continue
    return pd.DataFrame(picks).head(5)

# --- UI 레이아웃 ---
stock_info = load_stock_info()
st.title("🏛️ Medallion Quant Intelligence")
st.caption("시스템 상태: 섹터 분석 및 정밀 차트 모드 활성")

# 섹션 1: 추천 종목 (섹터 정보 포함)
if st.button("🚀 실시간 통계 분석 시작"):
    with st.spinner('섹터별 통계적 우위를 분석 중...'):
        recomm = get_medallion_picks(stock_info)
        if not recomm.empty:
            cols = st.columns(len(recomm))
            for i, (_, row) in enumerate(recomm.iterrows()):
                with cols[i]:
                    st.success(f"**{row['종목명']}**")
                    st.caption(f"📂 {row['섹터']}") # 섹터 정보 표시
                    st.metric(label="현재 금액", value=row['현재금액'])
                    st.info(f"통계 신뢰도
