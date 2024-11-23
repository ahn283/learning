# filename: extract_keywords.py
import re

sentence = "The quick brown fox jumps over the lazy dog."
# 정규 표현식을 사용하여 단어를 추출하고 소문자로 변환
words = re.findall(r'\b\w+\b', sentence.lower())
# 중복 제거
keywords = set(words)
print(keywords)