from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_openai import ChatOpenAI
import asyncio
import keyring

# We ill disable streaming for a specific node while keeping it enabled for the rest of the graph
OPENAI_API_KEY = keyring.get_password('openai', 'key_for_windows')
llm = ChatOpenAI(model='o1-preview', temperature=1, disable_streaming=False, api_key=OPENAI_API_KEY)

# Define the graph
graph_builder = StateGraph(MessagesState)

def chatbot(state: MessagesState):
    return {"messages":[llm.invkoke(state["messages"])]}

# Add nodes and edges
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()

input = {"messages":{"role":"user", "content":"How many r's are in strawberry?"}}
try:
    for event in graph.stream_events(input, version="v2"):
        if event["event"] == "on_chat_model_end":
            print(event["data"]["output"].content, end="", flush=True)
except:
    print("Streaming not supported!")