${\textsf{\huge{\color{teal}Object-centric Causal Nets}}}$

This is the repository for the Object-centric C-nets master thesis project at DSV/SU 😊

There are two folders containing the files related to traditional and object-centric process discovery, respectively [traditional](https://github.com/ednira/cnets_project/tree/fdceeab8b91db557fcd7908b9b1f5cbf36b58dac/traditional) and [object-centric](https://github.com/ednira/cnets_project/tree/08e0f3d77420009cb6979adbe2f6e72dc5f6782e/object-centric).

### Traditional C-nets
<img width="120" alt="Cnet" src="https://github.com/ednira/cnets_project/assets/69249709/a0794eb0-7f80-4aa7-bf58-93725495bbef">

Here is a description of the steps followed to mine C-nets from a log with a single case notion.

**1 - read a log file in csv format**
  
  file import_log -- function def read_log(path): input csv, output dictionary 'log' {caseID:event(task, eid, timestamp)}


**2 - mine traces**
  The traces are mined from the log.

**3 count activity totals**
  
  This counts the occurrences of each activity in the log.
  
  file dep_matrix -- function def activity_total(log): input 'log' dictionary (item 1), output dictionary 'act_total' {activity name: count}
  
**4 - count frequencies**

  This counts the frequencies of one activity followed by another.
  
  file dep_matrix -- function def activity_frequencies(log): input 'log' dictionary (item 1), output nested dictionary 'act_frequencies' {activity name: {activity name: count}}
  
**5 - convert frequencies dictionary into a Dataframe**

  The Dataframe is the frequency matrix where each row shows how many times one activity is followed by other activities in the log (each activity is a column).
  
  file dep_matrix -- function def frequencies(act_frequencies): input nested dictionary 'act_frequencies', output pd Dataframe 'frequencies' (index: activity name, column: activity name)
  
**6 - calculate the dependency measure**
  
  This is to visualize the dependency matrix as a dataframe.
  
  file dep_matrix -- function def dependency_matrix(frequencies): input Dataframe 'frequencies', output Dataframe 'dependency_matrix' (index: activity name, column: activity name). The cells show the dependency measure of the activity to the other activity
  
**7 - convert dependency matrix Dataframe into dictionary**
  
  This dictionary will be used in the cnet algorithm and in the visualization algorithm
  
  file dep_matrix -- function def dependency_dict(dependency_matrix):
input Dataframe 'dependency_matrix', output dictionary 'dependency_dict' {activity name: {activity name: dependency}}

**8 - find the next-best dependency**
  
  This is the activity with highest dependency although below the threshold. All activities need to be connected in the C-nets, so this is used for activities without outgoing edge because their dependencies in relation to other activities are below the threshold. The activity will be connected to the activity with the next-best dependency.
  
  file dep_graph -- function def best_dependency(dependency_dict):
  input dictionary 'dependency_dict', output dictionary 'best_dependency' {activity name: {activity name: dependency(max)}}
  
**9 - mine the traces**
  
  Extract the traces of the log. The trace is the sequence of activity names that occur in a case.
  
  file import_log -- function def traces(log): input dictionary 'log', output dictionary 'traces' {caseID:trace(list of activities)}
  
**10 - calculate long-distance dependencies (LDD)**

  This is needed to depict choices made in one step of the process that determine activities that will follow in other parts of the process. The LDD is calculated using the formula presented in the papers 'Flexible_Heuristics_Miner_FHM' (Weijters and Ribeiro) 2012 and 'Fodina - A robust and flexible heuristic process discovery technique' (Seppe K.L.M. vanden Broucke, Jochen De Weerdt) 2017.
  
  file dep_matrix -- function def long_distance_dependency(act_total, traces):
  input dictionary 'act_total' and dictionary 'traces', output dictionary 'long_dep' {activity name: {activity name: LDD}}
  
**11 - discover all the potential input activities of each activity**
  
  This is used in the dependency_graph function (file dep_graph). 
  
  file bindings -- function def in_bindings(activity_frequencies):
  input dictionary ''act_frequencies' (item 3), output dictionary 'inbindings_list' {activity name: list of bindings each bindng is a list of activities) 
  
**12 - build the dependency graph**
  
  The dependency graph is composed of nodes and edges. The nodes are the activities and the edges are tuples with the source and the target activities which are connected. 
  
  The edges are defined based on the thresholds (act_total, frequency, dependency and ldd). First, the edge is defined based on the best dependency measure, the activity with highest dependency and above the dependency threshold. If the activity has no outgoing edge because of the thresholds, an edge based on the next_best successor is defined. If the activity has no incoming edge, because it has only one incoming predecessor and it lost the race in the next_best, an edge from its only predecessor to the activity is created. At the end, edges for ldd are created.
  
  file dep_graph -- function def dependency_graph(activity_total, activity_frequencies, dependency_dict, long_dep, long_distance=0.8, act_threshold=1, frequency_threshold=1, dependency_threshold=0.9):
  input dictionaries 'act_total', 'activity_frequencies', 'dependency_dict', 'long_dep', output 'dep_graph' (a named tuple with nodes and edges), end_act, start_act, original_start, original_end
  
**13 - visualize the dependency graph**
  
  The dependency graph shows nodes (activities) connected by edges, with annotation of total counts of activities, frequencies of activities followed by other activities, and dependency measures
  
  file graphviz_visualization -- function def pygraph_visualization(graph, act_total, activity_frequencies, dep_dict):
  input graph 'dep_graph', dictionary 'act_total', dictionary 'act_frequencies', and dictionary 'dependency_dict', output plotted graph in file 'graph_cnet_frequencies.png'
  
**14 - identify the input and output arcs**
  
  After the dependency graph is defined using thresholds and connecting all activities, the input and output arcs are defined to make it possible to use the replay based on traces and discover the input and output bindings
  
  file bindings -- functions def input_arcs(dep_graph) and def output_arcs(dep_graph):
  input graph 'dep_graph', output dictionaries 'in_bindings' and 'out_bindings', respectively
  
**15 - discover the input and output bindings using replay based on traces**
  
  The traces are replayed on the arcs of each activity and the bindings and their respective frequencies are defined
  
  file replay -- functions def input_bindings(traces, out_arcs, in_arcs) and def output_bindings(traces, out_arcs, in_arcs):
  input dictionary 'traces', dictionary 'in_bindings' (function input_arcs) and dictionary 'out_bindings' (function output_arcs), output dictionaries cnet_inbindings and cnet_outbindings, respectively
  
**16 - visualize C-nets**
  
  The visualization in Graphviz uses the nodes and edges generated in the dep_graph to create dataframes of nodes and edges needed to generate the graph representation in Graphviz.
  
  file pyvis_visualization -- function def visualization(graph, dependency_matrix, frequencies, activity_total):
  input graph 'dep_graph', dictionaries cnet_inbindings and cnet_outbindings, output a graph is rendered on the screen


### Object-centric C-nets

(under development)
