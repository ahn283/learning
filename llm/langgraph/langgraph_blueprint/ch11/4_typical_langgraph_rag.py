import asyncio
from typing import TypedDict, List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import os
import keyring
from display_graph import display_graph


# OPENAI_API_KEY
OPENAI_API_KEY = keyring.get_password('openai', 'key_for_mac')

# Set up LangSmith observability
os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_ENDPOINT'] = "https://api.smith.langchain.com"
os.environ['LANGCHAIN_API_KEY'] = keyring.get_password('langsmith', 'learning_agent')
os.environ['LANGCHAIN_PROJECT'] = "pr-stupendous-hood-8"

#1. Index 3 websites by adding them to a vector DB
urls = [
    "https://github.com/facebookresearch/faiss",
    "https://github.com/facebookresearch/faiss/wiki",
    "https://github.com/facebookresearch/faiss/wiki/Faiss-indexes"
]

docs = [WebBaseLoader(url).load() for url in urls]
docs_list = [item for sublist in docs for item in sublist]
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=250, chunk_overlap=0
)
doc_splits = text_splitter.split_documents(docs_list)
vectorstore = Chroma.from_documents(
    documents=doc_splits,
    collection_name="rag-chroma",
    embedding=OpenAIEmbeddings(api_key=OPENAI_API_KEY),
)
retriever = vectorstore.as_retriever()

#2. Prepare the RAG chain
prompt = ChatPromptTemplate.from_template(
    """ 
    You are an assistant for question-answering tasks.
    Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know.
    Use three sentences maximum and keep the answer concise.
    Question: {question}
    Context: {context}
    Answer:
    """
)

model = ChatOpenAI(model='gpt-4o-mini', api_key=OPENAI_API_KEY, temperature=0)
rag_chain = (
    prompt |model |StrOutputParser()
)

#3. Define the graph
class GraphState(TypedDict):
    """ 
    Represents the state of our graph.
    
    Attributes:
        question: question
        generation: LLM generation
        documents: list of documents
    """
    question: str
    generation: str
    web_search: str
    documents: List[str]
    
# Retrieve node
def retrieve(state):
    """ 
    Retrieve documents
    Args:
        state(dict): The current graph state
    Returns:
        state(dict): New key added to state, documents, that contains retrieved documents
    """
    print("--RETRIEVE--")
    question = state['question']
    
    # Retrieval
    documents = retriever.invoke(question)
    return {"documents": documents, "question": question}

#5. Generate node
def generate(state):
    """ 
    Generate answer
    Args:
        state(dict): The current graph state
    Returns:
        state(dict): New key added to state, generation, that contains LLM generation
    """
    print("---GENERATE---")
    question = state['question']
    documents = state['documents']
    
    # RAG generation
    generation = rag_chain.invoke({"context": documents, "question": question})
    return {"documents": documents, "question": question, "generation": generation}

#6. Define the workflow
def create_workflow():
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("generate", generate)
    
    # Add edges
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    return workflow.compile(checkpointer=MemorySaver())

#7. Run the workflow
async def run_workflow():
    app = create_workflow()
    
    # Visualize the graph
    display_graph(app)
    
    config = {
        "configurable": {"thread_id": "1"},
        "recursion_limit": 50
    }
    inputs = {"question": f"What are flat indexs?"}
    
    try:
        async for event in app.astream(inputs, config=config, stream_mode="values"):
            if "errors" in event:
                print(f"Error: {event['error']}")
                break
            print(event)
    except Exception as e:
        print(f"Workflow execution failed: {str(e)}")
        
if __name__ == "__main__":
    asyncio.run(run_workflow())