import keyring
import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from langchain_community.chat_models import ChatOllama


OPENAI_API_KEY = keyring.get_password('openai', 'key_for_windows')
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY


# Llama llm model
llm_llama = ChatOllama(model='llama3.1')

# OpenAI llm model
llm = ChatOpenAI(model='gpt-4o', api_key=OPENAI_API_KEY)

# text loader
loader = TextLoader('./data/ai-discussion.txt', encoding='UTF-8')
documents = loader.load()

# chunking
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = text_splitter.split_documents(documents)

# embedding
embeddings = OpenAIEmbeddings(openai_api_type=OPENAI_API_KEY)

# embedding model for Hugguingface
model_id_huggingface = 'intfloat/multilingual-e5-large-instruct'
# model_id_huggingface = 'BAAI/bge-m3'
embeddings_huggingface = HuggingFaceEmbedding(model_name=model_id_huggingface)

# vector database
vectore_store = Chroma.from_documents(chunks, embeddings)

# retriver
retriever = vectore_store.as_retrieVer()

# prompts
system_prompt = (
    "You are an assistant for question-answering tasks. ",
    "Use the following pieces of retrieved context to answer "
    "the question. If you don't know the answer, say that you "
    "don't know. Use three sentences maximum and keep the "
    "answer concise."
    "\n\n"
    "{context}"
)
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

question = input("Ask Your Qeustion: ")
if question:
    response = rag_chain.invoke({"input": question})
    print(response["answer"])
 

