from langchain.agents import AgentState
from typing import Annotated

def str_replace(left: str | None, right: str | None) -> str | None:
    """
    Replace the left string with the right string.
    """
    if left is None:
        left = ""
    if right is None:
        right = ""
    return right

class SimulationState(AgentState):
    """
    State for the simulation agent.
    """
    edges_filepath: Annotated[str, str_replace]  # path to the edges file
    nodes_filepath: Annotated[str, str_replace]  # path to the nodes file
    output_dir: Annotated[str, str_replace]  # path to the output directory