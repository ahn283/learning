import operator
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_openai import ChatOpenAI
import keyring
from typing import Annotated, TypedDict
import asyncio
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessageChunk, HumanMessage

# Define the state schema
class State(TypedDict):
    messages: Annotated[list, add_messages]
    
# Initialize the LLM
OPENAI_API_KEY = keyring.get_password('openai', 'key_for_windows')
model = ChatOpenAI(model='gpt-4o-mini', api_key=OPENAI_API_KEY)

# Define a node to handle LLM queries
async def call_llm(state: State):
    messages = state["messages"]
    response = await model.ainvoke(messages)
    return {"messages":[response]}

# Define the graph
workflow = StateGraph(State)
workflow.add_node("call_llm", call_llm)
workflow.add_edge(START, "call_llm")
workflow.add_edge("call_llm", END)

app = workflow.compile()

# Simulate interaction and stream tokens
async def simulate_interaction():
    input_messages = {"messages":[("human", "Tell me a short joke")]}
    first = True
    # Stream LLM tokens
    async for msg, metadata in app.astream(input_messages, stream_mode=["messages", "updates"]):
        print(metadata[0].content)
        if metadata[0].content:
            print(metadata[0].content, end="|", flush=True)

asyncio.run(simulate_interaction())