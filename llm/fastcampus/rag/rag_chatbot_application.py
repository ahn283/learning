import streamlit as st      # !pip install streamlit    # for an app in this browser
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from decouple import config
from langchain.memory import ConversationBufferWindowMemory
import os
import keyring

OPENAI_API_KEY = keyring.get_password('openai', 'key_for_windows')
prompt = PromptTemplate(
    input_variables=['chat_history', 'question'],
    template=""" 
You are a AI assistant. You are currently having a conversation with a human. Answer the questions.

chat_history: {chat_history},
Human: {question}
AI:"""
)

llm = ChatOpenAI(
                api_key=OPENAI_API_KEY, 
                temperature=0, 
                model='gpt-4-0314'
                )

# 윈도우 크기 K를 지정하면 최근 K개의 대화만 기억하고 이전 대화는 삭제
memory = ConversationBufferWindowMemory(memory_key='chat_history', k=4)     # k개 대화만 기억

llm_chain = LLMChain(
    llm=llm,
    memory=memory,
    prompt=prompt
)

st.title("ChatGPT AI Assistant")

# 세션에서 메시지를 확인하고 존재하지 않는 경우 생성
if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {'role': 'assistant', 'content': '안녕하세요, 저는 AI Assistant입니다.'}
    ]

# 모든 메시지 표시
for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.write(message['content'])

user_prompt = st.chat_input()

# 사용자 입력 보여주기
if user_prompt is not None:
    st.session_state.messages.append({"role": "user", "content": user_prompt})      # append를 통해 대화 내용 계속 축적
    with st.chat_message("user"):
        st.write(user_prompt)

# 마지막 메시지가 assistant로부터 받은게 아니라면 새로운 답변 생성
if st.session_state.messages[-1]['role'] != 'assistant':        # 가장 최신 message가 누구인지 확인 -> assistant가 아니면 답변 진행
    with st.chat_message("assistant"):
        with st.spinner("Loading..."):
            ai_response = llm_chain.predict(question=user_prompt)
    new_ai_message = {"role": "assistant", "content": ai_response}
    st.session_state.messages.append(new_ai_message)
