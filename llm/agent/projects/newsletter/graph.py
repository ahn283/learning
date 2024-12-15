from langgraph.graph import StateGraph, END, START
from state import State
from nodes import (
    search_keyword_news,
    generate_newsletter_theme,
    search_sub_theme_articles,
    write_newsletter_section,
    aggregate_results,
    edit_newsletter
)
import logging

logger = logging.getLogger(__name__)

def create_newsletter_graph(n_sections=5):
    logger.info('Creating newsletter graph')
    workflow = StateGraph(State)
    
    # add nodes
    workflow.add_node("editor", edit_newsletter)
    workflow.add_node('search_news', search_keyword_news)
    workflow.add_node('generate_theme', generate_newsletter_theme)
    workflow.add_node('search_sub_themes', search_sub_theme_articles)
    workflow.add_node('aggregate', aggregate_results)
    
    workflow.add_edge('aggregate', 'editor')
    workflow.add_edge('editor', END)
    
    # graph nodes
    for i in range(n_sections):
        node_name = f"write_section_{i}"
        workflow.add_node(node_name, lambda s, i=1: write_newsletter_section(s, s['newsletter_theme'].sub_themes[i]))
        
    # connect edges
    workflow.add_edge(START, "search_news")
    workflow.add_edge("search_news", "generate_theme")
    workflow.add_edge('generate_theme', 'search_sub_themes')
    for i in range(n_sections):
        workflow.add_edge("search_sub_themes", f"write_section_{i}")
        workflow.add_edge(f"write_section_{i}", "aggregate")   
        
    logger.info("Newletter graph created successfully")
    return workflow.compile()