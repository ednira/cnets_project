import warnings
import pathlib
from collections import Counter, namedtuple
import csv
from io import StringIO
from itertools import combinations

import pandas as pd
import numpy as np

import pm4py
from pm4py.statistics.ocel import ot_activities as ot

warnings.filterwarnings('ignore')



def import_log(ocel_path):
    
    file_extension = pathlib.Path(ocel_path).suffix
    
    if file_extension == '.sqlite':
        ocel = pm4py.read_ocel2_sqlite(ocel_path)
    elif file_extension == '.json':
        ocel = pm4py.read_ocel2_json(ocel_path)
    elif file_extension == '.xml':
        ocel = pm4py.read_ocel2_xml(ocel_path)
    else:
        raise Exception("The file formats supported are sqlite, json, ans xml.")


    try:

        
        ot_activities = ot.get_object_type_activities(ocel)
    

        
        obj_to_obj = ocel.o2o
        event_to_obj = ocel.relations

        return ocel, ot_activities, event_to_obj, obj_to_obj

    
    except FileNotFoundError:
        return None
   
    except Exception as e:
        print("An error occurred:", str(e))
        return None
    


def ot_act_stats(event_to_obj):
    
    unique_activities = event_to_obj[['ocel:eid', 'ocel:activity']].drop_duplicates()
    total_act = unique_activities['ocel:activity'].value_counts().to_dict()


    
    ot_counts = (
        event_to_obj.groupby(['ocel:activity', 'ocel:type'])
        .size()
        .unstack(fill_value=0)
        .to_dict(orient='index')
    )

    obj_mean = {
        activity: {obj_type: np.round(np.mean(count / total_act[activity]),2)
                for obj_type,count in counts.items()}
        for activity,counts in ot_counts.items()
    }

    
    obj_counts = event_to_obj.groupby(["ocel:activity", "ocel:eid", "ocel:type"]).size().reset_index(name="count")

    
    obj_aggregated = obj_counts.groupby(["ocel:activity", "ocel:type"])["count"].agg(["median", "min", "max"]).reset_index()

   
    obj_median = (
        obj_aggregated.groupby("ocel:activity")
        .apply(lambda x: dict(zip(x["ocel:type"], np.round(x["median"]).astype(int))))
        .to_dict()
    )

    obj_min = (
        obj_aggregated.groupby("ocel:activity")
        .apply(lambda x: dict(zip(x["ocel:type"], x["min"])))
        .to_dict()
    )

    obj_max = (
        obj_aggregated.groupby("ocel:activity")
        .apply(lambda x: dict(zip(x["ocel:type"], x["max"])))
        .to_dict()
    )

    return total_act, ot_counts, obj_mean, obj_median, obj_min, obj_max




def flatten_log(ocel, ot_activities):

    flattened_logs = {}
    
    for o_type in ot_activities.keys():
        flt = pm4py.ocel_flattening(ocel, o_type)
        flt_csv = flt.to_csv()
        if o_type not in flattened_logs.keys():
            flattened_logs[o_type] = flt_csv
    
    return flattened_logs



def read_log(flattened_logs):

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



def activity_total(log):
   
   act_total = dict()
   
   for caseID in log:
      for i in range(0, len(log[caseID])):
         ai = log[caseID] [i] [0]
         if ai not in act_total:
            act_total[ai] = 0
         act_total[ai] += 1

   return act_total


def activity_frequencies(log):
   
   act_frequencies = dict()

   for caseID in log:
      for i in range(0, len(log[caseID])-1): 
         ai = log[caseID] [i] [0]
         aj = log[caseID] [i+1] [0]
         if ai not in act_frequencies:
            act_frequencies[ai] = dict()
         if aj not in act_frequencies[ai]:
            act_frequencies[ai][aj] = 0
         act_frequencies[ai][aj] += 1
         if aj not in act_frequencies:
            act_frequencies[aj] = dict()
   

   for key in act_frequencies:
      if key not in act_frequencies[key]:
         act_frequencies[key][key] = 0
   
   return act_frequencies

def frequencies(act_frequencies):

   frequencies = pd.DataFrame.from_dict(act_frequencies, orient='index')
   frequencies = frequencies.fillna(0)
   
   return frequencies


def in_bindings(activity_frequencies):
    
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


def original_start(act_total, activity_freq):
   
   incoming = in_bindings(activity_freq)
   original_start = list()

   for act in act_total.keys():
      if act not in incoming.keys() and act not in original_start:
         original_start.append(act)

   return original_start



