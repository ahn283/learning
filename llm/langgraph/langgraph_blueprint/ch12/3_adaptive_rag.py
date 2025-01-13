import os
import keyring
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from typing import Literal, TypedDict, List
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.schema import Document
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END
from pprint import pprint
from display_graph import display_graph


# API KEY
OPENAI_API_KEY = keyring.get_password('openai', 'key_for_mac')
TAVILY_API_KEY = keyring.get_password('tavily', 'key_for_mac')
os.environ['TAVILY_API_KEY'] = TAVILY_API_KEY
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

# Set up LangSmith observability
os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_ENDPOINT'] = "https://api.smith.langchain.com"
os.environ['LANGCHAIN_API_KEY'] = keyring.get_password('langsmith', 'learning_agent')
os.environ['LANGCHAIN_PROJECT'] = "pr-stupendous-hood-8"

### Step 1. Building the Index
# Define documents for indexing
urls = [
    "https://lilianweng.github.io/posts/2023-06-23-agent/",
    "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
    "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/"
]

# Load and split documents
docs = [WebBaseLoader(url).load() for url in urls]
docs_list = [item for sublist in docs for item in sublist]
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500)
doc_splits = text_splitter.split_documents(docs_list)

# Store documents in a vector database (Chroma)
vectorstore = Chroma.from_documents(
    doc_splits, collection_name="adaptive-rag",
    embedding=OpenAIEmbeddings(api_key=OPENAI_API_KEY)
) 
retriever = vectorstore.as_retriever()

### Step 2. Query Routing
# Define routing model
class RouteQuery(BaseModel):
    datasource: Literal["vectorstore", "web_search"]

route_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert at routing a user question to vectorstore or web search."),
    ("human", "{question}")
])

question_router = route_prompt | ChatOpenAI(model='gpt-4o-mini', temperature=0).with_structured_output(RouteQuery)

### Step 3. Retrieval Grader and Self-Correction
class GradeDocuments(BaseModel):
    binary_score: str = Field(description="Documents are relevant to the question, 'yes' or 'no'")
    
grade_prompt = ChatPromptTemplate.from_messages([
    ("system", "Evaluate if the document is relevant to the question. Answer 'yes' or 'no'."),
    ("human", "Document: {document} \nQuestion: {question}")
])

retrieval_grader = grade_prompt | ChatOpenAI(model='gpt-4o-mini', temperature=0).with_structured_output(GradeDocuments)

### Step 4. Web Search and RAG Generation
web_search_tool = TavilySearchResults(k=3)
def web_search(state):
    search_result = web_search_tool.invoke({"query":state["question"]})
    web_documents = [Document(page_content=result["content"])
                     for result in search_result if "content" in result]
    return {"documents":web_documents, "question":state["question"]}

### Step 5. Decision-Making Login and Workflow Graph
# Define adaptive RAG State
class GraphState(TypedDict):
    question: str
    generation: str
    documents: List[str]

def generate(state):
    prompt_template = """ 
        Use the following context to answer the question concisely and accurately:
        Question: {question}
        Context: {context}
        Answer:
    """
    
    # Define ChatPromptTemplate using the above template
    rag_prompt = ChatPromptTemplate.from_template(prompt_template)
    
    # Create the RAG generation chain with LLM and output parsing
    rag_chain = (
        rag_prompt |
        ChatOpenAI(model='gpt-4o-mini', temperature=0,api_key=OPENAI_API_KEY) |
        StrOutputParser()
    )
    generation = rag_chain.invoke({"context":state["documents"], "question":state["question"]})
    return {"generation": generation}

def grade_documents(state):
    question = state['question']
    documents = state['documents']
    filtered_docs = []
    web_search_needed = "No"
    for doc in documents:
        grade = retrieval_grader.invoke({"question":question, "document":doc.page_content}).binary_score
        
        if grade == 'yes':
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(doc)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
            web_search_needed = "Yes"
            
    return {"documents":filtered_docs, "question": question, "web_search": web_search_needed}

def retrieve(state):
    question = state['question']
    documents = retriever.invoke(question)
    return {"documents": documents, "question":question}

# Route question based on source
def route_question(state):
    source = question_router.invoke({"question":state["question"]}).datasource
    return "web_search" if source == "web_search" else "retrieve"

def decide_to_generate(state):
    """ 
    Determines whether to generate an answer, or re-generate a question.
    
    Args:
        state(dict): The current graph state
    Returns:
        str: Binary decision for next node to call
    """
    print("---ASSESS GRADED DOCUMENTS---")
    state['question']
    web_search = state['web_search']
    state['documents']
    if web_search == 'Yes':
        # All documents have been filtered check_relevance
        # We will re-generate a new query
        print("---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFROM QUERY---")
        return "transform_query"
    return "generate"

# Compile and run the Graph
workflow = StateGraph(GraphState)
workflow.add_node("web_search", web_search)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("retrieve", retrieve)
workflow.add_node("generate", generate)

workflow.add_conditional_edges(
    START,
    route_question,
    {"web_search": "web_search",
     "retrieve": "retrieve"}
)
workflow.add_edge("web_search", "generate")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_edge("grade_documents", "generate")
workflow.add_edge("generate", END)
app = workflow.compile()

# Visualize the graph
display_graph(app)

# Run the example inputs
inputs = {"question": "What are the types of agent memory?"}
for output in app.stream(inputs):
    print(output)