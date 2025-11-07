# Agent Initialization Guide

This document provides essential information for AI agents (LLMs) working on the DFL Visualization MCP Server project.

---

## Quick Start for New Agents

### 1. Project Context
This is a **Model Context Protocol (MCP) Server** for analyzing and visualizing workflow data flow lifecycles (DFL). The server processes I/O traces and workflow schemas to construct bipartite dataflow graphs (DFL-DAG) and provides analytical tools for performance optimization.

**Primary Users**: HPC scientists, workflow developers, performance engineers

**Key Technology Stack**:
- Python 3.12+
- NetworkX (graph construction)
- FastMCP (MCP protocol)
- Plotly (interactive visualizations)

### 2. Essential Reading Order

Before starting any work, read these files in order:

1. **[README.md](README.md)** - Project overview and usage instructions
2. **[GEMINI.md](GEMINI.md)** - Project history and bootstrapping context
3. **[docs/spec.md](docs/spec.md)** - Technical specification and system architecture
4. **[docs/workflow_structure.md](docs/workflow_structure.md)** - Workflow traces organization
5. **[docs/FILTERING_GUIDE.md](docs/FILTERING_GUIDE.md)** - Task filtering and Sankey generation guide

### 3. Recent Development History

Check the latest session summaries to understand recent changes:

**Session Files Location**: `sessions/`

**Latest Sessions**:
- `cursor-nov-4-2025.txt` - Task Name Priority System implementation (Claude 4.5 Sonnet)
- `nov-4-2025.txt` - Previous session notes
- `nov-3-2025.txt` - Earlier session notes

**Important**: Always check the most recent session file before starting work to avoid duplicating effort or breaking recent fixes.

---

## Project Architecture Overview

### Core Components

```
src/dfl_mcp/
??? server.py              # MCP server, tool registration, workflow loading
??? data_parser.py         # Trace file parsing (BlockTrace, DatalifeTrace)
??? graph_builder.py       # DFL-DAG construction with task name priority
??? models.py              # Data models (WorkflowSchema, CorrelatedTrace)
??? config.py              # Configuration constants
??? uri_utils.py           # URI parsing utilities
??? analysis/
    ??? sankey_utils.py    # Sankey diagram generation
    ??? metrics.py         # Summary statistics
    ??? critical_path.py   # Critical path analysis (GCPA)
    ??? task_ordering.py   # Task ordering and filtering utilities
```

### Key Design Patterns

#### 1. Task Name Priority System
**Most Critical Feature** (implemented Nov 4, 2025)

The system uses a **3-tier priority hierarchy** for mapping PIDs to tasks:
1. **Tier 1 (Highest)**: Direct `task_name` from trace files
2. **Tier 2**: Schema-based pattern matching for write operations
3. **Tier 3**: Schema-based pattern matching for read operations

**Why This Matters**:
- Workflows like Montage have `task_name` in traces ? use it directly
- Workflows like DDMD rely on schema patterns ? fallback mechanism
- Adaptive parallelism: runtime PIDs override schema's `parallelism` value

**Implementation Files**:
- `data_parser.py`: Lines 85-101 (priority-based correlation)
- `graph_builder.py`: Lines 64-99 (PID mapping), 101-147 (task nodes), 184-251 (edges)

#### 2. Lazy Loading with Caching
- Workflows loaded on-demand via `_load_workflow(workflow_name)`
- Results cached in `self.loaded_workflows` dictionary
- Enables multi-workflow sessions without memory bloat

#### 3. Bipartite Graph Structure
- **Task nodes**: Represent workflow tasks (e.g., `openmm_0`, `aggregate_0`)
- **File nodes**: Represent data files (e.g., `stage0000_task0000.h5`)
- **Edges**: Directed, annotated with DFL properties (volume, op_count, rate)

---

## Current System Capabilities

### Supported Workflows
1. **DDMD** (Drug Discovery, Molecular Dynamics)
   - Schema-based pattern matching
   - Parallelism defined in schema
   - Standard JSON traces

