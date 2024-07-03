import pathlib
import csv
from io import StringIO
import pandas as pd

import pm4py
from pm4py.statistics.ocel import ot_activities as ot

from flt_import_ocel import *


def flatten_log(ocel, ot_activities):
    """
    Generate a dictionary with flattened logs for each object type in the OCEL 2.0 log.

    Args:
        ocel: the OCEL 2.0 log
        ot_activities (dict): keys are object types and their corresponding activities to be considered from the OCEL log. If no dictionary is given, all the OT and respective activities will be considered.

    Returns:
        Dictionary (dict): keys are object type names and values are the set of activities the ot has.
    """

    
    ot_activities = ot.get_object_type_activities(ocel)

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


def traces(flattened_logs, ot_activities, obj_to_obj, event_to_obj, ot_sequence, relations, cardinalities):
    """
    Mine traces for each object within each object type. The trace is a list of activities (tasks) ordered by timestamp.

    Args:
        flattened_logs (dict): Dictionary with object types as keys and their corresponding csv flattened log as values.

    Returns:
        Dictionary (dict): outer keys are object type names inner keys are objects and values are their corresponding traces.
    """

    # Check if there are pairs of OT with the same quantitiy of objects in all activities
    # If there are, it means that this must be considered when mining their traces. For example, an item and a product. The same product may have several items, so the traces of products must be divided
    # Initialize list to store tuples of objects with the same quantity of objects in all activities
    ot_same_obj_qty = []

    for o_type1 in ot_activities.keys():
        for o_type2 in ot_activities.keys():
            if o_type1 != o_type2:
                # Group by event and activity, then count object types
                grouped = event_to_obj.groupby(['ocel:eid', 'ocel:activity', 'ocel:type']).size().unstack(fill_value=0)
                # Check if the counts of OT1 and OT2 are the same for each activity
                compare_obj_qty = grouped.apply(lambda x: x[o_type1] == x[o_type2], axis=1)
                # Check if all values in the comparison are True
                all_true = compare_obj_qty.all()
                # Add tuple of OT1 and OT2 to list of OT with the same number of objects in all activities
                if all_true:
                    index_ot1 = ot_sequence.index(o_type1)
                    index_ot2 = ot_sequence.index(o_type2)
                    if index_ot1 < index_ot2:
                        pair = (o_type1, o_type2)
                    else:
                        pair = (o_type2, o_type1)
                    if pair not in ot_same_obj_qty:
                        ot_same_obj_qty.append(pair)


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

    if ot_same_obj_qty:
        for pair in ot_same_obj_qty:
            pair_cardinality = cardinalities[pair[0]][pair[1]]
            if pair_cardinality[0] == 1 and pair_cardinality[1] > 1:
                pair0 = pair[0]
                pair1 = pair[1]
                normalized_obj = f'normalized - {pair1}'
                all_traces[normalized_obj] = {}
                grouped_many = relations.groupby('ocel:type_2')
                for obj_type, group in grouped_many:
                    if obj_type == pair1:
                        for _,row in group.iterrows():
                            pair1_obj = row['ocel:oid_2']
                            pair0_obj = row['ocel:oid']
                            trace = all_traces[pair0].get(pair0_obj)
                            if trace:
                                combined_key = f'{pair1_obj} - {pair0_obj}'
                                all_traces[normalized_obj][combined_key] = trace

            #elif pair_cardinality[0] > 1 and pair_cardinality[1] == 1:

            else:
                continue

    return all_traces



