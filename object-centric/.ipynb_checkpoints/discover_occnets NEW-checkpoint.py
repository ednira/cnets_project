import warnings
import pathlib
from collections import Counter, namedtuple
import csv
from io import StringIO
from itertools import combinations

import pandas as pd
import numpy as np

import pm4py
from pm4py.statistics.ocel import ot_activities as ot

warnings.filterwarnings('ignore')


def import_log(ocel_path, profile=None):
    """
    Generate the OCEL dataframe based on the activities in an OCEL log and a profile.

    Args:
        path (str): the OCEL log path
        profile (dict): Dictionary defining the profile with object types and their corresponding activities to be considered from the OCEL log. If no dictionary is given, all the OT and respective activities will be considered.

    Returns:
        ocel_df (pd.DataFrame): rows are events and columns have only data with 'ocel:' suffix, like the activity, the timestamp, the object types
        ot_activities (dict): keys are OT and values are sets of OT activities
        activity_to_object_types (dict): keys are activities and values are the list of OT related to the activity
        obj_to_obj (pd.DataFrame): rows are objects and there are three columns 'ocel:oid', 'ocel:oid_2' and 'ocel:qualifier'
        event_to_obj (pd.DataFrame): rows are events, columns are ocel:eid, ocel:oid, ocel:qualifier, ocel:activity, ocel:timestamp, ocel:type
    """ 

    # Read OCEL log
    
    file_extension = pathlib.Path(ocel_path).suffix
    
    if file_extension == '.sqlite':
        ocel = pm4py.read_ocel2_sqlite(ocel_path)
    elif file_extension == '.json':
        ocel = pm4py.read_ocel2_json(ocel_path)
    elif file_extension == '.xml':
        ocel = pm4py.read_ocel2_xml(ocel_path)
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

    # Return error message if the file provided in the file_path is not found
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
            else:
                pass

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

def flatten_log(ocel, ot_activities):
    """
    Generate a dictionary with flattened logs for each object type in the OCEL 2.0 log.

    Args:
        ocel: the OCEL 2.0 log
        ot_activities (dict): keys are object types and their corresponding activities to be considered from the OCEL log. If no dictionary is given, all the OT and respective activities will be considered.

    Returns:
        Dictionary (dict): keys are object type names and values are the set of activities the ot has.
    """

    flattened_logs = {}
    
    for o_type in ot_activities.keys():
        flt = pm4py.ocel_flattening(ocel, o_type)
        flt_csv = flt.to_csv()
        if o_type not in flattened_logs.keys():
            flattened_logs[o_type] = flt_csv
    
    return flattened_logs



def read_log(flattened_logs):
    """
    Generate a dictionary with a list of events for each object within each object type.

    Args:
        flattened_logs (dict): Dictionary with object types as keys and their corresponding csv flattened log as values.

    Returns:
        Dictionary (dict): outer keys are object type names inner keys are objects and value is the list of corresponding events (task, eid, timestamp) of the object.
    """

    logs = dict()

    for o_type, fltlog in flattened_logs.items():
        if o_type not in logs.keys():
            logs[o_type] = {}
        csv_io = StringIO(fltlog)
        reader = csv.DictReader(csv_io)
        for row in reader:
            case_col = next((col for col in reader.fieldnames if col.lower() == 'case:concept:name'), None)
            task_col = next((col for col in reader.fieldnames if col.lower() == 'concept:name'), None)
            eid_col = next((col for col in reader.fieldnames if col.lower() == 'ocel:eid'), None)
            time_col = next((col for col in reader.fieldnames if col.lower() == 'time:timestamp'), None)

            caseID = row.get(case_col)
            task = row.get(task_col)
            eid = row.get(eid_col)
            timestamp = row.get(time_col)

            if caseID not in logs[o_type]:
                logs[o_type][caseID] = []
            event = (task, eid, timestamp)
            logs[o_type][caseID].append(event)

        for caseID in sorted(logs[o_type].keys()):
            logs[o_type][caseID].sort(key = lambda event: event[-1])

    return logs



def traces(flattened_logs):
    """
    Mine traces for each object within each object type. The trace is a list of activities (tasks) ordered by timestamp.

    Args:
        flattened_logs (dict): Dictionary with object types as keys and their corresponding csv flattened log as values.

    Returns:
        Dictionary (dict): outer keys are object type names inner keys are objects and values are their corresponding traces.
    """

    # Initialize the dictionary that contains OT as outer keys, objects as inner keys and their traces as values
    all_traces = {}

    for o_type, fltlog in flattened_logs.items():
        if o_type not in all_traces.keys():
            all_traces[o_type] = {}
        csv_io = StringIO(fltlog)
        reader = csv.DictReader(csv_io)

        for row in reader:
            case_col = next((col for col in reader.fieldnames if col.lower() == 'case:concept:name'), None)
            task_col = next((col for col in reader.fieldnames if col.lower() == 'concept:name'), None)
            eid_col = next((col for col in reader.fieldnames if col.lower() == 'ocel:eid'), None)
            time_col = next((col for col in reader.fieldnames if col.lower() == 'time:timestamp'), None)

            caseID = row.get(case_col)
            task = row.get(task_col)
            eid = row.get(eid_col)
            timestamp = row.get(time_col)
            event = (task, eid, timestamp)

            if caseID not in all_traces[o_type]:
                all_traces[o_type][caseID] = []
            if row.get('case:concept:name') == caseID:
                all_traces[o_type][caseID].append(task)

    return all_traces

