# MCP Server for Workflow DFL Visualization Technical Specification

## 1. System Overview

### Core Purpose and Value Proposition

This system is a Python-based server that implements the Model Context Protocol (MCP). Its core purpose is to act as a **DFL Analytics Engine** that generates and analyzes the complex data flow graphs of scientific workflows. It processes dynamic I/O traces and schema data into a **Bipartite Dataflow Graph (DFL-DAG)**. The server exposes specialized analytic tools (Sankey data preparation, summary statistics, and Critical Path Analysis) to guide LLM agents in identifying performance bottlenecks, data reuse patterns, and optimal scheduling opportunities.

### Server Startup and Workflow Discovery

On initialization, the server:
1. **Discovers Available Workflows**: Scans the `workflow_traces/` directory to identify all available workflow datasets
2. **Displays Startup Message**: Prints a concise list of available workflows and registered tools
3. **Lazy Loading**: Workflows are loaded on-demand when requested by tools, with results cached for efficiency
4. **Multi-Workflow Support**: The server can analyze multiple workflows in a single session without restart

### Key Workflows

1.  **Initialization and Graph Construction:** The server is launched with a specified input directory containing trace files and a schema. It ingests this data once on startup and constructs the persistent in-memory **DFL-DAG (NetworkX)**.
2.  **Visualization Preparation:** The client LLM agent requests Sankey-formatted data, filtered by specific tasks or files. The server queries the DFL-DAG and prepares a JSON data structure (nodes/links) suitable for immediate visualization.
3.  **Advanced Analysis (GCPA/CT):** The LLM agent requests the Critical Path Analysis tool, specifying a weighting metric (e.g., Data Volume). The server executes a **Generalized Critical Path Analysis (GCPA)**, extends it to find the **DFL Caterpillar Tree (CT)**, and returns a ranked list of identified bottleneck patterns.

### System Architecture

The system is a single, standalone Python application designed to run as a command-line process. It relies on internal, in-memory graph structures (`networkx`) rather than external databases.

* **Transport Layer:** Standard input/output (`stdio`) for communication with the MCP client.
* **Protocol Layer:** `fastmcp` library handles MCP message framing, lifecycle, and serialization.
* **Application Layer:** The core logic, containing the graph model, parsing utilities, and the three main analytic tool implementations.
* **Analytics Layer:** The `networkx` library is used for graph construction, traversal, filtering, and algorithm execution (e.g., longest path).

The server is **stateful** after initialization, holding the entire DFL-DAG in memory for rapid, repeated analysis via tool calls.

## 2. Project Structure

The project will be organized into a modular Python package structure, focusing on the separation of data handling, graph logic, and server interfaces.
```
flow-viz-mcp/ ├── src/dfl_mcp/ │   ├── init.py │   ├── server.py            # Main MCP Server application class (Tool handlers) │   ├── config.py            # Configuration and constants (Input paths) │   ├── models.py            # Data models (TraceEntry, DFLProperties) │   ├── uri_utils.py         # URI parsing for 'dfl://' scheme │   ├── data_parser.py       # Trace and Schema file parsing logic │   ├── graph_builder.py     # Core DFL-DAG construction and annotation │   ├── analysis/ │   │   ├── init.py │   │   ├── sankey_utils.py  # Filtering and Sankey JSON conversion logic │   │   ├── metrics.py       # Summary stats calculation │   │   └── critical_path.py # GCPA, CT extension, and pattern identification ├── tests/ │   ├── init.py │   ├── test_builder.py      # Tests for DFL-DAG construction │   ├── test_sankey.py       # Tests for Sankey tool output │   └── test_gcpa.py         # Tests for Critical Path algorithms ├── pyproject.toml           # Project dependencies (networkx, fastmcp) └── run_server.py            # CLI entry point
```

## 3. Feature Specification

### 3.1. DFL-DAG Construction and Initialization

