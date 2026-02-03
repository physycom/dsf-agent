from typing import Annotated
import geopandas as gpd
import pandas as pd
from shapely import wkt
from .utils import fuzzy_match, read_edges_file
from datetime import datetime
from langchain.tools import tool, ToolRuntime
from langgraph.types import Command
from langchain_core.messages import ToolMessage

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

    # (!) ---------------------------------------------------------------------------------------------
    # NOTE: this removes the whole street, not a lane. To remove a lane, you would need to remove by id
    # (!) ---------------------------------------------------------------------------------------------

    # Read as DataFrame specifying the separator ";"
    edges_filepath = runtime.state["edges_filepath"]
    print(f"Reading edges file from {edges_filepath}...")    
    edges_gdf = read_edges_file(edges_filepath)

    # names are saved under the 'name' field like this: via_alessandro_codivilla
    # the llm needs a way to match natural language input with the exact name: use fuzzy match! 
    match, score = fuzzy_match(edges_gdf, "name", street_name)
    if match is None or score < 75: # threshold is 85 because it's the minimum score to be considered a match
        tool_err = f"No match found for '{street_name}'"
        return Command(update={"messages": [ToolMessage(tool_err, tool_call_id=runtime.tool_call_id)]})

    print(f"Removing street '{match}' from the simulation's cartography... (score: {score})")

    # remove the edge from the file - but wrap in geodf because it can degrade to simple df
    edges_gdf = gpd.GeoDataFrame(edges_gdf[edges_gdf["name"] != match])
    
    # save the modified edges file w/ a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    edges_filepath = f"./input/bologna_edges_{timestamp}.geojson"
    edges_gdf.to_file(edges_filepath, driver="GeoJSON") # NOTE: no need to modify nodes because there's only a warning in dsf mobility if not found

    return Command(
        update={
            "messages": [ToolMessage(f"Street '{match}' has been removed.", tool_call_id=runtime.tool_call_id)],
            "edges_filepath" : edges_filepath # save the edges file in state
        }
    )

@tool 
def change_number_of_lanes(
    runtime : ToolRuntime,
    street_name: Annotated[str, "The name of the street to change the number of lanes of"],
    number_of_lanes: Annotated[int, "The number of lanes to change the street to"] = 2
)->Command:
    """
    Use this tool to change the number of lanes of a street.

    Args:
        street_name: The name of the street to change the number of lanes of
        number_of_lanes: The number of lanes to change the street to

    Returns:
        A message indicating that the number of lanes has been changed. If no match is found, an error message is returned.
    """

    # check if the lane to change is 0: in that case return a message saying it needs to use the other tool (remove edge entirely)
    if number_of_lanes == 0:
        tool_err = "Cannot change the number of lanes to 0. Use the `remove_edge` tool instead."
        return Command(update={"messages": [ToolMessage(tool_err, tool_call_id=runtime.tool_call_id)]})

    # get edges file from state
    edges_filepath = runtime.state["edges_filepath"]
    print(f"Reading edges file from {edges_filepath}...")    
    edges_gdf = read_edges_file(edges_filepath)

    # fuzzy match the street name
    match, score = fuzzy_match(edges_gdf, "name", street_name)
    if match is None:
        tool_err = f"No match found for '{street_name}'"
        return Command(update={"messages": [ToolMessage(tool_err, tool_call_id=runtime.tool_call_id)]})

    # Fai una copia esplicita per evitare warning di SettingWithCopy
    edges_gdf = edges_gdf.copy()

    # Assegna i valori
    edges_gdf.loc[edges_gdf["name"] == match, "nlanes"] = number_of_lanes

    # save the modified edges file w/ a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    edges_filepath = f"./input/bologna_edges_{timestamp}.geojson"
    edges_gdf.to_file(edges_filepath, driver="GeoJSON")
    
    # update state
    return Command(
        update={
            "messages": [ToolMessage(f"Number of lanes for street '{match}' has been changed to {number_of_lanes}.", tool_call_id=runtime.tool_call_id)],
            "edges_filepath" : edges_filepath # save the edges file in state
        }
    )
