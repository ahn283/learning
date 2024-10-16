import keyring
from langchain import hub
import streamlit as st
from langchain.agents import create_react_agent, AgentExecutor
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain_openai import ChatOpenAI
import os


OPENAI_API_KEY = keyring.get_password('openai', 'key_for_windows')
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# LangSmithUserError: API key must be provided when using hosted LangSmith API
os.environ.pop("LANGCHAIN_TRACING_V2", None)

llm = ChatOpenAI(model='gpt-4o', api_key=OPENAI_API_KEY)
prompt = hub.pull("hwchase17/react")
tools = load_tools(['wikipedia', 'ddg-search', 'llm-math'], llm)
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

st.title("AI Agent")

question = st.chat_input("Give me a task:")
agent_executor.invoke({"input": question})
# if question:
#     with st.chat_message("user"):
#         st.markdown(question)
#     with st.chat_message("assistant"):
#         for response in agent_executor.stream({"input": question}):
#             # agent action
#             if "action" in response:
#                 for action in response["actions"]:
#                     st.write(f"Calling Tool : '{action.tool}' with input '{action.tool_input}'")
#             # observation
#             elif "steps" is response:
#                 for step in response["steps"]:
#                     st.write(f"Tool Result: '{step.observation}'")
#             # Final result
#             elif "output" in response:
#                 st.write(f'Final output: {response["output"]}')
#             else:
#                 raise ValueError()
#             st.write("---")