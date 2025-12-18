import pathlib
import shutil
from dsf import mobility, set_log_level, LogLevel
from langchain.tools import tool, ToolRuntime
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from typing import Annotated
from tqdm.rich import trange
import geopandas as gpd
from .utils import fuzzy_match, get_epoch_time
import numpy as np 
import pickle
from datetime import datetime

import warnings
from tqdm import TqdmExperimentalWarning
# I hate warnings
warnings.filterwarnings("ignore", category=TqdmExperimentalWarning)

@tool 
def remove_edge(
    runtime : ToolRuntime,
    street_name: Annotated[str, "The name of the street to remove"]
)->Command:
    """
    Use this tool to remove a street from the simulation's cartography.

    Args:
        street_name: The name of the street to remove.

    Returns:
        A message indicating that the street has been removed. If no match is found, an error message is returned.
    """

    # read the edges file from state
    edges_gdf = gpd.read_file(runtime.state["edges_filepath"]) 

    # names are saved under the 'name' field like this: via_alessandro_codivilla
    # the llm needs a way to match natural language input with the exact name: use fuzzy match! 
    match, score = fuzzy_match(edges_gdf, "name", street_name)
    if match is None:
        tool_err = f"No match found for '{street_name}'"
        return Command(update={"messages": [ToolMessage(tool_err, tool_call_id=runtime.tool_call_id)]})

    # remove the edge from the file
    edges_gdf = edges_gdf[edges_gdf["name"] != match]
    
    # save the modified edges file w/ a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    edges_filepath = f"./input/bologna_edges_{timestamp}.geojson"
    edges_gdf.to_file(edges_filepath, driver="GeoJSON")

    return Command(
        update={
            "messages": [ToolMessage(f"Street '{match}' has been removed.", tool_call_id=runtime.tool_call_id)],
            "edges_filepath" : edges_filepath # save the edges file in state
        }
    )


@tool 
def run_simulation(
    runtime : ToolRuntime,
    dt_agent : Annotated[int, "Time interval for agent spawning"] = 10,
    duration : Annotated[int, "Duration of the simulation, in seconds"] = 24 * 60 * 60,
    day : Annotated[str, "The day of the simulation in the format YYYY-MM-DD"] = '2022-01-31',
    start_hour: Annotated[int, "The hour of the day to start the simulation at, as an integer between 0 and 23"] = 0,
    # start_minute: Annotated[int, "The minute of the hour to start the simulation at, as an integer between 0 and 59"] = 0,  array is hourly computed so no need for minutes now
)-> Command:
    """
    Use this tool to run the mobility simulation. 

    Args:
        dt_agent: Time interval for agent spawning
        duration: Duration of the simulation, in seconds
        day: The day of the simulation in the format YYYY-MM-DD
        start_hour: The hour of the day to start the simulation at, as an integer between 0 and 23
    Returns:
        A message indicating that the simulation has been run.
        The path to the output directory containing the simulation results.
    """

    print(f"\n=== RUNNING SIMULATION ===\n\nAttempting to run simulation with parameters: dt_agent={dt_agent}, duration={duration}, day={day}, start_hour={start_hour}\n")

    edges_filepath = runtime.state["edges_filepath"]
    print(f">>> Loading edges from {edges_filepath}...")

    set_log_level(LogLevel.ERROR)

    SCALE = 25  # hardcoded 
    NORM_WEIGHTS = False
    SMOOTHING_HOURS = 3  # Number of hours to average over (odd number recommended)

    input_vehicles = np.load("./input/vehicles10seconds_spline.npy")

    print(">>> Loading origin and destination nodes...")
    origin_nodes = pickle.load(open("./input/origin_dicts.pkl", "rb"))
    destination_nodes = pickle.load(open("./input/destination_dicts.pkl", "rb"))

    # Make all weights 1
    if NORM_WEIGHTS:
        for origin_dict in origin_nodes:
            for key in origin_dict:
                origin_dict[key] = 1
        for dest_dict in destination_nodes:
            for key in dest_dict:
                dest_dict[key] = 1

    rn = mobility.RoadNetwork()
    rn.importEdges(edges_filepath)
    # rn.importNodeProperties("./input/node_props.csv") # not needed for now
    rn.makeRoundabout(72)

    print(f">>> Bologna's road network has {rn.nNodes()} nodes and {rn.nEdges()} edges.")
    print(f">>> There are {rn.nCoils()} magnetic coils, {rn.nTrafficLights()} traffic lights and {rn.nRoundabouts()} roundabouts\n")

    # Clear output directory
    output_dir = pathlib.Path("./output")
    output_dir.mkdir(parents=True, exist_ok=True)
    for file in output_dir.glob("*"):
        if file.is_file():
            file.unlink()

    rn.adjustNodeCapacities()
    rn.autoMapStreetLanes()

    # Copy edges file to output directory for reference
    shutil.copy(edges_filepath, "./output/edges.csv")

    simulator = mobility.Dynamics(rn, False, 69, 0.8)
    simulator.killStagnantAgents(10.0)

    # Get the epoch time for the actual day of the simulation
    epoch_time = get_epoch_time(day, start_hour) # start minute
    simulator.setInitTime(epoch_time)

    start_time_seconds = start_hour * 3600
    end_time_seconds = start_time_seconds + duration

    # NOTE: simulate from start_hour until start_hour + duration 
    for i in trange(start_time_seconds, end_time_seconds + 1, desc="Simulating flows"):
        if i % 3600 == 0 and i // 3600 < len(origin_nodes):
            # do a mean over the weights for SMOOTHING_HOURS hours (centered on current hour)
            origins = origin_nodes[
                i // 3600
            ].copy()  # Create a copy to avoid modifying original
            destinations = destination_nodes[i // 3600]

            # Collect all unique keys from the smoothing window
            all_keys = set(origins.keys())
            half_window = SMOOTHING_HOURS // 2
            for offset in range(-half_window, half_window + 1):
                hour_idx = i // 3600 + offset
                if 0 <= hour_idx < len(origin_nodes):
                    all_keys.update(origin_nodes[hour_idx].keys())

            # For each key, average available values from the smoothing window
            for key in all_keys:
                values = []
                for offset in range(-half_window, half_window + 1):
                    hour_idx = i // 3600 + offset
                    if 0 <= hour_idx < len(origin_nodes) and key in origin_nodes[hour_idx]:
                        values.append(origin_nodes[hour_idx][key])

                if values:
                    origins[key] = sum(values) / len(values)
            simulator.setOriginNodes(origins)
            simulator.setDestinationNodes(destinations)
        if i % 300 == 0:
            simulator.updatePaths()
            # print(f"Hour {i // 3600}: updated paths")
        if i >= 0:
            # if i % 3600 == 0:
            #     simulator.saveOutputStreetCounts("./output/counts.csv", True)
            if i % 300 == 0:
                simulator.saveStreetDensities("./output/densities.csv", True)
                simulator.saveTravelData("./output/speeds.csv")
                # if i % 1500 == 0:
                simulator.saveMacroscopicObservables("./output/data.csv")
        if i % dt_agent == 0 and i // dt_agent < len(input_vehicles):
            n_agents = int(input_vehicles[i // dt_agent] / SCALE)
            simulator.addAgentsRandomly(n_agents if n_agents > 0 else 0)
        simulator.evolve(False)

    print("\n=== SIMULATION COMPLETED SUCCESSFULLY ===\n")

    return Command(
        update={
            "messages": [ToolMessage(f"Simulation completed successfully. Results saved to ./output directory.", tool_call_id=runtime.tool_call_id)]
        }
    )