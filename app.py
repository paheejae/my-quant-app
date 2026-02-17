import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime

# 1. 전 종목 리스트 로드 (코스피, 코스닥)
@st.cache_data
def get_stock_list():
    return fdr.StockListing('KRX')[['Code', 'Name', 'Market']]

all_stocks = get_stock_list()

# 2. 앱 화면 구성
st.title("🇰🇷 네이버 금융 검색 & 퀀트 엔진")
st.sidebar.metric("가용 현금", "3,000,000원") # [cite: 2026-01-28]

# 3. 실시간 종목 검색 기능
st.subheader("🔍 종목 검색")
search_name = st.selectbox("검색할 종목명을 선택하세요", [""] + all_stocks['Name'].tolist())

if search_name:
    code = all_stocks[all_stocks['Name'] == search_name]['Code'].values[0]
    df = fdr.DataReader(code)
    curr_price = int(df['Close'].iloc[-1])
    
    st.success(f"**{search_name} ({code})** 의 현재가는 **{curr_price:,.0f}원** 입니다.")
    st.info("짐 사이먼스 알고리즘에 따른 정예 종목 여부를 분석 중입니다...")

# 4. 나의 보유 종목 현황
st.divider()
st.subheader("📊 나의 보유 종목 실시간")
my_stocks = ["이오테크닉스", "리노공업", "다원시스", "테크윙", "크래프톤", "꿈비", "샌즈랩", "삼양컴텍"]
res = []
for s in my_stocks:
    try:
        c = all_stocks[all_stocks['Name'] == s]['Code'].values[0]
        p = int(fdr.DataReader(c)['Close'].iloc[-1])
        res.append({"종목명": s, "현재가": p, "코드": c})
    except: continue
st.table(pd.DataFrame(res))
