from langchain.agents import AgentState

class SimulationState(AgentState):
    """
    State for the simulation agent.
    """
    edges_filepath: str  # path to the edges file (no reducer because str_replace is fine)