import pm4py
from pm4py.statistics.ocel import ot_activities as ot

import pandas as pd


def frequency_matrix(file_path, profile):
    """
    Generate the activity frequency matrix based on the activities in an OCEL log file and a profile.

    Args:
        file_path (str): Path to the OCEL log file.
        profile (dict): Dictionary defining the profile with object types and their corresponding activities to be considered from the OCEL log.

    Returns:
        pd.DataFrame: Frequency matrix where rows and columns represent activities, and cells represent frequency counts of one activity followed by another.
    """
    try:
        # Read OCEL log
        ocel = pm4py.read_ocel(file_path)

        # Get the set of activities of each object type in the log
        ot_activities = ot.get_object_type_activities(ocel)

        # Check if all object types and activities in the profile dictionary are in the log
        for obj_type, activities in profile.items():
            if obj_type not in ot_activities:
                raise ValueError(f"Object type '{obj_type}' does not correspond to any object type in the log.")
            for activity in activities:
                if activity not in ot_activities[obj_type]:
                    raise ValueError(f"Activity '{activity}' is not performed for object type '{obj_type}' in the log.")
                
        # Filter object types and activities from the log based on a profile 
        filtered_ocel = pm4py.filter_ocel_object_types_allowed_activities(ocel, profile)

        # get_extended_table returns data in a dataframe
        df = filtered_ocel.get_extended_table()

        # Create an empty dictionary to store the mapping of activities to object types
        activity_to_object_types = {}

        # Iterate over each object type and its corresponding activities in the profile
        for obj_type, activities in profile.items():
            # Iterate over each activity and map it to the current object type
            for activity in activities:
                if activity not in activity_to_object_types:
                    activity_to_object_types[activity] = []
                activity_to_object_types[activity].append(obj_type)

        # Create a reverse mapping to lookup categories for each activity
        activity_to_category = {activity: obj_types for activity, obj_types in activity_to_object_types.items()}

        # Convert 'ocel:timestamp' column to datetime type
        df['ocel:timestamp'] = pd.to_datetime(df['ocel:timestamp'])

        # Sort DataFrame by timestamp
        df_sorted = df.sort_values(by='ocel:timestamp')

        # Create a new column 'category' to represent the category of each activity
        df_sorted['category'] = df_sorted['ocel:activity'].map(activity_to_category)

        # Explode the lists into individual rows
        df_expanded = df_sorted.explode('ocel:type:Order').explode('ocel:type:Item').explode('ocel:type:Package').explode('category')

        # Define a function to calculate the next activity based on timestamp within each sub-group
        def calculate_next_activity(group):
            # Drop duplicates within the subgroup based on the combination of activity and timestamp
            group = group.drop_duplicates(subset=['ocel:activity', 'ocel:timestamp'])
            
            # Sort the subgroup by timestamp to ensure correct ordering
            group = group.sort_values(by='ocel:timestamp')
            
            # Calculate the next activity based on timestamp
            group['next_activity'] = group['ocel:activity'].shift(-1)
            
            return group

        # Group the DataFrame by the 'category' column
        df_grouped = df_expanded.groupby('category')

        # List to store all sub-grouped DataFrames
        sub_grouped_dfs = []

        # Iterate over the groups and then group by category-specific columns
        for group_name, group_df in df_grouped:
            category_cols = [col for col in group_df.columns if group_name in col]  # Get columns related to the current category
            if len(category_cols) > 0:
                # Group by category-specific columns
                sub_grouped = group_df.groupby(category_cols)
                for sub_group_name, sub_group_df in sub_grouped:
                    
                    # Apply the function to calculate the next activity within each sub-group
                    sub_group_df_with_next_activity = sub_group_df.groupby(['category']).apply(calculate_next_activity)
                    
                    # Append the resulting DataFrame to the list
                    sub_grouped_dfs.append(sub_group_df_with_next_activity)
            else:
                print("No category-specific columns found in this group.")

        # Concatenate all sub-grouped DataFrames into one big DataFrame
        big_df = pd.concat(sub_grouped_dfs)


        # Get all unique activities from 'ocel:activity' and 'next_activity'
        activities = pd.unique(big_df[['ocel:activity', 'next_activity']].values.ravel('K'))
        activities = activities[~pd.isna(activities)]


        # Create an empty DataFrame with activities as both rows and columns
        freq_df = pd.DataFrame(index=activities, columns=activities)

        # Initialize all cells with zeros
        freq_df = freq_df.fillna(0)


        # Loop through each row in the original DataFrame and update the frequency counts in freq_df
        for i, row in big_df.iterrows():
            activity = row['ocel:activity']
            next_activity = row['next_activity']
            
            # Check if next_activity is not NaN
            if pd.notna(next_activity):
                freq_df.loc[activity, next_activity] += 1

        # Return the resulting DataFrame
        return freq_df

    # Return error message if the file provided in the file_path is not found
    except FileNotFoundError:
        return None
    # Handle other errors
    except Exception as e:
        print("An error occurred:", str(e))
        return None