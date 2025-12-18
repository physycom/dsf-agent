from rapidfuzz import process, fuzz
import pandas as pd

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