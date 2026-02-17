import streamlit as st
import FinanceDataReader as fdr

st.title("💎 Sungjun's Quant App")
search = st.text_input("종목명 입력 (예: 삼성전자)")
if search:
    st.write(f"{search} 데이터를 불러오는 중입니다...")