def original_end(act_total, activity_freq):
   
   outgoing = out_bindings(activity_freq)
   original_end = list()

   for act in act_total.keys():
      if act in outgoing.keys():
         if len(outgoing[act]) == 0 and act not in original_end:
            original_end.append(act)
      else:
         original_end.append(act)
   
   return original_end


def dependency_matrix(frequencies):

   freq = frequencies

   def calculate_dependency(pair):
      a, b = pair
      if b == a:
         return freq.loc[a,b]/(freq.loc[a,b] + 1)
      else:
         return (freq.loc[a,b] - freq.loc[b,a])/(freq.loc[a,b] + freq.loc[b,a] + 1)
                  
   
   dependency_matrix = pd.DataFrame(index=freq.index, columns=freq.columns)

   for col in freq.columns:
      for index in freq.index:
         dependency_matrix.loc[index,col] = calculate_dependency((index,col))

   return dependency_matrix


def dependency_dict(dependency_matrix):
   
   dependency_dict = dependency_matrix.to_dict('index')

   return dependency_dict


def count_occurrences_between(traces, a, b):
    
    def count_occurrences_recursive(trace, a, b):
        
        count = 0
        if a in trace:
            a_indices = [i for i, activity in enumerate(trace) if activity == a]
            for a_index in a_indices:
                remaining_trace = trace[a_index+1:]
                if b in remaining_trace:
                    b_index = remaining_trace.index(b)
                    if any(activity != a and activity != b for activity in remaining_trace[:b_index]):
                        count += 1
                    count += count_occurrences_recursive(remaining_trace, a, b)
        return count

    total_count = 0
    for trace_id, trace in traces.items():
        trace_count = count_occurrences_recursive(trace, a, b)
        total_count += trace_count

    return total_count


def path_exists_from_to_without_visiting(ts, te, intermediary, traces):
    for trace in traces.values():
        if ts in trace and te in trace:
            ts_index = trace.index(ts)
            te_index = trace.index(te)
            if ts_index < te_index:
                
                subsequence = trace[ts_index + 1:te_index]
                
                if intermediary not in subsequence:
                    
                    return True
    
    return False



def long_distance_dependency(act_total, traces, start_activity, end_activity, AbsUseThres=1, AbsThres=0.95):

    
    long_dep = {a: {b: 0 for b in act_total if b not in start_activity} for a in act_total if a not in start_activity}

    for a in act_total:
        if a in start_activity:
            continue
        freq_a = act_total[a]
        for b in act_total:
            if b in start_activity or a == b:
                continue
            freq_b = act_total[b]
            
            for end_activity in end_activity:
                
                if path_exists_from_to_without_visiting(a, end_activity, b, traces) == False or path_exists_from_to_without_visiting(start_activity, end_activity, a, traces) == False or path_exists_from_to_without_visiting(start_activity, end_activity, b, traces) == False:
                    
                    count_ab = count_occurrences_between(traces, a, b)
                    
                    n_events = freq_a + freq_b
                    
                    LongDistanceDependency = (2 * count_ab) / (n_events + 1) - (2 * abs(freq_a - freq_b)) / (n_events + 1)
                    
                    if count_ab >= AbsUseThres and LongDistanceDependency >= AbsThres:
                        
                        long_dep[a][b] = LongDistanceDependency
                    break

    return long_dep


def best_dependency(dependency_dict):
    
    best_dependency = {}

    for key,value in dependency_dict.items():
        best={k:v for k,v in value.items() if v==max(value.values()) and v > 0}
        if key not in best_dependency:
            best_dependency[key] = {}
        best_dependency[key] = best
        
    return best_dependency

def best_predecessor(dependency_matrix):
    
    best_predecessors = {}
    
    dependency_by_columns_dict = dependency_matrix.to_dict()

    for key,value in dependency_by_columns_dict.items():
        best_predecessor = {k:v for k,v in value.items() if v==max(value.values()) and v > 0}
        if key not in best_predecessors:
            best_predecessors[key] = {}
        best_predecessors[key] = best_predecessor
        
    return best_predecessors


