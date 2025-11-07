import networkx as nx
import re
import os
from typing import List, Dict
from .models import WorkflowSchema, CorrelatedTrace

import matplotlib.pyplot as plt
from networkx.drawing.nx_pydot import graphviz_layout

def save_graph_visualization(G: nx.DiGraph, file_path: str):
    """
    Saves a visualization of the graph to a file.

    Args:
        G: The graph to visualize.
        file_path: The path to save the visualization to.
    """
    plt.figure(figsize=(9, 8))
    G.graph['graph'] = {'rankdir': 'LR'}
    pos = graphviz_layout(G, prog="dot", args='-Gnodesep=0.5 -Gsplines=true')
    nx.draw(G, pos, with_labels=True, arrows=True)
    plt.savefig(file_path)


def _get_pid_to_task_name_map(traces: List[CorrelatedTrace], schema: WorkflowSchema) -> Dict[int, str]:
    """
    Creates a mapping from PID to task name.
    
    Priority:
    1. Use task_name from trace file if available (direct mapping)
    2. Fall back to schema-based pattern matching for traces without task_name
    """
    pid_to_task_name = {}
    
    # First priority: Use task_name directly from trace files if available
    for trace in traces:
        if trace.task_name and trace.pid not in pid_to_task_name:
            pid_to_task_name[trace.pid] = trace.task_name
    
    # Second priority: map PIDs based on write operations (producers) using schema
    for trace in traces:
        if trace.operation == 'write' and trace.pid not in pid_to_task_name:
            for task_name, task in schema.tasks.items():
                for output_regex in task.outputs:
                    if re.match(output_regex, trace.file_name):
                        pid_to_task_name[trace.pid] = task_name
                        break
    
    # Third priority: map PIDs based on read operations for tasks that might only read
    # Check if a PID reads from files that are inputs to a specific task
    for trace in traces:
        if trace.operation == 'read' and trace.pid not in pid_to_task_name:
            for task_name, task in schema.tasks.items():
                # Check if this file is a predecessor (input) to this task
                for input_task_name, input_patterns in task.predecessors.items():
                    for pattern_type, patterns in input_patterns.items():
                        for pattern in patterns:
                            if re.match(pattern, trace.file_name):
                                pid_to_task_name[trace.pid] = task_name
                                break
    
    return pid_to_task_name

def _create_pid_to_task_node_map(traces: List[CorrelatedTrace], pid_to_task_name: Dict[int, str], schema: WorkflowSchema) -> Dict[int, str]:
    """
    Creates a mapping from PID to task_node_id.
    
    When traces have task_name, uses actual PID count instead of schema parallelism.
    This handles cases where actual parallelism differs from schema.
    """
    task_name_to_pids = {}
    has_task_name_in_traces = any(trace.task_name for trace in traces)
    
    for trace in traces:
        if trace.pid in pid_to_task_name:
            task_name = pid_to_task_name[trace.pid]
            if task_name not in task_name_to_pids:
                task_name_to_pids[task_name] = set()
            task_name_to_pids[task_name].add(trace.pid)
    
    # Now assign PIDs to task instances - sort PIDs and assign sequentially
    pid_to_task_node = {}
    for task_name, pids in task_name_to_pids.items():
        sorted_pids = sorted(list(pids))
        
        # If traces have task_name, use actual PID count as parallelism
        # Otherwise, use schema parallelism
        if has_task_name_in_traces:
            actual_parallelism = len(sorted_pids)
        else:
            task = schema.tasks.get(task_name)
            actual_parallelism = task.parallelism if task else len(sorted_pids)
        
        for i, pid in enumerate(sorted_pids):
            if i < actual_parallelism:
                task_node_id = f"{task_name}_{i}"
                pid_to_task_node[pid] = task_node_id
    
    return pid_to_task_node

def _add_task_nodes(G: nx.DiGraph, schema: WorkflowSchema, traces: List[CorrelatedTrace], pid_to_task_name: Dict[int, str]):
    """Adds task nodes to the graph with PID tracking."""
    # Create a mapping from PID to task_node_id
    pid_to_task_node = _create_pid_to_task_node_map(traces, pid_to_task_name, schema)
    
    # Create reverse mapping from task_node_id to PID
    task_node_to_pid = {task_node_id: pid for pid, task_node_id in pid_to_task_node.items()}
    
    # Determine actual parallelism: either from PIDs (if task_name in traces) or schema
    has_task_name_in_traces = any(trace.task_name for trace in traces)
    
    # Get actual task instances from PID mapping
    actual_task_instances = {}
    for task_node_id in task_node_to_pid.keys():
        task_name, instance = task_node_id.rsplit('_', 1)
        if task_name not in actual_task_instances:
            actual_task_instances[task_name] = set()
        actual_task_instances[task_name].add(int(instance))
    
    # Group tasks by their x-position (layer) to assign unique y-positions
    tasks_by_layer = {}
    for task_name, task in schema.tasks.items():
        x_pos = task.stage_order * 2 - 1
        if x_pos not in tasks_by_layer:
            tasks_by_layer[x_pos] = []
        
        # Use actual instances from traces if available, otherwise use schema parallelism
        if task_name in actual_task_instances:
            instances = sorted(list(actual_task_instances[task_name]))
        else:
            instances = list(range(task.parallelism))
        
        for instance_i in instances:
            tasks_by_layer[x_pos].append((task_name, instance_i))
    
    # Add task nodes with unique y-positions per layer
    for x_pos, task_instances in tasks_by_layer.items():
        for y_index, (task_name, instance_i) in enumerate(task_instances):
            node_id = f"{task_name}_{instance_i}"
            G.add_node(
                node_id,
                type='task',
                task_name=task_name,
                task_instance=instance_i,
                pid=task_node_to_pid.get(node_id),
                pos=(x_pos, y_index)
            )