* **User Story:** As an LLM agent, I need a ready-to-query graph representation of the workflow as soon as the server is running.
* **Requirements:**
    * The `DFLVisualizationMCP` server must build the DFL-DAG once upon initialization using the provided input folder.
    * The graph must be **Bipartite**: Nodes must be one of two types: **Task** or **File**.
    * Edges must be directed and annotated with aggregated lifecycle properties (Volume, Count, Rate).
    * **PID Tracking:** All nodes must track their associated PIDs:
        * Task nodes store their PID in a `pid` attribute
        * File nodes store two lists: `write_pids` (PIDs that wrote to the file) and `read_pids` (PIDs that read from the file)
    * **Task Name Priority:** When trace files contain a `task_name` field, this information takes **priority over schema-based pattern matching** for determining task-file relationships.
* **Implementation Steps (Modules: `data_parser.py`, `graph_builder.py`):**
    1.  **Parsing with Task Name Priority:** `data_parser.py` loads the JSON schema and parses all I/O trace files with intelligent correlation:
        * **Task Name Extraction:** If a trace file contains a `task_name` field, it is extracted and stored in both `BlockTrace` and `CorrelatedTrace` objects.
        * **Priority-Based Correlation:** When `task_name` is present in a block trace, the trace is included even if there's no matching datalife trace. This ensures workflows with embedded task names (like Montage) are processed correctly.
        * **Approximation for Missing Data:** When creating traces without datalife matches, uses block-level data with approximations (bytes = blocks × 4096, op_count = total_blocks_accessed).
    2.  **Construction with Adaptive Parallelism:** `graph_builder.py` builds the graph using a flexible approach that adapts to actual runtime behavior:
        * **PID Mapping with Priority System:** `_get_pid_to_task_name_map` uses a 3-tier priority system:
            1. **Highest Priority:** Uses `task_name` directly from trace if present
            2. **Second Priority:** Falls back to schema-based pattern matching for write operations
            3. **Third Priority:** Falls back to schema-based pattern matching for read operations
        * **Adaptive Parallelism:** `_create_pid_to_task_node_map` determines parallelism based on data source:
            * When traces contain `task_name`: Uses actual PID count as parallelism (e.g., creates 54 mDiffFit instances for 54 unique PIDs, even if schema says parallelism=1)
            * When traces lack `task_name`: Falls back to schema's `parallelism` value
    3.  **Dynamic Node Creation:** Nodes are created based on actual runtime data:
        * **Task Nodes:** Created for all unique PIDs found in traces when `task_name` is present, otherwise follows schema parallelism
        * **File Nodes:** Created on-demand during edge annotation if not already present, with position based on producer task or as initial data (x=0)
    4.  **Node Positioning:** Calculate node positions to avoid overlaps:
        * X-position (layer): Determined by `stage_order` for tasks (x = stage_order * 2 - 1) and producer task layer + 1 for files
        * Y-position: All nodes on the same layer are assigned unique, sequential y-positions (0, 1, 2, ...) to prevent overlap
    5.  **Edge Annotation:** Iterates over correlated traces and creates edges with on-demand file node creation:
        * Creates file nodes automatically if they don't exist
        * Aggregates I/O metrics and annotates edges with DFL properties
        * Tracks PIDs for both write and read operations
    6.  **Debug Logging:** When DEBUG mode is enabled, writes detailed node information to `sankey_debug.log`:
        * For task nodes: Includes position and PID
        * For file nodes: Includes position, write PIDs list, and read PIDs list
        * Logs both initial and normalized positions for verification

### 3.2. Tool 1: Sankey Visualization (`get_sankey_data`)

