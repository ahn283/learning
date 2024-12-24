from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_openai import ChatOpenAI
import uuid
import os
import keyring

# Load API key
OPENAI_API_KEY = keyring.get_password('openai', 'key_for_windows')

# Initialize the LLM
model = ChatOpenAI(model='gpt-4o-mini', api_key=OPENAI_API_KEY)

# Initialize an in-memory store to store user information across sessions
in_memory_store = InMemoryStore()

# Function to store user information across session
def store_user_info(state: MessagesState, config, *, store=in_memory_store):
    user_id = config["configurable"]['user_id']
    namespace = (user_id, "memories")
    # Store user's name in memory
    memory_id = str(uuid.uuid4())
    user_name = state["user_name"]
    memory = {"user_name": user_name}
    
    # Save the memory in the in-memory store
    store.put(namespace, memory_id, memory)
    
    return {"messages": ["User information saved."]}

# Function to retrieve stored user information
def retrieve_user_info(state: MessagesState, config, *, store=in_memory_store):
    user_id = config["configurable"]["user_id"]
    namespace = (user_id, "memories")
    
    # Retrieve stored user info
    memories = store.search(namespace)
    if memories:
        info = f"Hello {memories[-1].value['user_name']}, welcome back!"
    else:
        info = "I don't have any information about you yet."
    return {"messages": [info]}

# Function to handle store or retrieving user info based on input
def call_model(state: MessagesState, config):
    last_message = state["messages"][-1].content.lower()
    
    if "remember my name" in last_message:
        # Store user's name in state and memory
        user_name = last_message.split("remember my name is")[-1].strip()
        state["user_name"] = user_name
        return store_user_info(state, config)
    if "what's my name" in last_message or "what is my name" in last_message:
        # Retrieve the user's name from memory
        return retrieve_user_info(state, config)
    
    # Default LLM response for other inputs
    return {"messages": ["I didn't understand your request."]}


# Build the LangGraph workflow
workflow = StateGraph(MessagesState)
workflow.add_node("call_model", call_model)
workflow.add_edge(START, "call_model")
workflow.add_edge("call_model", END)

# Compile the graph with memory management
app_with_memory = workflow.compile(checkpointer=MemorySaver(), store=in_memory_store)

# Simulate sessions
def simulate_session():
    # First session: store user's name
    config = {"configurable": {"thread_id":"session_1", "user_id":"user_123"}}
    input_message = {"messages":[{"type":"user", "content":"Remember my name is Alice"}]}
    for chunk in app_with_memory.stream(input_message, config=config, stream_mode="values"):
        chunk["messages"][-1].pretty_print()
        
    # Store session: retrieve user's name
    config = {"configurable": {"thread_id":"sessoin_2", "user_id":"user_123"}}
    input_message = {"messages": [{"type":"user", "content":"What is my name?"}]}
    for chunk in app_with_memory.stream(input_message, config=config, stream_mode="values"):
        chunk["messages"][-1].pretty_print()
        
# Run the session simulations
simulate_session()