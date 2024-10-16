from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
import streamlit as st 
import re 



llm = ChatOllama(model='llama3.1')


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an AI chatbot having a conversation with a human. Use the following context to understand the human question. Answer only in Korean if I don't ask for an answer in a specific language. Do not answer the fake answer.",
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ]
)

chain = prompt | llm

history = StreamlitChatMessageHistory()

chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: history,
    input_messages_key='input',
    history_messages_key='chat_history'
)

st.title("Llama3 Q&A")
            
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    
for content in st.session_state.chat_history:
    with st.chat_message(content['role']):
        st.markdown(content['message'])


def is_web_page(url):
    pattern = r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Mo-z0-9.-][^<>]{2,12}$"
    if re.match(pattern, url):
        return True
    else:
        return False


if question := st.chat_input("메세지를 입력하세요."):
    
    if is_web_page(question):
        print()
    else:
        # display user message in chat message container
        with st.chat_message("user"):
            st.markdown(question)
            st.session_state.chat_history.append(
                {'role':'user', 'message':question}
            )
            
        # add question to conversations
        llm = ChatOllama(model='llama3')
        response = chain_with_history.invoke(
            {"input": question},
            config={"configurable": {"session_id": "any"}}
        )   # session_id determines thread
        
        # add answers to conversations
            
        # display assistant response in chat message container
        with st.chat_message('assistant'):
            st.markdown(response.content)
            # add assistant response to chat history
            st.session_state.chat_history.append(
                {'role':'assistant', 'message':response.content}
            )