def dependency_graph(activity_total, original_start, original_end, frequencies, dep_matrix, dependency_dict, long_dep, dependency_threshold):
    
    long_distance=0.9
    act_threshold=1

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

    
    for key,value in activity_total.items():
        if value >= act_threshold and key not in dep_graph.nodes:
            dep_graph.nodes.append(key)

    
    for node in dep_graph.nodes:
        if node not in original_end and node not in end_act:
            best = [k for k,v in dependency_dict[node].items() if v > dependency_threshold]
            if len(best) == 0:
                best = next_best[node]
            for successor in best:
                act_edge = (node,successor)
                if act_edge not in dep_graph.edges:
                    dep_graph.edges.append(act_edge)
    
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
       
     
    if len(original_start) > 1:
        start = 'start'
        for act in original_start:
            act_edge = (start,act)
            if act_edge not in dep_graph.edges:
                dep_graph.edges.append(act_edge)
        start_act.append(start)
        dep_graph.nodes.append(start)

   
    if len(original_end) > 1:
        end = 'end'
        for act in original_end:
            act_edge = (act,end)
            if act_edge not in dep_graph.edges:
                dep_graph.edges.append(act_edge)
        end_act.append(end)
        dep_graph.nodes.append(end)
   
    
    for col in frequencies.columns:
       
        row_index = frequencies.index[frequencies[col] > 0].tolist()
        
        if len(row_index) == 1:
            only_one_predecessor[col] = row_index[0]

    
    for key in only_one_predecessor.keys():            
        if key not in [edge[1] for edge in dep_graph.edges]:
            dep_graph.edges.append(tuple((only_one_predecessor[key], key)))
            

    
    for node in dep_graph.nodes:
        if node not in original_start and node not in start_act and node not in original_end and node not in end_act:
            for k,v in long_dep[node].items():
                if v > long_distance and k not in original_end:
                    act_edge = (node, k)
                    if act_edge not in dep_graph.edges:
                        label = ("(" + str(round(v, 2)) + ")")
                        dep_graph.edges.append(act_edge + (label,))

    return dep_graph


def input_arcs(dep_graph):
    
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


def output_arcs(dep_graph):
    
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


def output_bindings(traces, out_arcs, in_arcs):
    

    outbindings = {}

    
    for activity in out_arcs:
        outbindings[activity] = []

        
        for trace in traces.values():
            bindings = []
            occurrences = [i for i, x in enumerate(trace) if x == activity]

            for i in range(len(occurrences)):
                start_index = occurrences[i]
                end_index = occurrences[i+1] if i < len(occurrences) - 1 else len(trace)
                binding = []
                search_space = trace[start_index:end_index]  

                for arc in out_arcs[activity]:
                    
                    if arc == activity and len(search_space) == 1:
                        binding.append(arc)
                    
                    if arc not in search_space:
                        continue

                    
                    if not any(other in search_space and search_space.index(other) > search_space.index(activity) and search_space.index(other) < search_space.index(arc) for other in in_arcs.get(arc, [])):
                        
                        if arc != activity:
                            binding.append(arc)

                
                if binding:
                    bindings.append(binding)

            
            outbindings[activity].extend(bindings)

   
    cnet_outbindings = {}


    for key, value in outbindings.items():
        if key != 'start' and key!= 'end':
            
            flattened_values = [tuple(sublist) for sublist in value]
            
            sorted_values = [tuple(sorted(sublist)) for sublist in flattened_values]
            
            bindings_counter = Counter(sorted_values)
            
            cnet_outbindings[key] = dict(bindings_counter)

    return cnet_outbindings


