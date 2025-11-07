# V2 Implementation Plan

This plan outlines the implementation of the V2 DFL MCP Server, including the original completed work and the new components to be added.

## Phase 1: Core DFL-DAG Engine (V1 - Completed)
---

- [x] **Step 1: Project Setup, Data Models, and Dependencies**
  - **Task**: Initialize project, install `networkx`, `fastmcp`, `plotly`, etc. Define core data models for traces and schema.

- [x] **Step 2: DFL-DAG Construction Logic**
  - **Task**: Implement the trace/schema parser and the core `build_dfl_dag` function. This includes creating task/file nodes and the producer/consumer edges.

- [x] **Step 3: DFL Edge Property Annotation**
  - **Task**: Enhance the graph builder to calculate and annotate edges with DFL lifecycle properties (Volume, Op Count, Rate).

- [x] **Step 4: MCP Server and Visualization Tool**
  - **Task**: Implement the `DFLVisualizationMCP` server, the `get_sankey_data` tool, and the underlying graph filtering and Plotly HTML generation logic.

- [x] **Step 5: Summary Statistics and Critical Path Analysis Tools**
  - **Task**: Implement the `get_flow_summary_stats` and `analyze_critical_path` tools, including the GCPA and pattern detection logic.

- [x] **Step 6: Task Name Priority & Adaptive Parallelism**
  - **Task**: Refactor the graph builder to implement the 3-tier task name priority system, adaptive parallelism, and on-demand node creation. (Completed in Nov 4 session).

- [x] **Step 7: Unit and Integration Testing**
  - **Task**: Write tests for the data parser, graph builder, and all V1 MCP tools.

## Phase 2: Profiling and Recommendation Engines (V2 - New)
---

- [ ] **Step 8: Add Multi-Profiler Support (HDF5/DaYu)**
  - **Task**: Modify `data_parser.py` to support multiple I/O trace formats. Implement a format detection mechanism. Add a new parser for HDF5-based `DaYu` traces using the `h5py` library.
  - **Files**: `src/dfl_mcp/data_parser.py`, `pyproject.toml` (add `h5py`).
  - **Dependencies**: Phase 1.

- [ ] **Step 9: Implement Dataflow Performance Matching (DPM) Component**
  - **Task**: Create the core logic for the DPM engine. This involves defining the structure for the performance model library and implementing the matching algorithm that compares a workflow's DFL-DAG metrics against the library.
  - **Files**: `src/dfl_mcp/analysis/dpm.py`.
  - **Dependencies**: Step 8.

- [ ] **Step 10: Expose DPM as an MCP Tool (`run_dpm`)**
  - **Task**: Implement the `run_dpm` MCP tool in `server.py`. This tool will call the DPM logic from `dpm.py` and format the results as a JSON report.
  - **Files**: `src/dfl_mcp/server.py`.
  - **Dependencies**: Step 9.

- [ ] **Step 11: Implement Workflow Optimization Advisor Component**
  - **Task**: Create the `optimization_advisor.py` module. Implement the rule-based engine for analyzing the DFL-DAG and identifying common I/O anti-patterns (e.g., many small I/Os, read-after-write hazards, inefficient parallelism).
  - **Files**: `src/dfl_mcp/analysis/optimization_advisor.py`.
  - **Dependencies**: Phase 1.

- [ ] **Step 12: Expose Advisor as an MCP Tool (`get_optimization_advice`)**
  - **Task**: Implement the `get_optimization_advice` MCP tool in `server.py`. This tool will orchestrate the analysis from `optimization_advisor.py` and return a ranked list of actionable recommendations.
  - **Files**: `src/dfl_mcp/server.py`.
  - **Dependencies**: Step 11.

- [ ] **Step 13: V2 Integration Testing**
  - **Task**: Write new integration tests for the HDF5 parser and the new `run_dpm` and `get_optimization_advice` tools. Ensure they work with both DDMD and Montage workflows.
  - **Files**: `tests/test_dpm.py`, `tests/test_advisor.py`, `tests/test_parser.py` (updated).
  - **Dependencies**: Step 12.