* **User Story:** As an LLM agent, I want an HTML file containing an interactive Sankey diagram to visualize the data flow for a specific part of the workflow.
* **Requirements:**
    * **Workflow Selection:** The tool requires a `workflow_name` parameter to specify which workflow to visualize. The server discovers available workflows in the `workflow_traces/` directory on startup.
    * **Task Range Filtering:** Instead of manually listing tasks, users can specify `start_task_id` and `end_task_id` to visualize all tasks in a topologically-ordered range. The tool uses a task ordering utility to determine the sequence.
    * **File Filtering:** The tool accepts an optional list of `selected_files` to filter specific file nodes.
    * **Edge Width:** Edge widths in the Sankey diagram are always proportional to the Volume attribute (in Bytes). The diagram size is increased (1800x2000 pixels) with node padding of 30 pixels and font size of 12 to provide better vertical spacing, label readability, and visualization of edge thickness and overall flow structure.
    * **Critical Path Highlighting:** When enabled (default: True), the tool automatically calculates the critical path based on the selected metric and highlights all edges along the critical path in orange color. Non-critical edges are displayed in light gray with transparency. Critical path edges also include a "[CRITICAL PATH]" indicator in their hover text.
    * **Output:** The tool will generate an HTML file with an interactive Sankey diagram and return the path to the file along with task count information.
    * **Node Hover Information:** When hovering over nodes in the Sankey diagram, display PID information:
        * For task nodes: Show the task PID
        * For file nodes: Show separate lists of write PIDs and read PIDs
    * **Edge Hover Information:** When hovering over edges (links) in the Sankey diagram, display all edge attributes:
        * Source and target node names
        * Volume (converted from Bytes to MB, displayed with 2 decimal places)
        * Operation count (with thousand separators)
        * Rate (converted from Bytes/sec to MB/sec, displayed with 2 decimal places)
* **Tool Contract (`tools/call`):**
    * **Name:** `get_sankey_data`
    * **Input Schema:** JSON object with:
        * `workflow_name: string` (required) - Name of the workflow to visualize
        * `start_task_id: string` (optional) - Starting task for range filtering
        * `end_task_id: string` (optional) - Ending task for range filtering
        * `selected_files: list[string]` (optional) - List of file IDs to filter
        * `metric: string` (default: 'volume') - Edge attribute for flow value
        * `output_file: string` (default: 'sankey.html') - Output HTML filename
        * `highlight_critical_path: boolean` (default: true) - Whether to highlight critical path
    * **Output:** A string containing the path to the generated HTML file and task filtering information.
* **Implementation Steps (Modules: `sankey_utils.py`, `server.py`, `task_ordering.py`):**
    1.  Load the specified workflow's DFL-DAG using the `_load_workflow()` method with caching.
    2.  If `start_task_id` and/or `end_task_id` are provided, use `get_tasks_in_range()` to determine the task list based on topological ordering.
    3.  Implement a utility function (`filter_subgraph`) that takes a base graph and selection lists to return the corresponding filtered subgraph.
    4.  Calculate the critical path using GCPA based on the selected metric (if `highlight_critical_path` is enabled).
    5.  Implement the main tool handler to generate an interactive Sankey diagram as an HTML file using `plotly`.
    6.  Configure edge colors: orange for critical path edges, light gray with transparency for non-critical edges.
    7.  Configure custom hover templates to display PID information for each node type.
    8.  Configure custom hover templates for edges to display all edge attributes (volume, op_count, rate) with appropriate formatting, unit conversion, and critical path indicator.

### 3.3. Tool 2: Flow Summary Statistics (`get_flow_summary_stats`)

* **User Story:** As an LLM agent, I need to save summary metrics on the total I/O activity for a flow section I'm investigating to a file.
* **Requirements:**
    * The tool calculates the aggregate metrics for a selectively filtered subgraph.
    * Output must be saved to a `.txt` file. The user can optionally provide a filename, otherwise it defaults to the workflow name.
* **Tool Contract (`tools/call`):**
    * **Name:** `get_flow_summary_stats`
    * **Input Schema:** JSON object including optional `selected_tasks`, `selected_files`, and `output_file` (string).
    * **Output:** A string confirming the path to the saved summary file.
* **Implementation Steps (Module: `metrics.py`):**
    1.  Utilize `sankey_utils.filter_subgraph` (from Tool 1) to define the boundary.
    2.  Iterate over the edges of the subgraph, using the directionality (Task → File or File → Task) to classify edges for aggregation.
    3.  Save the summary statistics to the specified output file, or a default file named after the workflow.

### 3.4. Tool 3: Critical Path Analysis (`analyze_critical_path`)

