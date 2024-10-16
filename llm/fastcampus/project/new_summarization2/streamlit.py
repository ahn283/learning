import streamlit as st  
import pandas as pd 

data = [
    {
        "org": "삼성전자",
        "date": "2024-03-02",
        "category": "인수합병",
        "summarization": "삼성전자가 HVAC(냉난방공조) 사업 인수를 타진 중이며, 이는 기존 가전 사업의 약점 보완을 목적으로 한다.",
        "events": ["기업 인수합병"]
    },
    {
        "org": "삼성전자",
        "date": "2024-03-24",
        "category": "인수합병",
        "summarization": "테스트 하나 둘 셋",
        "events": ["신제품 출시"]
    },
    {
        "org": "현대차",
        "date": "2024-04-02",
        "category": "인수합병",
        "summarization": "삼성전자가 HVAC(냉난방공조) 사업 인수를 타진 중이며, 이는 기존 가전 사업의 약점 보완을 목적으로 한다.",
        "events": ["기업 인수합병", "신제품 출시"]
    },
    # 추가 데이터 항목들...
]

df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])

st.sidebar.title("Filter option")
selected_compnay = st.sidebar.selectbox("Org. selection", df['org'].unique())
date_range = st.sidebar.date_input('Date', [df['date'].min().date(), df['date'].max().date()])

# date_range에서 받은 값을 start, end date로 변경
start_date = pd.to_datetime(date_range[0])
end_date = pd.to_datetime(date_range[1])

# 기업명과 날짜로 필터링
filtered_df = df[(df['org'] == selected_compnay) & (df['date'].between(start_date, end_date))]

# 필터링된 데이터 날짜로 그룹화
grouped_df = filtered_df.groupby('date').agg({
    'category': 'first',
    'events': 'first',
    'summarization': 'first',
}).reset_index()

# 결과를 테이블 형태로 표시
st.title(f"{selected_compnay}의 문서 목록")
st.dataframe(grouped_df[['date', 'category', 'events']])

# 요약 볼 수 있는 기능 추가
if st.checkbox("요약 보기"):
    for idx, row in grouped_df.iterrows():
        st.subheader(f"{row['date']} - {row['category']}")
        st.write(row['summarization'])