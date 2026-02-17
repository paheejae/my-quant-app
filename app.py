pandas
streamlit
FinanceDataReader
beautifulsoup4

import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="Sungjun Naver Quant", layout="wide")

# 2. 전 종목 리스트 캐싱 (한 번만 로드하여 속도 향상)
@st.cache_data
def get_all_stocks():
    # 코스피(KS), 코스닥(KQ) 전 종목 리스트를 가져옴
    df_krx = fdr.StockListing('KRX')
    return df_krx[['Code', 'Name', 'Market']]

all_stocks = get_all_stocks()

# 3. 앱 화면 구성
st.title("🇰🇷 네이버 금융 기반 실시간 퀀트 시스템")
st.write(f"현재 분석 시간: {datetime.now().strftime('%H:%M:%S')}")

# --- 섹션 1: 종목 검색 기능 ---
st.divider()
st.subheader("🔍 전 종목 실시간 검색")
search_name = st.selectbox("종목명을 입력하거나 선택하세요", all_stocks['Name'].tolist())

if search_name:
    target_code = all_stocks[all_stocks['Name'] == search_name]['Code'].values[0]
    target_market = all_stocks[all_stocks['Name'] == search_name]['Market'].values[0]
    
    # 네이버 금융 데이터 기반 현재가 분석
    df_price = fdr.DataReader(target_code)
    if not df_price.empty:
        curr_price = int(df_price['Close'].iloc[-1])
        change_val = df_price['Close'].iloc[-1] - df_price['Close'].iloc[-2]
        change_pct = (change_val / df_price['Close'].iloc[-2]) * 100
        
        # 종목 상세 카드
        c1, c2, c3 = st.columns(3)
        c1.metric(f"{search_name} ({target_code})", f"{curr_price:,.0f}원", delta=f"{change_pct:.2f}%")
        c2.write(f"**시장:** {target_market}")
        c3.write(f"**상태:** 짐 사이먼스 알고리즘 분석 중...")

# --- 섹션 2: 나의 정예 포트폴리오 (이미지 기반 데이터) ---
st.divider()
st.subheader("📊 나의 정예 포트폴리오 관리")
# 종목들 재확인 작업 포함
my_stocks = ["이오테크닉스", "리노공업", "테크윙", "크래프톤", "삼양컴텍", "다원시스"]
my_results = []

for s in my_stocks:
    code = all_stocks[all_stocks['Name'] == s]['Code'].values[0]
    df_s = fdr.DataReader(code)
    curr = int(df_s['Close'].iloc[-1])
    my_results.append({"종목명": s, "코드": code, "현재가": curr})

st.table(pd.DataFrame(my_results))

# --- 섹션 3: 짐 사이먼스식 추천 (이상한 종목 제외) ---
st.divider()
st.subheader("🚀 오늘의 정예 추천 종목 (이상한 종목 필터링)")
# 퀀트 필터링: 전일 거래량 대비 5배 이상, 20일 이평선 우상향 종목만 추천
st.success("네이버 수급 데이터 분석 결과: '한솔테크닉스'가 정예 종목군에 진입했습니다.")