def activity_total(log):
   """Calculate total activity counts and store them in a dictionary. A total activity count is how many times an activity occurs"""
   
   act_total = dict()
   
   for caseID in log:
      for i in range(0, len(log[caseID])):
         ai = log[caseID] [i] [0]
         if ai not in act_total:
            act_total[ai] = 0
         act_total[ai] += 1

   return act_total


def activity_frequencies(log):
   """Calculate frequencies of activity ai followed by activity aj and store them in a dictionary"""
   
   act_frequencies = dict()

   for caseID in log:
      for i in range(0, len(log[caseID])-1): 
         ai = log[caseID] [i] [0]
         aj = log[caseID] [i+1] [0]
         if ai not in act_frequencies:
            act_frequencies[ai] = dict()
         if aj not in act_frequencies[ai]:
            act_frequencies[ai][aj] = 0
         act_frequencies[ai][aj] += 1
         if aj not in act_frequencies:
            act_frequencies[aj] = dict()
   

   for key in act_frequencies:
      if key not in act_frequencies[key]:
         act_frequencies[key][key] = 0
   
   return act_frequencies

def frequencies(act_frequencies):
   """Convert the activity frequencies dictionary into a dataframe in pandas with frequencies"""

   frequencies = pd.DataFrame.from_dict(act_frequencies, orient='index')
   frequencies = frequencies.fillna(0)
   
   return frequencies


def in_bindings(activity_frequencies):
    """
    Calculate all potential input bindings of each activity.
    This is used in the dependency graph function of file dep_graph.
    Take dictionary of activities as argument.
    Returns dictionary with possible combinations of input activities.
    """
    fr = activity_frequencies
    in_filter = {}
    in_arcs = {}
    filtered = []
    in_bindings = {}
    all_combinations = []

    inbindings_list = {}
    value_list = []


    for key, value in fr.items():
        for value in value.keys():
            if fr[key][value] != 0:
                filtered.append(value)
            if value not in in_filter:
                in_filter[value] = {}
        in_filter[value] = filtered
        filtered = []

    for key in in_filter:
        for i in in_filter[key]:
            if i not in in_arcs:
                in_arcs[i] = []
            in_arcs[i].append(key)
        
    for key in in_arcs:
        if key not in in_bindings:
            in_bindings[key] = {}
            n = len(in_arcs[key])
        while n > 0:
            combinations_list = list(combinations(in_arcs[key], n))
            all_combinations.extend(combinations_list)
            n -= 1
        in_bindings[key] = all_combinations
        all_combinations = []
    
    for key,value in in_bindings.items():
        for i in value:
            j = []
            for a in i:
                j.append(a)
            value_list.append(j)
        
        inbindings_list[key] = value_list
        value_list = []

    
    return inbindings_list


def out_bindings(activity_frequencies):
    """
    Calculate all potential output bindings of each activity.
    This is used in the dependency graph function of file dep_graph.
    Take dictionary of activities with their sucessors as argument.
    Returns dictionary with possible combinations of output activities.
    """
    fr = activity_frequencies

    out_arcs = {}
    filtered = []
    out_bindings = {}
    all_combinations = []

    outbindings_list = {}
    value_list = []

    for key in fr:
        for value in fr[key]:
            if fr[key][value] != 0:
                filtered.append(value)
        if key not in out_arcs:
            out_arcs[key] = {}
            out_arcs[key] = filtered
        filtered = []

    for key in out_arcs:
        if key not in out_bindings:
            out_bindings[key] = {}
            n = len(out_arcs[key])
        while n > 0:
            combinations_list = list(combinations(out_arcs[key], n))
            all_combinations.extend(combinations_list)
            n -= 1
        out_bindings[key] = all_combinations
        all_combinations = []
    

    for key,value in out_bindings.items():
        for i in value:
            j = []
            for a in i:
                j.append(a)
            value_list.append(j)
        
        outbindings_list[key] = value_list
        value_list = []

    return outbindings_list


def original_start(act_total, activity_freq):
   """
   Identify the start activity(ies) in the log based on the inbindings of each activity
   """
   incoming = in_bindings(activity_freq)
   original_start = list()

   for act in act_total.keys():
      if act not in incoming.keys() and act not in original_start:
         original_start.append(act)

   return original_start



def original_end(act_total, activity_freq):
   """
   Identify the end activity(ies) in the log based on the outbindings of each activity
   """
   outgoing = out_bindings(activity_freq)
   original_end = list()

   for act in act_total.keys():
      if act in outgoing.keys():
         if len(outgoing[act]) == 0 and act not in original_end:
            original_end.append(act)
      else:
         original_end.append(act)
   
   return original_end


def dependency_matrix(frequencies):
   """Generate the dependency matrix Dataframe"""

   freq = frequencies

   def calculate_dependency(pair):
      a, b = pair
      if b == a:
         return freq.loc[a,b]/(freq.loc[a,b] + 1)
      else:
         return (freq.loc[a,b] - freq.loc[b,a])/(freq.loc[a,b] + freq.loc[b,a] + 1)
                  
   
   dependency_matrix = pd.DataFrame(index=freq.index, columns=freq.columns)

   for col in freq.columns:
      for index in freq.index:
         dependency_matrix.loc[index,col] = calculate_dependency((index,col))

   return dependency_matrix


def dependency_dict(dependency_matrix):
   """Convert a dependency matrix Dataframe into a dictionary"""
   
   dependency_dict = dependency_matrix.to_dict('index')

   return dependency_dict


