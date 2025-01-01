from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import keyring
from display_graph import display_graph

# Define the state for the agent
class AgentState(TypedDict):
    """The state of the agent."""
    # 'add_messages' is a reducer that manages the message sequence.
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
from langchain_core.tools import tool
from textblob import TextBlob

# Define Sentiment Analysis Tool
@tool
def analyze_sentiment(feedback: str) -> str:
    """Analyze custom feedback sentiment with custom logic."""
    analysis = TextBlob(feedback)
    if analysis.sentiment.polarity > 0.5:
        return "positive"
    elif analysis.sentiment.polarity == 0.5:
        return "neutral"
    else:
        return "negative"

# Define Response Generation Tool    
@tool
def respond_based_on_sentiment(sentiment: str) -> str:
   """Respond to the customer based on the analyzed sentiment."""
   if sentiment == "positive":
       return "Thank you for your positive feedback!"
   elif sentiment == "neutral":
       return "We appreciate your feedback."
   else:
       return "We're sorry to hear that you're not satisfied. How can we help?"
   
# Bind the tools to the LLM
from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage, SystemMessage

tools = [analyze_sentiment, respond_based_on_sentiment]

# Initialize the LLM
OPENAI_API_KEY = keyring.get_password('openai', 'key_for_windows')
llm = ChatOpenAI(model='gpt-4o-mini', api_key=OPENAI_API_KEY)
llm = llm.bind_tools(tools)

# Create a dictionary of tools by their names for easy lookup
tools_by_name = {tool.name: tool for tool in tools}

# Define tool execution node
import json
from langchain_core.messages import ToolMessage

# Tool node to handle sentiment analysis and response generation
def tool_node(state: AgentState):
    outputs = []
    for tool_call in state["messages"][-1].tool_calls:
        tool_result = tools_by_name[tool_call["name"]].invoke(tool_call["args"])
        outputs.append(
            ToolMessage(
                content=json.dumps(tool_result),
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )
    return {"messages":outputs}

# Define the LLM Reasoning Node
from langchain_core.runnables import RunnableConfig

# LLM reasoning node to process the feedback and call tools if needed
def call_model(state: AgentState, config: RunnableConfig):
    system_prompt = SystemMessage(
        content="You are a helpful assistant tasked with responding to customer feedack."
    )
    response = llm.invoke([system_prompt] + state["messages"], config)
    return {"messages":[response]}

# Define state transitions
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    # If there is no tool call, then we finish
    if not last_message.tool_calls:
        return "end"
    else:
        return "continue"
    
# Build the StateGraph
from langgraph.graph import StateGraph, END, START

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue":"tools",
        "end": END,
    }
)
workflow.add_edge("tools", "agent")

# Compile the graph
graph = workflow.compile()

# Visualize the Graph
display_graph(graph)

# Initialize the agent's state with the user's feedback
initial_state = {"messages":[("user", "The product was great but the delivery was poor.")]}

# Helper function to print the conversation
def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()
            
# Run the agent
print_stream(graph.stream(initial_state, stream_mode="values"))