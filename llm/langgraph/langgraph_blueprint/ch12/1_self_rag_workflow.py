import os
import keyring
from typing import TypedDict, List
from pydantic import BaseModel, Field
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END
from display_graph import display_graph

# OPENAI API
OPENAI_API_KEY = keyring.get_password('openai', 'key_for_mac')

# Set up LangSmith observability
os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_ENDPOINT'] = "https://api.smith.langchain.com"
os.environ['LANGCHAIN_API_KEY'] = keyring.get_password('langsmith', 'learning_agent')
os.environ['LANGCHAIN_PROJECT'] = "pr-stupendous-hood-8"

### Indexing documents

# List of URLs to retrieve documents from 
urls = [
    "https://lilianweng.github.io/posts/2023-06-23-agent/",
    "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
    "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/"
]

# Load documents and split into manageable chunks
docs = [WebBaseLoader(url).load() for url in urls]
docs_list = [item for sublist in docs for item in sublist]

# Split documents for improved retrieval
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=250, chunk_overlap=0
) 
doc_splits = text_splitter.split_documents(docs_list)

# Store documents in Chroma vector store
vectorstore = Chroma.from_documents(
    documents=doc_splits, collection_name="rag-chroma",
    embedding=OpenAIEmbeddings(api_key=OPENAI_API_KEY)
)
retriever = vectorstore.as_retriever()

# Set up prompt and model
prompt = ChatPromptTemplate.from_template(
    """ 
    Use the following context to answer the question concisely:
    Question: {question}
    Context: {context}
    Answer:
    """
)

model = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=OPENAI_API_KEY)

rag_chain = (prompt | model | StrOutputParser())

### Implementing Self-reflective Workflow Steps
# Define nodes for retrieval, generation, grading, and query transformation

class GraphState(TypedDict):
    question: str
    generation: str
    documents: List[str]
    
# Retrieval grader setup
class GradeDocuments(BaseModel):
    binary_score: str = Field(description="Documents are relevant to the quedtion, 'yes' or 'no'" )

retrieval_prompt = ChatPromptTemplate.from_template(
    """
    You are a grader assessing if a document is relevant to a user's question.
    Document: {document}
    Question: {question}
    Is the document relevant? Answer 'yes' or 'no'.
    """
)

retrieval_grader = retrieval_prompt | ChatOpenAI(model='gpt-4o-mini', temperature=0, api_key=OPENAI_API_KEY).with_structured_output(GradeDocuments)

# Hallucination grader setup
class GradeHallucinations(BaseModel):
    binary_score: str = Field(description="Answer is grounded in the documents, 'yes' or 'no'")

hallucination_prompt = ChatPromptTemplate.from_template(
    """ 
    You are a grader assessing if an answer is grounded in retrieved documents.
    Documents: {documents}
    Answer: {generation}
    Is the answer grounded in the documents?
    Answer 'yes' or 'no'.
    """
)

hallucination_grader = hallucination_prompt | ChatOpenAI(model='gpt-4o-mini', temperature=0, api_key=OPENAI_API_KEY).with_structured_output(GradeHallucinations)

# Answer greder setup
class GradeAnswer(BaseModel):
    binary_score: str = Field(description="Answer addresses the question, 'yes' or 'no'")

answer_prompt = ChatPromptTemplate.from_template(
    """ 
    You are a grader assessing if an answer addresses the user's question.
    Question: {question}
    Answer: {generation}
    Does the answer address the question? Answer 'yes' or 'no'.
    """
)

answer_grader = answer_prompt | ChatOpenAI(model='gpt-4o-mini', temperature=0, api_key=OPENAI_API_KEY).with_structured_output(GradeAnswer)

# Define LangGraph functions
def retrieve(state):
    question = state['question']
    documents = retriever.invoke(question)
    return {"documents": documents, "question": question}

def generate(state):
    question = state['question']
    documents = state['documents']
    generation = rag_chain.invoke({"context": documents, "question": question})
    return {"documents": documents, "question": question, "generation": generation}

def grade_documents(state):
    """ 
    Grades documents based on relevance to the question.
    Only relevant documents are retained in 'relevant_docs'.
    """
    question = state['question']
    documents = state['documents']
    relevant_docs = []
    for doc in documents:
        response = retrieval_grader.invoke({"question": question, "document": doc.page_content})
        if response.binary_score == 'yes':
            relevant_docs.append(doc)
    
    return {"document": relevant_docs, "question": question}

def decide_to_generate(state):
    """ 
    Decides whether to proceed with generation or transform the query.
    """
    if not state["documents"]:
        return "transform_query"        # No relevant docs found; rephrase query
    return "generate"       # Relevant docs found; proceed to generate

def grade_generation_v_documents_and_questions(state):
    """ 
    Checks if the generation is grounded in retrieved documents and answers the question.
    """
    question = state['question']
    documents = state['documents']
    generation = state['generation']
    
    # Step 1: Check if the generation is grounded in documents
    hallucination_check = hallucination_grader.invoke({"documents":documents, "generation": generation})
    
    if hallucination_check.binary_score == 'no':
        return "not supported"      # Regenerate if generation isn't grounded in documents
    
    # Step 2: Check if generation addresses the question
    answer_check = answer_grader.invoke({"question": question, "generation": generation})
    
    return "useful" if answer_check.binary_score == "yes" else "not useful"

def transform_query(state):
    """ 
    Rephrases the query for improved retrieval if initial attempts do not yield relevant documents.
    """ 
    transform_prompt = ChatPromptTemplate.from_template(
        """ 
        You are a question re-writer that converts an input question to a better version optimized for retrieving relevant documents.
        Original question: {question}
        Please provide a rephrased question.
        """
    )
    
    question_rewriter = transform_prompt | ChatOpenAI(model='gpt-4o-mini', temperature=0, api_key=OPENAI_API_KEY) | StrOutputParser()
    question = state['question']
    # Rephrase the question using LLM
    transformed_question = question_rewriter.invoke({"question": question})
    
    return {"question": transformed_question, "documents": state["documents"]}

# Set up the workflow graph
workflow = StateGraph(GraphState)
workflow.add_node("retrieve", retrieve)
workflow.add_node("generate", generate)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("transform_query", transform_query)
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate, 
    {"transform_query": "transform_query",
     "generate": "generate"}
)
workflow.add_edge("transform_query", "retrieve")
workflow.add_conditional_edges(
    "generate",
    grade_generation_v_documents_and_questions,
    {"not supported": "generate",
     "useful": END, 
     "not useful": "transform_query"}
)

# Compile the app and run
app = workflow.compile()

# Visualize the graph
display_graph(app)

# Example input
inputs = {"question": "Explain how the different types of agent memory work?"}

for output in app.stream(inputs):
    print(output)