from langgraph.graph import StateGraph, START
from langchain.agents import AgentState, create_agent
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv   
from typing import Literal

from .tools.slow_charge_tool import simulate_slow_charge
from .tools.simulation_tools import run_simulation, remove_edge
from .prompts.prompt import prompt
from .state import SimulationState
from datetime import datetime

load_dotenv()

def make_graph(
    checkpointer=None,
    plot_graph=False
) -> StateGraph:
    """
    Builds the graph and compiles it.

    Args: 
        checkpointer: Checkpointer object
        plot_graph: Whether to plot the graph

    Returns:
        StateGraph: The compiled graph
    """

    # instantiate the agent
    agent = create_agent(
        model=ChatOpenAI(model="gpt-4.1-mini", temperature=0.0),
        tools=[simulate_slow_charge, run_simulation, remove_edge],
        system_prompt=prompt,
        state_schema=SimulationState
    )

    # define nodes
    async def invoke_agent(state : SimulationState) -> Command[Literal['__end__']]:
        """
        Node that simply invokes the agent
        """
        result = await agent.ainvoke(state)
        last_msg_content = result['messages'][-1].content

        return Command(
            update={"messages": [HumanMessage(content=last_msg_content)]}
        )

    # build graph
    builder = StateGraph(SimulationState)
    builder.add_node("mobility agent", invoke_agent)
    builder.add_edge(START, "mobility agent")

    graph = builder.compile(checkpointer=checkpointer)

    if plot_graph == True:
        img_bytes = graph.get_graph().draw_mermaid_png()
        from pathlib import Path
        output_dir = Path("graph_plot")
        output_dir.mkdir(exist_ok=True)
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = output_dir / f"supervised_{timestamp}.png"
        # Write bytes to file
        with open(filename, 'wb') as f:
            f.write(img_bytes)
        print(f"Graph saved to {filename}")

    return graph 