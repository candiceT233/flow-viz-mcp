# MCP Server for Workflow DFL Visualization - V2 Technical Specification

## 1. System Overview

### Core Purpose and Value Proposition

This system is a Python-based server that implements the Model Context Protocol (MCP). Its core purpose is to act as a **DFL Analytics and Optimization Engine**. It transforms raw workflow I/O traces into a **Bipartite Dataflow Graph (DFL-DAG)** and exposes a suite of powerful tools for an LLM agent to visualize, analyze, and recommend specific I/O performance optimizations.

The V2 server introduces advanced capabilities, including **Dataflow Performance Matching (DPM)** against known I/O models and a **Workflow Optimization Advisor** that provides actionable recommendations.

### Key Workflows

1.  **Visualization and Exploration**: An agent visualizes a workflow's dataflow using the Sankey tool, filters to specific areas, and retrieves summary statistics.
2.  **Automated Analysis and Recommendation**: An agent uses the `get_optimization_advice` tool to automatically characterize a workflow, identify bottlenecks, and receive concrete suggestions for improvement (e.g., "Enable collective I/O for task X," "Change the storage layout for file Y").
3.  **Performance Matching**: An agent uses the `run_dpm` tool to match a workflow's I/O patterns against a library of known performance models, providing deeper insights into hardware/software alignment.

### System Architecture

The system remains a single, standalone Python application running as a command-line process and using in-memory graph structures for maximum performance.

*   **Transport Layer**: `stdio` for MCP communication.
*   **Protocol Layer**: `fastmcp` library.
*   **Application Layer**: Core logic, including an expanded set of analysis tools.
*   **Analytics Layer**: `networkx` for graph operations, with new modules for DPM and optimization analysis.

## 2. Project Structure

The project structure will be expanded to include the new analysis modules.
```
flow-viz-mcp/
├── src/dfl_mcp/
│   ├── ... (existing files)
│   └── analysis/
│       ├── ... (existing analysis files)
│       ├── dpm.py                     # NEW: Dataflow Performance Matching logic
│       └── optimization_advisor.py    # NEW: Workflow optimization analysis
└── ...
```

## 3. Performance, Efficiency, and Agent Interaction

This section details the server's internal design choices that prioritize performance, resource efficiency, and a responsive experience for the interacting LLM agent.

### 3.1. Agent Interaction Model

The server is designed for an efficient, iterative analysis workflow:
1.  **One-Time Load**: An agent requests analysis for a given `workflow_name`. The server performs a one-time operation to parse traces and construct the full DFL-DAG. This is the most computationally intensive step.
2.  **In-Memory Caching**: The constructed graph is cached in memory, associated with its `workflow_name`.
3.  **Rapid, Iterative Queries**: All subsequent tool calls for the *same workflow* are near-instantaneous. They query the cached, in-memory graph without needing to re-read or re-process any files from disk.

This "load once, query many times" model enables an agent to rapidly explore a workflow, filter different views, and run multiple analyses without performance degradation.

### 3.2. Performance and Resource Management

The server's architecture is optimized for speed and efficient use of resources.

#### 3.2.1. Lazy Loading and Caching
*   **On-Demand Loading**: The server does not load all available workflows at startup. A workflow's data is only loaded into memory when an agent first requests it via a tool call. This ensures a fast server startup time and low initial memory footprint.
*   **In-Memory Caching**: Once a workflow's DFL-DAG is constructed, it is stored in a dictionary (`self.loaded_workflows`). Subsequent requests for the same workflow retrieve the cached `networkx` graph object directly, eliminating redundant processing.

#### 3.2.2. In-Memory Graph Processing
*   The server's core data structure is a `networkx` graph object held entirely in memory.
*   All analytical operations—such as filtering, pathfinding (GCPA), and metric calculations—are performed using highly optimized, in-memory algorithms provided by `networkx`.
*   This design completely avoids the latency associated with disk I/O or external database queries during analysis, ensuring that tool calls are executed as quickly as possible.

## 4. Feature Specification

### 4.1. DFL-DAG Construction and Profiling Support

*   **Requirements:**
    *   The server must support multiple profiling sources for trace data.
    *   **POSIX I/O**: Continue to support `Datalife` traces (the current JSON format).
    *   **HDF5 I/O**: Add support for `DaYu` traces, which are in HDF5 format. The `data_parser` must be able to detect the format and use the appropriate reader (`h5py` for HDF5).

### 4.2. Tool 1: Sankey Visualization (`get_sankey_data`)
*   (No changes from v1 specification. This tool remains for visualization.)

### 4.3. Tool 2: Flow Summary Statistics (`get_flow_summary_stats`)
*   (No changes from v1 specification.)

### 4.4. Tool 3: Critical Path Analysis (`analyze_critical_path`)
*   (No changes from v1 specification. This tool can be used for focused analysis or as a building block for the new advisor tool.)

### 4.5. Tool 4 (NEW): Dataflow Performance Matching (`run_dpm`)

*   **User Story**: As an LLM agent, I want to match the workflow's I/O patterns against a database of known hardware/software performance models to understand how well the workflow is utilizing the underlying storage system.
*   **Requirements**:
    *   The tool will take a `workflow_name` as input.
    *   It will extract key I/O metrics (e.g., request sizes, concurrency, access patterns) from the DFL-DAG.
    *   It will compare these metrics against an internal library of performance models.
    *   The output will be a report identifying the best-matching model and highlighting key performance deltas.
*   **Tool Contract (`tools/call`):**
    *   **Name**: `run_dpm`
    *   **Input Schema**: `{ "workflow_name": "string" }`
    *   **Output**: A JSON object with the matching report.

### 4.6. Tool 5 (NEW): Workflow Optimization Advisor (`get_optimization_advice`)

*   **User Story**: As an LLM agent, I want to get a prioritized list of actionable I/O optimization recommendations for a given workflow.
*   **Requirements**:
    *   This tool will perform a holistic analysis of the DFL-DAG.
    *   It will use a combination of critical path analysis, pattern detection (extending `analyze_critical_path`), and rule-based heuristics.
    *   It will identify common I/O bottlenecks and anti-patterns.
    *   The output will be a ranked list of human-readable recommendations, including the specific tasks or files to which they apply.
*   **Tool Contract (`tools/call`):**
    *   **Name**: `get_optimization_advice`
    *   **Input Schema**: `{ "workflow_name": "string" }`
    *   **Output**: A JSON object containing a list of recommendations, e.g., `{"recommendations": [{"severity": "High", "description": "Task 'mDiffFit_3' is performing many small read operations. Consider using a larger buffer or collective I/O.", "applies_to": ["task/mDiffFit_3"]}]}`.

## 5. Database Schema

Not applicable. The DPM component's "library of performance models" will be implemented as configuration files or internal data structures, not an external database.

## 6. Server Actions

This section is updated to include actions for the new components.
*   `analysis.dpm.match_performance(graph) -> dict`: Core logic for the DPM tool.
*   `analysis.optimization_advisor.analyze_and_recommend(graph) -> dict`: Core logic for the optimization advisor tool.
*   `data_parser.load_inputs`: Logic to be updated to handle both JSON and HDF5 trace files.

## 7. Task Name Priority System
(No changes from v1 specification.)

## 8. Component Architecture

*   **`Analysis Modules` (`analysis/*`)**: This is expanded to include:
    *   `dpm.py`: Implements the Dataflow Performance Matching logic.
    *   `optimization_advisor.py`: Implements the rules and heuristics for generating optimization recommendations.
*   **`Data Parser` (`data_parser.py`)**: Will be updated to include format detection logic and a reader for HDF5-based `DaYu` traces.
