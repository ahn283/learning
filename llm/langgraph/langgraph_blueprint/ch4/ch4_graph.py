from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from display_graph import display_graph

class HelloWorldState(TypedDict):
    """The state"""
    message: str    # This state key will store the message

def hello_world_node(state: HelloWorldState):
    """The node function"""
    state['message'] += "Hello World"   # This node does this simple task
    return state

# Define the graph
graph_builder = StateGraph(HelloWorldState)
graph_builder.add_node("hello_world", hello_world_node)
graph_builder.add_edge(START, "hello_world")
graph_builder.add_edge("hello_world", END)

# Compile and run the graph
graph = graph_builder.compile()
result = graph.invoke({"message":"Hi!"})

# Output the result
print(result)

# Visualize the result
display_graph(graph)