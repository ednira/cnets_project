
from flt_import_ocel import *
from flt_flatten_log import *
from flt_dep_matrix import *
from flt_dep_graph import *
from flt_bindings import *
from flt_replay import *
from flt_visualization import *
from flt_depgraph_visualization import *
from flt_long_distance import *
from flt_visualization_dictionaries import *

#pd.set_option('display.max_columns', None)

# TEST 1 - import an OCEL 2.0 and print the dictionary with the flattened logs
# it was tested with invalid files and the code correctly raised the error file not found


# ORDERMGMT
path = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/OCEL2.0/OCEL_OrderMgt/order-management.sqlite"
path_complete = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/OCEL2.0/Complete logs/order-management.json" 


""" 
# LOGISTICS
path = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/OCEL2.0/OCEL_Logistics/ContainerLogistics.sqlite"
path_complete = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/OCEL2.0/Complete logs/ContainerLogistics.sqlite" 
 """

""" 
# P2P
# This only has path complete
path = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/OCEL2.0/Complete logs/ocel2-p2p.sqlite"
 """
ocel, ocel_df, ot_activities, activity_to_object_types, obj_to_obj, event_to_obj = import_log(path)
#ocel_comp, ocel_df_comp, ot_activities_comp, activity_to_object_types_comp, obj_to_obj_comp, event_to_obj_comp = import_log(path_complete)


flt = flatten_log(ocel, ot_activities)
#flt_comp = flatten_log(ocel_comp, ot_activities_comp)

logs = read_log(flt)
""" 

# TEST 2 - discover traces for each object in each object type



# TEST 3 - discover the cnets for an object type, based on the dependencies and thresholds


"""
cardinalities, ot1_ot2_cardinalities, ot2_ot1_cardinalities, relations = ot_cardinalities(obj_to_obj, event_to_obj, ot_activities) 

partially_common, totally_common, ot_seq = ot_sequence(ot_activities, ot1_ot2_cardinalities, ot2_ot1_cardinalities, event_to_obj)


all_traces = traces(flt, ot_activities, obj_to_obj, event_to_obj, ot_seq, relations, cardinalities)

ot_traces = all_traces['items']     
# ORDERMGMT OT: employees, customers, orders, items, products, packages
# LOGISTICS OT: Customer Order, Transport Document, Vehicle, Container, Handling Unit, Truck, Forklift
# P2P OT: purchase_requisition, quotation, purchase_order, goods receipt, invoice receipt, payment, material
act_total = activity_total(logs['items'])
activities = activity_frequencies(logs['items'])

or_start = original_start(act_total, activities)
or_end = original_end(act_total, activities)

freq = frequencies(activities)

dep = dependency_matrix(freq)

dep_dict = dependency_dict(dep)

best = best_dependency(dep_dict)
pred = best_predecessor(dep)

long = long_distance_dependency(act_total, ot_traces, or_start, or_end)

"""

 
print(f'OT1 cardinalities: {ot1_ot2_cardinalities}')

print('==========')
print(f'OT2 cardinalities: {ot2_ot1_cardinalities}')

print(cardinalities) """

print('===========FREQ=============')
print(freq)
print('===========DEP=============')
print(dep)
""" 
print('===========PRED=============')
for k,v in pred.items():
    print(f'{k}: {v}')
 """ 
print('===========LONG=============')
print(long)
print('')
print('============ ACT TOTAL ================')
print(act_total)
""" 
print(ot_activities)

print(flt['items'])
"""
print('===========TRACES=============')
print(ot_traces) 

# =============== FUNCTION TO REMOVE CONSECUTIVE DUPLICATES FROM TRACES =====================
""" 
print(ot_traces['cr2'].count('Load Truck')) # Count the number of times an activity appears in a trace
print(ot_traces['cr14'])



def remove_consecutive_duplicates(traces):
    # Function to remove consecutive duplicates in a trace
    def process_list(lst):
        if not lst:
            return lst
        result = [lst[0]]
        for item in lst[1:]:
            if item != result[-1]:
                result.append(item)
        return result
    # Iterate over each key in the dictionary and process the list
    for key in traces:
        traces[key] = process_list(traces[key])
    
    return traces



result = remove_consecutive_duplicates(ot_traces)

print(result['cr14'])

print(cardinalities) """
print('')
print('============= OT SEQUENCE ================')
print(f'ot_sequence is {ot_seq}')                
print('==========================================')
# =======================================================================

"""
print('===========O2O=============')
print(obj_to_obj)

print('===========E2O=============')
print(event_to_obj)

print('===========OCEL DF=============')
print(ocel_df) """


# ++++++++++++++++++++++++++++++++++++++++++ GRAPH GENERATION +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# The graph (nodes and edges) is created, based on the thresholds
depgraph = dependency_graph(act_total, or_start, or_end, freq, dep, dep_dict, long, long_distance=0.95)

# Visualize the dependency graph, the file is saved as 'graph_cnet_frequencies.png'
#pygraph_visualization(depgraph, act_total, activities, dep_dict)

# Generate the arcs based on the edges of the dep_graph
in_arcs = input_arcs(depgraph)
out_arcs = output_arcs(depgraph)

# Find the bindings in the incoming and outgoing arcs of the graph, after replay (replay.py):
output, cnet_outbindings = output_bindings(ot_traces, out_arcs, in_arcs)
input, cnet_inbindings = input_bindings(ot_traces, out_arcs, in_arcs) 

print('')
print('============== NODES ===============')
print(depgraph.nodes)
print('')
print('============== EDGES ===============')
print(depgraph.edges)
print('')
# ++++++++++++++++++++++++++++++++++++++++++ GRAPH VISUALIZATION +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# Visualize the OT C-nets, the image pops in the screen
cnet_visualization = visualization(depgraph, act_total, activities, dep_dict, cnet_inbindings, cnet_outbindings)

""" 
print('=============Cnets input bindings================')
print(cnet_inbindings)
print('**** inbindings ****')
print(input['create package'])
print('payment reminder:')
print(input['payment reminder'])   
print('=============Cnets output bindings===============')
print(cnet_outbindings)
print('')
print('=============Cnets in_arcs================')
print(in_arcs)
print('=============Cnets out_arcs===============')
print(out_arcs)  """

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# PRINTING NODES AND EDGES DATAFRAMES

nodes_df, edges_df = visualization_dict(depgraph, act_total, activities, dep_dict, cnet_inbindings, cnet_outbindings)
print('')
print('======================= NODES ==========================')
print(nodes_df)
print('')
print('======================= EDGES ==========================')
print(edges_df)