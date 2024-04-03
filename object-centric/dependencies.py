import pandas as pd

def dependency_matrix(df):
    """
    Calculate the dependency matrix for the given DataFrame.

    Args:
        df (pd.DataFrame): DataFrame representing the activities frequency matrix.

    Returns:
        pd.DataFrame: DataFrame containing the dependency matrix.
    """
    # Create an empty DataFrame to store the dependency measures
    dependency_df = pd.DataFrame(index=df.index, columns=df.columns)
    
    # Iterate over each cell in the frequency DataFrame
    for i, row in df.iterrows():
        for j, value in row.items():
            # Calculate the dependency measure using the formula
            if i == j:
                freq_XY = df.loc[i, j]
                dependency = freq_XY / (freq_XY + 1)
            else:
                freq_XY = df.loc[i, j]
                freq_YX = df.loc[j, i]
                dependency = (freq_XY - freq_YX) / (freq_XY + freq_YX + 1)
            
            # Round the dependency to two decimal places
            dependency_rounded = round(dependency, 2)

            # Store the dependency measure in the corresponding cell of the dependency DataFrame
            dependency_df.loc[i, j] = dependency_rounded
    
    return dependency_df