def input_bindings(traces, out_arcs, in_arcs):
    
    inbindings = {}

    
    for activity in in_arcs:
        inbindings[activity] = []

        
        for trace in traces.values():
            bindings = []
            first_occ_binding = []

            occurrences = [i for i, x in enumerate(trace) if x == activity]
            
            if occurrences:
                if len(trace[:occurrences[0]]) == 1 and trace[0] in in_arcs[activity]:
                    bindings.append([trace[0]])
                elif len(trace[:occurrences[0]]) > 1:
                    for element in trace[:occurrences[0]+1]:
                        if element not in in_arcs[activity]:
                            continue
                        else:
                            
                            if not any(other in trace[:occurrences[0]+1] and trace[:occurrences[0]+1].index(other) < trace[:occurrences[0]+1].index(activity) and trace[:occurrences[0]+1].index(other) > trace[:occurrences[0]+1].index(element) for other in out_arcs.get(element, [])):
                                first_occ_binding.append(element)
                    if first_occ_binding:
                        bindings.append(first_occ_binding)
                        first_occ_binding = []
                

            for i in range(len(occurrences)):
                start_index = occurrences[i]
                end_index = occurrences[i+1] if i < len(occurrences) - 1 else None
                binding = []
                search_space = trace[start_index:end_index]  


                for arc in in_arcs[activity]:
                    
                    if arc not in search_space:
                        continue

                    
                    if not any(other in search_space and search_space.index(other) < search_space.index(activity) and search_space.index(other) > search_space.index(arc) for other in out_arcs.get(arc, [])):
                        binding.append(arc)

                
                if binding:
                    bindings.append(binding)

            
            inbindings[activity].extend(bindings)

   
    cnet_inbindings = {}


    for key, value in inbindings.items():
        if key != 'start'and key!= 'end':
            flattened_values = []
            for sublist in value:
                
                if len(sublist) > 1 and len(set(sublist)) == 1:
                    flattened_values.append((sublist[0],))
                elif len(sublist) > 1 and len(set(sublist)) > 1:
                    flattened_values.append(tuple(set(sublist)))
                else:
                    flattened_values.append(tuple(sublist))
            
            sorted_values = [tuple(sorted(sublist)) for sublist in flattened_values]
            
            bindings_counter = Counter(sorted_values)
            
            cnet_inbindings[key] = dict(bindings_counter)

    return cnet_inbindings


