import networkx as nx

def calculate_critical_path_gcpa(graph: nx.DiGraph, weight_property: str) -> list:
    """
    Calculates the Generalized Critical Path Analysis (GCPA) for a DFL-DAG.

    Args:
        graph: The DFL-DAG (networkx.DiGraph).
        weight_property: The edge property to use as weight for critical path calculation (e.g., 'volume', 'count').

    Returns:
        A list of edges representing the critical path.
    """
    # Create a DAG by removing cycles (edges where a task both reads and writes the same file)
    # This creates cycles like: task -> file -> task (when a task writes then reads the same file)
    weighted_graph = nx.DiGraph()
    for u, v, data in graph.edges(data=True):
        weight = data.get(weight_property, 0)
        op_type = data.get('op_type', 'unknown')
        
        # Skip self-loop edges (file -> same task that wrote it)
        # This happens when a task writes a file and then reads it back
        if op_type == 'read':
            # Check if there's a corresponding write edge from the same task
            # If task A writes to file F, and file F reads back to task A, skip the read edge
            file_node = u  # source is file for read operations
            task_node = v  # target is task for read operations
            # Check if this task also writes to this file
            if graph.has_edge(task_node, file_node):
                # This is a self-loop cycle, skip it for critical path calculation
                continue
        
        weighted_graph.add_edge(u, v, weight=weight)

    critical_path_edges = []
    max_path_weight = -float('inf')
    
    # Find all source nodes (nodes with no incoming edges)
    source_nodes = [n for n, d in weighted_graph.in_degree() if d == 0]
    # Find all sink nodes (nodes with no outgoing edges)
    sink_nodes = [n for n, d in weighted_graph.out_degree() if d == 0]

    if not source_nodes or not sink_nodes:
        # Handle cases where there are no clear sources or sinks
        return []

    # Check if the graph is a DAG (no cycles)
    if nx.is_directed_acyclic_graph(weighted_graph):
        # Use dag_longest_path for true DAGs
        try:
            longest_path = nx.dag_longest_path(weighted_graph, weight='weight')
            if longest_path:
                critical_path_edges = [(u, v) for u, v in zip(longest_path[:-1], longest_path[1:])]
        except (nx.NetworkXError, nx.NetworkXNotImplemented):
            pass
    else:
        # Graph has cycles - use a different approach
        # Find the path with maximum weight between any source-sink pair
        for source in source_nodes:
            for sink in sink_nodes:
                try:
                    # Use all_simple_paths with limited cutoff to avoid infinite loops
                    for path in nx.all_simple_paths(weighted_graph, source, sink, cutoff=100):
                        path_weight = sum(weighted_graph[u][v]['weight'] for u, v in zip(path[:-1], path[1:]))
                        if path_weight > max_path_weight:
                            max_path_weight = path_weight
                            critical_path_edges = [(u, v) for u, v in zip(path[:-1], path[1:])]
                except nx.NetworkXNoPath:
                    continue
                except nx.NodeNotFound:
                    continue

    return critical_path_edges

def extend_to_caterpillar_tree(graph: nx.DiGraph, critical_path_edges: list) -> nx.DiGraph:
    """
    Extends the critical path to include all distance-one fan-in and fan-out nodes,
    forming the DFL Caterpillar Tree (CT).

    Args:
        graph: The original DFL-DAG (networkx.DiGraph).
        critical_path_edges: A list of edges representing the critical path.

    Returns:
        A subgraph representing the DFL Caterpillar Tree.
    """
    ct_nodes = set()
    for u, v in critical_path_edges:
        ct_nodes.add(u)
        ct_nodes.add(v)

        # Add fan-in nodes (predecessors) of u and v
        for predecessor in graph.predecessors(u):
            ct_nodes.add(predecessor)
        for predecessor in graph.predecessors(v):
            ct_nodes.add(predecessor)

        # Add fan-out nodes (successors) of u and v
        for successor in graph.successors(u):
            ct_nodes.add(successor)
        for successor in graph.successors(v):
            ct_nodes.add(successor)

    # Create a subgraph induced by the CT nodes
    ct_subgraph = graph.subgraph(ct_nodes).copy()

    return ct_subgraph