def traces_no_divergence(flattened_logs, ot_activities, obj_to_obj, event_to_obj, ot_sequence, relations, cardinalities):
    """  
    Mine traces for each object within each object type eliminating divergence by using OT sequence

    Args:
        flattened_logs (dict): Dictionary with object types as keys and their corresponding csv flattened log as values.

    Returns:
        Dictionary (dict): outer keys are object type names inner keys are objects and values are their corresponding traces.
    """    


    # FIRST, mine all traces and store in a dictionary that contains OT as outer keys, objects as inner keys and their traces as values
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


    # SECOND, check if there are traces with repeated tasks, to ckeck if they are due to divergence
    # Find the next OT of the current OT, because divergence is caused by it
    result = {}
    for obj_type in all_traces:
        for i, item in enumerate(ot_sequence):
            if item == obj_type:
                current_ot = ot_sequence[i]
                next_ot = ot_sequence[i+1]
                break
        # Check if there are loops of length 1 in the traces of the object type
        for obj, trace in all_traces[current_ot].items():
            # Initialize variables to track consecutive counts
            current_activity = None
            current_count = 0
            max_consecutive_count = 0
            
            # Loop through the activities to count consecutive occurrences
            for activity in trace:
                if activity == current_activity:
                    current_count += 1
                else:
                    # Update max_consecutive_count if needed
                    if current_count > max_consecutive_count:
                        max_consecutive_count = current_count

                    # Count the number of objects associated with the key in the DataFrame
                    count_related_objects = obj_to_obj[[obj_to_obj['ocel:oid'] == activity], [obj_to_obj['ocel:type_2'] == next_ot]].shape[0]
                    if count_related_objects == max_consecutive_count:
                        pass
                    """     count_related_objects = df[(df['ocel:oid'] == current_ot) & (df['ocel:oid_2'].str.contains(next_ot))].shape[0]

                    # Store the result in the dictionary
                    result[obj] = {
                        'max_consecutive_count': max_consecutive_count,
                        'count_related_objects': count_related_objects
                                current_activity = activity
                                current_count = 1} """
                
                

    # A function to remove activity duplicates from a trace 
    def remove_consecutive_duplicates(traces):
        def process_list(lst):
            if not lst:
                return lst
            result = [lst[0]]
            for item in lst[1:]:
                if item != result[-1]:
                    result.append(item)
            return result
        # Iterate over each key in the dictionary and process the list
        for key in traces:
            traces[key] = process_list(traces[key])
        
        return traces
    
    # Remove activity duplicates from traces where divergence was detected

    #  CODE HERE

    # Check if there are pairs of OT with the same quantitiy of objects in all activities
    # If there are, it means that this must be considered when mining their traces. For example, an item and a product. The same product may have several items, so the traces of products must be divided
    # into traces of products related to them
    # Initialize list to store tuples of objects with the same quantity of objects in all activities
    ot_same_obj_qty = []

    for o_type1 in ot_activities.keys():
        for o_type2 in ot_activities.keys():
            if o_type1 != o_type2:
                # Group by event and activity, then count object types
                grouped = event_to_obj.groupby(['ocel:eid', 'ocel:activity', 'ocel:type']).size().unstack(fill_value=0)
                # Check if the counts of OT1 and OT2 are the same for each activity
                compare_obj_qty = grouped.apply(lambda x: x[o_type1] == x[o_type2], axis=1)
                # Check if all values in the comparison are True
                all_true = compare_obj_qty.all()
                # Add tuple of OT1 and OT2 to list of OT with the same number of objects in all activities
                if all_true:
                    index_ot1 = ot_sequence.index(o_type1)
                    index_ot2 = ot_sequence.index(o_type2)
                    if index_ot1 < index_ot2:
                        pair = (o_type1, o_type2)
                    else:
                        pair = (o_type2, o_type1)
                    if pair not in ot_same_obj_qty:
                        ot_same_obj_qty.append(pair)


    # Substitute the traces of the second OT in the tuple ot_same_obj_qty for the traces of the first OT in the tuple, which comes first in the OT sequence
    # This is done by checking the cardinalities first. If ot ocel:oid has cardinality 1 in relation to ot ocel:oid2 but not vice-versa, it means that one object of ot ocel:oid2 
    # is related to many objects of ocel:oid and these 'subtraces'need to substitute the traces of ot ocel:oid 
    if ot_same_obj_qty:
        for pair in ot_same_obj_qty:
            pair_cardinality = cardinalities[pair[0]][pair[1]]
            if pair_cardinality[0] == 1 and pair_cardinality[1] > 1:
                pair0 = pair[0]
                pair1 = pair[1]
                normalized_obj = f'normalized - {pair1}'
                all_traces[normalized_obj] = {}
                grouped_many = relations.groupby('ocel:type_2')
                for obj_type, group in grouped_many:
                    if obj_type == pair1:
                        for _,row in group.iterrows():
                            pair1_obj = row['ocel:oid_2']
                            pair0_obj = row['ocel:oid']
                            trace = all_traces[pair0].get(pair0_obj)
                            if trace:
                                combined_key = f'{pair1_obj} - {pair0_obj}'
                                all_traces[normalized_obj][combined_key] = trace

            else:
                continue

    return all_traces