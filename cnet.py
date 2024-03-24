
import pygraphviz as pgv

from import_log import *
from dep_matrix import *
from dep_graph import *
from bindings import *
from replay import *
from graphviz_visualization import *


log = read_log('/Users/ednira/Documents/My Masters/0 THESIS/event logs/example with two start two end act copy.csv')
#log = read_log('/Users/ednira/Documents/My Masters/0 THESIS/event logs/testlog copy.csv')
#log = read_log('/Users/ednira/Documents/My Masters/0 THESIS/event logs/booklog.csv')
#log = read_log('/Users/ednira/Documents/My Masters/0 THESIS/event logs/long_distance.csv')
#log = read_log('/Users/ednira/Documents/My Masters/0 THESIS/event logs/logcnet2.csv')
#log = read_log('/Users/ednira/Documents/My Masters/0 THESIS/event logs/logcnet.csv')

activities = activity_frequencies(log)

act_total = activity_total(log)

freq = frequencies(activities)

dep = dependency_matrix(freq)

dep_dict = dependency_dict(dep)

best = best_dependency(dep_dict)

alltraces = traces(log)

long = long_distance_dependency(act_total, alltraces)

depgraph, end, start, or_start, or_end = dependency_graph(act_total,activities,dep_dict, long)

pygraph_visualization(depgraph, act_total, activities, dep_dict)

in_arcs = input_arcs(depgraph)
out_arcs = output_arcs(depgraph)

output, cnet_outbindings = output_bindings(alltraces, out_arcs, in_arcs)

input, cnet_inbindings = input_bindings(alltraces, out_arcs, in_arcs)

print('###################################')
print('###################################')
print('Given a log, these are the ACTIVITIES')
print(activities)

print('Then, a dependency graph is generated.')
print('These are the graph EDGES')
print(depgraph.edges)

print('OUTPUT BINDINGS OF THE C-NET found in the TRACES')
print(output)
print('INPUT BINDINGS OF THE C-NET found in the TRACES')
print(input)

print('TRACES')
print(alltraces)
print('CNET OUTPUT')
print(cnet_outbindings)
print('CNET INPUT')
print(cnet_inbindings)
