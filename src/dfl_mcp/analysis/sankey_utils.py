
import networkx as nx
import math
from networkx.drawing.nx_pydot import graphviz_layout
import plotly.graph_objects as go
from typing import List

def expand_task_names_to_ids(G: nx.DiGraph, task_names: List[str]) -> List[str]:
    """
    Expands task name prefixes to actual task node IDs.
    
    For example, if task_names = ["openmm", "aggregate"], this will find all nodes
    like "openmm_0", "openmm_1", "aggregate_0", etc.
    
    Args:
        G: The DFL-DAG.
        task_names: List of task name prefixes or exact task IDs.
    
    Returns:
        A list of actual task node IDs that match the given names.
    """
    if not task_names:
        return []
    
    expanded_ids = []
    task_names_set = set(task_names)
    
    for node, data in G.nodes(data=True):
        if data.get('type') == 'task':
            node_id = node
            task_name = data.get('task_name', '')
            
            # Check if exact node ID matches
            if node_id in task_names_set:
                expanded_ids.append(node_id)
            # Check if task name matches (prefix match)
            elif task_name in task_names_set:
                expanded_ids.append(node_id)
            # Check if node_id starts with any task name prefix
            else:
                for prefix in task_names_set:
                    if node_id.startswith(prefix + '_') or node_id == prefix:
                        expanded_ids.append(node_id)
                        break
    
    return list(set(expanded_ids))  # Remove duplicates

def _recalculate_positions_for_subgraph(G: nx.DiGraph) -> None:
    """
    Recalculates node positions for a filtered subgraph to ensure proper ordering.
    Tasks are ordered by their original stage, and files are positioned between their producer and consumer tasks.
    
    Args:
        G: The filtered subgraph (modified in place).
    """
    # Get all task nodes and sort by their original x position (stage)
    task_nodes = [(node, G.nodes[node]) for node in G.nodes() if G.nodes[node].get('type') == 'task']
    
    if not task_nodes:
        return
    
    # Sort tasks by their original x position to maintain stage order
    task_nodes.sort(key=lambda x: (x[1].get('pos', (0, 0))[0], x[1].get('task_instance', 0)))
    
    # Assign new x positions to tasks (0, 2, 4, ...)
    task_x_positions = {}
    for i, (node, data) in enumerate(task_nodes):
        task_x_positions[node] = i * 2
        # Update task position
        old_pos = data.get('pos', (0, 0))
        G.nodes[node]['pos'] = (i * 2, old_pos[1])
    
    # Now position file nodes based on their connections
    file_nodes = [(node, G.nodes[node]) for node in G.nodes() if G.nodes[node].get('type') == 'file']
    
    for file_node, file_data in file_nodes:
        # Find all tasks that write to this file (producers)
        producer_tasks = [u for u, v in G.in_edges(file_node) if G.nodes[u].get('type') == 'task']
        # Find all tasks that read from this file (consumers)
        consumer_tasks = [v for u, v in G.out_edges(file_node) if G.nodes[v].get('type') == 'task']
        
        if producer_tasks and consumer_tasks:
            # File is between producer and consumer - position it between them
            max_producer_x = max(task_x_positions.get(t, 0) for t in producer_tasks)
            min_consumer_x = min(task_x_positions.get(t, float('inf')) for t in consumer_tasks)
            # Position file between producer and consumer
            file_x = (max_producer_x + min_consumer_x) / 2
        elif producer_tasks:
            # File is only produced, position it right after the producer
            max_producer_x = max(task_x_positions.get(t, 0) for t in producer_tasks)
            file_x = max_producer_x + 1
        elif consumer_tasks:
            # File is only consumed (input file), position it before the consumer
            min_consumer_x = min(task_x_positions.get(t, float('inf')) for t in consumer_tasks)
            file_x = max(0, min_consumer_x - 1)
        else:
            # File has no task connections, keep original position
            old_pos = file_data.get('pos', (0, 0))
            file_x = old_pos[0]
        
        # Update file position
        old_pos = file_data.get('pos', (0, 0))
        G.nodes[file_node]['pos'] = (file_x, old_pos[1])

def filter_subgraph(G: nx.DiGraph, selected_tasks: List[str], selected_files: List[str]) -> nx.DiGraph:
    """
    Filters the DFL-DAG to include only the selected tasks and files and their direct neighbors.
    Recalculates node positions to ensure proper ordering in the filtered view.

    Args:
        G: The DFL-DAG.
        selected_tasks: A list of selected task IDs.
        selected_files: A list of selected file IDs.

    Returns:
        A new DiGraph containing the filtered subgraph with recalculated positions.
    """
    if not selected_tasks and not selected_files:
        return G

    nodes_to_include = set(selected_tasks) | set(selected_files)
    
    if selected_tasks and not selected_files:
        for task_node in selected_tasks:
            if G.has_node(task_node):
                nodes_to_include.update(G.predecessors(task_node))
                nodes_to_include.update(G.successors(task_node))

    elif selected_files and not selected_tasks:
        for file_node in selected_files:
            if G.has_node(file_node):
                nodes_to_include.update(G.predecessors(file_node))
                nodes_to_include.update(G.successors(file_node))

    # Create filtered subgraph
    filtered_G = G.subgraph(nodes_to_include).copy()
    
    # Recalculate positions for the filtered subgraph
    _recalculate_positions_for_subgraph(filtered_G)
    
    return filtered_G

