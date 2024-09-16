from itertools import combinations



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

# The two next fucntions enable calculating the potential bindings
# This function allows to discover the start activity (has no precedent activities)
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