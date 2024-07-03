from flt_dep_matrix import *
from flt_dep_graph import *
from flt_bindings import *
from flt_replay import *



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