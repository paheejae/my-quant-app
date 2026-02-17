import streamlit as st
import FinanceDataReader as fdr
import pandas as pd

# 1. 전 종목 리스트 로드 (코스피, 코스닥)
@st.cache_data
def get_stock_list():
    return fdr.StockListing('KRX')[['Code', 'Name', 'Market']]

# 메인 로직 시작
try:
    all_stocks = get_stock_list()

    st.title("🚀 Sungjun's Naver Quant Engine")
    st.sidebar.metric("가용 현금", "3,000,000원") # [cite: 2026-01-28]

    # 2. 종목 검색 기능
    st.subheader("🔍 실시간 종목 검색")
    search_name = st.selectbox("분석할 종목을 선택하세요", [""] + all_stocks['Name'].tolist())

    if search_name:
        code = all_stocks[all_stocks['Name'] == search_name]['Code'].values[0]
        df = fdr.DataReader(code).tail(2)
        if not df.empty:
            curr = int(df['Close'].iloc[-1])
            st.success(f"**{search_name}** ({code}) 현재가: **{curr:,.0f}원**")

    # 3. 나의 보유 종목 현황
    st.divider()
    st.subheader("📊 나의 정예 포트폴리오")
    my_list = ["이오테크닉스", "리노공업", "다원시스", "테크윙", "크래프톤", "꿈비", "샌즈랩", "삼양컴텍"]
    res = []
    for s in my_list:
        try:
            c = all_stocks[all_stocks['Name'] == s]['Code'].values[0]
            p = int(fdr.DataReader(c)['Close'].iloc[-1])
            res.append({"종목명": s, "현재가": p, "코드": c})
        except: continue
    st.table(pd.DataFrame(res))

except Exception as e:
    st.error("데이터 엔진을 초기화 중입니다. 1~2분만 기다려주세요.")
