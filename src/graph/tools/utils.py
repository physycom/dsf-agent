from rapidfuzz import process, fuzz
import pandas as pd
from datetime import datetime

def fuzzy_match(dataset : pd.Dataframe, column_name : str, input_str : str, threshold : int = 65) -> str: 
    """
    Performs fuzzy matching to find the best match for the input string
    within a specified column of a dataset.

    Returns the best matching string and score if above the threshold,
    otherwise a message indicating no match.

    Args: 
        dataset: The dataset to search in
        column_name: The column to search in
        input_str: The input string to match
        threshold: The threshold for the match score

    Returns:
        A tuple containing the best matching string and score if above the threshold,
        otherwise None. 
        
        Example: input "torre del orologio" returns ("Torre dell'Orologio", 92)
    """

    known_strs = (
        dataset[column_name]
        .dropna()
        .astype(str)
        .str.strip().unique()
    )

    match_result = process.extractOne(
        input_str,
        known_strs,
        scorer=fuzz.token_sort_ratio   # maybe there are others that work better w/ street names?
    )

    if match_result is None or score < threshold:
        return None

    match, score, _ = match_result
    return match, score

def get_epoch_time(day : str, start_hour : int) -> int:
    """
    Returns the epoch time for a given day and hour.

    Args:
        day: The day of the simulation in the format YYYY-MM-DD
        start_hour: The hour of the day to start the simulation at, as an integer between 0 and 23

    Returns:
        The epoch time for the given day and hour in UTC.
    """
    return datetime.strptime(day, "%Y-%m-%d").timestamp() + start_hour * 3600   # UTC