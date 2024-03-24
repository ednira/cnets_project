from collections import namedtuple
from bindings import *



def best_dependency(dependency_dict):
    """Create a dictionary of all activity_total and their best successor candidates"""
    
    best_dependency = {}

    for key,value in dependency_dict.items():
        best={k:v for k,v in value.items() if v==max(value.values())}
        if key not in best_dependency:
            best_dependency[key] = {}
        best_dependency[key] = best
        
    return best_dependency


def dependency_graph(activity_total, activity_frequencies, dependency_dict, long_dep, long_distance=0.9, act_threshold=1, frequency_threshold=1, dependency_threshold=0.9):
    """Create a dictionary with all activity_total connected based on frequencies, dependencies, and thresholds.
    Long_dep is a dictionary with long-distance dependency measures of activities in relation to one another, like the dependency measure.
    It is obtained using the function "def long_distance_dependency(act_total, traces)".
    The resutlt is like this:
    {'a': {'e': 0.8641975308641975, 'b': -0.2903225806451613, 'c': -0.2903225806451613, 'd': -0.6551724137931034}, 'e': {'a': 0, 'b': 0, 'c': 0, 'd': 0}, 
    'b': {'a': 0, 'e': -0.2903225806451613, 'c': 0, 'd': 0}, 'c': {'a': 0, 'e': -0.2903225806451613, 'b': 0, 'd': 0}, 'd': {'a': 0, 'e': 0, 'b': 0, 'c': 0}}
    """

    Graph = namedtuple("Graph", ["nodes", "edges", "is_directed"])
    dep_graph = Graph
    dep_graph.nodes = []
    dep_graph.edges = []
    dep_graph.is_directed = True

    original_start = list()
    start_act = list()
    original_end = list()
    end_act = list()

    incoming = in_bindings(activity_frequencies)
    next_best = best_dependency(dependency_dict)

    # Include in the nodes list every activity which has frequency above the threshold
    for key,value in activity_total.items():
        if value >= act_threshold and key not in dep_graph.nodes:
            dep_graph.nodes.append(key)

    # Identify the start activity(ies)
    for node in dep_graph.nodes:
        if node not in incoming.keys() and node not in original_start:
            original_start.append(node)

    # Identify the end activity(ies)
    for node in dep_graph.nodes:
        for k,v in next_best[node].items():
            if v <= 0 and node not in original_end:
                original_end.append(node)
    
    # For all-activities-connected, build edges between nodes, first based on dependency threshold
    # Then, if a node has no outgoing edge, build it based on the next-best dependency
    for node in dep_graph.nodes:
        if node not in original_end and node not in end_act:
            best = [k for k,v in dependency_dict[node].items() if v > dependency_threshold]
            if len(best) == 0:
                best = next_best[node]
            for successor in best:
                act_edge = (node,successor)
                if act_edge not in dep_graph.edges:
                    dep_graph.edges.append(act_edge)
        
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
    # In this case, it is connected to its only predecessor
    for node in dep_graph.nodes:
        if node in incoming.keys() and len(incoming[node]) == 1 and (tuple(incoming[node][0])[0],node) not in dep_graph.edges:
            dep_graph.edges.append((tuple(incoming[node][0])[0],node))

    # Add edge related to long-distance dependency 
    # and define the special label as the third element of the tuple
    for node in dep_graph.nodes:
        if node not in start_act and node not in original_end and node not in end_act:
            for k,v in long_dep[node].items():
                if v > long_distance and k not in original_end:
                    act_edge = (node, k)
                    label = ("(" + str(round(v, 2)) + ")")
                    act_edge = (node, k, label)
                if act_edge not in dep_graph.edges:
                    dep_graph.edges.append(act_edge)

    return dep_graph, end_act, start_act, original_start, original_end