2. **Montage** (Astronomy image mosaicking)
   - Task names embedded in traces
   - Runtime parallelism differs from schema
   - Demonstrates task name priority system

### MCP Tools Available
1. `get_sankey_data` - Generate interactive Sankey diagrams
2. `get_flow_summary_stats` - Compute flow statistics
3. `analyze_critical_path` - Identify bottlenecks using GCPA

### Usage Modes
1. **Interactive CLI**: `python interactive_cli.py` (recommended for users)
2. **MCP Client Tools**: For LLM agent integration (Claude Desktop, etc.)
3. **MCP Inspector**: Development and debugging
4. **Python Client**: Automated testing (`run_client.py`)

---

## Important Constraints & Conventions

### Code Style
- Use type hints for all function signatures
- Docstrings required for all public functions
- Follow existing naming patterns (`_private_method`, `public_method`)
- Keep functions focused (single responsibility principle)

### Graph Construction Rules
1. **Never modify the schema during graph construction** - it's the ground truth
2. **Task nodes**: Created based on actual PIDs when `task_name` present, else schema parallelism
3. **File nodes**: Created on-demand during edge annotation if not pre-existing
4. **Position assignment**: Tasks at x=(stage_order*2-1), Files at x=(producer_x+1) or x=0 (initial)

### Testing Requirements
Before committing changes:
1. Test DDMD workflow (ensure no regression)
2. Test Montage workflow (ensure task name priority works)
3. Check edge count in `output/sankey_debug.log`
4. Verify PID mappings are consistent

### Documentation Updates
When adding features, update:
1. `docs/spec.md` - Technical specification
2. `docs/TODO.md` - Future enhancements (if suggesting new features)
3. `README.md` - User-facing documentation (if changing usage)
4. Session summary file in `sessions/` folder

---

## Common Tasks & How To

### Adding a New MCP Tool

1. **Define tool in `server.py`**:
```python
@self.mcp.tool()
def new_tool_name(workflow_name: str, param1: str) -> str:
    """Tool description for LLM."""
    # Implementation
    return result
```

2. **Update `docs/spec.md`**:
   - Add tool contract to Section 3
   - Document input/output schema
   - Add to Section 5 (Server Actions)

3. **Add CLI menu option** in `interactive_cli.py` (if applicable)

4. **Test with both workflows** (DDMD, Montage)

### Debugging Graph Construction Issues

1. **Enable debug logging**: Check `output/sankey_debug.log` after generation
2. **Key sections in debug log**:
   - "Initial Positions" - shows node placement
   - "Edges" - shows all graph edges with attributes
   - "Normalized Positions" - shows final layout

3. **Check PID mappings**:
```python
from src.dfl_mcp.graph_builder import _get_pid_to_task_name_map
pid_to_task = _get_pid_to_task_name_map(traces, schema)
print(f"Mapped PIDs: {len(pid_to_task)}")
```

4. **Verify task instances**:
```python
from src.dfl_mcp.analysis.task_ordering import get_unique_task_names
tasks = get_unique_task_names(dag)
for name, stage, parallelism in tasks:
    print(f"{name}: stage={stage}, parallelism={parallelism}")
```

### Adding Support for New Trace Formats

See `docs/TODO.md` Priority 1-3 for planned extensions:
- Priority 1: HDF5 trace support
- Priority 2: Pegasus WMS, Python code analysis
- Priority 3: User-defined workflows (CSV/JSON input)

**Implementation pattern**:
1. Create new parser class (e.g., `HDF5TraceParser`)
2. Convert to `CorrelatedTrace` format
3. Maintain compatibility with existing `graph_builder.py`
4. Add format auto-detection in `data_parser.py`

---

## Known Issues & Limitations

### Current Limitations
1. **No real-time streaming**: Workflows must complete before analysis
2. **In-memory only**: Large workflows (>10GB traces) may hit memory limits
3. **JSON/HDF5 only**: Other trace formats require new parsers
4. **Static schemas**: No support for dynamic workflow structures yet

