import os
from rapidfuzz import process, fuzz
import geopandas as gpd
from datetime import datetime, timezone
import pandas as pd
from shapely import wkt
import shutil

def fuzzy_match(gdf : gpd.GeoDataFrame, column_name : str, input_str : str) -> tuple[str, int]: 
    """
    Performs fuzzy matching to find the best match for the input string
    within a specified column of a dataset.

    Returns the best matching string and score,

    Args: 
        gdf: The geodataframe to search in
        column_name: The column to search in
        input_str: The input string to match

    Returns:
        A tuple containing the best matching string and score. 
        
        Example: input "torre del orologio" returns ("Torre dell'Orologio", 92)
    """

    known_strs = (
        gdf[column_name]
        .dropna()
        .astype(str)
        .str.lower()
        .str.strip().unique()
    )

    match_result = process.extractOne(
        input_str.lower().strip(),
        known_strs,
        scorer=fuzz.ratio   # maybe there are others that work better w/ street names?
    )

    if match_result is None:
        return None

    match, score, _ = match_result

    return match, score

def read_edges_file(filepath: str) -> gpd.GeoDataFrame:
    """
    Reads the edges file from the given filepath and returns a GeoDataFrame.

    We need to read the file as a DataFrame first, then convert the string column to real geometric objects, and then create a GeoDataFrame.

    Args:
        filepath: The path to the edges file
    Returns:
        A GeoDataFrame containing the edges data.
    """
    edges_df = pd.read_csv(filepath, sep=";")
    # convert the string column to real geometric objects
    edges_df['geometry'] = edges_df['geometry'].apply(wkt.loads)
    # create a GeoDataFrame
    return gpd.GeoDataFrame(edges_df, geometry='geometry', crs="EPSG:4326")

def get_epoch_time(day: str, start_hour: int, start_minute: int = 0, include_tram = False) -> int:
    """
    Returns the epoch time for a given day and hour in UTC.

    Args:
        day: The day of the simulation in the format YYYY-MM-DD
        start_hour: The hour of the day to start the simulation at, as an integer between 0 and 23
        start_minute: The minute of the hour to start the simulation at, as an integer between 0 and 59
        include_tram: wether we have to account for the tram existing or not. If yes, we add 2 years to the epoch.
    Returns:
        The epoch time for the given day and hour in UTC, as an integer.
    """
    # 1. Parse string to datetime (Naive: 2023-01-01 00:00:00)
    t = datetime.strptime(day, "%Y-%m-%d")
    
    # 2. Set the hour AND set the timezone to UTC explicitly
    # This ensures .timestamp() treats the input as UTC, not local time.
    t_utc = t.replace(hour=start_hour, minute=start_minute, tzinfo=timezone.utc)
    
    # 3. Convert to int (timestamp returns float)
    t_int = int(t_utc.timestamp())

    # 4. Adjust epoch for tram (+2 years)
    if include_tram:
        t_int += 365 * 24 * 60 * 60 * 2 

    return t_int

def create_output_dir(output_dir: str = "output") -> str:
    """
    Creates the output directory if it does not exist, with a timestamp in the name.

    Args:
        output_dir: The path to the output directory (Optional: default is "output")
    Returns:
        The path to the output directory with the timestamp in the name
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(f"{output_dir}_{timestamp}", exist_ok=True)
    return f"{output_dir}_{timestamp}"

def copy_as_csv(source_path: str, destination_path: str) -> None:
    """
    Copies a file from the source path to the destination path as a csv file.
    Made to copy edges file, which can be a geojson or a csv.
    If it is a geojson, we convert it to csv.

    Args:
        source_path: The path to the source file
        destination_path: The path to the destination file
    """
    if source_path.endswith(".geojson"):
        df = gpd.read_file(source_path)
        df.to_csv(destination_path, index=False, sep=";")
    else:
        shutil.copy(source_path, destination_path)