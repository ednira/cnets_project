from collections import Counter

def output_bindings(traces, out_arcs, in_arcs):
    """Find the output bindings for each activity based on its out_arcs and in_arcs of the dependency graph 
    and replay of the traces
    """

    outbindings = {}

    # Iterate over each activity in out_arcs
    for activity in out_arcs:
        outbindings[activity] = []

        # Iterate over each trace in TRACES.values()
        for trace in traces.values():
            bindings = []
            occurrences = [i for i, x in enumerate(trace) if x == activity]

            for i in range(len(occurrences)):
                start_index = occurrences[i]
                end_index = occurrences[i+1] if i < len(occurrences) - 1 else len(trace)
                binding = []
                search_space = trace[start_index:end_index]  # Construct search space from current activity until next occurrence or end of trace

                # print("Search space:", search_space)

                for arc in out_arcs[activity]:
                    # Check if search space is only the activity followed by itself and include the binding
                    if arc == activity and len(search_space) == 1:
                        binding.append(arc)
                    # Check if arc is present in search_space
                    if arc not in search_space:
                        continue

                    # Check if no value in in_arcs[arc] occurs between activity and arc
                    if not any(other in search_space and search_space.index(other) > search_space.index(activity) and search_space.index(other) < search_space.index(arc) for other in in_arcs.get(arc, [])):
                        # We will exclude the activity followed by itself because it was included previously
                        if arc != activity:
                            binding.append(arc)

                # Add the binding to the list of bindings for the current activity
                if binding:
                    bindings.append(binding)

            # Append bindings for the current trace to outbindings
            outbindings[activity].extend(bindings)

   
    cnet_outbindings = {}


    for key, value in outbindings.items():
        if key != 'start'and key!= 'end':
            # Convert nested lists to tuples to make them hashable
            flattened_values = [tuple(sublist) for sublist in value]
            # Sort the tuples to ensure order doesn't matter
            sorted_values = [tuple(sorted(sublist)) for sublist in flattened_values]
            # Count occurrences using Counter
            bindings_counter = Counter(sorted_values)
            # Convert Counter to a dictionary and store it in cnet_outbindings
            cnet_outbindings[key] = dict(bindings_counter)

    return outbindings, cnet_outbindings



def input_bindings(traces, out_arcs, in_arcs):
    """Find the put bindings for each activity based on its in_arcs and out_arcs of the dependency graph 
    and replay of the traces
    """
    inbindings = {}

    # Iterate over each activity in in_arcs
    for activity in in_arcs:
        inbindings[activity] = []

        # Iterate over each trace in TRACES.values()
        for trace in traces.values():
            bindings = []
            first_occ_binding = []

            occurrences = [i for i, x in enumerate(trace) if x == activity]
            
            # The first search space would not be covered by the loop later on, 
            # because in the loop only search spaces between two occurrences are considered. This is different from the output_bindings search spaces.
            # Here the first search space from the beginning is to be considered, but not the last, from the last occurrence to the end of the trace.
            # Check if in the first occurrence the activity is preceded by one of the in_arcs and include in bindings
            if occurrences:
                if len(trace[:occurrences[0]]) == 1 and trace[0] in in_arcs[activity]:
                    bindings.append([trace[0]])
                elif len(trace[:occurrences[0]]) > 1:
                    for element in trace[:occurrences[0]+1]:
                        if element not in in_arcs[activity]:
                            continue
                        else:
                            # Check if no value in in_arcs[arc] occurs between activity and arc
                            if not any(other in trace[:occurrences[0]+1] and trace[:occurrences[0]+1].index(other) < trace[:occurrences[0]+1].index(activity) and trace[:occurrences[0]+1].index(other) > trace[:occurrences[0]+1].index(element) for other in out_arcs.get(element, [])):
                                first_occ_binding.append(element)
                    if first_occ_binding:
                        bindings.append(first_occ_binding)
                        first_occ_binding = []
                

            for i in range(len(occurrences)):
                start_index = occurrences[i]
                end_index = occurrences[i+1] if i < len(occurrences) - 1 else None
                binding = []
                search_space = trace[start_index:end_index]  # Construct search space from current activity until next occurrence or end of trace

                #print("Search space:", search_space)

                for arc in in_arcs[activity]:
                    # Check if arc is present in search_space
                    if arc not in search_space:
                        continue

                    # Check if no value in in_arcs[arc] occurs between activity and arc
                    if not any(other in search_space and search_space.index(other) < search_space.index(activity) and search_space.index(other) > search_space.index(arc) for other in out_arcs.get(arc, [])):
                        binding.append(arc)

                # Add the binding to the list of bindings for the current activity
                if binding:
                    bindings.append(binding)

            # Append bindings for the current trace to inbindings
            inbindings[activity].extend(bindings)

   
    cnet_inbindings = {}


    for key, value in inbindings.items():
        if key != 'start'and key!= 'end':
            flattened_values = []
            for sublist in value:
                # Convert nested lists to sets only if the sublist has more than one element
                if len(sublist) > 1 and len(set(sublist)) == 1:
                    flattened_values.append((sublist[0],))
                else:
                    flattened_values.append(tuple(sublist))
            # Sort the tuples to ensure order doesn't matter
            sorted_values = [tuple(sorted(sublist)) for sublist in flattened_values]
            # Count occurrences using Counter
            bindings_counter = Counter(sorted_values)
            # Convert Counter to a dictionary and store it in cnet_inbindings
            cnet_inbindings[key] = dict(bindings_counter)

    return inbindings, cnet_inbindings