def _add_file_nodes(G: nx.DiGraph, schema: WorkflowSchema, traces: List[CorrelatedTrace], pid_to_task_name: Dict[int, str]):
    """Adds file nodes to the graph with PID tracking for read and write operations."""
    # Create consistent PID to task_node mapping
    pid_to_task_node = _create_pid_to_task_node_map(traces, pid_to_task_name, schema)
    
    task_to_files = {node_id: [] for node_id in G.nodes if G.nodes[node_id]['type'] == 'task'}
    all_output_files = set()
    # Track PIDs for each file
    file_write_pids = {}
    file_read_pids = {}
    
    # Group files by their producer task instance.
    for trace in traces:
        if trace.operation == 'write':
            all_output_files.add(trace.file_name)
            task_node_id = pid_to_task_node.get(trace.pid)
            if task_node_id and G.has_node(task_node_id):
                task_to_files[task_node_id].append(trace.file_name)
            
            # Track write PIDs
            if trace.file_name not in file_write_pids:
                file_write_pids[trace.file_name] = []
            if trace.pid not in file_write_pids[trace.file_name]:
                file_write_pids[trace.file_name].append(trace.pid)
        
        elif trace.operation == 'read':
            # Track read PIDs
            if trace.file_name not in file_read_pids:
                file_read_pids[trace.file_name] = []
            if trace.pid not in file_read_pids[trace.file_name]:
                file_read_pids[trace.file_name].append(trace.pid)

    # Group files by their x-axis layer.
    files_by_layer = {}
    for task_node_id, files in task_to_files.items():
        task_pos = G.nodes[task_node_id]['pos']
        layer = task_pos[0] + 1
        if layer not in files_by_layer:
            files_by_layer[layer] = set()
        files_by_layer[layer].update(files)

    # Add file nodes with evenly distributed y-positions for each layer.
    for layer, files in files_by_layer.items():
        files = sorted(list(files))
        num_files = len(files)
        for i, file_name in enumerate(files):
            if not G.has_node(file_name) or 'pos' not in G.nodes[file_name]:
                G.add_node(
                    file_name,
                    type='file',
                    write_pids=file_write_pids.get(file_name, []),
                    read_pids=file_read_pids.get(file_name, []),
                    pos=(layer, i)
                )

    all_files = {trace.file_name for trace in traces}
    initial_files = sorted(list(all_files - all_output_files))
    # Add initial files that are not produced by any task in the workflow.
    for i, file_name in enumerate(initial_files):
        if not G.has_node(file_name):
            G.add_node(
                file_name,
                type='file',
                write_pids=file_write_pids.get(file_name, []),
                read_pids=file_read_pids.get(file_name, []),
                pos=(0, i)
            )

