import streamlit as st 
import pandas as pd 
from pymongo import MongoClient

client = MongoClient(host='localhost', port=27017)
db = client['test']
collection = db['NewsAnalysis']

data = list(collection.find())

sentiments = []
for item in data:
    sentiments.extend(item['sentiments'])
    
df = pd.DataFrame(sentiments)

# x-axis : date
df['seendate'] = pd.to_datetime(df['seendate'])

# title
st.title("기업별 날짜에 따른 감성 지수 변화")

# select org
organization = st.selectbox("Select org.", ['Microsoft', 'Apple', 'Tesla'])

# data filtering
selected_df = df.loc[df['organization'] == organization].set_index('seendate')

# sentiment analysis chart
st.line_chart(selected_df[['positive', 'negative', 'neutral']])