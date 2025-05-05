import warnings

import random
import pandas as pd
import graphviz
import seaborn as sns

from IPython import display
from PIL import Image

from pathlib import Path

warnings.filterwarnings('ignore')


def all_ot_visualization(ot_activities, subgraphs_dict, profile=None):
  
    graph = graphviz.Digraph()
    
    profile_error = []

    if profile is None:
        profile = list(ot_activities.keys())
    else:
        for obj_type in profile:
            if obj_type not in ot_activities.keys():
                profile_error.append(obj_type)
        if len(profile_error) > 0:
            raise ValueError(f"Object type(s) {profile_error} not in the log.")
        else:
            profile = profile
            

    palette = sns.color_palette('hls', desat=0.8, n_colors=12).as_hex()

    ot_info = {}

    for obj_type in profile:
        if not palette:
            palette = sns.color_palette('hls', desat=0.8).as_hex()
            random.shuffle(palette)
        ot_color = random.choice(palette)
        palette.remove(ot_color)
        if obj_type not in ot_info:
            color = 'color'
            ot_info[obj_type] = {}
        ot_info[obj_type][color] = ot_color

    
    def add_new_columns(df, obj_type):
        df['obj_type'] = obj_type
        df['ot_color'] = ot_info[obj_type][color]
        return df

    
    filtered_profile_nodes = [add_new_columns(subgraphs_dict[obj_type][0], obj_type) for obj_type in profile if obj_type in subgraphs_dict]
    
    all_ot_nodes_df = pd.concat(filtered_profile_nodes)

    filtered_profile_edges = [add_new_columns(subgraphs_dict[obj_type][1], obj_type) for obj_type in profile if obj_type in subgraphs_dict]

    all_ot_edges_df = pd.concat(filtered_profile_edges)

    
    filter_nodes_binding_len1 = all_ot_nodes_df[all_ot_nodes_df['len_binding'] == 1]
    nodes_len1 = set(filter_nodes_binding_len1['node'])

    
    valid_sources = set(all_ot_edges_df[(all_ot_edges_df['source'].str.startswith('o_')) & (all_ot_edges_df['target'].str.startswith('i_'))]['source'])
    valid_targets = set(all_ot_edges_df[(all_ot_edges_df['source'].str.startswith('o_')) & (all_ot_edges_df['target'].str.startswith('i_'))]['target'])
    
    
    valid_sources = {source for source in valid_sources if all_ot_edges_df[all_ot_edges_df['source'] == source].shape[0] == 1}
    valid_targets = {target for target in valid_targets if all_ot_edges_df[all_ot_edges_df['target'] == target].shape[0] == 1}

    
    activity_nodes = set(all_ot_nodes_df[all_ot_nodes_df['type'] == 'activity']['node'])

    valid_sources = nodes_len1.intersection(valid_sources)
    valid_targets = nodes_len1.intersection(valid_targets)

    
    edges1 = all_ot_edges_df[all_ot_edges_df.apply(lambda row: row['source'] in activity_nodes and row['target'] in valid_sources, axis=1)]
    
    edges2 = all_ot_edges_df[all_ot_edges_df.apply(lambda row: row['source'] in valid_sources and row['target'] in valid_targets, axis=1)]
    
    edges3 = all_ot_edges_df[all_ot_edges_df.apply(lambda row: row['source'] in valid_targets and row['target'] in activity_nodes, axis=1)]

    
    edges_to_merge = pd.DataFrame()

   
    for _, edge1 in edges1.iterrows():
        source1, target1 = edge1['source'], edge1['target']

        
        middle_edges = edges2[edges2['source'] == target1]

        for _, edge2 in middle_edges.iterrows():
            target2 = edge2['target']

            
            final_edges = edges3[(edges3['source'] == target2) & (edges3['target'].isin(activity_nodes))]

            for _, edge3 in final_edges.iterrows():
                
                edges_to_merge = pd.concat([edges_to_merge, pd.DataFrame([edge1]), pd.DataFrame([edge2]), pd.DataFrame([edge3])], ignore_index=True)

    edges_to_merge = edges_to_merge.drop_duplicates()
    
    
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

    
    resulting_edges = pd.concat([joined_edges, remaining_edges]).reset_index(drop=True)

    nodes_of_joined_edges = set(joined_edges['source']).union(set(joined_edges['target']))

    
    nodes_to_merge = set(edges_to_merge['source']).union(set(edges_to_merge['target']))
    
    resulting_nodes = set(resulting_edges['source']).union(set(resulting_edges['target']))
    nodes_not_used = nodes_to_merge - resulting_nodes

    all_ot_nodes_df = all_ot_nodes_df[~all_ot_nodes_df['node'].isin(nodes_not_used)]

    
    for _, row in all_ot_nodes_df.iterrows():
        shape = 'point' if row['shape'] == 'dot' else row['shape']
        width = str(row['size']) if row['type'] == 'activity' else '0.3in'
        height = 'default' if row['type'] == 'activity' else '0.3in'
        label = row['label'] if row['label'] != None else None
        tooltip = row['tooltip'] if row['tooltip'] != None else None


        if row['type'] != 'activity':
            graph.node(row['node'], xlabel=label, label='', fontname='sans-serif', color='black', fontsize='20', fillcolor=row['ot_color'], shape=shape, width=width, height=height, style='filled') 
        else:
            graph.node(row['node'], fontname='sans-serif', fontsize='24', label=label, tooltip=tooltip, shape=shape, color= 'white', fillcolor='lightcyan:powderblue', gradientangle='270', width=width, height=height, style='rounded,filled', margin='0.4', penwidth='2')
            


    for _, row in resulting_edges.iterrows():
        length_str = str(row['length'])
        if row['type'] == 'vis_binding':
            graph.edge(row['source'], row['target'], fontname='sans-serif', fontsize='20', fontcolor=row['ot_color'], label=str(row['label']), color='black', style='dashed', penwidth=str(row['width']), arrowhead='none', labeldistance='1.5')
           
        elif row['arrow'] and row['type'] != 'ldd_visualization':
            graph.edge(row['source'], row['target'], fontsize='20', label=str(row['label']), color='black', penwidth=str(row['width']), minlen=length_str, arrowhead='vee', dir='forward')
        elif row['arrow'] and row['type'] == 'ldd_visualization':
            graph.edge(row['source'], row['target'], color='red', style='dotted', penwidth=str(row['width']), arrowhead='vee')
        
        else:
            graph.edge(row['source'], row['target'], fontname='sans-serif', fontsize='20', label=str(row['label']), fontcolor=row['ot_color'], color='black', penwidth=str(row['width']), minlen=length_str, arrowhead='none')
                
                

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
    
    
    graph.body.append(subgraph_legend)

    
    graph.node('invisible', '', style='invis')

    
    graph.edge('invisible', 'legend_entities', style='invis', minlen='60')
   


    graph.attr(colorscheme='pastel28', nodesep='0.5', ranksep='0.5', pad='1', splines='spline', rankdir='TB') 

    
    graphviz.set_jupyter_format('svg')

    
    graph.render('graphviz_cnet', format='svg', cleanup=True, view=False)

    
    class InteractiveSVG:
        def __init__(self, file_name='./graphviz_cnet.svg'):
            with open(file_name, 'r', encoding='utf-8') as svg_fh:
                self.svg_content = svg_fh.read()
                
        def _repr_html_(self):
            return self.svg_content

    display.display(InteractiveSVG('./graphviz_cnet.svg'))