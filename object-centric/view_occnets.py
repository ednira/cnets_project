import random
import pandas as pd
import graphviz
import seaborn as sns


def all_ot_visualization(ot_activities, ot_sequence, subgraphs_dict, profile=None):
    """
    Generate the visualization in GRAPHVIZ of C-nets based on the given subgraphs.

    Args:
        subgraphs_dict (dictionary): dictionary where the keys are the object types and the values are tuples of nodes and edges.
    Returns:
        png file: png file containing the visualization of the C-nets model that represents the process.
    """
    
    # ---- VISUALIZATION IN GRAPHVIZ ----

    # Create graph
    graph = graphviz.Digraph()
    
   # Check if the user defined a profile, if not generate the model for all OT
    if profile is None:
        profile = list(ot_activities.keys())
    else:
        profile == profile

    palette = sns.color_palette('hls', desat=0.8, n_colors=12).as_hex()
    # random.shuffle(palette)

    # Iterate over the OT to produce a subgraph for each
    ot_info = {}

    for obj_type in ot_sequence:
        if obj_type in profile:
            if not palette:
            # Refill the palette if all colors are alreadyused
                palette = sns.color_palette('hls', desat=0.8).as_hex()
                random.shuffle(palette)
            ot_color = random.choice(palette)
            palette.remove(ot_color)
            if obj_type not in ot_info:
                color = 'color'
                ot_info[obj_type] = {}
            ot_info[obj_type][color] = ot_color

    # New columns for OT and ot_color
    def add_new_columns(df, obj_type):
        df['obj_type'] = obj_type
        df['ot_color'] = ot_info[obj_type][color]
        return df

    # Filter nodes and edges by profile
    filtered_profile_nodes = [add_new_columns(subgraphs_dict[obj_type][0], obj_type) for obj_type in profile if obj_type in subgraphs_dict]
    
    all_ot_nodes_df = pd.concat(filtered_profile_nodes)

    filtered_profile_edges = [add_new_columns(subgraphs_dict[obj_type][1], obj_type) for obj_type in profile if obj_type in subgraphs_dict]

    all_ot_edges_df = pd.concat(filtered_profile_edges)

    # Select nodes that are bindings len 1
    filter_nodes_binding_len1 = all_ot_nodes_df[all_ot_nodes_df['len_binding'] == 1]
    nodes_len1 = set(filter_nodes_binding_len1['node'])

    # Filter nodes based on condition: source begins with 'o_' and target begins with 'i_', to avoid merging edges that have composed bindings
    valid_sources = set(all_ot_edges_df[(all_ot_edges_df['source'].str.startswith('o_')) & (all_ot_edges_df['target'].str.startswith('i_'))]['source'])
    valid_targets = set(all_ot_edges_df[(all_ot_edges_df['source'].str.startswith('o_')) & (all_ot_edges_df['target'].str.startswith('i_'))]['target'])
    
    # Filter from them those which are only in this type of edge and have no other edge as source or target, respectively
    valid_sources = {source for source in valid_sources if all_ot_edges_df[all_ot_edges_df['source'] == source].shape[0] == 1}
    valid_targets = {target for target in valid_targets if all_ot_edges_df[all_ot_edges_df['target'] == target].shape[0] == 1}

    # Filter from all nodes the ones that are activities and not bindings
    activity_nodes = set(all_ot_nodes_df[all_ot_nodes_df['type'] == 'activity']['node'])

    valid_sources = nodes_len1.intersection(valid_sources)
    valid_targets = nodes_len1.intersection(valid_targets)

    # Select edges from activity to valid source
    edges1 = all_ot_edges_df[all_ot_edges_df.apply(lambda row: row['source'] in activity_nodes and row['target'] in valid_sources, axis=1)]
    # Select edges from valid source to valid target
    edges2 = all_ot_edges_df[all_ot_edges_df.apply(lambda row: row['source'] in valid_sources and row['target'] in valid_targets, axis=1)]
    # Select edges from valid target to activity
    edges3 = all_ot_edges_df[all_ot_edges_df.apply(lambda row: row['source'] in valid_targets and row['target'] in activity_nodes, axis=1)]

    # Create df to join edges1, edges2, and edges3
    edges_to_merge = pd.DataFrame()

    # Iterate through each group of edges to find the related sequence of edges
    for _, edge1 in edges1.iterrows():
        source1, target1 = edge1['source'], edge1['target']

        # Find corresponding middle edge (target1 as source)
        middle_edges = edges2[edges2['source'] == target1]

        for _, edge2 in middle_edges.iterrows():
            target2 = edge2['target']

            # Find corresponding final edge (target2 as source)
            final_edges = edges3[(edges3['source'] == target2) & (edges3['target'].isin(activity_nodes))]

            for _, edge3 in final_edges.iterrows():
                # Combine these edges into the merged_edges DataFrame
                edges_to_merge = pd.concat([edges_to_merge, pd.DataFrame([edge1]), pd.DataFrame([edge2]), pd.DataFrame([edge3])], ignore_index=True)

    edges_to_merge = edges_to_merge.drop_duplicates()
    
    # The other edges that will not be merged
    remaining_edges = pd.merge(all_ot_edges_df,edges_to_merge, indicator=True, how='outer').query('_merge=="left_only"').drop('_merge', axis=1)
    
    def merge_labels(x):
        labels = x.dropna()
        colors = edges_to_merge.loc[labels.index, 'ot_color'].dropna()
        
        formatted_labels = [f'<FONT COLOR="{color}">{label.strip()}</FONT>' for label, color in zip(labels, colors) if label.strip()]
        merged_label = '<BR ALIGN="LEFT"/>'.join(formatted_labels)
        merged_label = f'<{merged_label}>'

        return merged_label

    joined_edges = edges_to_merge.groupby(['original_edge', 'object_relation']).agg({
        'label': merge_labels,
        'obj_type': 'first',
        'ot_color': 'first',
        'type': 'first',
        'source': 'first',
        'target': 'first',
        'width': 'first',
        'color': 'first',
        'intensity': 'first',
        'arrow': 'first',
        'length': 'first'
    }).reset_index()    

    # Combine the edges which were merged to all other edges to obtain all graph edges after merging
    resulting_edges = pd.concat([joined_edges, remaining_edges]).reset_index(drop=True)

    nodes_of_joined_edges = set(joined_edges['source']).union(set(joined_edges['target']))

    # Identify the nodes belonging to edges merged and remove them from all_nodes df
    nodes_to_merge = set(edges_to_merge['source']).union(set(edges_to_merge['target']))
    
    resulting_nodes = set(resulting_edges['source']).union(set(resulting_edges['target']))
    nodes_not_used = nodes_to_merge - resulting_nodes

    all_ot_nodes_df = all_ot_nodes_df[~all_ot_nodes_df['node'].isin(nodes_not_used)]

    # Add nodes
    for _, row in all_ot_nodes_df.iterrows():
        shape = 'point' if row['shape'] == 'dot' else row['shape']
        width = str(row['size']) if row['type'] == 'activity' else '0.3in'
        height = 'default' if row['type'] == 'activity' else '0.3in'
        label = row['label'] if row['label'] != None else None
        tooltip = f"FREQUENCY: {row['act_total']}" if row['act_total'] != None else None


        if row['type'] != 'activity':
            # if row['node'] not in nodes_of_joined_edges:
            #     graph.node(row['node'], xlabel=label, color='black', fontsize='18', fillcolor='gray', shape=shape, width=width, height=height, style='filled') # , group=row['obj_group']
            # else:
            graph.node(row['node'], xlabel=label, label='', fontname='sans-serif', color='black', fontsize='20', fillcolor=row['ot_color'], shape=shape, width=width, height=height, style='filled') # , group=row['obj_group']
        else:
            graph.node(row['node'], fontname='sans-serif', fontsize='24', label=label, tooltip=tooltip, shape=shape, color= 'white', fillcolor='lightcyan:powderblue', gradientangle='270', width=width, height=height, style='rounded,filled', margin='0.4', penwidth='2')
            # rank += row['node'] + " "


    # Add edges
    for _, row in resulting_edges.iterrows():
        length_str = str(row['length'])
        if row['type'] == 'vis_binding': # this is the dashed line conecting binding groups
            graph.edge(row['source'], row['target'], fontname='sans-serif', fontsize='20', fontcolor=row['ot_color'], label=str(row['label']), color='black', style='dashed', penwidth=str(row['width']), arrowhead='none', labeldistance='1.5')
        # Add arrowhead to the edge that points to the target node    
        elif row['arrow'] and row['type'] != 'ldd_visualization':
            graph.edge(row['source'], row['target'], fontsize='20', label=str(row['label']), color='black', penwidth=str(row['width']), minlen=length_str, arrowhead='vee', dir='forward')
        elif row['arrow'] and row['type'] == 'ldd_visualization':
            graph.edge(row['source'], row['target'], color='red', style='dotted', penwidth=str(row['width']), arrowhead='vee')
        # # This the middle edge that has info on freq / dep
        # elif row['object_relation'] == 'middle':
        #     graph.edge(row['source'], row['target'], fontname='sans-serif', label=str(row['label']), color=ot_color, penwidth=str(row['width']), arrowhead='none')
        else:
            graph.edge(row['source'], row['target'], fontname='sans-serif', fontsize='20', label=str(row['label']), fontcolor=row['ot_color'], color='black', penwidth=str(row['width']), minlen=length_str, arrowhead='none')
                
                

    

    # ---------------------------------------------------------
    # Create LEGEND

    # Create the legend in HTML
    table_rows = ""
    for obj_type, info in ot_info.items():
        color = info['color']
        table_rows += f"""    
            <tr>
                <td align="left" colspan="25"><font point-size="25">{obj_type}</font></td>
                <td align="left" colspan="3" bgcolor="{color}">&nbsp;</td>
            </tr>
        """
    legend_table = f"""
        <table border="0" cellborder="0" cellspacing="16">
            <tr>
                <td align="left" colspan="25"><font point-size="25"><b>Object Type</b></font></td>
                <td align="left" colspan="5"><font point-size="25"><b>Color</b></font></td>
            </tr>
            {table_rows}
        </table>
    """
    subgraph_legend = f"""
        subgraph cluster_legend {{
            id = legend
            colorscheme = x11
            fillcolor = ghostwhite
            label = <<font point-size="26"><b>Legend</b></font>>
            fontname="sans-serif"
            margin = 30
            pencolor = gray70
            style = filled
            shape = box
            

            legend_entities [
                shape = plaintext
                style = "" // leave blank to revert to the normal default styles
                fontname="sans-serif" 
                label = <{legend_table}>
            ]
        }}
    """
    
    # Append the legend in html to the graph
    graph.body.append(subgraph_legend)

    # First, add an invisible node to position the legend
    graph.node('invisible', '', style='invis')

    # Connect the invisible node to the legend to position it
    graph.edge('invisible', 'legend_entities', style='invis', minlen='60')
   


    graph.attr(colorscheme='pastel28', nodesep='0.5', ranksep='0.5', pad='1', splines='spline', rankdir='TB') # , ratio='1.7' , newrank='false'

    # Render the graph
    graph.render('graphviz_cnet', format='png', cleanup=True)

    # Display the graph
    graph.view()