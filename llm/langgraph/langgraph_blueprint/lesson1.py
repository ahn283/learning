from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables.graph import MermaidDrawMethod
from display_graph import display_graph

# Define the state structure
class HelloWorldState(TypedDict):
    greeting: str       # This key will store the greeting message
    
# Define the node function
def hello_world_node(state: HelloWorldState):
    state['greeting'] = "Hello world, " + state['greeting']
    return state

# Define an additional node function
def exlamation_nodes(state: HelloWorldState):
    state['greeting'] += "!"
    return state

# Initialize the graph and add the node
builder = StateGraph(HelloWorldState)
builder.add_node("greet", hello_world_node)
builder.add_node("exclaim", exlamation_nodes)

# Define the flow of execution using edges
builder.add_edge(START, "greet")    # Connect START to the 'greet' node
builder.add_edge("greet", "exclaim")    # Connet the 'greet' to 'exclaim'
builder.add_edge("greet", END)      # Connect the 'exclaim' node to END

# Compile and run the graph
graph = builder.compile()
result = graph.invoke({"greeting": "from Lang-Graph!"})

# Output the result
print(result)

# Visualize the graph
display_graph(graph)