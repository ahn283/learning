from typing import TypedDict, Literal
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from langchain_community.document_loaders import GithubFileLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings

from chromadb.config import Settings
import chromadb

from langgraph.graph import StateGraph, START, END
import os
import keyring

TAVILY_API_KEY = keyring.get_password('tavily', 'key_for_windows')
OPENAI_API_KEY = keyring.get_password('openai', 'key_for_windows')

os.environ['TAVILY_API_KEY'] = TAVILY_API_KEY
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

# state definition
class AgentState(TypedDict):
    """The state of our agent"""
    question: str 
    certainty_score: int        # LLM's centainty score
    search_results: list        # Web search results
    web_score: str              # whether web results can answer the question
    repo_name: str              # Github repository name
    generation: str
    github_chunks: list
    
llm = ChatOpenAI(model='gpt-4o-mini', temperature=0)

def check_certainty(state: AgentState) -> AgentState:
    """Evaluate certainty score for the query."""
    question = state['question']
    class CertaintyScoreResponse(BaseModel):
        score: int = Field(description="Certainty score from 1 to 100. Higher is better.")
    
    certainty_scorer = llm.with_structured_output(CertaintyScoreResponse)
    # get certainty score
    print("---CHECKING LLM'S CERTAINTY")
    score_response = certainty_scorer.invoke(question)
    
    return {
        "certainty_score": score_response.score
    }
    
def route_based_on_certainty(state: AgentState) -> Literal["web_search", "direct_response"]:
    """Route to appropriate node based on certainty score."""
    score = state['certainty_score']
    
    if score != 100:
        print("---LLM IS NOT CERTAIN SO IT WILL DO WEB SEARCH")
        return "web_search"
    else:
        print("---LLM IS CERTAIN SO IT WILL GENERATE ANSWER DIRECTLY")
        return "direct_response"
    
def direct_response(state: AgentState):
    question = state['question']
    result = llm.invoke(question)
    return {'generation': result.content}
