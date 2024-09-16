from import_ocel import *
from flatten_log import *
from dep_matrix import *
from dep_graph import *
from bindings import *
from replay import *
from long_distance import *
from ot_graph import *

def subgraphs_dict(path,long_distance=0.9,act_threshold=1, frequency_threshold=10, dependency_threshold=0.95):
    """
    Generate the dictionary with object types and respective nodes and edges to be used in the visualization of C-nets.

    Args:
        path (str): the OCEL log
    Returns:
        ot_graphs_dict (dict): dictionary where the keys are the object types and the values are tuples of nodes and edges.
    """
    ocel, ot_activities, event_to_obj, obj_to_obj = import_log(path)
    flt = flatten_log(ocel, ot_activities)
    logs = read_log(flt)

    all_traces = traces(flt)
    # all_traces = traces_no_divergence(flt, ot_activities, event_to_obj, ot_seq, relations, cardinalities)

    ot_subgraphs_dict = {}

    # Initialize the sequence number for in- and outbindings used by function ot_graph
    seq_i = 1
    seq_o = 1

    for obj_type in all_traces:
        act_threshold = act_threshold
        frequency_threshold = frequency_threshold
        dependency_threshold = dependency_threshold
        ot_traces = all_traces[obj_type]

        act_total = activity_total(logs[obj_type])
        activities = activity_frequencies(logs[obj_type])
        or_start = original_start(act_total, activities)
        or_end = original_end(act_total, activities)

        freq = frequencies(activities)

        dep = dependency_matrix(freq)

        dep_dict = dependency_dict(dep)

        long = long_distance_dependency(act_total, ot_traces, or_start, or_end)

        depgraph = dependency_graph(act_total, or_start, or_end, freq, dep, dep_dict, long, long_distance, act_threshold, frequency_threshold, dependency_threshold)

        # Generate the arcs based on the edges of the dep_graph
        in_arcs = input_arcs(depgraph)
        out_arcs = output_arcs(depgraph)

        # Find the bindings in the incoming and outgoing arcs of the graph, after replay (replay.py):
        output, cnet_outbindings = output_bindings(ot_traces, out_arcs, in_arcs)
        input, cnet_inbindings = input_bindings(ot_traces, out_arcs, in_arcs) 

        
        # Generate the OT C-nets nodes and edges and store in the dictionary
        ot_nodes, ot_edges, i_seq, o_seq = ot_graph(depgraph, act_total, activities, dep_dict, cnet_inbindings, cnet_outbindings, seq_i, seq_o)

        if obj_type not in ot_subgraphs_dict.keys():
            ot_subgraphs_dict[obj_type] = (ot_nodes, ot_edges)
        
        seq_i = i_seq
        seq_o = o_seq
    
    return ot_subgraphs_dict