* **User Story:** As an LLM agent, I want the system to execute sophisticated graph algorithms to automatically identify and rank the most significant data flow bottlenecks (critical paths and patterns).
* **Requirements:**
    * **GCPA:** Must support **Generalized Critical Path Analysis** by using a selectable DFL property (`Volume`, `Rate`, `Footprint`) as the edge weight for finding the longest (critical) path.
    * **CT Extension:** The critical path must be extended to include all adjacent fan-in/fan-out nodes, forming the **DFL Caterpillar Tree (CT)**.
    * **Pattern Identification:** Must implement logic to detect DFL patterns (e.g., "Inter-task data locality," "Data non-use") within the CT.
* **Tool Contract (`tools/call`):**
    * **Name:** `analyze_critical_path`
    * **Input Schema:** JSON object with `weight_property: string` (e.g., "Volume", "Footprint").
    * **Output:** JSON object containing the critical path structure and a ranked list of patterns:
        ```json
        {
          "critical_path_nodes": ["T1", "F_A", "T2", ...],
          "total_critical_weight": 520.5,
          "opportunities": [
            {"pattern": "Inter-task data locality", "severity_metric": 120.0, "nodes": ["F_B"]},
            {"pattern": "Data non-use", "severity_metric": 80.0, "nodes": ["F_C"]}
          ]
        }
        ```
* **Implementation Steps (Module: `critical_path.py`):**
    1.  Implement `calculate_critical_path_gcpa` using `networkx.longest_path` or a custom longest path algorithm, ensuring edge weights are correctly inverted for the max-path problem.
    2.  Implement `extend_to_caterpillar_tree` to perform the distance-one extension.
    3.  Implement pattern detection and ranking logic based on structural and property checks within the CT subgraph.

## 4. Database Schema

Not applicable, as the project's data (DFL-DAG) is constructed and held entirely in memory using the `networkx` library.

## 5. Server Actions

This section describes the core logic modules that handle data parsing and graph operations.

### 5.1. Data and Graph Actions

* **`data_parser.load_inputs(root_dir: str) -> tuple`**
    * **Description:** Loads and validates all I/O traces (both `BlockTrace` and `DatalifeTrace` files) and the workflow schema from the input directory. It will also correlate the two types of traces.
* **`graph_builder.build_dfl_dag(traces, schema) -> networkx.DiGraph`**
    * **Description:** Constructs the DFL-DAG by first building the graph structure from the `schema` (tasks, files, and their relationships), and then annotating the edges with aggregated DFL properties from the `traces`.
* **`server._load_workflow(workflow_name: str) -> networkx.DiGraph`**
    * **Description:** Loads a specific workflow's DFL-DAG with automatic schema and trace path detection. Uses caching to avoid redundant loading. Supports flexible directory structures and naming conventions.
* **`server._discover_workflows() -> List[str]`**
    * **Description:** Scans the `workflow_traces/` directory to identify all available workflow directories. Returns a sorted list of workflow names.
* **`analysis.sankey_utils.filter_subgraph(graph, selected_nodes) -> networkx.DiGraph`**
    * **Description:** Filters the graph based on specified nodes, maintaining the bipartite structure.
* **`analysis.critical_path.calculate_critical_path_gcpa(graph, weight_property) -> list`**
    * **Description:** Finds the longest path based on the selected edge property, removing self-loop cycles for proper DAG analysis.
* **`analysis.task_ordering.get_topological_task_order(graph) -> list`**
    * **Description:** Returns a topologically sorted list of all task nodes based on workflow stage order and dependencies.
* **`analysis.task_ordering.get_tasks_in_range(graph, start_task_id, end_task_id) -> list`**
    * **Description:** Returns all tasks between (and including) start and end tasks based on connectivity, enabling dataflow path filtering.
* **`analysis.task_ordering.get_unique_task_names(graph) -> List[Tuple[str, int, int]]`**
    * **Description:** Returns a list of unique task names (without instance indices) in stage order with their parallelism information.

## 6. Task Name Priority System

### 6.1. Overview

