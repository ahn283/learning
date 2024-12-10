from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL
from langchain_community.tools.tavily_search import TavilySearchResults
import io
import keyring
import os
import base64
import matplotlib.pyplot as plt
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = keyring.get_password('openai', 'key_for_windows')
TAVILY_API_KEY = keyring.get_password('tavily', 'key_for_windows')
os.environ['TAVILY_API_KEY'] = TAVILY_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

class GenImageSchema(BaseModel):
    prompt: str = Field(description="The prompt for image generation")
    
@tool (args_schema=GenImageSchema)
def generate_image(prompt: str) -> str:
    """ 
    Generate an image using DALL-E based on the given prompt.
    """
    response = client.images.generate(
        model='dall-e-3',
        prompt=prompt,
        size='1024x1024',
        quality='standard',
        n=1
    )
    
    return f"Successfuly generated the image!, {response.data[0].url}"

repl = PythonREPL()

@tool
def data_visualization(code: str):
    """Execute Python code. Use matplotlib for visualization."""
    try:
        repl.run(code)
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        img_str = base64.b64decode(buf.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        return f"Error creating chart: {str(e)}"
    
@tool
def python_repl(code: str):
    """Execute Python code."""
    return repl.run(code)

search = TavilySearchResults(max_results=2)

def get_tools(retriever_tool=None):
    base_tools = [generate_image, search, python_repl, data_visualization]
    if retriever_tool:
        base_tools.append(retriever_tool)
    return base_tools