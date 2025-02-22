import streamlit as st
import os
import keyring
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.messages import AIMessage, HumanMessage
from tool_calling_event import invoke_our_graph
import asyncio
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Optional, Tuple
from agent import create_agent
from langchain.tools.retriever import create_retriever_tool
import uuid
import chromadb

# chromadb 캐시 클리어
chromadb.api.client.SharedSystemClient.clear_system_cache()

# 환경 변수 로드
load_dotenv()
LANGCHAIN_API_KEY = keyring.get_password('langchain', 'key_for_windows')
os.environ['LANGCHAIN_API_KEY'] = LANGCHAIN_API_KEY
os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_ENDPOINT'] = "https://api.smith.langchain.com"

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [AIMessage(content="무엇을 도와드릴까요?")]
    if 'graph' not in st.session_state:
        st.session_state.graph = create_agent()
    if 'vectorstore' not in st.session_state:
        st.session_state.vectorstore = None
    if 'current_files_hash' not in st.session_state:
        st.session_state.current_file_hash = None
        
def get_files_hash(uploaded_files):
    """create hash value for uploaded files"""
    return hash(tuple(f.name + str(f.size) for f in uploaded_files))

def process_files(uploaded_files) -> Tuple[Optional[any], Optional[List[dict]]]:
    """  
    process uploaded files and return retrieved files
    """
    # calculate hash value of current files
    current_hash = get_files_hash(uploaded_files)
    
    # check if uploaded files are same as the processed files
    if (st.session_state.current_file_hash == current_hash and
        st.session_state.vectorstore is not None):
        st.write('기존 vectorstore 사용')
        
        retriever = st.session_state.vectorstore.as_retriever()
        test_results = retriever.get_relevant_documents('test query')
        st.write(f"Retriver test results: {len(test_results)} document found")
        
        file_names = ", ".join(f.name for f in uploaded_files)
        desciption = f"Search through the following documents: {file_names}"
        retriever_tool = create_retriever_tool(
            retriever,
            "search_docs",
            desciption,
        )
        return retriever_tool, st.session_state.docs_info
    st.write("새로운 vectorstore 생성")
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=500,
        chunk_overlap=0
    )
    
    all_docs = []
    docs_info = []
    
    for uploaded_file in uploaded_files:
        try:
            file_info = {
                "name": uploaded_file.name,
                "type": uploaded_file.type,
                "size": uploaded_file.size
            }
            
            if uploaded_file.type == "text/plain":
                text = uploaded_file.getValue().decode()
                docs = text_splitter.create_documents(
                    [text],
                    metadatas=[{"source": uploaded_file.name}]
                )
                all_docs.extend(docs)
                docs_info.append(file_info)
                
            elif uploaded_file.type == "application/pdf":
                with open("temp.pdf", "wb") as f:
                    f.write(uploaded_file.getvalue())
                loader = PyPDFLoader("temp.pdf")
                docs = loader.load_and_split()
                for doc in docs:
                    doc.metadata["source"] = uploaded_file.name
                docs = text_splitter.split_documents(docs)
                all_docs.extend(docs)
                docs_info.append(file_info)
                os.remove("temp.pdf")
            
            else:
                st.write(f"지원하지 않는 파일 형식입니다: {uploaded_file.type}")
        
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
            continue
        
    if all_docs:
        vectorstore = Chroma.from_documents(
            documents=all_docs,
            embedding=OpenAIEmbeddings(),
            collection_name=str(uuid.uuid4())
        )
        
        # save the vectorstore in the session state
        st.session_state.vectorstore = vectorstore
        st.session_state.current_file_hash = current_hash
        st.session_state.doc_info = docs_info
        
        retriver = vectorstore.as_retriever()
        file_names = ", ".join(d['name'] for d in docs_info)
        description = f"Search through the following documents: {file_names}"
        
        retriever_tool = create_retriever_tool(
            retriever,
            "search_docs",
            desciption,
        )
        
        return retriever_tool, docs_info
    
    return None, None

def format_doc_info(docs_info: List[dict]) -> str:
    """문서 정보를 포맷팅하여 문자열로 반환합니다."""
    upload_message = "📚 다음 문서들이 업로드되었습니다:\n"
    for doc in docs_info:
        file_type = "PDF" if "pdf" in doc['type'].lower() else 'Text'
        size_kb = doc['size'] / 1024
        upload_message += f"- {doc['name']} ({file_type}, {size_kb:.1f}KB)\n"
    upload_message += "\n이제 업로드된 문서들의 내용에 대해 질문해주세요!"
    return upload_message

# streamlit
st.title("LangGraph Chatbot")
initialize_session_state()

# OpenAI
OPENAI_API_KEY = keyring.get_password('openai', 'key_for_windows')
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

if not OPENAI_API_KEY:
    st.error("OpenAI API 키가 없습니다. env 파일에 API 키를 저장해주세요.")
    st.stop()
    
# file uploader for sidebar
with st.sidebar:
    st.header("📄 문서 업로드")
    uploaded_files = st.file_uploader(
        "Uploade documents",
        type=['text', 'pdf'],
        accept_multiple_files=True,
        help='Upload PDF or TXT'
    )
    if uploaded_files:
        with st.spinner("📝 문서 처리 중..."):
            retriever_tool, docs_info = process_files(uploaded_files)
            if retriever_tool and docs_info:
                # create a new graph
                st.session_state.graph = create_agent(docs_info, retriever_tool)
                st.success(f"✅ {len(uploaded_files)}개의 문서가 처리되었습니다!")
                
                # add a message for completing document upload
                upload_message = format_doc_info(docs_info)
                st.session_state.messages.append((AIMessage(content=upload_message)))
                
# chatting interface
for message in st.session_state.messages:
    with st.chat_message(message.type):
        st.write(message.content)
        
# user input
prompt = st.chat_input("메시지를 입력하세요.")

if prompt:
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message('user'):
        st.write(prompt)
    
    with st.chat_message("assistant"):
        placeholder = st.container()
        try:
            response = asyncio.run(invoke_our_graph(
                {"messages": st.session_state.messages}, 
                placeholder,
                st.session_state.graph  # 현재 세션의 그래프 전달
            ))
            st.session_state.messages.append(AIMessage(content=response))
        except RecursionError as e:
            error_message = f"⚠️ 너무 많은 재귀 호출이 발생했습니다: {str(e)}"
            st.error(error_message)
            st.session_state.messages.append(AIMessage(content=error_message))