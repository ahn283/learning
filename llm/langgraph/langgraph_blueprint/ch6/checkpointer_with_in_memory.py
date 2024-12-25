from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.graph import StateGraph, MessagesState, START, END
from typing import TypedDict
import keyring
import os
import uuid
from langchain_core.runnables.config import RunnableConfig
from langchain.storage import BaseStore

# Define the state schema using TypedDict
class State(TypedDict):
    foo: str
    bar: list[str]

# Define node function to update the state
def node_a(state: State):
    return {"foo":"a", "bar":["a"]}

def node_b(state: State):
    return {"foo":"b", "bar":["b"]}

# Build the workflow graph
worklfow = StateGraph(State)
worklfow.add_node(node_a)
worklfow.add_node(node_b)
worklfow.add_edge(START, "node_a")
worklfow.add_edge("node_a", "node_b")
worklfow.add_edge("node_b", END)

# Initialize the checkpointer and memory store
checkpointer = MemorySaver()
in_memory_store = InMemoryStore()

# Compile the graph with both
graph = worklfow.compile(checkpointer=checkpointer, store=in_memory_store)

# Invoke the graph with thread_id and user_id
config = {"configurable":{"thread_id":"session_1", "user_id":"1"}}
graph.invoke({"foo":""}, config)

# Acess memory in a Node
def update_memory(state: MessagesState, config: RunnableConfig, *, store: BaseStore):
    user_id = config["configurable"]["user_id"]
    namespace = (user_id, "memories")
    
    # Store memory
    memory_id = str(uuid.uuid4())
    store.put(namespace, memory_id, ["favorite_food", "pizza"])
    
    # Retrieve stored memories
    memories = store.search(namespace)
    return {"messages":[f"I remember you like {memories[-1].value['favorite_food']}"]}