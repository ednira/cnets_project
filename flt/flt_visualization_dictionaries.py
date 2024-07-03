from itertools import combinations
import pandas as pd
import numpy as np
import graphviz



def visualization_dict(graph, act_total, activities, dep_dict, cnet_inbindings, cnet_outbindings):
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
        png file: png file containing the visualization of the C-nets model that represents the process.
    """

    # ---- Create a dataframe of NODES with attributes, based on graph.nodes ----
    nodes_df = pd.DataFrame({'node': [node for node in graph.nodes if node not in ['start', 'end']]})
    nodes_df['label'] = nodes_df['node'].map(act_total).astype(str)
    nodes_df['label'] = nodes_df['node'] + '\n' + nodes_df['label']
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
    # Then, normalize the list of edges because they are tuples of two elements, but edges of long distance dependencies have a third element, the label
    # After normalization, all edges (tuples) will have three elements, the third one will be NaN if not a long-distance dependency
    col_len = 3
    normalized_edges = [tuple((list(edge_tuple) + [None] * (col_len - len(edge_tuple)))) for edge_tuple in edges_filtered]

    edges_df = pd.DataFrame(normalized_edges, columns=['source','target', 'long_distance_dep'])
    # edges_df = edges_df.replace({None: np.nan})

    # Create other columns for edges attributes
    edges_df['frequency'] = edges_df.apply(lambda row: activities.get(row['source'], {}).get(row['target'], np.nan), axis=1).astype(str)
    edges_df['dependency'] = edges_df.apply(lambda row: '{:.2f}'.format(round(dep_dict.get(row['source'], {}).get(row['target'], np.nan), 2)), axis=1)
    edges_df['label'] = "freq = " + edges_df['frequency'] + ' / ' + "dep = " + edges_df['dependency']
    edges_df['type'] = 'dependency'

    # ---- Create OUTPUT BINDING NODES in the nodes_df dataframe based on the cnet_outbindings dictionary ----
    # OUTPUT BINDING NODES are the nodes conected by dashed line to represent an AND connection
    new_nodes = []

    # Sequential number for nodes. This is used for the node name
    seq = 1

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
                        'node': f"o_{seq}", 
                        'label': None,
                        'type': 'outbinding',
                        'source': source,
                        'target': target,
                        'binding': binding,
                        'len_binding': len(binding),
                        'color': 'black',
                        'intensity': None,
                        'shape': 'point',
                        'size': 0.5,
                        'obj_group': None
                    })

                    seq += 1

            else:
                # These are SINGLE OUTPUT BINDINGS, not connected to other, they represent OR-relations
                # For single-element bindings, append only one row
                # Get the target from the binding tuple
                target = binding[0]
                # Append node information to the list
                new_nodes.append({
                    'node': f"o_{seq}",
                    'label': str(label),
                    'type': 'outbinding',
                    'source': source,
                    'target': target,
                    'binding': binding,
                    'len_binding': len(binding),
                    'color': 'black',
                    'intensity': None,
                    'shape': 'point',
                    'size': 0.5,
                    'obj_group': None
                })
                seq += 1       

    # Create DataFrame from new_nodes, append it to the existing nodes dataframe and reorder columns in the final df
    new_nodes_df = pd.DataFrame(new_nodes)
    nodes_df = nodes_df._append(new_nodes_df, ignore_index=True)
    nodes_df = nodes_df[['node','type','source','target','binding','len_binding','label','color','intensity','shape','size','obj_group']]


    # ---- Create INPUT BINDING NODES in the nodes_df dataframe based on the inbindings dictionary ----
    new_inbinding_nodes = []  # List to store new inbinding nodes

    # Sequential number for nodes. This is used for the node name
    seq = 1

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
                        'node': f"i_{seq}", 
                        'type': 'inbinding',
                        'source': source,
                        'target': target,
                        'binding': inbinding,
                        'len_binding': len(inbinding),
                        'label': None,
                        'color': 'black',
                        'intensity': None,
                        'shape': 'dot',
                        'size': 0.5,
                        'obj_group': None
                    })

                    seq += 1

            else:
                # For single-element inbindings, append only one row
                # Get the target from the inbinding tuple
                source = inbinding[0]
                # Append node information to the list
                new_inbinding_nodes.append({
                    'node': f"i_{seq}",
                    'type': 'inbinding',
                    'source': source,
                    'target': target,
                    'binding': inbinding,
                    'len_binding': len(inbinding),
                    'label': str(label),
                    'color': 'black',
                    'intensity': None,
                    'shape': 'dot',
                    'size': 0.5,
                    'obj_group': None
                })
                seq += 1       

    # Create DataFrame from new_inbinding_nodes and append it to the existing nodes dataframe
    new_inbinding_nodes_df = pd.DataFrame(new_inbinding_nodes)
    nodes_df = nodes_df._append(new_inbinding_nodes_df, ignore_index=True)


    # ---- Create VISUALIZATION EDGES to connect nodes and dots ----

    # First, create the dataframe of edges to be represented visually
    # Column 'object_relation' is to be used in object-centric and shows if it is intrabinding (between activities of the same object) or interbinding (between activities of different objects)
    vis_edges = pd.DataFrame(columns=['original_edge', 'source', 'target', 'label', 'type', 'color', 'intensity', 'width', 'object_relation', 'arrow']) 

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
        edges_data.append({'original_edge': f"{source} {target}", 'source': source, 'target': o_nodes.iloc[0]['node'], 'label': '', 'type': 'visualization', 'color': 'black', 'intensity': None, 'width': None, 'length': None, 'object_relation': None, 'arrow': False})
        for i in range(len(o_nodes) - 1):
            edges_data.append({'original_edge': f"{source} {target}", 'source': o_nodes.iloc[i]['node'], 'target': o_nodes.iloc[i+1]['node'], 'label': '', 'type': 'visualization', 'color': 'black', 'intensity': None, 'width': None, 'length': 1, 'object_relation': None, 'arrow': False})
        
        # Create edges between last o_node and first i_node
        label_edge = f"{activities[source][target]} / {dep_dict[source][target]:.2f}"
        edges_data.append({'original_edge': f"{source} {target}", 'source': o_nodes.iloc[-1]['node'], 'target': i_nodes.iloc[0]['node'], 'label':label_edge, 'type': 'visualization', 'color': 'black', 'intensity': None, 'width': None, 'length': 6, 'object_relation': None, 'arrow': False})
        
        # Create edges between i_nodes
        for i in range(len(i_nodes) - 1):
            edges_data.append({'original_edge': f"{source} {target}", 'source': i_nodes.iloc[i]['node'], 'target': i_nodes.iloc[i+1]['node'], 'label': '', 'type': 'visualization', 'color': 'black', 'intensity': None, 'width': None, 'length': 1, 'object_relation': None, 'arrow': False})
        
        # Create edge from last i_node to target
        edges_data.append({'original_edge': f"{source} {target}", 'source': i_nodes.iloc[-1]['node'], 'target': target, 'label': '', 'type': 'visualization', 'color': 'black', 'intensity': None, 'width': None, 'length': 1, 'object_relation': None, 'arrow': True})


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
                        'object_relation': None
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
                        'object_relation': None
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
                        'object_relation': None,
                        'arrow': True
                    })

    ldd_edges = pd.DataFrame(ldd)

    # Concatenate the original pyvis_edges DataFrame with additional_pyvis_edges
    vis_edges = pd.concat([vis_edges, additional_vis_edges, ldd_edges], ignore_index=True)



    # ---- DATAFRAMES WITH NODES AND EDGES ----

    return nodes_df, vis_edges