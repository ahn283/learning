from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END
import keyring
from typing import TypedDict
from display_graph import display_graph

# Define shared state for the agent and sub-graphs
class ReActAgentState(TypedDict):
    message: str        # Shared key between the parent graph and sub-graphs
    action: str         # Sub-graphs specific key (what action to perform)
    sub_action: str     # Additional sub-action to perform in a more complex scenario

# Reasoning Node I : Determine which action the agent should take based on the user query
def reasoning_node(state: ReActAgentState):
    query = state["message"]
    if "weather" in query:
        return {"action":"fetch_weather"}
    elif "news" in query:
        return {"action":"fetch_news"}
    elif "recommend" in query:
        return {"action":"recommendation", "sub_action":"book"}
    else:
        return {"action":"unknown"}
    
# Sub-graph for fetching weather information (acting phase)
def weather_subgraph_node(state: ReActAgentState):
    # Simulating a weather tool call
    return {"message":"The weather today is sunny."}

# Sub-graph for fetching news information (acting phase)
def news_subgrpah_node(state: ReActAgentState):
    # Simulate a news tool call
    return {"message":"Here are the latest news headlines."}

# Sub-graph for providing a book recommendation (acting phase)
def recommendation_subgrpah_node(state: ReActAgentState):
    if state.get("sub_action") == "book":
        return {"message":"I recommend reading 'The Pragmatic Programming'."}
    else:
        return {"message":"I have no other recommendation at the moment."}
    
# Build sub-graph for fetching weather information
weather_subgraph_builder = StateGraph(ReActAgentState)
weather_subgraph_builder.add_node("weather_action", weather_subgraph_node)
weather_subgraph_builder.set_entry_point("weather_action")
weather_subgraph = weather_subgraph_builder.compile()

# Build sub-graph for fetching news information
news_subgraph_builder = StateGraph(ReActAgentState)
news_subgraph_builder.add_node("news_action", news_subgrpah_node)
news_subgraph_builder.set_entry_point("news_action")
news_subgraph = news_subgraph_builder.compile()

# Build sub-graph for recommendation (e.g., book recommedation)
recommendation_subgraph_builder = StateGraph(ReActAgentState)
recommendation_subgraph_builder.add_node("recommendation_action", recommendation_subgrpah_node)
recommendation_subgraph_builder.set_entry_point("recommendation_action")
recommendation_subgraph = recommendation_subgraph_builder.compile()

# Define dynamic reasoning node in the parent graph to route to the correct sub-graph
def reasoning_state_manager(state: ReActAgentState):
    if state["action"] == "fetch_weather":
        return weather_subgraph
    elif state["action"] == "fetch_news":
        return news_subgraph
    elif state["action"] == "recommendation":
        return recommendation_subgraph
    else:
        return None
    
# Create the parent graph
parent_builder = StateGraph(ReActAgentState)
parent_builder.add_node("reasoning", reasoning_node)
parent_builder.add_node("action_dispatch", reasoning_state_manager)

# Define the edges in the parent graph
parent_builder.add_edge(START, "reasoning")
parent_builder.add_edge("reasoning", "action_dispatch")

# Compile the parent graph
react_agent_graph = parent_builder.compile()

# Visualize the graph
display_graph(react_agent_graph)
display_graph(weather_subgraph)
display_graph(news_subgraph)
display_graph(recommendation_subgraph)

# Test the agent with a weather-related query
inputs_weather = {"message":"What is the weather today?"}
result_weather = react_agent_graph.invoke(inputs_weather)
print(result_weather["message"])

# Test the agent with a news-related query
inputs_news = {"message":"Give me the latest news."}
result_news = react_agent_graph.invoke(inputs_news)
print(result_news["message"])

# Test the agent with a recommendation related query
inputs_recommendation = {"message":"Can you recommend a good book?"}
result_recommendation = react_agent_graph.invoke(inputs_recommendation)
print(result_recommendation["message"])