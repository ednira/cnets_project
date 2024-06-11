import pm4py
from pm4py.statistics.ocel import ot_activities as ot

import pandas as pd
import numpy as np

from collections import OrderedDict


def import_log(path, profile=None):
    """
    Generate the OCEL dataframe based on the activities in an OCEL log and a profile.

    Args:
        ocel (str): the OCEL log
        profile (dict): Dictionary defining the profile with object types and their corresponding activities to be considered from the OCEL log. If no dictionary is given, all the OT and respective activities will be considered.

    Returns:
        pd.DataFrame: rows are events and columns are the activity, the timestamp, the object types and added columns.
    """ 

    try:
        # Read OCEL log
        ocel = pm4py.read_ocel2_sqlite(path)

        # Get the set of activities of each object type in the log
        ot_activities = ot.get_object_type_activities(ocel)

        if profile is None:
            # If no profile is given as argument, all OT and respective activities are considered
            profile = ot_activities
        else:
            # Check if all object types and activities in the given profile dictionary are in the log
            for obj_type, activities in profile.items():
                if obj_type not in ot_activities.keys():
                    raise ValueError(f"Object type '{obj_type}' does not correspond to any object type in the log.")
                ot_activity_set = set(ot_activities[obj_type]) # Convert to set because sets are hashable
                profile_activities = set (activities)
                for activity in profile_activities:
                    if activity not in ot_activity_set:
                        raise ValueError(f"Activity '{activity}' is not performed for object type '{obj_type}' in the log.")
                    
        # Filter object types and activities from the log based on a profile 
        filtered_ocel = pm4py.filter_ocel_object_types_allowed_activities(ocel, profile)

        # get_extended_table returns data in a dataframe
        ocel_df = filtered_ocel.get_extended_table()

        # Create a dictionary where activities are the keys and object types are the values
        activity_to_object_types = {}

        # Iterate over each object type and its corresponding activities
        for obj_type, activities in ot_activities.items():
            # Iterate over each activity and map it to the current object type
            for activity in activities:
                if activity not in activity_to_object_types:
                    activity_to_object_types[activity] = []
                activity_to_object_types[activity].append(obj_type)

    
        # Keep only columns related to OCC-nets discovery
        ocel_df = ocel_df.loc[:, ocel_df.columns.str.contains('ocel:')]

        prefix = "ocel:type:"

        def get_categories(row):
            activity = row['ocel:activity']
            categories = []
            for col_name in ocel_df.columns:
                if col_name.startswith(prefix):
                    if (isinstance(row[col_name], list)):
                        categories.append(col_name[len(prefix):])
       
            return categories
        # Create a new column 'category' to represent the object types of each activity
        ocel_df['occnet:category'] = ocel_df.apply(get_categories, axis=1)
        
        # The ocel with the new column category containing lists of object types
        ocel_w_cat = ocel_df

        # Explode the dataframe by object types
        #ocel_expanded = ocel_df.explode('occnet:category')

        obj_to_obj = ocel.o2o
        event_to_obj = ocel.relations

        return ocel, ocel_w_cat, ot_activities, obj_to_obj, event_to_obj

    # Return error message if the file provided in the file_path pandas explodeis not found
    except FileNotFoundError:
        return None
    # Handle other errors
    except Exception as e:
        print("An error occurred:", str(e))
        return None
    


