import networkx as nx
from typing import List, Tuple, Dict

def get_topological_task_order(G: nx.DiGraph) -> List[str]:
    """
    Returns a topologically sorted list of all task nodes in the DFL-DAG.
    
    Args:
        G: The DFL-DAG (networkx.DiGraph).
    
    Returns:
        A list of task node IDs in topological (stage) order.
    """
    # Extract only task nodes
    task_nodes = [node for node, data in G.nodes(data=True) if data.get('type') == 'task']
    
    # Create a subgraph with only tasks and their dependencies
    task_subgraph = G.subgraph(task_nodes).copy()
    
    # If the subgraph has cycles (shouldn't happen for tasks), use stage_order
    if not nx.is_directed_acyclic_graph(task_subgraph):
        # Fall back to sorting by stage_order and task_instance
        task_nodes_with_order = []
        for node in task_nodes:
            node_data = G.nodes[node]
            task_name = node_data.get('task_name', '')
            task_instance = node_data.get('task_instance', 0)
            # Extract stage_order from pos if available
            pos = node_data.get('pos', (0, 0))
            stage_order = pos[0]  # x-position represents stage
            task_nodes_with_order.append((stage_order, task_instance, node))
        
        # Sort by stage_order, then task_instance
        task_nodes_with_order.sort(key=lambda x: (x[0], x[1]))
        return [node for _, _, node in task_nodes_with_order]
    
    # Use topological sort if it's a DAG
    try:
        return list(nx.topological_sort(task_subgraph))
    except nx.NetworkXError:
        # Fall back to position-based sorting
        task_nodes_with_pos = []
        for node in task_nodes:
            pos = G.nodes[node].get('pos', (0, 0))
            task_nodes_with_pos.append((pos[0], pos[1], node))
        
        task_nodes_with_pos.sort(key=lambda x: (x[0], x[1]))
        return [node for _, _, node in task_nodes_with_pos]


def get_tasks_in_range(G: nx.DiGraph, start_task_id: str, end_task_id: str) -> List[str]:
    """
    Returns all tasks between (and including) start_task_id and end_task_id based on connectivity.
    Only includes tasks that are on paths connecting start to end task instances.
    
    Args:
        G: The DFL-DAG (networkx.DiGraph).
        start_task_id: The starting task node ID.
        end_task_id: The ending task node ID.
    
    Returns:
        A list of task node IDs that are connected between start and end.
    """
    import networkx as nx
    
    # Validate that start and end tasks exist
    if not G.has_node(start_task_id):
        raise ValueError(f"Start task '{start_task_id}' not found in workflow")
    if not G.has_node(end_task_id):
        raise ValueError(f"End task '{end_task_id}' not found in workflow")
    
    # Get stage positions (x-coordinates) for start and end tasks
    start_stage = G.nodes[start_task_id].get('pos', (0, 0))[0]
    end_stage = G.nodes[end_task_id].get('pos', (0, 0))[0]
    
    # Ensure start stage comes before or equals end stage
    if start_stage > end_stage:
        raise ValueError(f"Start task '{start_task_id}' comes after end task '{end_task_id}' in workflow order")
    
    # Get all instances of start and end task names
    start_task_name = G.nodes[start_task_id].get('task_name')
    end_task_name = G.nodes[end_task_id].get('task_name')
    
    start_task_instances = []
    end_task_instances = []
    
    for node, data in G.nodes(data=True):
        if data.get('type') == 'task':
            if data.get('task_name') == start_task_name:
                start_task_instances.append(node)
            if data.get('task_name') == end_task_name:
                end_task_instances.append(node)
    
    # Find all tasks that are on any path from any start instance to any end instance
    tasks_on_paths = set()
    
    for start_instance in start_task_instances:
        for end_instance in end_task_instances:
            # Check if there's a path
            if nx.has_path(G, start_instance, end_instance):
                # Get all nodes on all simple paths (up to a reasonable limit)
                try:
                    for path in nx.all_simple_paths(G, start_instance, end_instance, cutoff=20):
                        for node in path:
                            if G.nodes[node].get('type') == 'task':
                                tasks_on_paths.add(node)
                except nx.NetworkXNoPath:
                    continue
    
    # Convert to list and sort by stage position, then by instance number
    tasks_list = list(tasks_on_paths)
    
    def sort_key(node_id):
        node_data = G.nodes[node_id]
        pos = node_data.get('pos', (0, 0))
        stage = pos[0]
        # Extract instance number from node_id (e.g., "openmm_5" -> 5)
        instance = 0
        if '_' in node_id:
            try:
                instance = int(node_id.rsplit('_', 1)[1])
            except (ValueError, IndexError):
                pass
        return (stage, instance)
    
    tasks_list.sort(key=sort_key)
    
    return tasks_list


