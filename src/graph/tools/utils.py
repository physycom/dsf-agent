from rapidfuzz import process, fuzz
import pandas as pd
from datetime import datetime, timezone

def fuzzy_match(dataset : pd.DataFrame, column_name : str, input_str : str, threshold : int = 65) -> str: 
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

    if match_result is None:
        return None

    match, score, _ = match_result

    return match, score

def get_epoch_time(day: str, start_hour: int, start_minute: int = 0) -> int:
    """
    Returns the epoch time for a given day and hour in UTC.

    Args:
        day: The day of the simulation in the format YYYY-MM-DD
        start_hour: The hour of the day to start the simulation at, as an integer between 0 and 23
        start_minute: The minute of the hour to start the simulation at, as an integer between 0 and 59
    Returns:
        The epoch time for the given day and hour in UTC, as an integer.
    """
    # 1. Parse string to datetime (Naive: 2023-01-01 00:00:00)
    t = datetime.strptime(day, "%Y-%m-%d")
    
    # 2. Set the hour AND set the timezone to UTC explicitly
    # This ensures .timestamp() treats the input as UTC, not local time.
    t_utc = t.replace(hour=start_hour, minute=start_minute, tzinfo=timezone.utc)
    
    # 3. Convert to int (timestamp returns float)
    return int(t_utc.timestamp())

if __name__ == "__main__":
    ts = get_epoch_time("2022-01-15", 11, 30)  
    print(datetime.fromtimestamp(ts, tz=timezone.utc))
