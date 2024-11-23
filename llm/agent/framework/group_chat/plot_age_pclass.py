# filename: plot_age_pclass.py
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 데이터셋 다운로드
url = "https://github.com/mwaskom/seaborn-data/raw/master/titanic.csv"
data = pd.read_csv(url)

# 데이터셋의 열 출력
print(data.columns.tolist())

# 'age'와 'pclass' 변수 간의 관계 시각화
plt.figure(figsize=(10, 6))
sns.boxplot(x='pclass', y='age', data=data)
plt.title('Age vs Pclass')
plt.xlabel('Pclass')
plt.ylabel('Age')
plt.savefig('age_vs_pclass.png')
plt.close()