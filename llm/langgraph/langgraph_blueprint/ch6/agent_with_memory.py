from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END
import os 
import keyring
from display_graph import display_graph
from langgraph.checkpoint.memory import MemorySaver

# Load API Key
OPENAI_API_KEY = keyring.get_password('openai', 'key_for_windows')

# Intialize the LLM
model = ChatOpenAI(model='gpt-4o-mini', api_key=OPENAI_API_KEY)

# Node function to handle the user query and call the LLM
# Update node function to invoke all messages to give the LLM context
def call_llm(state: MessagesState):
    messages = state['messages']
    # response = model.invoke(messages[-1].content)
    response = model.invoke(messages)
    return {"messages": [response]} 

# Intitialize the checkpinter for short-term memory
checkpointer = MemorySaver()

# Define the graph
workflow = StateGraph(MessagesState)

# Add the node to call the LLM
workflow.add_node('call_llm', call_llm)

# Define the edges (start -> LLM -> end)
workflow.add_edge(START, "call_llm")
workflow.add_edge('call_llm', END)

# Compile the workflow with short-term memory
app_with_memory = workflow.compile(checkpointer=checkpointer)

# Visualize the graph
display_graph(app_with_memory)

# Function to continuously take user input
def interact_with_agent_with_memory():
    # Use a thread ID to simulate a continuous session
    thread_id = "session_1"
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print('Ending the conversation.')
            break
        input_message = {
            "messages": [("human", user_input)]
        }
        
        # Invoke the graph with short-term memory enabled
        config = {"configurable": {"thread_id": thread_id}}
        for chunk in app_with_memory.stream(input_message, config=config, stream_mode="values"):
            chunk["messages"][-1].pretty_print()
            
# Start interacting with the agent
interact_with_agent_with_memory()