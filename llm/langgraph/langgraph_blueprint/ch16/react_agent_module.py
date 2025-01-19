from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import keyring
import os

# Define the state with query and markdown_result fields
class ReActAgentState(TypedDict):
    query: str
    search_results: List[str]
    markdown_result: str
    
# Initialize the ChatOpenAI for reasoning and web search
OPENAI_API_KEY = keyring.get_password('openai', 'key_for_mac')
llm_tool = ChatOpenAI(temperature=0, model='gpt-4o-mini', api_key=OPENAI_API_KEY)

# Node 1: Perform a web search based on a query
def perform_search(state: ReActAgentState) -> ReActAgentState:
    # Prompt for web search
    search_prompt = f"Search the web for information about: {state['query']}"
    search_message = HumanMessage(content=search_prompt)
    
    # Simulate search (replace with actual search API in production)
    search_response = llm_tool.invoke([search_message])
    state['search_results'] = search_response.content.split("\n")   # Simulate results as list
    return state

# Node 2: Filter relevant information
def filter_results(state: ReActAgentState) -> ReActAgentState:
    # Filtering relevant information based on prompt
    filter_prompt = "Select the most relevant information from the following list:\n" + "\n".join(state['search_results'])
    filter_message = HumanMessage(content=filter_prompt)
    
    # Reasoning steps to filter results
    filtered_response = llm_tool.invoke([filter_message])
    state['search_results'] = filtered_response.content.split("\n")
    return state

# Node 3: Compile Markdown document
def compile_markdown(state: ReActAgentState) -> ReActAgentState:
    # Compilation step to create a Markdown document
    compile_prompt = "Compile the following information into a Markdown document:\n" + "\n".join(state['search_results'])
    compile_message = HumanMessage(content=compile_prompt)
    
    # Generate the Markdown document
    markdown_response = llm_tool.invoke([compile_message])
    state['markdown_result'] = markdown_response.content
    return state

# Define the workflow
builder = StateGraph(ReActAgentState)
builder.add_node("perform_search", perform_search)
builder.add_node("filter_results", filter_results)
builder.add_node("compile_markdown", compile_markdown)
builder.add_edge(START, "perform_search")
builder.add_edge("perform_search", "filter_results")
builder.add_edge("filter_results", "compile_markdown")
builder.add_edge("compile_markdown", END)
grpah = builder.compile()

# Sample invocation with a query
initial_state = {"query": "Python programming best practices", "search_results": [], "markdown_result": ""}
result = grpah.invoke(initial_state)
print(result["markdown_result"])