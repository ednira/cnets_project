This is the repository for the Object-centric C-nets master thesis project at DSV/SU.

Traditional C-nets
Here a description of the files and functions in the sequence followed to mine the C-nets (traditional process mining)

1 - read a log file in csv format
  file import_log -- function def read_log(path): input csv, output dictionary 'log' {caseID:event(task, eid, timestamp)}
  
2 - count activity totals
  """Calculate total activity counts and store them in a dictionary""" 
  
  file dep_matrix -- function def activity_total(log): input 'log' dictionary (item 1), output dictionary 'act_total' {activity name: count}
  
3 - count frequencies
  """Calculate frequencies of activity ai followed by activity aj and store them in a dictionary"""
  
  file dep_matrix -- function def activity_frequencies(log): input 'log' dictionary (item 1), output nested dictionary 'act_frequencies' {activity name: {activity name: count}}
  
4 - convert frequencies dictionary into a Dataframe
  """Convert the activity frequencies dictionary into a dataframe in pandas with frequencies"""
  
  The Dataframe is the frequency matrix where each row shows how many times one activity is followed by activities in the log (each activity is a column)
  file dep_matrix -- function def frequencies(act_frequencies): input nested dictionary 'act_frequencies', output pd Dataframe 'frequencies' (index: activity name, column: activity name)
  
5 - calculate the dependency measure
  """Generate the dependency matrix Dataframe"""
  
  It is good to visualize the dependency matrix, although the algorithm only uses the dependency measures in the form of dictionary, the dependency_dict.
  file dep_matrix -- function def dependency_matrix(frequencies): input Dataframe 'frequencies', output Dataframe 'dependency_matrix' (index: activity name, column: activity name). The cells show the dependency measure of the activity to the other activity
  
6 - convert dependency matrix Dataframe to dictionary
  This dictionary will be used in the cnet algorithm and in the visualization algorithm
  
  file dep_matrix -- function def dependency_dict(dependency_matrix):
input Dataframe 'dependency_matrix', output dictionary 'dependency_dict' {activity name: {activity name: dependency}}

7 - find the next-best dependency
  This is the activity with highest dependency. All activities need to be connected in the C-nets, so this is used for activities without outgoing edge because their dependencies in relation to other activities are below the threshold. The activity will be connected to the activity with the next-best dependency.
  
  file dep_graph -- function def best_dependency(dependency_dict):
  input dictionary 'dependency_dict', output dictionary 'best_dependency' {activity name: {activity name: dependency(max)}}
  
8 - mine the traces
  Extract the traces of the log. The trace is the list of activity names that occur in a case.
  
  file import_log -- function def traces(log): input dictionary 'log', output dictionary 'traces' {caseID:trace(list of activities)}
  
9 - calculate long-distance dependencies (LDD)
  """Calculate if one activity eventually follows another one"""
  This is due to choices made in one step of the process flow that determine activities that will follow in other parts of the process. The LDD is calculated using the formula presented in the papers Flexible Heuristics Miner (FHM) in paper Flexible_Heuristics_Miner_FHM (Weijters and Ribeiro) in 2012 and Fodina - A robust and flexible heuristic process discovery technique (Seppe K.L.M. vanden Broucke, Jochen De Weerdt) in 2017.
  
  file dep_matrix -- function def long_distance_dependency(act_total, traces):
  input dictionary 'act_total' and dictionary 'traces', output dictionary 'long_dep' {activity name: {activity name: LDD}}
  
10 - discover all the potential input activities of each activity
  This is used in the dependency_graph function of file dep_graph. 
  
  file bindings -- function def in_bindings(activity_frequencies):
  input dictionary ''act_frequencies' (item 3), output dictionary 'inbindings_list' {activity name: list of bindings each bindng is a list of activities) 
  
11 - build the dependency graph
  The dependency graph is composed of nodes and edges. The nodes are the activities and the edges are tuples with the source and the target activities which are connected. 
  The edges are defined based on the thresholds (act_total, frequency, dependency and ldd). First, the edge is defined based on the best dependency measure, the activity with highest dependency and it is above the dependency threshold. If the activity has no outgoing edge because of the thresholds, an edge based on the next_best successor is defined. If the activity has no incoming edge, because it has only one incoming predecessor and it lost the race in the next_best, an edge from its only predecessor to the activity is created. At the end, edges for ldd are created.
  
  file dep_graph -- function def dependency_graph(activity_total, activity_frequencies, dependency_dict, long_dep, long_distance=0.8, act_threshold=1, frequency_threshold=1, dependency_threshold=0.9):
  input dictionaries 'act_total', 'activity_frequencies', 'dependency_dict', 'long_dep', output 'dep_graph' (a named tuple with nodes and edges), end_act, start_act, original_start, original_end
  
12 - visualize the dependency graph
  the dependency graph shows nodes (activities) connected by edges with annotation of frequencies of activities, frequencies of activities followed by other activities, dependency measures
  
  file graphviz_visualization -- function def pygraph_visualization(graph, act_total, activity_frequencies, dep_dict):
  input graph 'dep_graph', dictionary 'act_total', dictionary 'act_frequencies', and dictionary 'dependency_dict', output plotted graph in file 'graph_cnet_frequencies.png'
  
13 - identify the input and output arcs
  After the dependency graph is defined using thresholds and connecting all activities, the input and output arcs are defined to make it possible to use replay based on traces and discover the input and output bindings
  
  file bindings -- functions def input_arcs(dep_graph) and def output_arcs(dep_graph):
  input graph 'dep_graph', output dictionaries 'in_bindings' and 'out_bindings', respectively
  
14 - discover the input and output bindings using replay based on traces
  The traces are replayed on the arcs of each activity and the bindings and their respective frequencies are defined
  
  file replay -- functions def input_bindings(traces, out_arcs, in_arcs) and def output_bindings(traces, out_arcs, in_arcs):
  input dictionary 'traces', dictionary 'in_bindings' (function input_arcs) and dictionary 'out_bindings' (function output_arcs), output dictionaries cnet_inbindings and cnet_outbindings, respectively
  
15 - visualize C-nets
  The visualization in graphviz uses the nodes and edges generated in the dep_graph to create dataframes of nodes and edges needed to generate the graph representation in graphviz.
  
  file pyvis_visualization -- function def visualization(graph, dependency_matrix, frequencies, activity_total):
  input graph 'dep_graph', dictionaries cnet_inbindings and cnet_outbindings, output a graph is rendered on the screen
