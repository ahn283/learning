from langgraph.graph import StateGraph, START, MessagesState
from nodes import create_chatbot
from tools import get_tools
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt import ToolNode

def create_agent(docs_info=None, retriever_tool=None):
    graph_builder = StateGraph(MessagesState)
    
    # when creating chatbot node, pass docs_info and retriever_tool
    chatbot_node = create_chatbot(docs_info, retriever_tool)
    graph_builder.add_node("chatbot", chatbot_node)
    
    # create tool node
    tool_node = ToolNode(tools=get_tools(retriever_tool))
    graph_builder.add_node("tools", tool_node)
    
    graph_builder.add_conditional_edges(
        "chatbot",
        tools_condition
    )
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge(START, "chatbot")
    graph = graph_builder.compile()
    return graph
    