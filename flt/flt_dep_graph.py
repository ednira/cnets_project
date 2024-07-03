import pandas as pd
from collections import namedtuple

from flt_bindings import *



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


def dependency_graph(activity_total, original_start, original_end, frequencies, dep_matrix, dependency_dict, long_dep, long_distance=0.8, act_threshold=1, frequency_threshold=1, dependency_threshold=0.9):
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
        # If row_index is a list with only one element, it means that the activity (in the column index)
        # is only preceeded by one activity (the row_index). A entry in the only_one_predecessor is created.
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