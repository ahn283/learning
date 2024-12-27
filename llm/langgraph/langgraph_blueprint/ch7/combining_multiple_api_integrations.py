from langgraph.graph import StateGraph, MessagesState, START, END
import requests
import urllib

weather_api_key = "YOUR_OPENWEATHER_API_KEY"

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
    
# Define the Calculatgor Node
def calculator_node(state):
    last_message = state["messages"][-1].content.lower()
    
    # Extract the artithmetic expression from the user query
    expression = last_message.split("calculate")[-1].strip()
    
    # URL-encode the expression to ensure
    encoded_expression = urllib.parse.quote(expression)
    
    # Make the API call to math.js API with the URL-encoded expression
    url = f"http://api.mathjs.org/v4/?expr={encoded_expression}"
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.text
        return {"messages": [f"The result of {expression} is {result}"]}
    else:
        return {"messages": ["Sorry, I coundn't calcaulte that."]}


# Define the routing function
def routing_function(state):
    last_message = state['messages'][-1].content.lower()
    
    if "weather" in last_message:
        return "live_weather_node"
    elif "calculate" in last_message:
        return "calculator_node"
    return "default_node"

# Define the graph workflow
builder = StateGraph(MessagesState)

# Add the nodes
builder.add_node("live_weather_node", live_weather_node)
builder.add_node("calculator_node", calculator_node)
builder.add_node("default_node", lambda state: {"messages":["Sorry, I don't understand that request."]})

# Add conditional edges for routing
builder.add_conditional_edges(START, routing_function)

# Set up the edges
builder.add_edge("live_weather_node", END)
builder.add_edge("calculator_node", END)
builder.add_edge("default_node", END)

# Compile the graph
app = builder.compile()

# Simulate interaction with both APIs
def simulate_interaction():
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting...")
            break
        
        input_message = {"messages":[("human", user_input)]}
        
        # Stream the result
        for result in app.stream(input_message, stream_mode="values"):
            result["messages"][-1].pretty_print()
            
simulate_interaction()