# Gemini Code Assistant Project: MCP Server for Workflow Data Flow Lifecycle (DFL) Visualization

This project, bootstrapped by the Gemini Code Assistant, implements a Model Context Protocol (MCP) server for analyzing and visualizing the data flow in complex scientific workflows.

## Project Overview

The server constructs a Bipartite Dataflow Graph (DFL-DAG) from I/O traces and a workflow schema. This graph represents the relationships between tasks and data files in a workflow, with edges annotated with rich lifecycle properties such as data volume and access rates.

The primary goal of this project is to provide tools for HPC scientists, workflow developers, and performance engineers to understand and optimize the I/O behavior of their workflows.

## Key Features

*   **DFL-DAG Construction**: The server automatically builds a DFL-DAG from workflow data with adaptive parallelism and task name priority system.
*   **Sankey Diagram Visualization**: The `get_sankey_data` tool provides data structured for creating interactive Sankey diagrams to visualize data flow.
*   **Flow Summary Statistics**: The `get_flow_summary_stats` tool computes summary statistics for selected parts of the workflow.
*   **Critical Path Analysis**: The `analyze_critical_path` tool identifies the critical path in the workflow and suggests potential optimizations.
*   **Multi-Workflow Support**: Analyze multiple workflows (DDMD, Montage, etc.) in a single session with workflow discovery and lazy loading.
*   **Task Name Priority System**: Automatically adapts to workflows with embedded task metadata, ensuring accurate task-file relationship mapping.

## Project Structure

*   `request.md`: The original project request.
*   `prd.md`: The Product Requirements Document.
*   `planning.md`: The implementation plan for the project.
*   `workflow_traces/`: Contains sample workflow traces and data.
*   `docs/`: Comprehensive documentation (spec, guides, TODO).
*   `sessions/`: Development session summaries and history.
*   `GEMINI.md`: This file - a summary of the project.
*   **`AGENT.md`**: Essential guide for AI agents working on this project - **READ THIS FIRST!**

## For AI Agents

**If you are an AI agent (LLM) working on this project, please read [`AGENT.md`](AGENT.md) first.** It contains:
- Quick start guide and essential reading order
- System architecture overview
- Current capabilities and limitations
- Code conventions and best practices
- Common tasks and troubleshooting
- Recent development history

## Session Summaries

All development sessions are documented in the `sessions/` folder. Each session summary includes:
- **Date of session**
- **LLM model used** (e.g., "Claude 4.5 Sonnet", "GPT-4", "Gemini 1.5 Pro")
- Major issues resolved
- Code changes and testing performed
- Known issues and future work

**IMPORTANT**: When creating new session summaries, always include the LLM model information. This helps track which AI assistants contributed to different features and understand the context of development decisions.

### Recent Sessions
- `cursor-nov-4-2025.txt` - Task Name Priority System implementation (Claude 4.5 Sonnet)
- `nov-4-2025.txt` - Previous development work
- `nov-3-2025.txt` - Earlier development work

## Documentation

- **[README.md](README.md)** - User guide and usage instructions
- **[docs/spec.md](docs/spec.md)** - Technical specification
- **[docs/FILTERING_GUIDE.md](docs/FILTERING_GUIDE.md)** - Task filtering and Sankey generation
- **[docs/workflow_structure.md](docs/workflow_structure.md)** - Workflow traces organization
- **[docs/TODO.md](docs/TODO.md)** - Future enhancements and roadmap

## Current Status (November 4, 2025)

**Latest Major Features:**
- ? Task Name Priority System - handles workflows with embedded task metadata
- ? Adaptive Parallelism - runtime PIDs override schema parallelism
- ? Multi-workflow support with lazy loading and caching
- ? Path-based task range filtering for accurate Sankey generation
- ? Interactive CLI with streamlined workflow
- ? Comprehensive documentation and agent initialization guide

**Supported Workflows:**
- DDMD (Drug Discovery) - schema-based pattern matching
- Montage (Astronomy) - task name priority with adaptive parallelism

**Next Priorities** (see docs/TODO.md):
1. HDF5 trace format support
2. Pegasus WMS and Python code analysis
3. User-defined workflow input (CSV/JSON/Interactive)
