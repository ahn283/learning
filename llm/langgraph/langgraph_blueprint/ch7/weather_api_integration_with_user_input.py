import requests
import os

# Load api_key
weather_api_key = "YOUR-OPENWEAHTER-API-KEY"

# Define the node to fetch live weather data modified for user input
def live_weather_node(state):
    last_message = state["messages"][-1].content.lower()
    
    # Extract city name from user query
    if 'in' in last_message:
        city = last_message.split("in")[-1].strip()
    else:
        city = "London" # Default city
        
    # API call
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api_key}&units=metric"
    
    # Make the API call
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temperature = data['main']['temp']
        description = data['weather'][0]['description']
        return {"messages": [f"The weather in {city} is {temperature}°C with {description}"]}
    else:
        return {"messages": ["Sorry,I couldn't fetch the weather information."]}
    
    
    
from langgraph.graph import StateGraph, MessagesState, START, END

# Define the graph workflow
builder = StateGraph(MessagesState)

# Add the weather node
builder.add_node("live_weather_node", live_weather_node)

# Set up the edges
builder.add_edge(START, "live_weather_node")
builder.add_edge("live_weather_node", END)

# Compile the graph
app = builder.compile()

# Simulate interaction with the weather API
def simulate_interaction():
    city = input("City: ")
    input_messages = {"messages":[("human", f"Tell me the weather in {city}")]}
    
    # Process the input and stream the result
    for result in app.stream(input_messages, stream_mode='values'):
        result["messages"][-1].pretty_print()
        
simulate_interaction()