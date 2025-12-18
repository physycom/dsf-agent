import pathlib
import shutil
from dsf import mobility, set_log_level, LogLevel
from langchain.tools import tool, ToolRuntime
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from typing import Annotated
from tqdm.rich import trange

"""
Implementing the slow charge simulation logic in a langchain tool.
"""

@tool
def simulate_slow_charge(
    runtime : ToolRuntime,
    dt_agent : Annotated[int, "Time interval for agent spawning"] = 10,
    duration : Annotated[int, "Duration of the simulation, in seconds"] = 24 * 60 * 60,
    ) -> Command:
    """
    Simulates the slow charge of the network for a given time interval and number of agents.

    Args:
        dt_agent: Time interval for agent spawning. Default is 10 seconds.
        duration: Duration of the simulation, in seconds. Default is 24 hours.

    Returns:
        The path to the output directory containing the simulation results.
    """

    set_log_level(LogLevel.ERROR)

    OUT_FOLDER = "output_slow_charge"
    EDGES_FILE = "bologna_edges.geojson"  
    NODES_FILE = "bologna_nodes.csv"

    print("Constructing road network...")
    rn = mobility.RoadNetwork()
    rn.importEdges(f"./input/{EDGES_FILE}")
    rn.importNodeProperties(f"./input/{NODES_FILE}", separator=",")  # notice the separator is comma, not semicolon

    # Clear output directory
    output_dir = pathlib.Path(f"./{OUT_FOLDER}")
    output_dir.mkdir(parents=True, exist_ok=True)
    for file in output_dir.glob("*"):
        if file.is_file():
            file.unlink()

    rn.adjustNodeCapacities()
    rn.autoMapStreetLanes()

    print("Road network constructed successfully.")

    # Copy edges file to output directory for reference
    shutil.copy(f"./input/{EDGES_FILE}", f"./{OUT_FOLDER}/edges.geojson")

    simulator = mobility.Dynamics(rn, False, 69, 0.6)
    simulator.setMaxDistance(5e3)
    simulator.killStagnantAgents(10.0)

    # Get the epoch time for 2022-01-31 00:00:00 UTC
    epoch_time = 1643587200
    simulator.setInitTime(epoch_time)
    n_agents = 1

    for i in trange(0, duration + 1, desc="Simulating flows"):
        if i >= 0:
            if i % 300 == 0:
                simulator.saveStreetDensities(f"./{OUT_FOLDER}/densities.csv", True)
                simulator.saveTravelData(f"./{OUT_FOLDER}/speeds.csv")
                simulator.saveMacroscopicObservables(f"./{OUT_FOLDER}/data.csv")
        if i % dt_agent == 0 and n_agents > 0:
            simulator.addRandomAgents(n_agents)
            if i < 3600 * 7:
                n_agents += 1  # gradually increase number of agents added
            else:
                n_agents = 0
        simulator.evolve(False)

    return Command(
        update = {
            "messages" : [ToolMessage(content=f"Simulation completed successfully. Results saved to {OUT_FOLDER}.", tool_call_id=runtime.tool_call_id)]
        }
    )


# TODO: visualization tool 
'''
@tool
def visualize_simulation():
    """
    """'''