def count_occurrences_between(traces, a, b):
    """
    Count the occurrences of activity b following activity a with at least one other activity in between.
    """
    def count_occurrences_recursive(trace, a, b):
        """Recursively count occurrences of activity b following activity a with at least one other activity in between."""
        count = 0
        if a in trace:
            a_indices = [i for i, activity in enumerate(trace) if activity == a]
            for a_index in a_indices:
                remaining_trace = trace[a_index+1:]
                if b in remaining_trace:
                    b_index = remaining_trace.index(b)
                    # Check if there is at least one activity (other than a or b) between a and b
                    if any(activity != a and activity != b for activity in remaining_trace[:b_index]):
                        count += 1
                    # Continue counting in the remaining part of the trace
                    count += count_occurrences_recursive(remaining_trace, a, b)
        return count

    total_count = 0
    for trace_id, trace in traces.items():
        #print(f"Counting occurrences of {b} following {a} in trace {trace_id}:")
        trace_count = count_occurrences_recursive(trace, a, b)
        #print(f"Trace {trace_id}: {trace_count} occurrences found.")
        total_count += trace_count

    #print(f"Total occurrences of {b} following {a}: {total_count}")
    return total_count


def path_exists_from_to_without_visiting(ts, te, intermediary, traces):
    """
    Check if a path exists from ts to te without visiting the intermediary.
    """
    for trace in traces.values():
        if ts in trace and te in trace:
            ts_index = trace.index(ts)
            te_index = trace.index(te)
            if ts_index < te_index:
                # Extract the subsequence of activities between ts and te
                subsequence = trace[ts_index + 1:te_index]
                # Check if the intermediary exists in the subsequence
                if intermediary not in subsequence:
                    #print(f"Path exists from {ts} to {te} without visiting the intermediary {intermediary}.")
                    return True
    #print(f"No path exists from {ts} to {te} without visiting the intermediary {intermediary} in any trace.")
    return False


# Calculates the LDD measure
def long_distance_dependency(act_total, traces, start_activity, end_activity, AbsUseThres=1, AbsThres=0.95):
    """
    Calculate long-distance dependencies within a case.
    """

    # Initialize dictionary to count long distance dependencies
    long_dep = {a: {b: 0 for b in act_total if b not in start_activity} for a in act_total if a not in start_activity}

    for a in act_total:
        if a in start_activity:
            continue
        freq_a = act_total[a]
        for b in act_total:
            if b in start_activity or a == b:
                continue
            freq_b = act_total[b]
            # Check if escape to end is possible using path existence checks
            for end_activity in end_activity:
                #print(f"Checking paths between {a} and {end_activity} without visiting {b}...")
                if path_exists_from_to_without_visiting(a, end_activity, b, traces) == False or path_exists_from_to_without_visiting(start_activity, end_activity, a, traces) == False or path_exists_from_to_without_visiting(start_activity, end_activity, b, traces) == False:
                    # Calculate the occurrences of activity b following activity a with at least one other activity in between
                    count_ab = count_occurrences_between(traces, a, b)
                    # Calculate the sum of frequencies of activities a and b
                    n_events = freq_a + freq_b
                    # Calculate long-distance dependency using the recent formula
                    LongDistanceDependency = (2 * count_ab) / (n_events + 1) - (2 * abs(freq_a - freq_b)) / (n_events + 1)
                    #print(f"Dependency between {a} and {b}: Count_AB={count_ab}, n_events={n_events}, LongDistanceDependency={LongDistanceDependency}")
                    # Check if the dependency meets the thresholds
                    if count_ab >= AbsUseThres and LongDistanceDependency >= AbsThres:
                        # Add the dependency to the list
                        long_dep[a][b] = LongDistanceDependency
                    break

    return long_dep


def best_dependency(dependency_dict):
    """Create a nested dictionary of all keys in activity_total and their best successor candidates, where the activity is the outer, the successor activity is the inner key and the dependency measure is the inner value"""
    
    best_dependency = {}

    for key,value in dependency_dict.items():
        best={k:v for k,v in value.items() if v==max(value.values()) and v > 0}
        if key not in best_dependency:
            best_dependency[key] = {}
        best_dependency[key] = best
        
    return best_dependency

def best_predecessor(dependency_matrix):
    """
    Create a nested dictionary of all keys in activity_total and their best predecessor candidates
    Args:
    Dependency_matrix (pd.DataFrame): the dataframe obtained from the frequencies matrix by calculating the dependency measures
    Returns: 
    Dictionary (dict): the activity is the outer key, the predecessor activity is the inner key and the dependency measure is the inner value
    """
    
    best_predecessors = {}
    # Create the dependency dict using the columns
    # This shows the dependencies of preecessors, instead of successors
    dependency_by_columns_dict = dependency_matrix.to_dict()

    for key,value in dependency_by_columns_dict.items():
        best_predecessor = {k:v for k,v in value.items() if v==max(value.values()) and v > 0}
        if key not in best_predecessors:
            best_predecessors[key] = {}
        best_predecessors[key] = best_predecessor
        
    return best_predecessors


