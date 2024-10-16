from langchain_community.retrievers import BM25Retriever
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.retrievers import EnsembleRetriever
import transformers
import torch
import streamlit as st 

data = [
    {
        "기업명": "삼성전자",
        "날짜": "2024-03-02",
        "문서 카테고리": "인수합병",
        "요약": "삼성전자가 HVAC(냉난방공조) 사업 인수를 타진 중이며, 이는 기존 가전 사업의 약점 보완을 목적으로 한다.",
        "주요 이벤트": ["기업 인수합병"]
    },
    {
        "기업명": "삼성전자",
        "날짜": "2024-03-24",
        "문서 카테고리": "인수합병",
        "요약": "테스트 하나 둘 셋",
        "주요 이벤트": ["신제품 출시"]
    },
    {
        "기업명": "현대차",
        "날짜": "2024-04-02",
        "문서 카테고리": "인수합병",
        "요약": "삼성전자가 HVAC(냉난방공조) 사업 인수를 타진 중이며, 이는 기존 가전 사업의 약점 보완을 목적으로 한다.",
        "주요 이벤트": ["기업 인수합병", "신제품 출시"]
    },
]

doc_list = [item['요약'] for item in data]

# elastic search based retriever
bm25_retriever = BM25Retriever.from_texts(
    doc_list, metadatas=[{'source':i} for i in range(len(data))]
)
bm25_retriever.k = 1

# vector db faiss retriever
# with sentence-transformer embedding
embedding = SentenceTransformerEmbeddings(model_name='distiluse-base-multilingual-cased-v1')
faiss_vecorstore = FAISS.from_texts(
    doc_list, embedding, metadatas=[{'source': i} for i in data]
)
faiss_retriever = faiss_vecorstore.as_retriever(
    retriever=[bm25_retriever, faiss_vecorstore],
    weight=[0.5, 0.5]
)

# ensemble retriever
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, faiss_retriever], weights=[0.5, 0.5]
)

# sLLM name
model_name = '42dot/42dot_LLM-SFT-1.3B'

# check if cuda is available
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

pipeline = transformers.pipeline(
    'text-generation',
    model=model_name,
    device=device,
    model_kwargs={"torch_dtype": torch.float16}
)

# evaluation mode
pipeline.model.eval()

# revrieve docs
def retrieve(query):
    ensemble_docs = ensemble_retriever.invoke(query)
    return ensemble_docs

# sllm generation (output)
def sllm_generate(query):
    answer = pipeline(
        query,
        max_new_tokens=50,
        do_sample=True,
        temperature=0.9,
        repetition_penalty=1.2,
    )
    return answer[0]['generated_text'][len(query):]

# prompt and generation
def prompt_and_generation(query):
    docs = [doc for doc in retrieve(query)]
    prompt = f"""아래 질문을 기반으로 검색된 뉴스를 참고하여 질문에 대한 답변을 생성하시오.
    # 질문: {query} 
    """
    
    for i in range(len(docs)):
        prompt += f"뉴스{i+1}\n"
        prompt += f"요약: {docs[i].page_content}\n"
        prompt += "\n"
    prompt += "# 답변:"
    
    answer = sllm_generate(prompt)
    return answer

# streamlit ui

st.title("🤖 투자 어시스턴트")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])
        
if prompt := st.chat_input("궁금한 점을 물어보세요."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    response = f"bot: {prompt_and_generation(prompt.strip())}"
    
    with st.chat_message('assistant'):
        st.markdown(response)
    st.session_state.messages.append({'role': 'assistant', 'content': response})
