import pygraphviz as pgv



def pygraph_visualization(graph, act_total, activity_frequencies, dep_dict):
    """Create a visualization for the graph in Pygraphviz"""
    grapho = graph
    act_total = act_total
    activities = activity_frequencies
    dependencies = dep_dict
    # The graph is created. Note that strict is set to False, to allow self-loops
    G = pgv.AGraph(strict=False, directed=True)

    G.add_nodes_from(grapho.nodes)

    # Add dges to the plot 
    # Distinguish long-distance edges based on tuple length
    # because the third element is its label
    for edge in grapho.edges:
        if edge[0] == 'start' or edge[1] == 'end':
            label = ''
        elif len(edge) == 3:
            label = edge[2]
        else:
            for key,value in activities.items():
                for k,v in value.items():
                    if edge[0] == key and edge[1] == k:
                        label = (str(v) + "(" + str(round(dependencies[edge[0]][edge[1]], 2)) + ")")
        G.add_edge((edge[0],edge[1]), label=label)

    # Attributes set the direction of the graph, the node shape, color and style
    G.graph_attr['rankdir'] = 'LR'
    G.node_attr['shape'] = 'square'
    #G.node_attr['style'] = 'rounded'
    G.node_attr['fillcolor'] = 'lightblue' 
    G.node_attr['style'] = 'filled'
    #G.node_attr['fixedsize'] = 'true'

    # Including the activity total inside the nodes
    for key in act_total:
        text = key + '\n' + str(act_total[key])
        G.add_node(key, label=text)

    # The graph is plotted
    G.draw('graph_cnet_frequencies.png', prog='dot')