def _add_edges_and_annotate(G: nx.DiGraph, schema: WorkflowSchema, traces: List[CorrelatedTrace], pid_to_task_name: Dict[int, str]):
    """Adds edges to the graph and annotates them with DFL properties."""
    # Create consistent PID to task_node mapping
    pid_to_task_node = _create_pid_to_task_node_map(traces, pid_to_task_name, schema)
    
    # Track file PIDs for on-demand file node creation
    file_write_pids = {}
    file_read_pids = {}
    for trace in traces:
        if trace.operation == 'write':
            if trace.file_name not in file_write_pids:
                file_write_pids[trace.file_name] = []
            if trace.pid not in file_write_pids[trace.file_name]:
                file_write_pids[trace.file_name].append(trace.pid)
        else:
            if trace.file_name not in file_read_pids:
                file_read_pids[trace.file_name] = []
            if trace.pid not in file_read_pids[trace.file_name]:
                file_read_pids[trace.file_name].append(trace.pid)
    
    for trace in traces:
        task_node_id = pid_to_task_node.get(trace.pid)
        if not task_node_id:
            continue
        
        file_node_id = trace.file_name

        if trace.operation == 'write':
            source_node, target_node = task_node_id, file_node_id
            op_type = 'write'
        else: # read
            source_node, target_node = file_node_id, task_node_id
            op_type = 'read'

        # Create file node on-demand if it doesn't exist
        if not G.has_node(file_node_id):
            # Determine position based on operation and task position
            if trace.operation == 'write' and G.has_node(task_node_id):
                task_pos = G.nodes[task_node_id]['pos']
                file_x = task_pos[0] + 1
                file_y = 0  # Will be adjusted in normalization
            else:
                file_x = 0  # Initial data file
                file_y = 0
            
            G.add_node(
                file_node_id,
                type='file',
                write_pids=file_write_pids.get(file_node_id, []),
                read_pids=file_read_pids.get(file_node_id, []),
                pos=(file_x, file_y)
            )

        if G.has_node(source_node) and G.has_node(target_node):
            if not G.has_edge(source_node, target_node):
                G.add_edge(source_node, target_node)
                # Set the operation type for the edge
                G.edges[source_node, target_node]['op_type'] = op_type
            
            edge_data = G.edges[source_node, target_node]
            edge_data.setdefault('volume', 0)
            edge_data.setdefault('op_count', 0)
            
            edge_data['volume'] += trace.total_bytes
            edge_data['op_count'] += trace.op_count
            
            if trace.io_time > 0:
                edge_data['rate'] = trace.total_bytes / trace.io_time

def _normalize_positions(G: nx.DiGraph):
    """Normalizes the x and y positions of all nodes in the graph."""
    max_x = 0
    max_y = 0
    for node, data in G.nodes(data=True):
        pos = data.get('pos')
        if pos:
            max_x = max(max_x, pos[0])
            max_y = max(max_y, pos[1])

    for node, data in G.nodes(data=True):
        pos = data.get('pos')
        if pos:
            # Normalize x and y to the range [0.1, 0.99]
            norm_x = 0.1 + (pos[0] / max_x) * 0.89 if max_x > 0 else 0.1
            norm_y = 0.1 + (pos[1] / max_y) * 0.89 if max_y > 0 else 0.1
            G.nodes[node]['pos'] = (norm_x, norm_y)

def build_dfl_dag(schema: WorkflowSchema, traces: List[CorrelatedTrace], DEBUG: bool = False) -> nx.DiGraph:
    """
    Builds the DFL-DAG from the workflow schema and correlated traces.

    Args:
        schema: The workflow schema.
        traces: The list of correlated traces.
        DEBUG: If True, save node positions to a log file.

    Returns:
        A networkx.DiGraph representing the DFL-DAG.
    """
    G = nx.DiGraph()
    pid_to_task_name = _get_pid_to_task_name_map(traces, schema)
    _add_task_nodes(G, schema, traces, pid_to_task_name)
    _add_file_nodes(G, schema, traces, pid_to_task_name)
    _add_edges_and_annotate(G, schema, traces, pid_to_task_name)

    if DEBUG:
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        with open(os.path.join(output_dir, "sankey_debug.log"), "w") as f:
            f.write("------ Initial Positions ------\n")
            for node, data in G.nodes(data=True):
                node_type = data.get('type', 'unknown')
                pos_str = f"Position: {data.get('pos')}"
                
                if node_type == 'task':
                    pid = data.get('pid')
                    pid_str = f", PID: {pid}" if pid is not None else ", PID: N/A"
                elif node_type == 'file':
                    write_pids = data.get('write_pids', [])
                    read_pids = data.get('read_pids', [])
                    pid_str = f", Write PIDs: {write_pids}, Read PIDs: {read_pids}"
                else:
                    pid_str = ""
                
                f.write(f"Node: {node}, {pos_str}{pid_str}\n")
            f.write("------ Edges ------\n")
            for u, v, data in G.edges(data=True):
                f.write(f"Edge: {u} -> {v}, Data: {data}\n")

    _normalize_positions(G)

    if DEBUG:
        with open(os.path.join("output", "sankey_debug.log"), "a") as f:
            f.write("------ Normalized Positions ------\n")
            for node, data in G.nodes(data=True):
                node_type = data.get('type', 'unknown')
                pos_str = f"Position: {data.get('pos')}"
                
                if node_type == 'task':
                    pid = data.get('pid')
                    pid_str = f", PID: {pid}" if pid is not None else ", PID: N/A"
                elif node_type == 'file':
                    write_pids = data.get('write_pids', [])
                    read_pids = data.get('read_pids', [])
                    pid_str = f", Write PIDs: {write_pids}, Read PIDs: {read_pids}"
                else:
                    pid_str = ""
                
                f.write(f"Node: {node}, {pos_str}{pid_str}\n")

    for node, data in G.nodes(data=True):
        if 'pos' not in data:
            print(f"Warning: Node {node} does not have a 'pos' attribute.")

    if not nx.is_directed_acyclic_graph(G):
        print("Warning: The generated graph is not a DAG!")

    return G
