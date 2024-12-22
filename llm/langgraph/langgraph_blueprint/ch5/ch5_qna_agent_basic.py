from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END
import os 
import keyring
from display_graph import display_graph

# API KEY
OPENAI_API_KEY = keyring.get_password('openai', 'key_for_windows')
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

# Initialize the LLM model
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

# Define the edges(start -> LLM -> end)
workflow.add_edge(START, "call_llm")
workflow.add_edge("call_llm", END)

# Compile the workflow
app = workflow.compile()

# Example input message from the user
input_messages = {
    "messages": [
        ("human", "What is the capital of Kenya?")
    ]
}

# Run the workflow
for chunk in app.stream(input_messages, stream_mode='values'):
    chunk['messages'][-1].pretty_print()

# Visualize the graph
display_graph(app)
