from fastmcp.server import FastMCP
from typing import List
from .data_parser import SchemaLoader, TraceParser
from .graph_builder import build_dfl_dag
from .config import INPUT_DIR
from .analysis.sankey_utils import filter_subgraph, create_sankey_html, expand_task_names_to_ids
from .analysis.metrics import calculate_flow_summary_stats
from .analysis.task_ordering import get_topological_task_order, get_tasks_in_range, get_tasks_by_stage_numbers, get_stage_info
import os

from fastmcp.tools.tool import Tool
from .analysis.critical_path import calculate_critical_path_gcpa, extend_to_caterpillar_tree
from .analysis.pattern_rules import identify_patterns

class DFLVisualizationMCP(FastMCP):
    """
    MCP Server for DFL Visualization.
    """

    def __init__(self, workflow_name: str = None):
        super().__init__(name="flow-viz-mcp")
        
        # Discover available workflows
        self.available_workflows = self._discover_workflows()
        
        # Don't load workflow on init - will be loaded on demand
        self.dfl_dag = None
        self.workflow_name = None
        self.loaded_workflows = {}  # Cache for loaded workflows
        self.last_sankey_params = {} # Cache for last sankey params
        
        # Print available workflows on startup
        self._print_startup_message()

        # Register tools
        self.add_tool(Tool.from_function(self.get_sankey_data))
        self.add_tool(Tool.from_function(self.get_flow_summary_stats))
        self.add_tool(Tool.from_function(self.analyze_critical_path))
        self.add_tool(Tool.from_function(self.adjust_sankey_canvas_size))
        self.add_tool(Tool.from_function(self.list_workflow_stages))
    
    def adjust_sankey_canvas_size(self, width: int, height: int, font_size: int = 10, node_pad: int = 15, transform_link_value: bool = True) -> str:
        """
        Adjusts the canvas size of the last generated Sankey diagram.

        Args:
            width: The new width of the canvas.
            height: The new height of the canvas.

        Returns:
            A message confirming the adjustment.
        """
        if not self.last_sankey_params:
            return "Please generate a Sankey diagram first."

        params = self.last_sankey_params
        subgraph = params['subgraph']
        metric = params['metric']
        output_path = params['output_path']
        critical_path_edges = params['critical_path_edges']

        create_sankey_html(subgraph, metric, output_path, critical_path_edges, width, height, font_size, node_pad, transform_link_value)

        return f"Sankey diagram canvas size adjusted to {width}x{height} with font size {font_size}, node pad {node_pad} and transform link value {transform_link_value} in {output_path}"
    
    def _discover_workflows(self) -> List[str]:
        """
        Discovers available workflows in the workflow_traces directory.
        
        Returns:
            A list of available workflow names.
        """
        trace_dir = "workflow_traces"
        if not os.path.exists(trace_dir):
            return []
        
        workflows = []
        for item in os.listdir(trace_dir):
            item_path = os.path.join(trace_dir, item)
            if os.path.isdir(item_path):
                workflows.append(item)
        
        return sorted(workflows)
    
    def _print_startup_message(self):
        """
        Prints the startup message listing available workflows and tools.
        """
        print("\n" + "="*60)
        print("DFL Visualization MCP Server")
        print("="*60)
        print("\nAvailable Workflows:")
        if self.available_workflows:
            for workflow in self.available_workflows:
                print(f"  - {workflow}")
        else:
            print("  (No workflows found in workflow_traces/)")
        
        print("\nAvailable Tools:")
        print("  - get_sankey_data")
        print("  - get_flow_summary_stats")
        print("  - analyze_critical_path")
        print("  - adjust_sankey_canvas_size")
        print("  - list_workflow_stages")
        print("\n" + "="*60 + "\n")

    def _load_workflow(self, workflow_name: str):
        """
        Loads a specific workflow's DFL-DAG.
        
        Args:
            workflow_name: The name of the workflow to load.
            
        Returns:
            The loaded DFL-DAG.
        """
        # Check if already loaded in cache
        if workflow_name in self.loaded_workflows:
            return self.loaded_workflows[workflow_name]
        
        # Validate workflow exists
        if workflow_name not in self.available_workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found. Available workflows: {', '.join(self.available_workflows)}")
        
        # Auto-detect schema and trace paths
        workflow_dir = f"workflow_traces/{workflow_name}"
        
        # Find schema file (any JSON file ending with _schema.json)
        schema_path = None
        trace_path = None
        
        for file in os.listdir(workflow_dir):
            if file.endswith("_schema.json"):
                schema_path = os.path.join(workflow_dir, file)
                # Infer trace directory name from schema filename
                # e.g., "ddmd_4n_pfs_large_schema.json" -> "ddmd_4n_pfs_large"
                trace_dir_name = file.replace("_schema.json", "")
                potential_trace_path = os.path.join(workflow_dir, trace_dir_name)
                if os.path.isdir(potential_trace_path):
                    trace_path = potential_trace_path
                    break
        
        # If trace path not found by schema name, search for any subdirectory with trace files
        if not trace_path:
            for item in os.listdir(workflow_dir):
                item_path = os.path.join(workflow_dir, item)
                if os.path.isdir(item_path):
                    # Check if this directory contains trace files (*.json files)
                    try:
                        files = os.listdir(item_path)
                        # Look for trace files (BlockTrace or DatalifeTrace)
                        if any(f.endswith('.json') and ('BlockTrace' in f or 'DatalifeTrace' in f) for f in files):
                            trace_path = item_path
                            break
                    except PermissionError:
                        continue
        
        if not schema_path:
            raise FileNotFoundError(f"No schema file (*_schema.json) found in {workflow_dir}")
        if not trace_path:
            raise FileNotFoundError(f"No trace directory found for workflow '{workflow_name}' in {workflow_dir}")

        schema_loader = SchemaLoader()
        schema = schema_loader.load_schema(schema_path)

        trace_parser = TraceParser()
        traces = trace_parser.parse_and_correlate_traces(os.path.abspath(trace_path))
        
        dag = build_dfl_dag(schema, traces, DEBUG=True)
        
        # Cache the loaded workflow
        self.loaded_workflows[workflow_name] = dag
        
        return dag

    def get_sankey_data(self, workflow_name: str, start_task_id: str = None, end_task_id: str = None, selected_tasks: List[str] = [], stage_numbers: List[int] = None, selected_files: List[str] = [], metric: str = 'volume', output_file: str = 'sankey.html', highlight_critical_path: bool = True, font_size: int = 10, node_pad: int = 15, transform_link_value: bool = True) -> str:
        """
        Generates a Sankey diagram as an HTML file for the specified workflow.

        Args:
            workflow_name: The name of the workflow to visualize (required).
            start_task_id: Optional starting task ID for range filtering (e.g., 'openmm_0').
            end_task_id: Optional ending task ID for range filtering (e.g., 'training_0').
            selected_tasks: Optional list of task IDs or task name prefixes to include (e.g., ['openmm_0', 'openmm_1'] or ['openmm', 'aggregate']). Task name prefixes will be expanded to all matching task instances.
            stage_numbers: Optional list of stage numbers to include (0-based, e.g., [0, 1] for stages 1 and 2).
            selected_files: A list of selected file IDs (optional).
            metric: The edge attribute to use for the flow value ('volume', 'op_count', or 'rate').
            output_file: The name of the output HTML file.
            highlight_critical_path: Whether to highlight the critical path in orange (default: True).
            font_size: Font size for labels (default: 10).
            node_pad: Padding between nodes (default: 15).
            transform_link_value: Whether to transform link values for display (default: True).

        Returns:
            A message with the path to the generated HTML file and task ordering info.
            
        Note: Filtering priority: stage_numbers > selected_tasks > start_task_id/end_task_id > all tasks
        """
        # Load the workflow
        dag = self._load_workflow(workflow_name)
        
        # Determine which tasks to include (priority: stage_numbers > selected_tasks > start/end range)
        tasks_to_include = []
        
        if stage_numbers is not None and len(stage_numbers) > 0:
            # Filter by stage numbers (highest priority)
            tasks_to_include = get_tasks_by_stage_numbers(dag, stage_numbers)
        elif selected_tasks and len(selected_tasks) > 0:
            # Expand task name prefixes to actual task IDs (e.g., "openmm" -> ["openmm_0", "openmm_1", ...])
            tasks_to_include = expand_task_names_to_ids(dag, selected_tasks)
        elif start_task_id or end_task_id:
            # Use range filtering
            if start_task_id and not end_task_id:
                tasks_to_include = [start_task_id]
            elif end_task_id and not start_task_id:
                tasks_to_include = [end_task_id]
            else:
                # Both provided - get the range
                tasks_to_include = get_tasks_in_range(dag, start_task_id, end_task_id)
        # else: tasks_to_include remains empty, which means all tasks
        
        # Filter the graph
        subgraph = filter_subgraph(dag, tasks_to_include, selected_files)
        
        # Calculate critical path if highlighting is enabled
        critical_path_edges = None
        if highlight_critical_path:
            critical_path_edges = calculate_critical_path_gcpa(subgraph, metric)
        
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_path = os.path.join(output_dir, output_file)
        create_sankey_html(subgraph, metric, output_path, critical_path_edges, font_size=font_size, node_pad=node_pad, transform_link_value=transform_link_value)

        self.last_sankey_params = {
            'subgraph': subgraph,
            'metric': metric,
            'output_path': output_path,
            'critical_path_edges': critical_path_edges,
            'font_size': font_size,
            'node_pad': node_pad,
            'transform_link_value': transform_link_value,
        }
        
        # Build response message
        response = f"Sankey diagram saved to {output_path}"
        if tasks_to_include:
            response += f"\nFiltered tasks ({len(tasks_to_include)}): {', '.join(tasks_to_include[:5])}"
            if len(tasks_to_include) > 5:
                response += f" ... and {len(tasks_to_include) - 5} more"
            if stage_numbers is not None:
                response += f"\nStages included: {', '.join(map(str, stage_numbers))}"
        else:
            # Get all tasks for full workflow
            all_tasks = get_topological_task_order(dag)
            response += f"\nFull workflow visualized with {len(all_tasks)} tasks"
        
        return response

    def get_flow_summary_stats(self, workflow_name: str, selected_tasks: List[str] = [], selected_files: List[str] = [], output_file: str = None) -> str:
        """
        Computes comprehensive I/O summary statistics for a workflow or filtered subset.
        Returns workflow-level and per-task breakdowns for total, read, and write I/O operations,
        including volume, operation count, and average bandwidth (when available).

        Args:
            workflow_name: The name of the workflow to analyze (required).
            selected_tasks: A list of selected task IDs to filter (optional, empty list returns ALL tasks in the workflow).
            selected_files: A list of selected file IDs to filter (optional).
            output_file: Optional path to save the summary file (defaults to output/{workflow_name}_summary.txt).

        Returns:
            A formatted string containing:
            - Workflow totals (all I/O, read I/O, write I/O)
            - Per-task breakdown (all tasks if selected_tasks is empty, otherwise filtered tasks)
            - Each entry includes volume, operation count, and average bandwidth (when available)
        """
        dag = self._load_workflow(workflow_name)
        subgraph = filter_subgraph(dag, selected_tasks, selected_files)
        result = calculate_flow_summary_stats(subgraph, output_file, workflow_name)
        # Return the human-readable summary text instead of the dict
        return result["summary_text"]

    def analyze_critical_path(self, workflow_name: str, weight_property: str = 'volume') -> dict:
        """
        Identifies the critical path in the workflow and suggests potential optimizations.

        Args:
            workflow_name: The name of the workflow to analyze (required).
            weight_property: The edge property to use as weight for critical path calculation (e.g., 'volume', 'op_count', 'rate').

        Returns:
            A dictionary containing the critical path structure and a ranked list of opportunities.
        """
        dag = self._load_workflow(workflow_name)
        critical_path_edges = calculate_critical_path_gcpa(dag, weight_property)
        
        # Calculate total critical weight
        total_critical_weight = 0
        critical_path_nodes = []
        for u, v in critical_path_edges:
            total_critical_weight += dag[u][v].get(weight_property, 0)
            if u not in critical_path_nodes:
                critical_path_nodes.append(u)
            if v not in critical_path_nodes:
                critical_path_nodes.append(v)

        ct_subgraph = extend_to_caterpillar_tree(dag, critical_path_edges)
        opportunities = identify_patterns(ct_subgraph, weight_property)

        return {
            "workflow_name": workflow_name,
            "critical_path_nodes": critical_path_nodes,
            "total_critical_weight": total_critical_weight,
            "opportunities": opportunities
        }

    def list_workflow_stages(self, workflow_name: str) -> str:
        """
        Lists all stages in the workflow with their tasks and instance counts.
        Useful for understanding the workflow structure before filtering.

        Args:
            workflow_name: The name of the workflow to analyze (required).

        Returns:
            A formatted string containing stage information with task names and counts.
        """
        dag = self._load_workflow(workflow_name)
        stage_info = get_stage_info(dag)
        
        # Build formatted response string
        lines = [f"Workflow: {workflow_name}", f"Total Stages: {len(stage_info)}", ""]
        lines.append("Stages:")
        
        for stage_num, tasks in sorted(stage_info.items()):
            stage_display = stage_num + 1  # Convert 0-based to 1-based for display
            lines.append(f"\nStage {stage_display} (API index: {stage_num}):")
            for task_name, count in sorted(tasks):
                lines.append(f"  - {task_name}: {count} instance(s)")
        
        lines.append("\nNote: Stage numbers in API are 0-based (use [0, 1] for stages 1 and 2)")
        
        return "\n".join(lines)