def ot_graph(graph, act_total, total_activities, ot_counts, mean_dict, median_dict, min_dict, max_dict, activities, dep_dict, cnet_inbindings, cnet_outbindings, seq_i, seq_o):
   
    nodes_df = pd.DataFrame({'node': [node for node in graph.nodes if node not in ['start', 'end']]})
    nodes_df['act_total'] = nodes_df['node'].map(act_total).astype(str)
    
    
    nodes_df['label'] = nodes_df['node'].map(lambda x: f'<<FONT POINT-SIZE="25">{x}</FONT>>')

    
    def generate_tooltip(activity):
        
        obj_counts = ot_counts.get(activity, {})
        mean_values = mean_dict.get(activity, {})
        median_values = median_dict.get(activity, {})
        min_values = min_dict.get(activity, {})
        max_values = max_dict.get(activity, {})

        tooltip_lines = []

        for obj, count in obj_counts.items():
            if count > 0:
                mean = mean_values.get(obj, 0)
                median = median_values.get(obj, "N/A")
                min_val = min_values.get(obj, "N/A")
                max_val = max_values.get(obj, "N/A")
                
                tooltip_lines.append(
                    f"OT {obj}: {count}, mean = {mean}, median = {median}, min = {min_val}, max = {max_val}"
                )
        merged_tooltip = '\n'.join(tooltip_lines)

        return merged_tooltip
    

    nodes_df["tooltip"] = nodes_df['node'].map(generate_tooltip)
    

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

    
    edges_filtered = [edge for edge in graph.edges if 'start' not in edge and 'end' not in edge]
    
    col_len = 3
    normalized_edges = [tuple((list(edge_tuple) + [None] * (col_len - len(edge_tuple)))) for edge_tuple in edges_filtered]

    edges_df = pd.DataFrame(normalized_edges, columns=['source','target', 'long_distance_dep'])
    
    edges_df['frequency'] = edges_df.apply(lambda row: activities.get(row['source'], {}).get(row['target'], np.nan), axis=1).astype(str)
    edges_df['dependency'] = edges_df.apply(lambda row: '{:.2f}'.format(round(dep_dict.get(row['source'], {}).get(row['target'], np.nan), 2)), axis=1)
    edges_df['label'] = f"freq = {edges_df['frequency']}/dep = {edges_df['dependency']}"
    edges_df['type'] = 'dependency'

    
    new_nodes = []

    
    seq_o = seq_o

    
    for source, bindings in cnet_outbindings.items():
        
        for binding, label in bindings.items():
            
            if len(binding) > 1:
                
                for target in binding:
                    
                    new_nodes.append({
                        'node': f"o_{seq_o}", 
                        'label': None,
                        'type': 'outbinding',
                        'source': source,
                        'target': target,
                        'binding': binding,
                        'len_binding': len(binding),
                        'color': 'black',
                        'intensity': None,
                        'shape': 'point',
                        'size': 0.7,
                        'obj_group': f'out {source} - {target}'
                    })

                    seq_o += 1

            else:
                
                target = binding[0]
                
                new_nodes.append({
                    'node': f"o_{seq_o}",
                    'label': str(label),
                    'type': 'outbinding',
                    'source': source,
                    'target': target,
                    'binding': binding,
                    'len_binding': len(binding),
                    'color': 'black',
                    'intensity': None,
                    'shape': 'point',
                    'size': 0.7,
                    'obj_group': f'out single {source} - {target}'
                })
                seq_o += 1       

    
    seq_o = seq_o

   
    new_nodes_df = pd.DataFrame(new_nodes)
    nodes_df = nodes_df._append(new_nodes_df, ignore_index=True)
    nodes_df = nodes_df[['node','type','source','target','binding','len_binding','label', 'tooltip', 'act_total','color','intensity','shape','size','obj_group']]


    
    new_inbinding_nodes = []  

    
    seq_i = seq_i

    
    for target, inbindings in cnet_inbindings.items():
        
        for inbinding, label in inbindings.items():
            
            if len(inbinding) > 1:
                
                for source in inbinding:
                    
                    new_inbinding_nodes.append({
                        'node': f"i_{seq_i}", 
                        'type': 'inbinding',
                        'source': source,
                        'target': target,
                        'binding': inbinding,
                        'len_binding': len(inbinding),
                        'label': None,
                        'color': 'black',
                        'intensity': None,
                        'shape': 'diamond',
                        'size': 0.7,
                        'obj_group': f'out {target} - {source}'
                    })

                    seq_i += 1

            else:
                
                source = inbinding[0]
                
                new_inbinding_nodes.append({
                    'node': f"i_{seq_i}",
                    'type': 'inbinding',
                    'source': source,
                    'target': target,
                    'binding': inbinding,
                    'len_binding': len(inbinding),
                    'label': str(label),
                    'color': 'black',
                    'intensity': None,
                    'shape': 'diamond',
                    'size': 0.7,
                    'obj_group': f'out single {target} - {source}'
                })
                seq_i += 1       

    
    seq_i = seq_i

    
    new_inbinding_nodes_df = pd.DataFrame(new_inbinding_nodes)
    nodes_df = nodes_df._append(new_inbinding_nodes_df, ignore_index=True)

    vis_edges = pd.DataFrame(columns=['original_edge', 'source', 'target', 'label', 'type', 'color', 'intensity', 'width', 'length', 'object_relation', 'arrow']) 

   
    intermediary_nodes = nodes_df[(nodes_df['node'].str.startswith('o_') | nodes_df['node'].str.startswith('i_'))]

    
    intermediary_nodes_grouped = intermediary_nodes.groupby(['source', 'target'])

    edges_data = []

   
    for (source, target), group in intermediary_nodes_grouped:
       
        o_nodes = group[group['node'].str.startswith('o_')].sort_values(by='len_binding')
        i_nodes = group[group['node'].str.startswith('i_')].sort_values(by='len_binding', ascending=False)
        
       
        edges_data.append({'original_edge': f"{source} {target}", 'source': source, 'target': o_nodes.iloc[0]['node'], 'label': '', 'type': 'visualization', 'color': 'black', 'intensity': None, 'width': None, 'length': 1, 'object_relation': 'start', 'arrow': False})
       
        for i in range(len(o_nodes) - 1):
            edges_data.append({'original_edge': f"{source} {target}", 'source': o_nodes.iloc[i]['node'], 'target': o_nodes.iloc[i+1]['node'], 'label': '', 'type': 'visualization', 'color': 'black', 'intensity': None, 'width': None, 'length': 1, 'object_relation': 'continue_o', 'arrow': False})
        
       
        label_edge = f"freq = {activities[source][target]} / dep = {dep_dict[source][target]:.2f}"
        edges_data.append({'original_edge': f"{source} {target}", 'source': o_nodes.iloc[-1]['node'], 'target': i_nodes.iloc[0]['node'], 'label':label_edge, 'type': 'visualization', 'color': 'black', 'intensity': None, 'width': None, 'length': 4, 'object_relation': 'middle', 'arrow': False})
        
        
        for i in range(len(i_nodes) - 1):
            edges_data.append({'original_edge': f"{source} {target}", 'source': i_nodes.iloc[i]['node'], 'target': i_nodes.iloc[i+1]['node'], 'label': '', 'type': 'visualization', 'color': 'black', 'intensity': None, 'width': None, 'length': 1, 'object_relation': 'continue_i', 'arrow': False})
        
        
        edges_data.append({'original_edge': f"{source} {target}", 'source': i_nodes.iloc[-1]['node'], 'target': target, 'label': '', 'type': 'visualization', 'color': 'black', 'intensity': None, 'width': None, 'length': 1, 'object_relation': 'end', 'arrow': True})


    vis_edges = pd.DataFrame(edges_data)


    additional_edges = []

    nodes_df['len_binding'] = pd.to_numeric(nodes_df['len_binding'], errors='coerce')

    filtered_nodes_df = nodes_df[nodes_df['len_binding'] > 1]

    grouped_o_nodes = filtered_nodes_df[filtered_nodes_df['node'].str.startswith('o_')].groupby(['source', 'binding', 'len_binding'])

    
    for group_key, group in grouped_o_nodes:
        source, binding, len_binding = group_key
        if group.shape[0] > 1:
            
            o_nodes_comb = list(combinations(group['node'], 2))
            
            for node1, node2 in o_nodes_comb:
                binding_tuple = binding
                
                label = cnet_outbindings.get(source, {}).get(binding_tuple, None)
                if label is not None:
                   
                    additional_edges.append({
                        'original_edge': None,
                        'source': node1,
                        'target': node2,
                        'label': label,
                        'type': 'vis_binding',
                        'color': 'black',
                        'intensity': None,
                        'width': None,
                        'object_relation': 'binding_o'
                    })

    
    grouped_i_nodes = filtered_nodes_df[filtered_nodes_df['node'].str.startswith('i_')].groupby(['target', 'binding', 'len_binding'])

    
    for (target, binding, len_binding), group in grouped_i_nodes:
        if group.shape[0] > 1:
           
            i_nodes_comb = list(combinations(group['node'], 2))
            
            for node1, node2 in i_nodes_comb:
                binding_tuple = binding
                
                label = cnet_inbindings.get(target, {}).get(binding_tuple, None)
                if label is not None:
                    
                    additional_edges.append({
                        'original_edge': None,
                        'source': node1,
                        'target': node2,
                        'label': label,
                        'type': 'vis_binding',
                        'color': 'black',
                        'intensity': None,
                        'width': None,
                        'object_relation': 'binding_i'
                    })

   
    additional_vis_edges = pd.DataFrame(additional_edges)

   
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
                        'object_relation': 'ldd',
                        'arrow': True
                    })

    ldd_edges = pd.DataFrame(ldd)

    
    vis_edges = pd.concat([vis_edges, additional_vis_edges, ldd_edges], ignore_index=True)

    return nodes_df, vis_edges, seq_i, seq_o


