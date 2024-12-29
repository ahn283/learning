from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
import keyring
from langgraph.checkpoint.memory import MemorySaver

# Define tools
def product_info(product_name: str) -> str:
    """Fetch product information"""
    product_catalog = {
        "iPhone 20": "The latest iPhone features an A15 chip and improve camera",
        "MacBook": "The new MacBook has an M2 chip and 14-inch Retina display."
    }
    
    return product_catalog.get(product_name, "Sorry, product not found.")

# Intialize the memory saver for single thread memory
checkpointer = MemorySaver()

# Initialize the language model
OPENAI_API_KEY = keyring.get_password('openai', 'key_for_windows')
llm = ChatOpenAI(model='gpt-4o-mini', api_key=OPENAI_API_KEY)

# Create the ReAct agent with the memory saver
graph = create_react_agent(model=llm, tools=[product_info], checkpointer=checkpointer)

# Set up thread configuration to simulate single-threaded memory
config = {"configurable": {"thread_id":"thread-1"}}

# User input: initial query
inputs = {"messages": [("user", "Hi, I'm James. Tell me about the new iPhone 20.")]}
messages = graph.invoke(inputs, config=config)

for message in messages["messages"]:
    message.pretty_print()
    
# User input: repeated inquiry (memory recall)
inputs2 = {"messages": [("user", "Tell me more about the iPhone 20.")]}
messages2 = graph.invoke(inputs2, config=config)

for message in messages2['messages']:
    message.pretty_print()