def dependency_graph(activity_total, original_start, original_end, frequencies, dep_matrix, dependency_dict, long_dep, dependency_threshold=0.98):
    """
    Create a graph with all activities as nodes connected by edges based on frequencies, dependencies, and thresholds.
    Long_dep is a dictionary with long-distance dependency measures of activities in relation to one another, like the dependency measure. It is obtained using the function "def long_distance_dependency(act_total, traces)".
    Args:
    activity_total (dict): contains the activities and their counts
    original_start (list): contains the start activities mined from the traces
    end_start (list): contains the end activities mined from the traces
    frequencies (pd.DataFrame): the same as activity frequencies but is a dataframe
    dep_matrix (pd.DataFrame): contains the dependency measures of an activity in relations to others
    dependency_dict (dict): contains the dependency measures of an activity in relations to others
    long_dep (dict): contains the long-distance dependency measures of an activity in relations to others
    thresholds long_distance=0.8, act_threshold=1, frequency_threshold=1, dependency_threshold=0.9
    Returns:

    """
    # These variables were removed from this function args and moved here
    long_distance=0.9
    act_threshold=1
    # frequency_threshold=1

    Graph = namedtuple("Graph", ["nodes", "edges", "is_directed"])
    dep_graph = Graph
    dep_graph.nodes = []
    dep_graph.edges = []
    dep_graph.is_directed = True

    original_start = original_start
    start_act = list()
    original_end = original_end
    end_act = list()

    next_best = best_dependency(dependency_dict)
    best_pred = best_predecessor(dep_matrix)
    only_one_predecessor = {}

    # Include in the nodes list every activity which has frequency above the threshold
    for key,value in activity_total.items():
        if value >= act_threshold and key not in dep_graph.nodes:
            dep_graph.nodes.append(key)

    
    # For all-activities-connected, build edges between nodes, first based on dependency threshold
    # if a node has NO OUTGOING edge, build it based on the next-best dependency
    for node in dep_graph.nodes:
        if node not in original_end and node not in end_act:
            best = [k for k,v in dependency_dict[node].items() if v > dependency_threshold]
            if len(best) == 0:
                best = next_best[node]
            for successor in best:
                act_edge = (node,successor)
                if act_edge not in dep_graph.edges:
                    dep_graph.edges.append(act_edge)
    # if a node has NO INCOMING edge, build it based on the highest dependency in the dependency matrix (column)
            for edge in dep_graph.edges:
                if node not in edge[1]:
                    if node in best_pred:
                        pred = best_pred[node]
                    else:
                        continue
                    for predecessor in pred:
                        pred_edge = (predecessor,node)
                        if predecessor != node and pred_edge not in dep_graph.edges:
                            dep_graph.edges.append(pred_edge)
                        else:
                            continue
       
    # If there are more than one start activities, create an artificial start
    # and link it to the real starts
    # This is done because a C-net must have only one start 
    if len(original_start) > 1:
        start = 'start'
        for act in original_start:
            act_edge = (start,act)
            if act_edge not in dep_graph.edges:
                dep_graph.edges.append(act_edge)
        start_act.append(start)
        dep_graph.nodes.append(start)

    # If there are more than one end activities, create an artificial end
    # and link the real ends to it
    # This is done because a C-net must have only one end
    if len(original_end) > 1:
        end = 'end'
        for act in original_end:
            act_edge = (act,end)
            if act_edge not in dep_graph.edges:
                dep_graph.edges.append(act_edge)
        end_act.append(end)
        dep_graph.nodes.append(end)
   
    # To guarantee that all activities are connected, identify if there are activities not connected and link them
    # This can happen if an activity has only one incoming binding and lost the race in the next-best dependency race
    # In this case, it should be connected to its only predecessor
    for col in frequencies.columns:
        # Get the index of row columns with frequency > 0
        row_index = frequencies.index[frequencies[col] > 0].tolist()
        # If row_index is a list with only one element, it means that the activity (in the column index) is 
        # only preceeded by one activity (the row_index). An entry in the only_one_predecessor is created.
        # where the key is the activity (column index) and the value is its only predecessor.
        if len(row_index) == 1:
            only_one_predecessor[col] = row_index[0]

    # Now, we need to check if the nodes with only one predecessor are connected, if not, connect them
    # to their only predecessor
    for key in only_one_predecessor.keys():            
        if key not in [edge[1] for edge in dep_graph.edges]:
            dep_graph.edges.append(tuple((only_one_predecessor[key], key)))
            

    # Add edge related to long-distance dependency 
    # and define the special label as the third element of the tuple
    for node in dep_graph.nodes:
        if node not in original_start and node not in start_act and node not in original_end and node not in end_act:
            for k,v in long_dep[node].items():
                if v > long_distance and k not in original_end:
                    act_edge = (node, k)
                    if act_edge not in dep_graph.edges:
                        label = ("(" + str(round(v, 2)) + ")")
                        dep_graph.edges.append(act_edge + (label,))

    return dep_graph


def input_arcs(dep_graph):
    """
    Identify the input activities (arcs) of each activity of a dependency graph
    based on its incoming arcs.
    Take a dependency graph as argument.
    """
    in_arcs = []
    in_bindings = {}

    for node in dep_graph.nodes:
        if node not in ['start', 'end'] and node not in in_bindings.keys():
            in_bindings[node] = []
        for edge in dep_graph.edges:
            if len(edge) == 2 and edge[1] == node and edge[0] not in in_arcs:
                in_arcs.append(edge[0])
        in_bindings[node] = in_arcs
        in_arcs = []

    return in_bindings


def output_arcs(dep_graph):
    """Identify the output activities (arcs) of each activity in a dependency graph
    based on its outgoing arcs.
    Take a dependency graph as argument.
    """
    out_arcs = []
    out_bindings = {}

    for node in dep_graph.nodes:
        if node not in ['start', 'end'] and node not in out_bindings.keys():
            out_bindings[node] = []
        for edge in dep_graph.edges:
            if len(edge) == 2 and edge[0] == node and edge[1] not in out_arcs:
                out_arcs.append(edge[1])
        out_bindings[node] = out_arcs
        out_arcs = []

    return out_bindings


