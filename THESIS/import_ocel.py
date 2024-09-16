import pathlib
from collections import Counter
import pandas as pd

import pm4py
from pm4py.statistics.ocel import ot_activities as ot




def import_log(path, profile=None):
    """
    Generate the OCEL dataframe based on the activities in an OCEL log and a profile.

    Args:
        path (str): the OCEL log
        profile (dict): Dictionary defining the profile with object types and their corresponding activities to be considered from the OCEL log. If no dictionary is given, all the OT and respective activities will be considered.

    Returns:
        ocel_df (pd.DataFrame): rows are events and columns have only data with 'ocel:' suffix, like the activity, the timestamp, the object types
        ot_activities (dict): keys are OT and values are sets of OT activities
        activity_to_object_types (dict): keys are activities and values are the list of OT related to the activity
        obj_to_obj (pd.DataFrame): rows are objects and there are three columns 'ocel:oid', 'ocel:oid_2' and 'ocel:qualifier'
        event_to_obj (pd.DataFrame): rows are events, columns are ocel:eid, ocel:oid, ocel:qualifier, ocel:activity, ocel:timestamp, ocel:type
    """ 

    # Read OCEL log
    
    file_extension = pathlib.Path(path).suffix
    
    if file_extension == '.sqlite':
        ocel = pm4py.read_ocel2_sqlite(path)
    elif file_extension == '.json':
        ocel = pm4py.read_ocel2_json(path)
    elif file_extension == '.xml':
        ocel = pm4py.read_ocel2_xml(path)
    else:
        raise Exception("The file formats supported are sqlite, json, ans xml.")


    try:

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

        # Get the relationships o2o and e2o
        obj_to_obj = ocel.o2o
        event_to_obj = ocel.relations

        return ocel, ot_activities, event_to_obj, obj_to_obj

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
        relations (pd.DataFrame): the dataframe is based on o2o (pm4py) but additionally has the object type for both columns with object identifiers (ocel:oid and ocel:oid2)
    """

    # Merge the o2o relations to the e2o to get the object_types for both objects as new columns in the relations df
    relations = obj_to_obj.merge(event_to_obj[['ocel:oid', 'ocel:type']], left_on='ocel:oid', right_on='ocel:oid', how='left')
    relations = relations.merge(event_to_obj[['ocel:oid', 'ocel:type']], left_on='ocel:oid_2', right_on='ocel:oid', suffixes=('','_2_new'), how = 'left')
    relations = relations.drop_duplicates()
    relations = relations[['ocel:oid', 'ocel:oid_2', 'ocel:type', 'ocel:type_2_new']]
    relations.rename(columns={"ocel:type_2_new": "ocel:type_2"}, inplace=True)
   

    # Create dictionary to store the maximum count for each OT1_OT2 relation
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
    
    # Check cardinalities between pairs of OT 
    cardinalities = {}

    for outer_key in ot1_ot2_cardinalities:
        cardinalities[outer_key] = {}
        for inner_key in ot1_ot2_cardinalities[outer_key]:
            if ot1_ot2_cardinalities[outer_key][inner_key] > 0:
                cardinalities[outer_key][inner_key] = (ot1_ot2_cardinalities[outer_key][inner_key], ot2_ot1_cardinalities[inner_key][outer_key])
                
    return ot1_ot2_cardinalities, ot2_ot1_cardinalities



def ot_sequence(ot_activities, ot1_ot2_cardinalities, ot2_ot1_cardinalities, event_to_obj):
    """
    Discover the process generator(s) based on the cardinalities of the relations between object types, the activities, and the totally ordered event list, called event_to_obj.
    The generators are the object types that 'create'/motivate other object types but are not created/motivated by any other object type. 

    Args:
        ot_activities (dict): the dictionary contains the object types and corresponding activities, obtained with the library from pm4py.statistics.ocel import ot_activities as ot
        ot1_ot2_cardinalities (dict): outer keys are the object types (ot1), inner keys are the object types (ot2) and values are the maximum number of ot2 found for one ot1
        ot2_ot1_cardinalities (dict): outer keys are the object types (ot2), inner keys are the object types (ot1) and values are the maximum number of ot1 that one ot2 is contained in / has relation to
        event_to_obj (pd.DataFrame): the dataframe obtained from the OCEL by applying pm4py method relations (ocel.relations)

    Returns:
        list: order of object types in the process, starting with the generator
    """

    # Find the generator, first check the ot that generate other ot in ot1_ot2, then find which of them occurs first (timestamp)
    potential_generators = []

    for ot1, relationships in ot1_ot2_cardinalities.items():
        if all(value == 0 for value in relationships.values()) == False and ot1 in ot2_ot1_cardinalities.keys():
            if all(value == 0 for value in ot2_ot1_cardinalities[ot1].values()):
                potential_generators.append(ot1)

    event_to_obj['ocel:timestamp'] = pd.to_datetime(event_to_obj['ocel:timestamp'])
    timestamps = [(event_to_obj.loc[event_to_obj['ocel:type'] == item, 'ocel:timestamp'].values[0], item) for item in potential_generators if item in event_to_obj['ocel:type'].values]
    
    generator = min(timestamps)[1]

    remaining_generators = [gen for gen in potential_generators if gen != generator] 

    all_generators = [generator] + remaining_generators
 

    # Find which ot have the same activities
    # partially_common is a list of tuples where the first element is contained by the second element
    partially_common = []

    for k1,v1 in ot_activities.items():
        for k2,v2 in ot_activities.items():
            if k1 != k2 and v1.issubset(v2):
                partially_common.append((k1,k2))

    
    # totally_common is a set of ot with exactly the same activities
    ot_activities_tuples = {k: tuple(v) for k,v in ot_activities.items()}
    
    counts = Counter(ot_activities_tuples.values())

    totally_common = {k:v for k,v in ot_activities_tuples.items() if counts[v] > 1} 

    # Discover the OT sequence beginning with the generator
    o_types = list(ot_activities.keys())

    ot_sequence = [generator]
    current_ot = generator

    # Function to check in the potential_next which ot contains objects
    def contains_all(subset, superset_list, partial):
        return all(any(p == (s, subset) for p in partial) for s in superset_list if s != subset)

    while len(ot_sequence) < len(o_types):
        potential_next = [k for k, v in ot1_ot2_cardinalities[current_ot].items() if v > 0 and k not in ot_sequence]
        next_ot = None

        if len(potential_next) == 1:
            next_ot = potential_next[0]
        elif len(potential_next) == 2:
            for item in potential_next:
                if ot2_ot1_cardinalities[item][current_ot] > 0:
                    # Check if the item is only related to the current_ot
                    if sum(1 for val in ot2_ot1_cardinalities[item].values() if val > 0) == 1:
                        next_ot = item
                        break
        elif len(potential_next) > 2:
            # Filter out potential_next elements that contain all others
            filtered_potential_next = [item for item in potential_next if contains_all(item, potential_next, partially_common)]
            
            # Ensure the next_ot has a relationship with the current_ot
            if filtered_potential_next:
                for item in filtered_potential_next:
                    if ot1_ot2_cardinalities[current_ot][item] > 0:
                        next_ot = item
                        break
            
            # If no suitable next_ot found in filtered list, pick the first potential_next
            if next_ot is None:
                for item in potential_next:
                    if ot1_ot2_cardinalities[current_ot][item] > 0:
                        next_ot = item
                        break

        elif len(potential_next) == 0 and remaining_generators:
            next_ot = remaining_generators.pop(0)
        
        if next_ot is None:
            if remaining_generators:
                next_ot = remaining_generators.pop(0)
            elif potential_next:
                next_ot = potential_next[0]  # Choose the first potential next item if no unique match found
            else:
                break

        if next_ot:
            ot_sequence.append(next_ot)
            current_ot = next_ot
        

    # Ensure all o_types are in the sequence
    for ot in o_types:
        if ot not in ot_sequence:
            if remaining_generators:
                ot_sequence.append(remaining_generators[0])
            else:
             ot_sequence.append(ot)
            
    if remaining_generators is None:
        remaining_generators = []

    return ot_sequence