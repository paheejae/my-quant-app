import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="Sungjun Quant Dashboard", layout="wide")

# 2. 데이터 엔진 (전 종목 리스트 로드)
@st.cache_data
def get_all_stocks():
    return fdr.StockListing('KRX')[['Code', 'Name', 'Market']]

try:
    all_stocks = get_all_stocks()
    
    # 3. 사이드바: 가용 현금 정보
    st.sidebar.title("💰 자산 현황")
    st.sidebar.metric("가용 현금", "3,000,000원")
    
    # 4. 메인 화면: 종목 검색
    st.title("🇰🇷 네이버 금융 기반 퀀트 시스템")
    st.divider()
    
    st.subheader("🔍 실시간 종목 검색")
    search_name = st.selectbox("종목명을 선택하거나 입력하세요", [""] + all_stocks['Name'].tolist())

    if search_name:
        target_code = all_stocks[all_stocks['Name'] == search_name]['Code'].values[0]
        df_price = fdr.DataReader(target_code).tail(2)
        
        if not df_price.empty:
            curr_price = int(df_price['Close'].iloc[-1])
            prev_price = int(df_price['Close'].iloc[-2])
            change_pct = ((curr_price / prev_price) - 1) * 100
            
            st.metric(f"{search_name} ({target_code})", f"{curr_price:,.0f}원", delta=f"{change_pct:.2f}%")
            
            if change_pct > 3:
                st.success("🔥 강한 상승 모멘텀이 감지되었습니다! (정예 후보)")
            elif change_pct < -3:
                st.error("⚠️ 급락 주의: 퀀트 필터링 기준 제외 권고")

    # 5. 내 포트폴리오 섹션
    st.divider()
    st.subheader("📊 나의 정예 포트폴리오 (실시간)")
    # 종목 리스트 확인 작업 수행