def get_unique_task_names(G: nx.DiGraph) -> List[Tuple[str, int, int]]:
    """
    Returns a list of unique task names (without instance indices) in stage order.
    
    Args:
        G: The DFL-DAG (networkx.DiGraph).
    
    Returns:
        A list of tuples: (task_name, stage_index, parallelism)
        Sorted by stage_index (0-based integer).
    """
    # Collect unique task names with their stage order
    task_info = {}
    
    for node, data in G.nodes(data=True):
        if data.get('type') == 'task':
            task_name = data.get('task_name')
            if task_name and task_name not in task_info:
                # Get stage_order from pos (x-coordinate)
                pos = data.get('pos', (0, 0))
                x_pos = pos[0]  # x-position represents stage
                task_info[task_name] = x_pos
    
    # Count parallelism for each task
    task_parallelism = {}
    for node, data in G.nodes(data=True):
        if data.get('type') == 'task':
            task_name = data.get('task_name')
            if task_name:
                task_parallelism[task_name] = task_parallelism.get(task_name, 0) + 1
    
    # Sort by x_pos to get stage order
    sorted_tasks = sorted(task_info.items(), key=lambda x: x[1])
    
    # Assign stage indices (0, 1, 2, ...) based on unique x positions
    unique_x_positions = sorted(set(task_info.values()))
    x_pos_to_stage = {x: i for i, x in enumerate(unique_x_positions)}
    
    # Create list of tuples with stage indices
    result = []
    for task_name, x_pos in sorted_tasks:
        stage_index = x_pos_to_stage[x_pos]
        parallelism = task_parallelism.get(task_name, 1)
        result.append((task_name, stage_index, parallelism))
    
    return result


def get_tasks_by_stage_numbers(G: nx.DiGraph, stage_numbers: List[int]) -> List[str]:
    """
    Returns all task node IDs that belong to the specified stage numbers.
    
    Args:
        G: The DFL-DAG (networkx.DiGraph).
        stage_numbers: List of stage numbers (0-based indices, e.g., [0, 1] for stages 1 and 2).
    
    Returns:
        A list of task node IDs in the specified stages, sorted by stage then instance.
    """
    # Get unique x positions (stages) and map them to stage indices
    unique_x_positions = sorted(set(
        G.nodes[node].get('pos', (0, 0))[0]
        for node, data in G.nodes(data=True)
        if data.get('type') == 'task'
    ))
    
    x_pos_to_stage = {x: i for i, x in enumerate(unique_x_positions)}
    
    # Collect tasks in the specified stages
    tasks_in_stages = []
    for node, data in G.nodes(data=True):
        if data.get('type') == 'task':
            pos = data.get('pos', (0, 0))
            x_pos = pos[0]
            stage_index = x_pos_to_stage.get(x_pos, -1)
            if stage_index in stage_numbers:
                tasks_in_stages.append(node)
    
    # Sort by stage, then by instance number
    def sort_key(node_id):
        node_data = G.nodes[node_id]
        pos = node_data.get('pos', (0, 0))
        stage = x_pos_to_stage.get(pos[0], -1)
        instance = 0
        if '_' in node_id:
            try:
                instance = int(node_id.rsplit('_', 1)[1])
            except (ValueError, IndexError):
                pass
        return (stage, instance)
    
    tasks_in_stages.sort(key=sort_key)
    return tasks_in_stages


def get_stage_info(G: nx.DiGraph) -> Dict[int, List[Tuple[str, int]]]:
    """
    Returns information about all stages in the workflow.
    
    Args:
        G: The DFL-DAG (networkx.DiGraph).
    
    Returns:
        A dictionary mapping stage numbers (0-based) to lists of (task_name, instance_count) tuples.
    """
    # Get unique x positions (stages) and map them to stage indices
    unique_x_positions = sorted(set(
        G.nodes[node].get('pos', (0, 0))[0]
        for node, data in G.nodes(data=True)
        if data.get('type') == 'task'
    ))
    
    x_pos_to_stage = {x: i for i, x in enumerate(unique_x_positions)}
    
    # Group tasks by stage
    stage_info = {}
    for node, data in G.nodes(data=True):
        if data.get('type') == 'task':
            pos = data.get('pos', (0, 0))
            x_pos = pos[0]
            stage_index = x_pos_to_stage.get(x_pos, -1)
            
            if stage_index not in stage_info:
                stage_info[stage_index] = {}
            
            task_name = data.get('task_name', '')
            if task_name not in stage_info[stage_index]:
                stage_info[stage_index][task_name] = 0
            stage_info[stage_index][task_name] += 1
    
    # Convert to list of tuples
    result = {}
    for stage, task_counts in stage_info.items():
        result[stage] = [(task_name, count) for task_name, count in sorted(task_counts.items())]
    
    return result