def subgraphs_dict(path, dependency_threshold):
    
    ocel, ot_activities, event_to_obj, obj_to_obj = import_log(path)
    flt = flatten_log(ocel, ot_activities)
    logs = read_log(flt)

    all_traces = traces(flt)

    activity_counts, ot_counts, mean_dict, median_dict, min_dict, max_dict = ot_act_stats(event_to_obj)

    ot_subgraphs_dict = {}

    
    seq_i = 1
    seq_o = 1

    for obj_type in all_traces:
        ot_traces = all_traces[obj_type]

        act_total = activity_total(logs[obj_type])
        activities = activity_frequencies(logs[obj_type])
        or_start = original_start(act_total, activities)
        or_end = original_end(act_total, activities)

        freq = frequencies(activities)

        dep = dependency_matrix(freq)

        dep_dict = dependency_dict(dep)

        long = long_distance_dependency(act_total, ot_traces, or_start, or_end)
        
        depgraph = dependency_graph(act_total, or_start, or_end, freq, dep, dep_dict, long, dependency_threshold)

        
        in_arcs = input_arcs(depgraph)
        out_arcs = output_arcs(depgraph)

        
        cnet_outbindings = output_bindings(ot_traces, out_arcs, in_arcs)
        cnet_inbindings = input_bindings(ot_traces, out_arcs, in_arcs) 

        
        
        ot_nodes, ot_edges, i_seq, o_seq = ot_graph(depgraph, act_total, activity_counts, ot_counts, mean_dict, median_dict, min_dict, max_dict, activities, dep_dict, cnet_inbindings, cnet_outbindings, seq_i, seq_o)

        ot_edges["object_type"] = obj_type


        if obj_type not in ot_subgraphs_dict.keys():
            ot_subgraphs_dict[obj_type] = (ot_nodes, ot_edges)
        
        seq_i = i_seq
        seq_o = o_seq

    return ot_activities, ot_subgraphs_dict