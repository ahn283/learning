from typing import TypedDict

# Define the state for product recommendation
class RecommendationState(TypedDict):
    user_id: str            # User identifier
    preference: str         # User's current preference (e.g., genre, category)
    reasoning: str          # Reasoning process from LLM
    recommendation: str     # Final product recommendation
    memory: str             # User memory to store preferences

# Define recommendation tools
from langchain_core.tools import tool

# Tool function: Recommend a product based on the user's preference
@tool
def recommend_product(preference: str) -> str:
    """Recommend a product based on user's preferences."""
    product_db = {
        "science":"I recommend 'A breif History of Time' by Stephen Hawking.",
        "technology":"I recommend 'The innovators' by Walter Issacson.",
        "fiction":"I recommend 'The Alchemist' by Paulo Coello."
    }
    return product_db.get(preference, "I recommend exploring our latest products!")

# Initialize the LLM
from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage, SystemMessage
import keyring

OPENAI_API_KEY = keyring.get_password('openai', 'key_for_windows')
llm = ChatOpenAI(model='gpt-4o-mini', api_key=OPENAI_API_KEY)

# Bind the tools to the LLM
llm = llm.bind_tools([recommend_product])

# Tool function: Update the user's memory with the latest preference
def update_memory(state: RecommendationState):
    # Store the user's preference in the memory
    state["memory"][state["user_id"]] = state["preference"]
    return state


# Define Tool execution node
import json
from langchain_core.messages import ToolMessage

# Tool node to handle product recommendation
def tool_node(state: RecommendationState):
    tool_result = recommend_product.invoke({"preference":state["preference"]})
    return {
        "messages": [
            ToolMessage(
                content=json.dumps(tool_result),
                name="recommend_product",
                tool_call_id="recommendation_call"
            )
        ]
    }
    
# Define the LLM Reasoning node
from langchain_core.runnables import RunnableConfig

# LLM reasoning node to process user input and generate product recommendations
def call_model(state: RecommendationState, config: RunnableConfig):
    system_prompt = SystemMessage(
        content=f"You are a helpful assistant. Recommend a product based on the user's preference for {state['preference']}."
    )
    response = llm.invoke([system_prompt], config)
    print(response.content)
    # state["reasoning"] = response["message"]
    state['reasoning'] = response.content
    return {"messages":[response]}

# Conditional function to determine whether to call the tool or end
def should_continue(state: RecommendationState):
    last_message = state["reasoning"]
    if "recommend a product" in last_message:
        return "continue"
    else:
        return "end"
    
# Build the StateGraph
from langgraph.graph import StateGraph, END, START

workflow = StateGraph(RecommendationState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_node("memories", update_memory)
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue":"tools",
        "end":END
    },
)
workflow.add_edge("tools", "memories")
workflow.add_edge("memories", "agent")

# Compile the graph
graph = workflow.compile()

# Visualize the graph
from display_graph import display_graph
display_graph(graph)

# Initialize the agent's state with the user's preference and memory
initial_state = {
    "user_id":"user123",
    "preference":"science",
    "reasoning":"",
    "recommendation":"",
    "memory":{}
}

# Run the graph
result = graph.invoke(initial_state)

# Display the final result
print(f"Reasoning:{result['reasoning']}")
print(f"Product Recommendation: {result['messages'][-1].content}")
print(f"Updated Memory: {result['memory']}")