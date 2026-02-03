import pathlib
import shutil
from dsf import mobility, set_log_level, LogLevel
from langchain.tools import tool, ToolRuntime
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from typing import Annotated
from tqdm.rich import trange
from .utils import get_epoch_time
"""
Implementing the slow charge simulation logic in a langchain tool.
"""

@tool
def simulate_slow_charge(
    runtime : ToolRuntime,
    dt_agent : Annotated[int, "Time interval for agent spawning"] = 10,
    num_hours : Annotated[int, "Number of hours to simulate"] = 7,
    day : Annotated[str, "The day of the simulation in the format YYYY-MM-DD"] = '2022-01-31',
    start_hour : Annotated[int, "The hour of the day to start the simulation at, as an integer between 0 and 23"] = 0,
    ) -> Command:
    """
    Simulates the slow charge of the network for a given time interval and number of agents.

    Args:
        dt_agent: Time interval for agent spawning. Default is 10 seconds.
        num_hours: Number of hours to simulate. Default is 7.
        day: The day of the simulation in the format YYYY-MM-DD. Default is '2022-01-31'.
        start_hour: The hour of the day to start the simulation at, as an integer between 0 and 23. Default is 0.
    Returns:
        The path to the output directory containing the simulation results.
    """

    set_log_level(LogLevel.ERROR)

    OUT_FOLDER = "output_slow_charge"
    EDGES_FILE = runtime.state["edges_filepath"]
    NODES_FILE = runtime.state["nodes_filepath"]

    print("Constructing road network...")
    rn = mobility.RoadNetwork()
    rn.importEdges(EDGES_FILE)
    # rn.importNodeProperties(NODES_FILE)  

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
    shutil.copy(EDGES_FILE, f"./{OUT_FOLDER}/edges.geojson")

    simulator = mobility.Dynamics(rn, False, 69, 0.6)
    simulator.setMaxDistance(5e3)
    simulator.killStagnantAgents(10.0)

    # Get the epoch time for the actual day of the simulation
    epoch_time = get_epoch_time(day, start_hour)
    simulator.setInitTime(epoch_time)
    n_agents = 1

    for i in trange(start_hour * 3600, num_hours * 3600, desc="Simulating flows"):
        if i >= 0:
            if i % 300 == 0:
                simulator.saveStreetDensities(f"./{OUT_FOLDER}/densities.csv", True)
                simulator.saveTravelData(f"./{OUT_FOLDER}/speeds.csv")
                simulator.saveMacroscopicObservables(f"./{OUT_FOLDER}/data.csv")
        if i % dt_agent == 0 and n_agents > 0:
            simulator.addRandomAgents(n_agents)
            if i * num_hours:
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