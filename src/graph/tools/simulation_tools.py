import dsf
from dsf import mobility
from langchain.tools import tool, ToolRuntime
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from typing import Annotated
from tqdm.rich import trange
from .utils import get_epoch_time, create_output_dir, copy_as_csv
import numpy as np 
import pickle

# I hate warnings
dsf.set_log_level(dsf.LogLevel.ERROR)

from ...visualization import open_visualization

INPUT_FOLDER="./updated_input"

@tool 
def run_simulation(
    runtime : ToolRuntime,
    dt_agent : Annotated[int, "Time interval for agent spawning"] = 10,
    duration : Annotated[int, "Duration of the simulation, in seconds"] = 60 * 60,  # 1 hour default
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

    # Create output directory
    output_dir = create_output_dir()

    edges_filepath = runtime.state["edges_filepath"]
    print(f">>> Loading edges from {edges_filepath}...")

    SCALE = 25  # hardcoded 
    N_SIMULATIONS = 10  # hardcoded
    ALPHA = 0.9  # hardcoded
    NORM_WEIGHTS = False
    SMOOTHING_HOURS = 3  # Number of hours to average over (odd number recommended)

    print(f">>> Loading input data from {INPUT_FOLDER}...")
    input_vehicles_mean = np.load(f"{INPUT_FOLDER}/vehicles10s_2022_mean.npy")
    input_vehicles_std = np.load(f"{INPUT_FOLDER}/vehicles10s_2022_std.npy")
    # Ensure both are >= 0
    input_vehicles_mean = np.clip(input_vehicles_mean, 0, None)
    input_vehicles_std = np.clip(input_vehicles_std, 0, None)
    # Shift input vehicles ahead of 360 points (1 hour)
    input_vehicles_mean = np.roll(input_vehicles_mean, 360)
    input_vehicles_std = np.roll(input_vehicles_std, 360)

    origin_nodes = pickle.load(open(f"{INPUT_FOLDER}/origin_dicts.pkl", "rb"))
    destination_nodes = pickle.load(open(f"{INPUT_FOLDER}/destination_dicts.pkl", "rb"))

    # Make all weights 1
    if NORM_WEIGHTS:
        for origin_dict in origin_nodes:
            for key in origin_dict:
                origin_dict[key] = 1
        for dest_dict in destination_nodes:
            for key in dest_dict:
                dest_dict[key] = 1

    
    for _ in trange(N_SIMULATIONS, desc="Simulations"):
        # Generate random seed for each simulation
        SEED = np.random.randint(0, 1000000)
        # Set np seed for reproducibility
        np.random.seed(SEED)
        # Generate input_vehicles for this simulation by sampling from normal distribution
        input_vehicles = np.random.normal(input_vehicles_mean, input_vehicles_std)
        input_vehicles = np.clip(input_vehicles, 0, None)  # No negative vehicles
        rn = mobility.RoadNetwork()
        rn.importEdges(f"{INPUT_FOLDER}/edges.csv")
        rn.importNodeProperties(f"{INPUT_FOLDER}/node_props.csv")
        rn.makeRoundabout(72)  # hardcoded

        rn.adjustNodeCapacities()
        rn.autoMapStreetLanes()
        rn.autoAssignRoadPriorities()
        rn.autoInitTrafficLights()

        simulator = mobility.Dynamics(rn, False, SEED, ALPHA)
        simulator.killStagnantAgents(40.0)

        # Copy edges file to output directory for reference.
        # NOTE: if it's a csv, just copies it. If it's a geojson, converts it to csv.
        # copy_as_csv(edges_filepath, f"./{output_dir}/edges.csv")

        simulator.killStagnantAgents(10.0)

        # Get the epoch time for the actual day of the simulation
        epoch_time = get_epoch_time(day, start_hour) # start minute
        simulator.setInitTime(epoch_time)

        # NOTE: now saving data to a database
        simulator.connectDataBase(f"{output_dir}/database.db")
        simulator.saveData(300, True, True, True)

        turn_counts = []

        # start and end times
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
                simulator.updatePaths(False)
                
            if i >= 0:
                if i % 3600 == 0:
                    turn_counts.append(simulator.normalizedTurnCounts())
            if i % dt_agent == 0 and i // dt_agent < len(input_vehicles):
                n_agents = int(input_vehicles[i // dt_agent] / SCALE)
                simulator.addAgentsRandomly(n_agents if n_agents > 0 else 0)
                
            simulator.evolve(False)

    print("\n=== SIMULATION COMPLETED SUCCESSFULLY ===\n")

    # Open visualization webapp
    print(">>> Opening visualization webapp...")
    try:
        db_path = f"{output_dir}/database.db"
        open_visualization(db_path=db_path)
    except Exception as e:
        print(f"WARNING: Could not open visualization: {e}")
        print(">>> You can manually open the visualization later")

    return Command(
        update={
            "messages": [ToolMessage(f"Simulation completed successfully. Results saved to {output_dir} directory. Visualization opened in browser.", tool_call_id=runtime.tool_call_id)],
            "output_dir" : output_dir # save the output directory in state
        }
    )