### Recently Fixed (Nov 4, 2025)
- ? Montage workflow edge completeness (101 ? 391 edges)
- ? Adaptive parallelism (mDiffFit: 1 ? 54 instances)
- ? Task name priority system implementation
- ? On-demand file node creation

---

## Workflow Traces Organization

### Required Directory Structure
```
workflow_traces/
??? <workflow_name>/
    ??? <workflow_name>_schema.json          # Required: workflow definition
    ??? <trace_dir>/                         # Required: I/O traces
        ??? *_blk_trace.json                 # Block traces
        ??? *_dlife_trace.json               # Datalife traces (optional with task_name)
```

### Flexible Naming
- Schema file: Any `*_schema.json` file in workflow directory
- Trace directory: Auto-detected from schema name or by searching for trace files
- See `docs/workflow_structure.md` for complete details

---

## Best Practices for Agents

### Before Making Changes
1. ? Read the latest session summary in `sessions/`
2. ? Check `docs/spec.md` for system constraints
3. ? Review related code in context (use grep/search)
4. ? Test with both DDMD and Montage workflows

### When Implementing Features
1. ? Maintain backward compatibility (DDMD must still work)
2. ? Follow the task name priority system (don't bypass it)
3. ? Add comprehensive docstrings
4. ? Update relevant documentation files
5. ? Test edge cases (empty workflows, missing files, etc.)

### When Creating Session Summaries
**CRITICAL**: All future session summaries MUST include:
- Date of session
- **LLM model used** (e.g., "Claude 4.5 Sonnet", "GPT-4", "Gemini 1.5")
- Major issues resolved
- Code changes with line numbers
- Testing performed
- Files modified/created
- Known issues remaining

Save summaries to: `sessions/<tool>-<date>.txt`
Format: `cursor-nov-4-2025.txt`, `gemini-nov-5-2025.txt`, etc.

### Communication with User
- Be explicit about trade-offs and design decisions
- Ask clarifying questions before major architectural changes
- Provide progress updates for long-running tasks
- Suggest alternatives when user's request has issues

---

## Troubleshooting Guide

### Issue: "Workflow not found"
- Check `workflow_traces/<name>/` exists
- Verify `*_schema.json` file present
- Check directory has trace files

### Issue: "PID: N/A" for many tasks
- Check if traces have `task_name` field
- Verify PID mapping in `_get_pid_to_task_name_map`
- Confirm schema patterns match actual file names

### Issue: "Missing edges in Sankey"
- Enable debug logging, check `output/sankey_debug.log`
- Verify both source and target nodes exist
- Check `_add_edges_and_annotate` for edge creation logic
- Ensure on-demand file node creation is working

### Issue: "Graph contains cycles"
- Check for self-loop edges (task writes then reads same file)
- Review critical path calculation in `critical_path.py`
- Cycle removal logic is in place for GCPA

---

## Related Documentation Links

- **Project Overview**: [GEMINI.md](GEMINI.md)
- **User Guide**: [README.md](README.md)
- **Technical Spec**: [docs/spec.md](docs/spec.md)
- **Filtering Guide**: [docs/FILTERING_GUIDE.md](docs/FILTERING_GUIDE.md)
- **Workflow Structure**: [docs/workflow_structure.md](docs/workflow_structure.md)
- **Future Plans**: [docs/TODO.md](docs/TODO.md)
- **Session History**: [sessions/](sessions/)

---

## Contact & Contribution

**Project Owner**: mtang11  
**Primary Development Environment**: Cursor AI (with Claude 4.5 Sonnet), Gemini Code Assistant  
**Repository**: `.`

For any questions or clarifications, refer to session summaries or ask the user directly.

---

**Last Updated**: November 4, 2025  
**Version**: 1.0  
**Agent**: Claude 4.5 Sonnet (via Cursor)
