# Import libraries
import operator 
import os
import keyring
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from typing import Annotated, List, Tuple, TypedDict, Union
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from display_graph import display_graph

# Define diagnostic and action tools
@tool
def check_cpu_usage():
    """Simulate checking the CPU usage."""
    return "CPU Usage is 85%."

@tool
def check_disk_space():
    """Simulate checking the disk space."""
    return "Disk space is 10% free."

@tool
def check_network():
    """Simulate checking network connectivity."""
    return "Network connectivity is stable."

@tool
def restart_server():
    """Simulate restarting the server."""
    return "Server restarted sucessfully."

# Setup Tools
tools = [check_cpu_usage, check_disk_space, check_network, restart_server]

# Setup the model and agent executor
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an IT diagnostics agent."),
        ("placeholder", "{messages}")
    ]
)

# Initiate model
os.environ['OPENAI_API_KEY'] = keyring.get_password('openai', 'key_for_windows')
llm = ChatOpenAI(model='gpt-4o-mini')
agent_executor = create_react_agent(llm, tools, state_modifier=prompt)

# Define the Plan and Execution structure
class PlanExecute(TypedDict):
    input: str
    plan: List[str]
    past_steps: Annotated[List[Tuple], operator.add]
    response: str
    
class Plan(BaseModel):
    steps: List[str] = Field(description="Tasks to check and resolve server issues")

class Respone(BaseModel):
    response: str
    
class Act(BaseModel):
    action: Union[Respone, Plan] = Field(description="Action to perform. If you want to respond to user, user Response."
                                         "If you need further use tools to get the answer, use Plan.")
    
# Planning step
planner_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """For the given server issue, create a step-by-step diagnostic plan including CPU, disk, and network checks, followed by a server restart if necessary."""),
        ("placeholder", "{messages}")
    ]
)
planner = planner_prompt | ChatOpenAI(model='gpt-4o-mini', temperature=0).with_structured_output(Plan)

# Replanning step
replanner_prompt = ChatPromptTemplate.from_template(
    """For the given task, update the plan based on the current results:
    
    Your original task was:
    {input}
    
    You have completed the following steps:
    {past_steps}
    
    Update the plan accordingly. Only include the remaining tasks. If the server needs to be restarted, include that in the plan.
    """
)

replanner = replanner_prompt | ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(Act)


# Execute step function
async def execute_step(state: PlanExecute):
    plan = state['plan']
    task = plan[0]
    task_formatted = f"Executing step: {task}."
    agent_response = await agent_executor.ainvoke({"messages": [("user", task_formatted)]})
    return {
        "past_steps": [(task, agent_response["messages"][-1].content)],
    }
    
# Planning step function
async def plan_step(state: PlanExecute):
    plan = await planner.ainvoke({"messages": [("user", state['input'])]})
    return {"plan": plan.steps}

# Re-planning step function (in case execution needs adjustment)
async def replan_step(state: PlanExecute):
    output = await replanner.ainvoke(state)
    
    # If the replanner decides to return a response, we use it as the final answer
    if isinstance(output.action, Respone):              # Final response provided
        return {"response": output.action.response}     # Return the response to the user
    else:
        # Otherwise, we continue with the new plan (if planning suggests more steps)
        return {"plan": output.action.steps}

# Conditional check for ending
def should_end(state: PlanExecute):
    if "response" in state and state["response"]:
        return END
    else:
        return "agent"
    
# Build the workflow
workflow = StateGraph(PlanExecute)
workflow.add_node("planner", plan_step)
workflow.add_node("agent", execute_step)
workflow.add_node("replan", replan_step)

# Add edges to transition between nodes
workflow.add_edge(START, "planner")
workflow.add_edge("planner", "agent")
workflow.add_edge("agent", "replan")
workflow.add_conditional_edges(
    "replan",
    should_end,
    ["agent", END]
)

# Compile the workflow into an executable application
app = workflow.compile()

# Visualize the graph
display_graph(app)

# Example of running the agent
config = {"recursion_limit": 50}

import asyncio

# Function to run the Plan-and-Execute agent
async def run_plan_and_execute():
    # Input from the user
    inputs = {"input": "Diagnose the server issue and restart if necessary."}
    
    # Run the Plan-and-Execute agent asynchronously
    async for event in app.astream(inputs, config=config):
        print(event)

# Run the async function
if __name__ == "__main__":
    asyncio.run(run_plan_and_execute())