The system implements a **task name priority mechanism** that automatically adapts to different workflow trace formats. When trace files contain a `task_name` field, this information takes absolute priority over schema-based pattern matching, enabling more accurate and flexible workflow analysis.

### 6.2. Design Rationale

Different workflow tracing systems produce traces with varying levels of metadata:
* **High-fidelity traces** (e.g., Montage): Include `task_name` directly in trace files, providing explicit task-file relationships
* **Pattern-based traces** (e.g., DDMD): Rely on file path patterns in schema to infer task-file relationships

The priority system ensures both formats are handled correctly while maximizing accuracy when explicit task names are available.

### 6.3. Implementation Details

#### 6.3.1. Data Parsing Layer (`data_parser.py`)

**Task Name Extraction:**
* `_parse_block_trace()` extracts `task_name` from raw JSON if present
* Both `BlockTrace` and `CorrelatedTrace` models include optional `task_name` field

**Priority-Based Correlation:**
* When `task_name` exists in block trace: Creates `CorrelatedTrace` even without matching datalife trace
* When `task_name` is missing: Requires strict block-datalife correlation (backward compatibility)
* Missing datalife metrics are approximated using block-level data (bytes = blocks × 4096)

#### 6.3.2. Graph Building Layer (`graph_builder.py`)

**3-Tier PID Mapping Priority (`_get_pid_to_task_name_map`):**
1. **Tier 1 (Highest):** Direct use of `trace.task_name` if present in `CorrelatedTrace`
2. **Tier 2:** Schema pattern matching for write operations (producer task identification)
3. **Tier 3:** Schema pattern matching for read operations (consumer task identification)

**Adaptive Parallelism (`_create_pid_to_task_node_map`):**
* **With task_name:** Parallelism = number of unique PIDs for that task (actual runtime parallelism)
* **Without task_name:** Parallelism = schema's `parallelism` value (design-time parallelism)
* Example: Montage mDiffFit has schema parallelism=1 but actual parallelism=54 (54 PIDs), system creates 54 instances

**Dynamic Task Node Creation (`_add_task_nodes`):**
* Determines actual task instances from PID mapping (not just schema)
* Creates nodes for all PIDs when task_name is present
* Falls back to schema parallelism for tasks without traces

**On-Demand File Node Creation (`_add_edges_and_annotate`):**
* Creates file nodes automatically if referenced in traces but not in graph
* Assigns position based on producer task or as initial data (x=0)
* Ensures all traced I/O operations become edges, regardless of schema patterns

### 6.4. Benefits

* **Accuracy:** Workflows with explicit task names achieve near-perfect task-file relationship mapping
* **Flexibility:** Handles workflows where runtime parallelism differs from design-time schema
* **Robustness:** Processes traces with incomplete or missing datalife files
* **Backward Compatibility:** Continues to work correctly with schema-only workflows (DDMD)
* **Scalability:** Supports workflows with hundreds of task instances and complex file patterns

### 6.5. Example: Montage vs DDMD

| Feature | DDMD (Schema-based) | Montage (Task-name Priority) |
|---------|---------------------|------------------------------|
| Task name in traces | No | Yes |
| PID mapping | Schema patterns | Direct from traces |
| Parallelism source | Schema (12 openmm) | Actual PIDs (54 mDiffFit) |
| Edge completeness | ~100 edges | ~391 edges |
| Datalife requirement | Required | Optional |

## 7. Component Architecture

### 7.1. Modular Components

* **`Server` (`server.py`):** Responsible for Initialization (loading/building the graph) and registering the three analytic tools to the `fastmcp` runtime.
* **`GraphBuilder` (`graph_builder.py`):** Core data transformation module. Isolates all logic related to creating the NetworkX object and calculating DFL metrics. Implements the task name priority system for adaptive graph construction.
* **`Analysis Modules` (`analysis/*`):** Specialized modules that implement the complex algorithms (e.g., Sankey data structure, GCPA, CT logic) necessary to fulfill the tool contracts. This ensures the core `server.py` remains clean and focused on MCP communication.
* **`URI Utils` (`uri_utils.py`):** Provides parsing and validation for the custom `dfl://` URI scheme.