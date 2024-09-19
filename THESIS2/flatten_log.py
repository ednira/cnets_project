import csv
from io import StringIO

import pm4py
from pm4py.statistics.ocel import ot_activities as ot


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



def remove_consecutive_duplicates(traces):
    # Function to remove consecutive duplicates in a trace
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




def traces_no_divergence(flattened_logs, ot_activities, event_to_obj, ot_sequence, relations, cardinalities):
    """  
    Mine traces for each object within each object type eliminating divergence by using OT sequence

    Args:
        flattened_logs (dict): Dictionary with object types as keys and their corresponding csv flattened log as values.

    Returns:
        Dictionary (dict): outer keys are object type names inner keys are objects and values are their corresponding traces.
    """    


    # FIRST, mine all traces of all OT and store in a dictionary that contains OT as outer keys, objects as inner keys and their traces as values
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


    # SECOND, check if there are traces with repeated tasks, ckeck if they are due to divergence
    # Find the next OT of the current OT, because divergence is caused by it
    
    for obj_type in all_traces:
        for i, item in enumerate(ot_sequence):
            if item == obj_type:
                current_ot = ot_sequence[i]
                if i + 1 < len(ot_sequence):
                    next_ot = ot_sequence[i + 1]
                else:
                    next_ot = None
                break

        # If next_ot is None, we can't proceed to the next ot
        if next_ot is None:
            continue
        
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
                    current_activity = activity
                    current_count = 1
                    if max_consecutive_count > 1:
                        # Count the number of objects associated with the key in the DataFrame
                        count_related_objects = relations[(relations['ocel:oid'] == obj) & (relations['ocel:type_2'] == next_ot)].shape[0]
                        if count_related_objects == max_consecutive_count:
                            all_traces[current_ot][obj] = remove_consecutive_duplicates({obj: trace})[obj]

    return all_traces