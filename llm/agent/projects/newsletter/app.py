import streamlit as st 
import asyncio
from graph import create_newsletter_graph
import os 
import keyring

OPENAI_API_KEY = keyring.get_password('openai', 'key_for_windows')
TAVILY_API_KEY = keyring.get_password('tavily', 'key_for_windows')
ANTHROPIC_API_KEY = keyring.get_password('anthropic', 'key_for_windows')

os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
os.environ['TAVILY_API_KEY'] = TAVILY_API_KEY
os.environ['ANTHROPIC_API_KEY'] = ANTHROPIC_API_KEY

# Init Streamlit
st.title("AI Newletter generator")

keyword = st.text_input("Enter a keyword for the newsletter")
if keyword.strip == "":
    st.warning("Please enter a valid keyword")
    st.stop()
    
async def run_graph(inputs):
    graph = create_newsletter_graph()
    
    # create a stats container for progress tracking
    status_container = st.container()
    
    with status_container:
        col1, col2 = st.columns([2, 1])
        with col1:
            status_text = st.empty()
        with col2:
            progress_bar = st.progress(0)
            
        # create expandable status sections
        with st.expander("Detailed Progress", expanded=True):
            search_status = st.empty()
            theme_status = st.empty()
            subtheme_status = st.empty()
            write_status = st.empty()
            aggregate_status = st.empty()
            edit_status = st.empty()
            
    step = 0
    total_steps = 10    # total number of steps in our graph
    
    try:
        async for output in graph.astream(inputs):
            for key, value in output.items():
                step += 1
                progress_bar.progress(step / total_steps)
                status_text.text(f"Current Step: {key}")
                
                # update detailed status based on the current step
                if key == "search_news":
                    search_status.success("✓ Article search completed")
                elif key == "generate_theme":
                    theme_status.success("✓ Theme generation completed")
                elif key == "search_sub_theme":
                    subtheme_status.success("✓ Sub-theme research completed")
                elif key.startswith("write_section"):
                    write_status.success(f"✓ Section {key[-1]} written")
                elif key == 'aggregate':
                    aggregate_status.success("✓ Draft compilation completed")
                    # show draft in status container
                    with st.expander("Draft newletter", expanded=True):
                        st.markdown(value['messages'][0].content)
                elif key == "editor":
                    edit_status.success("✓ Final editing completed")
                    # show the final result outside status container
                    st.markdown("## Final Newsletter")
                    st.markdown(value['messages'][0].content)
                    
        status_text.success("Newsletter generation completed!")
        
    except Exception as e:
        status_text.error("Newsletter generation failed")
        with st.expander("Error Details"):
            st.error(f"An error occurred: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            
if st.button("Generate Newletter"):
    inputs = {"keyword": keyword}
    asyncio.run(run_graph(inputs))