from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict

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

# Initialize the checkpointer
checkpointer = MemorySaver()
graph = worklfow.compile(checkpointer=checkpointer)

# Run the graph with thread_id and capture checkpoints
config = {"configurable": {"thread_id":"1"}}
graph.invoke({"foo":"", "bar":[]}, config)
state_history = graph.get_state_history(config)
print("Get history")
for snapshot in state_history:
    print(snapshot.values)

print("----")
print(f"Current state: {graph.get_state(config).values}")