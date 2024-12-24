from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END
import keyring
from display_graph import display_graph

# Define a tool to get the weather for a city
@tool
def get_weather(location: str):
    """Fetch the current weather for a specific location."""
    weather_data = {
        "San Francisco":"It's 60 degrees and foggy.",
        "New York":"It's 90 degrees and sunny.",
        "London":"It's 70 degrees and cloudy."
    }
    return weather_data.get(location, "Weather information is unavailable for this location.")

# llm model and bind tool
model = ChatOpenAI(model='gpt-4o-mini', api_key=keyring.get_password('openai', 'key_for_windows')).bind_tools([get_weather])

# # Bind tool
# model = model.bind_tools([get_weather])

# create a ToolNode with weather tool
tool_node = ToolNode([get_weather])

# Function to handle user queries and process LLM + tool results
def call_llm(state: MessagesState):
    messages = state['messages']
    # The LLM will decide if it should invoke a tool based on the user input
    response = model.invoke(messages[-1].content)
    
    # If the LLM generates a tool call, handle it
    if response.tool_calls:
        tool_results = tool_node.invoke({"messages": [response]})
        # Append the tool's output to the response message
        tool_message = tool_results['messages'][-1].content
        response.content += f"\nTool Results: {tool_message}"
        
    return {"messages": [response]}

# Create the LangGraph workflow
workflow = StateGraph(MessagesState)

# Add the LLM node to the workflow
workflow.add_node('call_llm', call_llm)

# Define edges to control the flow
workflow.add_edge(START, 'call_llm')
workflow.add_edge('call_llm', END)

# Compile the workflow
app = workflow.compile()

# Visualize the Graph
display_graph(app)

# Function to continuously take user input and decide between LLM and tool calls
def interact_with_agent():
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Ending the conversation.")
            break
        input_message = {
            "messages":[("human", user_input)]
        }
        for chunk in app.stream(input_message, stream_mode="values"):
            chunk['messages'][-1].pretty_print()

# Start interacting with the agent
interact_with_agent()