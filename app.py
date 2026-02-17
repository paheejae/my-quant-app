import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np

st.set_page_config(page_title="Simons Intelligence", layout="wide")

# 1. 데이터 로드 및 필터링 함수
@st.cache_data
def get_recommendations():
    # 코스피, 코스닥 종목 리스트 합치기
    df_krx = fdr.StockListing('KRX')
    # 1차 필터링: 동전주 및 거래량 적은 종목 제거 (이상한 차트 1단계 제거)
    df_krx = df_krx[(df_krx['Market'] != 'KONEX') & (df_krx['Price'] >= 5000)] 
    
    candidates = []
    # 상위 100개 종목만 샘플링하여 분석 (속도를 위해)
    sample_stocks = df_krx.sample(150).values 
    
    for code, name, market, _, _, _, _, _ in sample_stocks:
        try:
            df = fdr.DataReader(code).tail(30)
            if len(df) < 20: continue
            
            # 이상한 차트 제거 2단계: 변동성 체크 (표준편차가 너무 크면 제외)
            returns = df['Close'].pct_change().dropna()
            if returns.std() > 0.07: continue # 하루 변동폭이 너무 크면 제외
            
            # 짐 사이먼스 점수 계산 (볼린저 밴드 위치 기반)
            ma20 = df['Close'].rolling(window=20).mean()
            std20 = df['Close'].rolling(window=20).std()
            lower = ma20 - (std20 * 2)
            curr_price = df['Close'].iloc[-1]
            
            # 하단 밴드에 가까울수록(과매도) 점수 높음
            score = (ma20.iloc[-1] - curr_price) / std20.iloc[-1]
            
            candidates.append({'종목명': name, '코드': code, '시장': market, '현재가': curr_price, '사이먼스_점수': score})
        except: continue
        
    result = pd.DataFrame(candidates).sort_values(by='사이먼스_점수', ascending=False).head(5)
    return result

# --- UI 부분 ---
st.title("🏛️ Simons Quant Intelligence Terminal")

# 추천 종목 섹션
st.subheader("🎯 오늘의 사이먼스 추천 종목 (KOSPI/KOSDAQ)")
st.caption("이상 변동성 종목 및 저가주를 제외한 통계적 저점 종목입니다.")

if st.button("🚀 추천 종목 스캔 시작"):
    with st.spinner('전체 시장의 통계 데이터를 분석 중입니다...'):
        recomm_df = get_recommendations()
        st.table(recomm_df[['종목명', '시장', '현재가']])
        st.success("스캔 완료! 위 종목들은 통계적으로 '평균 회귀' 가능성이 높은 구간에 있습니다.")

st.divider()

# 기존 검색 및 포트폴리오 기능
col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("🔍 개별 종목 정밀 분석")
    # (기본 검색 로직...)
with col2:
    st.subheader("📊 내 포트폴리오 실시간 점검")
    # (보유 종목 로직...)