def output_bindings(traces, out_arcs, in_arcs):
    """Find the output bindings for each activity based on its output_arcs (function) and input_arcs (function) of the dependency graph 
    and replay of the traces
    """

    outbindings = {}

    # Iterate over each activity in out_arcs
    for activity in out_arcs:
        outbindings[activity] = []

        # Iterate over each trace in TRACES.values()
        for trace in traces.values():
            bindings = []
            occurrences = [i for i, x in enumerate(trace) if x == activity]

            for i in range(len(occurrences)):
                start_index = occurrences[i]
                end_index = occurrences[i+1] if i < len(occurrences) - 1 else len(trace)
                binding = []
                search_space = trace[start_index:end_index]  # Construct search space from current activity until next occurrence or end of trace

                # print("Search space:", search_space)

                for arc in out_arcs[activity]:
                    # Check if search space is only the activity followed by itself and include the binding
                    if arc == activity and len(search_space) == 1:
                        binding.append(arc)
                    # Check if arc is present in search_space
                    if arc not in search_space:
                        continue

                    # Check if no value in in_arcs[arc] occurs between activity and arc
                    if not any(other in search_space and search_space.index(other) > search_space.index(activity) and search_space.index(other) < search_space.index(arc) for other in in_arcs.get(arc, [])):
                        # We will exclude the activity followed by itself because it was included previously
                        if arc != activity:
                            binding.append(arc)

                # Add the binding to the list of bindings for the current activity
                if binding:
                    bindings.append(binding)

            # Append bindings for the current trace to outbindings
            outbindings[activity].extend(bindings)

   
    cnet_outbindings = {}


    for key, value in outbindings.items():
        if key != 'start' and key!= 'end':
            # Convert nested lists to tuples to make them hashable
            flattened_values = [tuple(sublist) for sublist in value]
            # Sort the tuples to ensure order doesn't matter
            sorted_values = [tuple(sorted(sublist)) for sublist in flattened_values]
            # Count occurrences using Counter
            bindings_counter = Counter(sorted_values)
            # Convert Counter to a dictionary and store it in cnet_outbindings
            cnet_outbindings[key] = dict(bindings_counter)

    return cnet_outbindings


def input_bindings(traces, out_arcs, in_arcs):
    """Find the input bindings for each activity based on its in_arcs and out_arcs of the dependency graph 
    and replay of the traces
    """
    inbindings = {}

    # Iterate over each activity in in_arcs
    for activity in in_arcs:
        inbindings[activity] = []

        # Iterate over each trace in TRACES.values()
        for trace in traces.values():
            bindings = []
            first_occ_binding = []

            occurrences = [i for i, x in enumerate(trace) if x == activity]
            
            # The first search space would not be covered by the loop later on, 
            # because in the loop only search spaces between two occurrences are considered. This is different from the output_bindings search spaces.
            # Here the first search space from the beginning is to be considered, but not the last, from the last occurrence to the end of the trace.
            # Check if in the first occurrence the activity is preceded by one of the in_arcs and include in bindings
            if occurrences:
                if len(trace[:occurrences[0]]) == 1 and trace[0] in in_arcs[activity]:
                    bindings.append([trace[0]])
                elif len(trace[:occurrences[0]]) > 1:
                    for element in trace[:occurrences[0]+1]:
                        if element not in in_arcs[activity]:
                            continue
                        else:
                            # Check if no value in in_arcs[arc] occurs between activity and arc
                            if not any(other in trace[:occurrences[0]+1] and trace[:occurrences[0]+1].index(other) < trace[:occurrences[0]+1].index(activity) and trace[:occurrences[0]+1].index(other) > trace[:occurrences[0]+1].index(element) for other in out_arcs.get(element, [])):
                                first_occ_binding.append(element)
                    if first_occ_binding:
                        bindings.append(first_occ_binding)
                        first_occ_binding = []
                

            for i in range(len(occurrences)):
                start_index = occurrences[i]
                end_index = occurrences[i+1] if i < len(occurrences) - 1 else None
                binding = []
                search_space = trace[start_index:end_index]  # Construct search space from current activity until next occurrence or end of trace


                for arc in in_arcs[activity]:
                    # Check if arc is present in search_space
                    if arc not in search_space:
                        continue

                    # Check if no value in in_arcs[arc] occurs between activity and arc
                    if not any(other in search_space and search_space.index(other) < search_space.index(activity) and search_space.index(other) > search_space.index(arc) for other in out_arcs.get(arc, [])):
                        binding.append(arc)

                # Add the binding to the list of bindings for the current activity
                if binding:
                    bindings.append(binding)

            # Append bindings for the current trace to inbindings
            inbindings[activity].extend(bindings)

   
    cnet_inbindings = {}


    for key, value in inbindings.items():
        if key != 'start'and key!= 'end':
            flattened_values = []
            for sublist in value:
                # Convert nested lists to sets if the sublist has more than one element
                if len(sublist) > 1 and len(set(sublist)) == 1:
                    flattened_values.append((sublist[0],))
                elif len(sublist) > 1 and len(set(sublist)) > 1:
                    flattened_values.append(tuple(set(sublist)))
                else:
                    flattened_values.append(tuple(sublist))
            # Sort the tuples to ensure order doesn't matter
            sorted_values = [tuple(sorted(sublist)) for sublist in flattened_values]
            # Count occurrences using Counter
            bindings_counter = Counter(sorted_values)
            # Convert Counter to a dictionary and store it in cnet_inbindings
            cnet_inbindings[key] = dict(bindings_counter)

    return cnet_inbindings