def create_sankey_html(G: nx.DiGraph, metric: str, output_path: str, critical_path_edges: list = None, width: int = 1800, height: int = 2000, font_size: int = 10, node_pad: int = 15, transform_link_value: bool = True):
    """
    Creates a Sankey diagram as an HTML file with PID information on hover.

    Args:
        G: The DiGraph to convert.
        metric: The edge attribute to use for the flow value.
        output_path: The path to save the HTML file to.
        critical_path_edges: Optional list of tuples (source, target) representing edges on the critical path to highlight in orange.
    """
    pos = nx.get_node_attributes(G, 'pos')
    
    nodes = sorted(list(G.nodes()), key=lambda n: (pos.get(n, (0,0))[0], pos.get(n, (0,0))[1]))
    node_indices = {node: i for i, node in enumerate(nodes)}
    
    labels = [node for node in nodes]
    colors = ["red" if G.nodes[node].get('type') == 'task' else "blue" for node in nodes]
    
    # Extract x and y positions from the 'pos' attribute
    x_positions = [pos.get(node, (0, 0))[0] for node in nodes]
    y_positions = [pos.get(node, (0, 0))[1] for node in nodes]
    
    # Create custom hover text with PID information
    customdata = []
    for node in nodes:
        node_data = G.nodes[node]
        node_type = node_data.get('type', 'unknown')
        
        if node_type == 'task':
            pid = node_data.get('pid')
            if pid is not None:
                hover_text = f"Task: {node}<br>PID: {pid}"
            else:
                hover_text = f"Task: {node}<br>PID: N/A"
        elif node_type == 'file':
            write_pids = node_data.get('write_pids', [])
            read_pids = node_data.get('read_pids', [])
            hover_text = f"File: {node}<br>"
            if write_pids:
                hover_text += f"Write PIDs: {', '.join(map(str, write_pids))}<br>"
            if read_pids:
                hover_text += f"Read PIDs: {', '.join(map(str, read_pids))}"
        else:
            hover_text = f"Node: {node}"
        
        customdata.append(hover_text)
    
    source_indices = []
    target_indices = []
    values = []
    link_customdata = []
    link_colors = []
    
    # Convert critical_path_edges to a set for faster lookup
    critical_edges_set = set(critical_path_edges) if critical_path_edges else set()

    for source, target, data in G.edges(data=True):
        source_indices.append(node_indices[source])
        target_indices.append(node_indices[target])
        
        # Always use volume for edge width (value)
        volume_bytes = data.get('volume', 0)
        if transform_link_value:
            values.append(math.log1p(volume_bytes))
        else:
            values.append(volume_bytes)
        
        # Determine edge color - orange for critical path, default gray otherwise
        if (source, target) in critical_edges_set:
            link_colors.append('orange')
        else:
            link_colors.append('rgba(200, 200, 200, 0.4)')  # Light gray with transparency
        
        # Create custom hover text for edges with all attributes
        volume_mb = volume_bytes / (1024 * 1024) if volume_bytes > 0 else 0
        op_count = data.get('op_count', 0)
        rate_bytes_per_sec = data.get('rate', 0)
        rate_mb_per_sec = rate_bytes_per_sec / (1024 * 1024) if rate_bytes_per_sec > 0 else 0
        
        # Add critical path indicator to hover text
        critical_indicator = " [CRITICAL PATH]" if (source, target) in critical_edges_set else ""
        
        edge_hover = (
            f"Edge: {source} -> {target}{critical_indicator}<br>"
            f"Volume: {volume_mb:.2f} MB<br>"
            f"Op Count: {op_count:,}<br>"
            f"Rate: {rate_mb_per_sec:.2f} MB/sec"
        )
        link_customdata.append(edge_hover)

    fig = go.Figure(data=[go.Sankey(
        arrangement = 'freeform',
        node = dict(
          pad = node_pad,  # Moderate padding for better spacing without making nodes too small
          thickness = 20,
          line = dict(color = "black", width = 0.5),
          label = labels,
          color = colors,
          x = x_positions,
          customdata = customdata,
          hovertemplate='%{customdata}<extra></extra>'
        ),
        link = dict(
          source = source_indices,
          target = target_indices,
          value = values,
          color = link_colors,
          customdata = link_customdata,
          hovertemplate='%{customdata}<extra></extra>'
      ),
        # Control overall appearance
        valueformat = ".0f",
        valuesuffix = " Bytes"
    )])

    fig.update_layout(
        title_text="DFL Sankey Diagram", 
        font_size=font_size,
        width=width, 
        height=height,
        autosize=True,
        margin=dict(
            l=width/100,
            r=width/20,
            b=height/10,
            t=height/100,
        ))
    fig.write_html(output_path)
