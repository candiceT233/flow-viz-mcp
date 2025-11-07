# Implementation Plan

## 1. Project Setup, Data Models, and Dependencies
---
- [ ] Step 1: Initialize Project and Install Core Libraries
  - **Task**: Set up the initial Python project structure. Install essential libraries: `networkx` for graph construction/analysis, `fastmcp` for the server interface, `matplotlib` and `pydot` for visualization, `plotly` for Sankey diagrams, and dependencies for parsing (e.g., `json`, `pathlib`).
  - **User Instructions**: Run installation commands for `fastmcp`, `networkx`, `matplotlib`, `pydot`, and `plotly` (e.g., `pip install networkx fastmcp matplotlib pydot plotly`).

- [ ] Step 2: Define Core Data Structures
  - **Task**: Define the data models (`dataclasses` or similar) for the two types of trace files: `BlockTrace` and `DatalifeTrace`. Also define a detailed `WorkflowSchema` model that includes fields for `stage_order`, `parallelism`, `predecessors`, and `outputs` for each task. Finally, define the `DFLProperties` output structure.
  - **Files**:
    - `src/dfl_mcp/models.py`: Defines `BlockTrace`, `DatalifeTrace`, `WorkflowSchema`, `DFLProperties`.
    - `src/dfl_mcp/uri_utils.py`: Implement basic URI utility functions for the `dfl://` scheme.
  - **Step Dependencies**: Step 1.
  - **User Instructions**: None.

## 2. DFL-DAG Construction Logic
---
- [ ] Step 3: Implement Trace and Schema Parser
  - **Task**: Implement the file parsing logic. The `TraceParser` will read both `BlockTrace` and `DatalifeTrace` files and correlate them. The `SchemaLoader` will read the JSON schema file (`ddmd_4n_pfs_large_schema.json`) and parse the task definitions, including `stage_order`, `parallelism`, `predecessors`, and `outputs` with regular expressions.
  - **Files**:
    - `src/dfl_mcp/data_parser.py`: Implements `TraceParser` and `SchemaLoader`.
  - **Step Dependencies**: Step 2.
  - **User Instructions**: None.

- [ ] Step 4: Implement Bipartite DFL-DAG Builder Core
  - **Task**: Create the primary function (`build_dfl_dag`) that uses the parsed schema to build the graph structure. It will: 1. Initialize a `networkx.DiGraph`. 2. Add **Task nodes** for each task defined in the schema, considering `parallelism` and `stage_order`. When adding parallel tasks, ensure they are evenly spaced along the y-axis, ordered by PID. 3. Add **File nodes** based on the `outputs` and `predecessors` in the schema, using regular expressions to match file names. For files on the same layer, ensure they are also evenly spaced along the y-axis. 4. Create directed **Producer (Task $\rightarrow$ File)** and **Consumer (File $\rightarrow$ Task)** edges based on the schema's `predecessors` and `outputs`.
  - **Files**:
    - `src/dfl_mcp/graph_builder.py`: Implements `build_dfl_dag` (excluding property calculation).
  - **Step Dependencies**: Step 3, `src/dfl_mcp/models.py`.
  - **User Instructions**: None.

- [ ] Step 4a: Add Intermediate Graph Visualization
  - **Task**: Add a function to `graph_builder.py` that takes the `networkx` graph and saves a simplified PNG image of it. This function will be used for debugging and verifying the graph structure and node layout. The image should show only nodes and directed edges.
  - **Files**:
    - `src/dfl_mcp/graph_builder.py`: Add the new visualization function.
  - **Step Dependencies**: Step 4.
  - **User Instructions**: None.

- [ ] Step 5: Calculate and Annotate DFL Edge Properties
  - **Task**: Enhance the `build_dfl_dag` function to iterate over all traces and calculate core DFL **lifecycle properties** (Volume, Operation Count, Read/Write Rate). Store these aggregated metrics as attributes on the corresponding graph edges.
  - **Files**:
    - `src/dfl_mcp/graph_builder.py`: Update `build_dfl_dag` to calculate and set edge attributes.
  - **Step Dependencies**: Step 4a.
  - **User Instructions**: None.

## 3. MCP Server and Sankey Visualization Tool
---
- [ ] Step 6: Define and Initialize the MCP Server
  - **Task**: Create the `DFLVisualizationMCP` server class. Implement the initialization logic to load data and build the persistent DFL-DAG instance for the server to use for all tool calls (relying on Steps 3-5).
  - **Files**:
    - `src/dfl_mcp/server.py`: Implements `DFLVisualizationMCP` class.
    - `run_server.py`: Simple script to initialize and run the MCP server instance.
  - **Step Dependencies**: Step 5.
  - **User Instructions**: None.