def ot_graph(graph, act_total, activities, dep_dict, cnet_inbindings, cnet_outbindings, seq_i, seq_o):
    """
    Generate the visualization in GRAPHVIZ of C-nets for the given graph.

    Args:
        graph (Graph): namedtuple("Graph", ["nodes", "edges", "is_directed"]) where nodes are activities and edges are dependencies based on thresholds.
        act_total (dictionary): dictionary representing the total frequency of activities in the log, where the key is the activity and the value is the frequency.
        activities (dictionary): nested dictionary presenting as outer key the activity, as inner key the activities that follow it with frequency as value.
        dep_dict (dictionary): nested dictionary representing the dependency measures between activities.
        cnet_inbindings (dictionary): nested dictionary with the input bindings (inner keys) for each activity (outer keys) based on its output_arcs and input_arcs of the dependency graph generated for the defined thresholds and replay of the traces.
        cnet_outbindings (dictionary): nested dictionary with the output bindings (inner keys) for each activity (outer keys) based on its output_arcs and input_arcs of the dependency graph generated for the defined thresholds and replay of the traces.
    Returns:
        ot_nodes (Dataframe): dataframe containing the nodes of the C-nets to be used in the visualization.
        ot_edges (Dataframe): dataframe containing the edges of the C-nets to be used in the visualization.
    """

    # ---- Create a dataframe of NODES with attributes, based on graph.nodes ----
    nodes_df = pd.DataFrame({'node': [node for node in graph.nodes if node not in ['start', 'end']]})
    nodes_df['act_total'] = nodes_df['node'].map(act_total).astype(str)
    # nodes_df['label'] = nodes_df['node'].map(lambda x: f'<<FONT>{x}</FONT>>')
    nodes_df['label'] = nodes_df['node'].map(lambda x: f'<<FONT>{x}</FONT><BR/><FONT POINT-SIZE="16">{act_total.get(x, "Unknown")}</FONT>>')
    new_columns = {
        'type': 'activity',
        'source': 'NaN', 
        'target': 'NaN',
        'binding': 'NaN',
        'len_binding': 'NaN',
        'color': '#97c2fc',
        'intensity': np.nan, 
        'shape': 'box',
        'size': 2,
        'obj_group': np.nan
    }
    nodes_df = nodes_df.assign(**new_columns)

    # ---- Create a dataframe of EDGES with attributes, based on graph.edges ----
    # First, filter out edges containing 'start' and 'end' activities
    edges_filtered = [edge for edge in graph.edges if 'start' not in edge and 'end' not in edge]
    # Then, it is needed to normalize the list of edges because they are tuples of two elements, but edges of long distance dependencies have a third element, the label
    # After normalization, all edges (tuples) will have three elements, the third one will be NaN if not a long-distance dependency
    col_len = 3
    normalized_edges = [tuple((list(edge_tuple) + [None] * (col_len - len(edge_tuple)))) for edge_tuple in edges_filtered]

    edges_df = pd.DataFrame(normalized_edges, columns=['source','target', 'long_distance_dep'])
    # edges_df = edges_df.replace({None: np.nan})

    # Create other columns for edges attributes
    edges_df['frequency'] = edges_df.apply(lambda row: activities.get(row['source'], {}).get(row['target'], np.nan), axis=1).astype(str)
    edges_df['dependency'] = edges_df.apply(lambda row: '{:.2f}'.format(round(dep_dict.get(row['source'], {}).get(row['target'], np.nan), 2)), axis=1)
    edges_df['label'] = f"freq = {edges_df['frequency']}/dep = {edges_df['dependency']}"
    edges_df['type'] = 'dependency'

    # ---- Create OUTPUT BINDING NODES in the nodes_df dataframe based on the cnet_outbindings dictionary ----
    # OUTPUT BINDING NODES are the nodes conected by dashed line to represent an AND connection
    new_nodes = []

    # Sequential number for outbinding nodes. This is used for the node name
    seq_o = seq_o

    # Iterate over the dictionary
    for source, bindings in cnet_outbindings.items():
        # Iterate over each binding
        for binding, label in bindings.items():
            # Convert binding to string
            #binding_str = ' '.join(binding)
            
            # If binding has multiple elements, create separate rows for each element
            if len(binding) > 1:
                # Iterate over each element in the binding tuple
                for target in binding:
                    # Append node information to the list
                    new_nodes.append({
                        'node': f"o_{seq_o}", 
                        'label': None,
                        'type': 'outbinding',
                        'source': source,
                        'target': target,
                        'binding': binding,
                        'len_binding': len(binding),
                        'color': 'black',
                        'intensity': None,
                        'shape': 'point',
                        'size': 0.7,
                        'obj_group': f'out {source} - {target}'
                    })

                    seq_o += 1

            else:
                # These are SINGLE OUTPUT BINDINGS, not connected to other, they represent OR-relations
                # For single-element bindings, append only one row
                # Get the target from the binding tuple
                target = binding[0]
                # Append node information to the list
                new_nodes.append({
                    'node': f"o_{seq_o}",
                    'label': str(label),
                    'type': 'outbinding',
                    'source': source,
                    'target': target,
                    'binding': binding,
                    'len_binding': len(binding),
                    'color': 'black',
                    'intensity': None,
                    'shape': 'point',
                    'size': 0.7,
                    'obj_group': f'out single {source} - {target}'
                })
                seq_o += 1       

    # This sequential will be returned by the function
    seq_o = seq_o

    # Create DataFrame from new_nodes, append it to the existing nodes dataframe and reorder columns in the final df
    new_nodes_df = pd.DataFrame(new_nodes)
    nodes_df = nodes_df._append(new_nodes_df, ignore_index=True)
    nodes_df = nodes_df[['node','type','source','target','binding','len_binding','label', 'act_total','color','intensity','shape','size','obj_group']]


    # ---- Create INPUT BINDING NODES in the nodes_df dataframe based on the inbindings dictionary ----
    new_inbinding_nodes = []  # List to store new inbinding nodes

    # Sequential number for inbinding nodes. This is used for the node name
    seq_i = seq_i

    # Iterate over the dictionary
    for target, inbindings in cnet_inbindings.items():
        # Iterate over each inbinding
        for inbinding, label in inbindings.items():
            # Convert inbinding to string
            #inbinding_str = ' '.join(inbinding)

            
            # These are the input nodes that are composite (AND relation) and connected to other nodes with dashed line

            # If inbinding has multiple elements, create separate rows for each element
            if len(inbinding) > 1:
                # Iterate over each element in the inbinding tuple
                for source in inbinding:
                    # Append node information to the list
                    new_inbinding_nodes.append({
                        'node': f"i_{seq_i}", 
                        'type': 'inbinding',
                        'source': source,
                        'target': target,
                        'binding': inbinding,
                        'len_binding': len(inbinding),
                        'label': None,
                        'color': 'black',
                        'intensity': None,
                        'shape': 'diamond',
                        'size': 0.7,
                        'obj_group': f'out {target} - {source}'
                    })

                    seq_i += 1

            else:
                # For single-element inbindings, append only one row
                # Get the target from the inbinding tuple
                source = inbinding[0]
                # Append node information to the list
                new_inbinding_nodes.append({
                    'node': f"i_{seq_i}",
                    'type': 'inbinding',
                    'source': source,
                    'target': target,
                    'binding': inbinding,
                    'len_binding': len(inbinding),
                    'label': str(label),
                    'color': 'black',
                    'intensity': None,
                    'shape': 'diamond',
                    'size': 0.7,
                    'obj_group': f'out single {target} - {source}'
                })
                seq_i += 1       

    # This sequential will be returned by the function
    seq_i = seq_i

    # Create DataFrame from new_inbinding_nodes and append it to the existing nodes dataframe
    new_inbinding_nodes_df = pd.DataFrame(new_inbinding_nodes)
    nodes_df = nodes_df._append(new_inbinding_nodes_df, ignore_index=True)


    # ---- Create VISUALIZATION EDGES to connect nodes and dots ----

    # First, create the dataframe of edges to be represented visually
    # Column 'object_relation' is to be used in object-centric and shows if it is intrabinding (between activities of the same object) or interbinding (between activities of different objects)
    vis_edges = pd.DataFrame(columns=['original_edge', 'source', 'target', 'label', 'type', 'color', 'intensity', 'width', 'length', 'object_relation', 'arrow']) 

    # Iterate over rows of nodes_df to populate the visualization dataframe
    # Filter intermediary nodes
    intermediary_nodes = nodes_df[(nodes_df['node'].str.startswith('o_') | nodes_df['node'].str.startswith('i_'))]

    # Group intermediary nodes by source and target
    intermediary_nodes_grouped = intermediary_nodes.groupby(['source', 'target'])

    # Initialize list to store edges data
    edges_data = []

    # Iterate over each group
    for (source, target), group in intermediary_nodes_grouped:
        # Extract intermediary nodes
        o_nodes = group[group['node'].str.startswith('o_')].sort_values(by='len_binding')
        i_nodes = group[group['node'].str.startswith('i_')].sort_values(by='len_binding', ascending=False)
        
        # Create edges between source and o_nodes
        # object relation attribute was populated with values 'start' etc to enable merging the same edge segments in the visualization layer
        #if not o_nodes.empty:
        edges_data.append({'original_edge': f"{source} {target}", 'source': source, 'target': o_nodes.iloc[0]['node'], 'label': '', 'type': 'visualization', 'color': 'black', 'intensity': None, 'width': None, 'length': 1, 'object_relation': 'start', 'arrow': False})
        # Create edges between o_nodes
        for i in range(len(o_nodes) - 1):
            edges_data.append({'original_edge': f"{source} {target}", 'source': o_nodes.iloc[i]['node'], 'target': o_nodes.iloc[i+1]['node'], 'label': '', 'type': 'visualization', 'color': 'black', 'intensity': None, 'width': None, 'length': 1, 'object_relation': 'continue_o', 'arrow': False})
        
        # Create edges between last o_node and first i_node
        #if not o_nodes.empty and not i_nodes.empty:
        label_edge = f"freq = {activities[source][target]} / dep = {dep_dict[source][target]:.2f}"
        edges_data.append({'original_edge': f"{source} {target}", 'source': o_nodes.iloc[-1]['node'], 'target': i_nodes.iloc[0]['node'], 'label':label_edge, 'type': 'visualization', 'color': 'black', 'intensity': None, 'width': None, 'length': 4, 'object_relation': 'middle', 'arrow': False})
        
        # Create edges between i_nodes
        #if not i_nodes.empty:
        for i in range(len(i_nodes) - 1):
            edges_data.append({'original_edge': f"{source} {target}", 'source': i_nodes.iloc[i]['node'], 'target': i_nodes.iloc[i+1]['node'], 'label': '', 'type': 'visualization', 'color': 'black', 'intensity': None, 'width': None, 'length': 1, 'object_relation': 'continue_i', 'arrow': False})
        
        # Create edge from last i_node to target
        edges_data.append({'original_edge': f"{source} {target}", 'source': i_nodes.iloc[-1]['node'], 'target': target, 'label': '', 'type': 'visualization', 'color': 'black', 'intensity': None, 'width': None, 'length': 1, 'object_relation': 'end', 'arrow': True})


    # Populate pyvis_edges DataFrame with edges data
    vis_edges = pd.DataFrame(edges_data)


    # ---- Create EDGES TO CONNECT THE BINDINGS with len > 1 ----
    additional_edges = []

    nodes_df['len_binding'] = pd.to_numeric(nodes_df['len_binding'], errors='coerce')

    # Filter nodes_df to consider only rows with len_binding > 1
    filtered_nodes_df = nodes_df[nodes_df['len_binding'] > 1]


    # OUTPUT bindings

    # Group nodes_df by 'source', 'binding', and 'len_binding' for nodes beginning with 'o_'
    grouped_o_nodes = filtered_nodes_df[filtered_nodes_df['node'].str.startswith('o_')].groupby(['source', 'binding', 'len_binding'])

    # Iterate over groups
    for group_key, group in grouped_o_nodes:
        source, binding, len_binding = group_key
        if group.shape[0] > 1:
            # Extract combinations of nodes to create edges
            o_nodes_comb = list(combinations(group['node'], 2))
            # Iterate over combinations
            for node1, node2 in o_nodes_comb:
                binding_tuple = binding
                # Lookup label in the dictionary
                label = cnet_outbindings.get(source, {}).get(binding_tuple, None)
                if label is not None:
                    # Add edge data
                    additional_edges.append({
                        'original_edge': None,
                        'source': node1,
                        'target': node2,
                        'label': label,
                        'type': 'vis_binding',
                        'color': 'black',
                        'intensity': None,
                        'width': None,
                        'object_relation': 'binding_o'
                    })

    # INPUT bindings

    # Group nodes_df by 'target', 'binding', and 'len_binding' for nodes beginning with 'i_'
    grouped_i_nodes = filtered_nodes_df[filtered_nodes_df['node'].str.startswith('i_')].groupby(['target', 'binding', 'len_binding'])

    # Iterate over groups
    for (target, binding, len_binding), group in grouped_i_nodes:
        if group.shape[0] > 1:
            # Extract combinations of nodes to create edges
            i_nodes_comb = list(combinations(group['node'], 2))
            # Iterate over combinations
            for node1, node2 in i_nodes_comb:
                binding_tuple = binding
                # Lookup label in the dictionary
                label = cnet_inbindings.get(target, {}).get(binding_tuple, None)
                if label is not None:
                    # Add edge data
                    additional_edges.append({
                        'original_edge': None,
                        'source': node1,
                        'target': node2,
                        'label': label,
                        'type': 'vis_binding',
                        'color': 'black',
                        'intensity': None,
                        'width': None,
                        'object_relation': 'binding_i'
                    })

    # Create DataFrame with additional edges
    additional_vis_edges = pd.DataFrame(additional_edges)

    # Create Dataframe with long_dstance_dependency edges
    ldd = []

    for index, row in edges_df.iterrows():
        if row['long_distance_dep'] != None:
            ldd.append({
                        'original_edge': None,
                        'source': row['source'],
                        'target': row['target'],
                        'label': "",
                        'type': 'ldd_visualization',
                        'color': 'red',
                        'intensity': None,
                        'width': None,
                        'object_relation': 'ldd',
                        'arrow': True
                    })

    ldd_edges = pd.DataFrame(ldd)

    # Concatenate the original pyvis_edges DataFrame with additional_pyvis_edges
    vis_edges = pd.concat([vis_edges, additional_vis_edges, ldd_edges], ignore_index=True)

    return nodes_df, vis_edges, seq_i, seq_o