def ot_cardinalities(obj_to_obj, event_to_obj, ot_activities):
    
    """
    Generate two dictionaries with the cardinalities of the relations between the object types of ot1_to_ot2 and ot2_to_ot1 from the e2o relationships dataframe (pm4py ocel.relations).
    The cardinalities mean that for one object of type ot1 there is a maximum number of objects of type ot2 and vice-versa in the second dictionary.

    Args:
        obj_to_obj (pd.DataFrame): the dataframe obtained from the OCEL by applying pm4py method o2o (ocel.o2o)
        event_to_obj (pd.DataFrame): the dataframe obtained from the OCEL by applying pm4py method relations (ocel.relations)
        ot_activities (dict): the dictionary contains the object types and corresponding activities, obtained with the library from pm4py.statistics.ocel import ot_activities as ot

    Returns:
        dictionary ot1_ot2: outer keys are the object types (ot1), inner keys are the object types (ot2) and values are the maximum number of ot2 found for one ot1
        dictionary ot2_ot1: outer keys are the object types (ot2), inner keys are the object types (ot1) and values are the maximum number of ot1 found for one ot2
    """

    relations = obj_to_obj
    obj_types = event_to_obj

    # Merge the o2o relations to the e2o to get the object_types for both objects as new columns in the relations df
    relations = relations.merge(obj_types[['ocel:oid', 'ocel:type']], left_on='ocel:oid', right_on='ocel:oid', how='left')
    relations = relations.merge(obj_types[['ocel:oid', 'ocel:type']], left_on='ocel:oid_2', right_on='ocel:oid', suffixes=('','_2'), how = 'left')
    relations = relations.drop_duplicates()

    # Create dictionary to store the meximum count for each OT1_OT2 relation
    ot1_ot2_cardinalities = {obj_type: {obj_type_2: 0 for obj_type_2 in ot_activities} for obj_type in ot_activities}

    

    for obj_type in ot1_ot2_cardinalities:
        for obj_type_2 in ot1_ot2_cardinalities:
            filtered_relations = relations[(relations['ocel:type_2'] == obj_type_2) & (relations['ocel:type'] == obj_type)]
            if not filtered_relations.empty:
                counts = filtered_relations['ocel:oid'].value_counts()          
                # Find the maximum count for this pair of object types
                max_count = counts.max()
                # Store the result in the dictionary
                ot1_ot2_cardinalities[obj_type][obj_type_2] = max_count
            else:
                pass

    # Create dictionary to store the meximum count for each OT12_OT1 relation
    ot2_ot1_cardinalities = {obj_type_2: {obj_type: 0 for obj_type in ot_activities} for obj_type_2 in ot_activities}

    for obj_type_2 in ot2_ot1_cardinalities:
        for obj_type in ot2_ot1_cardinalities:
            filtered_relations = relations[(relations['ocel:type_2'] == obj_type_2) & (relations['ocel:type'] == obj_type)]
            if not filtered_relations.empty:
                counts = filtered_relations.groupby(['ocel:type_2'])['ocel:oid_2'].value_counts()
                max_count = counts.max()
                ot2_ot1_cardinalities[obj_type_2][obj_type] = max_count
            else:
                pass
                
    return ot1_ot2_cardinalities, ot2_ot1_cardinalities

    

    

def e_to_e(ocel_expanded):
    
    """
    Generate an event-to-event dictionary. This is a collection of all object traces.

    Args:
        ocel_expanded (str): the OCEL log expanded returned by the import_log function

    Returns:
        dictionary: outer keys are the object types, inner keys are the objects and values are the list of events of each object ordered according to their timestamps
    """

    # Group the DataFrame by the 'category' column
    ocel_expanded_grouped = ocel_expanded.groupby('occnet:category')
    
    # Dictionary to store all object traces in the grouped DataFrame
    e_to_e = {}
    prefix = "ocel:type:"

    # Iterate over the groups and then group by object
    for group_name, group_df in ocel_expanded_grouped:
        # Find the column that contains the objects of the current category
        category_col = next((col for col in group_df.columns if col.startswith(prefix) and group_name in col), None)
        # Skip if no such column exists
        if not category_col:
            continue

        # Sort the group by timestamp
        group_df = group_df.sort_values(by='ocel:timestamp')

        # Initialize the category in the dictionary if it does not exist
        if group_name not in e_to_e:
            e_to_e[group_name] = {}

        # Iterate through rows in the group
        for _, row in group_df.iterrows():
            objects = row[category_col]
            activity = row['ocel:activity']
            event = row['ocel:eid']

            for object in objects:
                if object not in e_to_e[group_name]:
                    e_to_e[group_name][object] = []

                e_to_e[group_name][object].append(activity)
            

    return e_to_e


"""
def top_traces (e_to_e):
    
    Take a dictionary of traces and return dictionary with trace as key and trace count in log as value
    Ordered from highest to lowest counts
    
    Args:
        e_to_e (dict): event-to-event dictionary, with the traces found for each object in each object type

    Returns:
        dictionary: outer keys are the object types, inner keys are the traces and values are the counts of traces in descending order
   
   
    tracelist = []
    trace_counts = {}

    for obj_types in e_to_e:
        for object in traces:
            trace = tuple(traces[trace])
            tracelist.append(trace)

    for trace in tracelist:
        count = tracelist.count(trace)
        if trace not in trace_counts.keys():
            trace_counts[trace] = {}
        trace_counts[trace] = count
        

    highest_traces = OrderedDict(sorted(trace_counts.items(), key=lambda t: t[1], reverse=True))

    return highest_traces



# Define a function to calculate the next activity based on timestamp within each sub-group
def calculate_next_activity(group):
    # Sort the subgroup by timestamp to ensure correct ordering
    group = group.sort_values(by='ocel:timestamp')        
    # Calculate the next activity based on timestamp
    group['occnet:next_activity'] = group['ocel:activity'].shift(-1)            
    return group
"""