- [ ] Step 7: Implement Tool 1 (Part 1): Graph Filtering Logic
  - **Task**: Create a core utility function (`filter_subgraph`) that takes the DFL-DAG and lists of selected tasks/files. It should return a filtered subgraph containing only the requested flow, ensuring all edges flow between the selected bipartite nodes.
  - **Files**:
    - `src/dfl_mcp/analysis/sankey_utils.py`: Implements `filter_subgraph`.
  - **Step Dependencies**: Step 6.
  - **User Instructions**: None.

- [ ] Step 8: Implement Tool 1 (Part 2): Sankey Data Generation (`get_sankey_data`)
  - **Task**: Implement the `get_sankey_data` MCP tool method. This method must: 1. Call `filter_subgraph` (Step 7). 2. Use the specified `metric` (e.g., 'Volume') to set the flow value. 3. Generate an interactive Sankey diagram as an HTML file using `plotly`. 4. Return the path to the generated HTML file.
  - **Files**:
    - `src/dfl_mcp/server.py`: Implement the `get_sankey_data` tool method.
    - `src/dfl_mcp/analysis/sankey_utils.py`: Implement the HTML generation logic.
  - **Step Dependencies**: Step 7.
  - **User Instructions**: None.

## 4. Summary Statistics and Critical Path Analysis
---
- [ ] Step 9: Implement Tool 2: Flow Summary Statistics (`get_flow_summary_stats`)
  - **Task**: Implement the `get_flow_summary_stats` MCP tool method. This tool must: 1. Call `filter_subgraph` (Step 7). 2. Iterate over the filtered edges, calculating the total **Volume** and counting **Producer relations** (Task → File) and **Consumer relations** (File → Task). 3. Save the summary statistics to a `.txt` file. The user can optionally provide a filename, otherwise it defaults to the workflow name.
  - **Files**:
    - `src/dfl_mcp/server.py`: Implement the `get_flow_summary_stats` tool method.
    - `src/dfl_mcp/analysis/metrics.py`: Implements the calculation logic and file writing.
  - **Step Dependencies**: Step 8.
  - **User Instructions**: None.

- [ ] Step 10: Implement Tool 3 (Part 1): Generalized Critical Path Analysis (GCPA)
  - **Task**: Implement the core graph algorithm for **GCPA** (longest path). The function must accept a DFL-DAG and a `weight_property` (e.g., 'Volume', 'Footprint') and return the set of edges defining the critical path based on the selected property.
  - **Files**:
    - `src/dfl_mcp/analysis/critical_path.py`: Implements `calculate_critical_path_gcpa`.
  - **Step Dependencies**: Step 9.
  - **User Instructions**: None.

- [ ] Step 11: Implement Tool 3 (Part 2): DFL Caterpillar Tree (CT) Extension
  - **Task**: Implement the logic to extend the critical path (from Step 10) into the **DFL Caterpillar Tree (CT)**. The extension must include all distance-one fan-in and fan-out nodes adjacent to the critical path nodes.
  - **Files**:
    - `src/dfl_mcp/analysis/critical_path.py`: Implement `extend_to_caterpillar_tree`.
  - **Step Dependencies**: Step 10.
  - **User Instructions**: None.

- [ ] Step 12: Implement Tool 3 (Part 3): Pattern Identification and Ranking (`analyze_critical_path`)
  - **Task**: Implement the final `analyze_critical_path` MCP tool. This tool: 1. Calls Step 11 to get the DFL CT. 2. Implements logic to identify key DFL patterns (e.g., Data non-use, Inter-task data locality) by inspecting local graph entities within the CT. 3. Ranks the identified patterns/opportunities by a severity metric (e.g., total volume of the pattern).
  - **Files**:
    - `src/dfl_mcp/server.py`: Implement the `analyze_critical_path` tool method.
    - `src/dfl_mcp/analysis/pattern_rules.py`: Define rules for pattern detection.
  - **Step Dependencies**: Step 11.
  - **User Instructions**: None.

## 5. Testing and Finalization
---
- [ ] Step 13: Implement Graph Builder and Parser Unit Tests
  - **Task**: Write unit tests to validate the data parsing (Step 3) and the core DFL-DAG construction, ensuring correct node types, edge directions, and property annotation (Step 5).
  - **Files**:
    - `tests/test_parser.py`: Unit tests for `data_parser.py`.
    - `tests/test_builder.py`: Unit tests for `graph_builder.py`.
  - **Step Dependencies**: Step 12.
  - **User Instructions**: None.

- [ ] Step 14: Implement Tool Logic Unit and Integration Tests
  - **Task**: Write integration tests to validate the output formats and calculation logic for all three MCP tools, ensuring they handle filtering, metric calculation, and critical path extension correctly.
  - **Files**:
    - `tests/test_sankey.py`: Tests for `get_sankey_data`.
    - `tests/test_stats.py`: Tests for `get_flow_summary_stats`.
    - `tests/test_gcpa.py`: Tests for `analyze_critical_path`.
  - **Step Dependencies**: Step 13.
  - **User Instructions**: None.

---
Would you like to move forward with implementing **