def subgraphs_dict(path):
    """
    Generate the dictionary with object types and respective nodes and edges to be used in the visualization of C-nets.

    Args:
        path (str): the OCEL log path
    Returns:
        ot_graphs_dict (dict): dictionary where the keys are the object types and the values are tuples of nodes and edges.
    """
    ocel, ot_activities, event_to_obj, obj_to_obj = import_log(path)
    flt = flatten_log(ocel, ot_activities)
    logs = read_log(flt)

    all_traces = traces(flt)
   
    ot1_ot2_cardinalities, ot2_ot1_cardinalities = ot_cardinalities(obj_to_obj, event_to_obj, ot_activities) 

    ot_seq = ot_sequence(ot_activities, ot1_ot2_cardinalities, ot2_ot1_cardinalities, event_to_obj)

    ot_subgraphs_dict = {}

    # Initialize the sequence number for in- and outbindings used by function ot_graph
    seq_i = 1
    seq_o = 1

    for obj_type in all_traces:
        ot_traces = all_traces[obj_type]

        act_total = activity_total(logs[obj_type])
        activities = activity_frequencies(logs[obj_type])
        or_start = original_start(act_total, activities)
        or_end = original_end(act_total, activities)

        freq = frequencies(activities)

        dep = dependency_matrix(freq)

        dep_dict = dependency_dict(dep)

        long = long_distance_dependency(act_total, ot_traces, or_start, or_end)
        
        depgraph = dependency_graph(act_total, or_start, or_end, freq, dep, dep_dict, long)

        # Generate the arcs based on the edges of the dep_graph
        in_arcs = input_arcs(depgraph)
        out_arcs = output_arcs(depgraph)

        # Find the bindings in the incoming and outgoing arcs of the graph, after replay (replay.py):
        cnet_outbindings = output_bindings(ot_traces, out_arcs, in_arcs)
        cnet_inbindings = input_bindings(ot_traces, out_arcs, in_arcs) 

        
        # Generate the OT C-nets nodes and edges and store in the dictionary
        ot_nodes, ot_edges, i_seq, o_seq = ot_graph(depgraph, act_total, activities, dep_dict, cnet_inbindings, cnet_outbindings, seq_i, seq_o)

        if obj_type not in ot_subgraphs_dict.keys():
            ot_subgraphs_dict[obj_type] = (ot_nodes, ot_edges)
        
        seq_i = i_seq
        seq_o = o_seq
    
    return ot_activities, ot_seq, ot_subgraphs_dict