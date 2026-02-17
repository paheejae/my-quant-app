import streamlit as st
import FinanceDataReader as fdr
import pandas as pd

# 전 종목 리스트 로드
@st.cache_data
def get_stock_list():
    return fdr.StockListing('KRX')[['Code', 'Name', 'Market']]

try:
    all_stocks = get_stock_list()
    st.title("🚀 Sungjun's Naver Quant Engine")
    
    # 종목 검색
    search_name = st.selectbox("분석할 종목 선택", [""] + all_stocks['Name'].tolist())
    if search_name:
        code = all_stocks[all_stocks['Name'] == search_name]['Code'].values[0]
        df = fdr.DataReader(code).tail(1)
        curr = int(df['Close'].iloc[0])
        st.success(f"**{search_name}** ({code}) 현재가: **{curr:,.0f}원**")

    # 나의 보유 종목
    st.divider()
    st.subheader("📊 보유 종목 실시간")
    my_list = ["이오테크닉스", "리노공업", "다원시스", "테크윙", "크래프톤", "꿈비", "샌즈랩", "삼양컴텍"]
    res = []
    for s in my_list:
        try:
            c = all_stocks[all_stocks['Name'] == s]['Code'].values[0]
            p = int(fdr.DataReader(c).tail(1)['Close'].iloc[0])
            res.append({"종목명": s, "현재가": p})
        except: continue
    st.table(pd.DataFrame(res))
except:
    st.info("데이터 엔진 로딩 중... 잠시만 기다려주세요.")
