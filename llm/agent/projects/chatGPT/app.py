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