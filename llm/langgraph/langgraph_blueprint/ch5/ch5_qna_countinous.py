from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END
from display_graph import display_graph
import keyring
import os

# Load API key
OPENAI_API_KEY = keyring.get_password('openai', 'key_for_windows')

# Initialize the LLM
model = ChatOpenAI(model='gpt-4o-mini', api_key=OPENAI_API_KEY)

# Node function to handle the user query and call the LLM
def call_llm(state: MessagesState):
    messages = state['messages']
    response = model.invoke(messages[-1].content)
    return {"messages": [response]}

# Define the graph
workflow = StateGraph(MessagesState)

# Add the node to call the LLM
workflow.add_node("call_llm", call_llm)

# Define the edges (start -> LLM -> end)
workflow.add_edge(START, "call_llm")
workflow.add_edge('call_llm', END)

# Compile the workflow
app = workflow.compile()

# Function to continuously take user input
def interact_with_agent():
    while True: 
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Ending the conversations.")
            break
        input_message = {
            "messages":[("human", user_input)]
        }       
        for chunk in app.stream(input_message, stream_mode="values"):
            chunk['messages'][-1].pretty_print()

# Start interacting with the agent
interact_with_agent()