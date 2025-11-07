
import networkx as nx
import math
from networkx.drawing.nx_pydot import graphviz_layout
import plotly.graph_objects as go
from typing import List

def filter_subgraph(G: nx.DiGraph, selected_tasks: List[str], selected_files: List[str]) -> nx.DiGraph:
    """
    Filters the DFL-DAG to include only the selected tasks and files and their direct neighbors.

    Args:
        G: The DFL-DAG.
        selected_tasks: A list of selected task IDs.
        selected_files: A list of selected file IDs.

    Returns:
        A new DiGraph containing the filtered subgraph.
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

    return G.subgraph(nodes_to_include)

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
