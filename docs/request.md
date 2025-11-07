# Project Name
MCP Server for Workflow Data Flow Lifecycle (DFL) Visualization

## Project Description
This Model Context Protocol (MCP) server implements the core of **Data Flow Lifecycle (DFL) analysis**. It processes dynamic workflow information (I/O traces and a workflow schema) to construct a comprehensive **Bipartite Dataflow Graph (DFL-DAG)**. The graph's vertices consist of two distinct sets: **tasks** (red circles) and **data files** (blue rectangles). Edges are directed to show the data flow and are annotated with rich **lifecycle properties** (e.g., data volume, access rates). The server exposes specialized tools for interactive analysis and visualization to guide performance remediation strategies.

## Target Audience
HPC scientists, workflow developers, and performance engineers who use agentic assistants (e.g., in research environments) to analyze and optimize the **I/O behavior and coordination** of complex scientific workflows.

## Desired Features
### Graph Construction & Data Enrichment
- [ ] On initialization, the server loads a single directory path (provided as a configuration argument) containing:
    - [ ] Many task I/O trace files (representing dynamic measurement data).
    - [ ] One JSON workflow schema file (correlating task-data dependency).
- [ ] The server constructs a **Bipartite DFL-DAG** where:
    - [ ] **Task vertices ($T$)** are tasks, and **Data vertices ($D$)** are data files.
    - [ ] **Edges ($E$)** are directed from $D \rightarrow T$ for Reads (**Consumer relations**) and $T \rightarrow D$ for Writes (**Producer relations**).
    - [ ] **Edge Attributes:** Store computed DFL lifecycle properties such as **Data volume**, **Access count**, and **Read/Write rates**.

### Visualization and Opportunity Analysis Tools
- [ ] Provide a tool (`get_sankey_data`) that returns the graph data structured for a **Sankey diagram visualization**.
    - [ ] The tool must accept parameters to **selectively filter** the data flow to include only a subset of specified task or data nodes (a DFL entity) for partial workflow analysis.
    - [ ] The Sankey flow widths must be proportional to a selectable DFL property (e.g., Data Volume or Data Rate).

- [ ] Provide a tool (`get_flow_summary_stats`) that computes summary statistics for a selected data flow section (DFL entity).
    - [ ] Output must include the total volume and count of **Producer relations** (Task $\rightarrow$ File) and **Consumer relations** (File $\rightarrow$ Task) for the selected section.

- [ ] Provide a tool (`analyze_critical_path`) that calculates and identifies the **DFL Caterpillar Tree (CT)**.
    - [ ] The calculation must support **Generalized Critical Path Analysis (GCPA)** by allowing the user to select the edge property (e.g., Volume, Flow Rate, or Footprint) used as the path weighting metric.
    - [ ] The output should be a ranked set of lifecycle **patterns/opportunities** (e.g., "Inter-task data locality" or "Data non-use") found along the critical and near-critical path.

## Design Requests
- [ ] Define a clear URI scheme for addressing the workflow and its components.
    - [ ] Proposed: `dfl://<workflow_name>/<component_type>/<component_id>` (e.g., `dfl://my_workflow/task/T1` or `dfl://my_workflow/data/file.h5`).
- [ ] Define the JSON Schema for the `get_sankey_data` tool's input parameters (`metric: string`, `selected_tasks: list`, `selected_files: list`).

## Other Notes
- [!] **Scalability:** The DFL-DAG measurement is designed to be highly scalable, using space proportional only to the number of task-file instances (edges) and is constant per data file.
- [!] **Efficiency:** The automated opportunity analysis is designed to be efficient, with a worst-case complexity that is linear in edges and vertices.
- [ ] **DFL Graph Type:** The primary graph generated is the **DFL-DAG** (acyclic) because each task instance is a distinct vertex. Aggregating instances to form a DFL-Template (DFL-T) that may contain cycles is a future consideration.
