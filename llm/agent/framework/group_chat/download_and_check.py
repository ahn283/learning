# filename: download_and_check.py
import pandas as pd

# CSV 파일 다운로드
url = "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/titanic.csv"
df = pd.read_csv(url)

# 데이터셋의 열 출력
print(df.columns.tolist())