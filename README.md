# DFL Visualization MCP Server

This project implements a Model Context Protocol (MCP) server for visualizing and analyzing Data Flow Lifecycle (DFL) data from scientific workflows. It provides tools to generate interactive Sankey diagrams, calculate flow statistics, and identify critical paths in workflow execution traces.

## Installation

1.  Create a virtual environment using `uv`:
    ```bash
    uv venv
    ```

2.  Activate the virtual environment:
    ```bash
    source .venv/bin/activate
    ```

3.  Install the project dependencies:
    ```bash
    pip install -e .
    ```

## Usage

### Option 1: Interactive CLI (Recommended for Direct Use)

The easiest way to use the DFL Visualization tools is through the interactive command-line interface:

```bash
python interactive_cli.py
```

**Features:**
- **Generate Sankey Diagrams** - Interactive visualization of workflow data flows
  - Filter by task range (start/end tasks) or visualize full workflow
  - Choose metric (volume, operation count, or rate)
  - Optional critical path highlighting
- **Flow Summary Statistics** - Analyze I/O patterns and bottlenecks
- **Critical Path Analysis** - Identify performance-critical operations
- **List Tasks** - View all tasks in topological order with PIDs
- **Multi-Workflow Support** - Switch between different workflows
- **Adjustable Canvas Size** - Interactively adjust the Sankey diagram canvas size

**Workflow Discovery:**
The CLI automatically discovers all available workflows in the `workflow_traces/` directory on startup and lets you select which one to analyze.

### Option 2: MCP Client Tools (For LLM Integration)

The MCP server is designed to work with LLM applications that support the Model Context Protocol. The server exposes three main tools:

**Available Tools:**
- `get_sankey_data` - Generate interactive Sankey diagram HTML
- `get_flow_summary_stats` - Calculate workflow statistics
- `analyze_critical_path` - Identify critical path and optimization opportunities
- `adjust_sankey_canvas_size` - Adjust the canvas size of the last generated Sankey diagram

#### Running the MCP Server

Start the server with:

```bash
python run_server.py
```

The server will start and wait for an MCP client to connect. On startup, it:
- Discovers all available workflows in `workflow_traces/`
- Lists available tools
- Loads workflows on-demand with caching

#### Claude Desktop Integration

To use the DFL Visualization tools directly in Claude Desktop conversations:

1. **Install Claude Desktop** from [claude.ai](https://claude.ai/download)

2. **Configure the MCP Server** by adding to your Claude Desktop config file:

   **Linux:** `~/.config/Claude/claude_desktop_config.json`
   **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "dfl-visualization": {
         "command": "python",
         "args": ["<path-to-your-project-directory>/run_server.py"],
         "cwd": "<path-to-your-project-directory>",
         "env": {
           "PATH": "<path-to-your-project-directory>/.venv/bin:${PATH}"
         }
       }
     }
   }
   ```

   **Important:** Replace `<path-to-your-project-directory>` with the absolute path to your `flow-viz-mcp` directory.

3. **Restart Claude Desktop** - The tools will appear in your conversations

4. **Use Natural Language** to request analyses:
   - "Generate a Sankey diagram for the ddmd workflow"
   - "Analyze the critical path using volume as the metric"
   - "Show me flow statistics for tasks openmm_0 through openmm_3"

#### Other MCP-Compatible Tools

The server also works with:
- **Cursor IDE** - Configure in Cursor settings
- **Cline** - VS Code extension for Claude
- **Other MCP clients** - Any tool supporting the Model Context Protocol

### Configuration

To use this tool effectively, you may need to edit the following files and values:

1.  **Claude Desktop Configuration (`claude_desktop_config.json`)**:
    *   **File**: `~/.config/Claude/claude_desktop_config.json` (Linux), `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS), or `%APPDATA%\Claude\claude_desktop_config.json` (Windows).
    *   **Values to Edit**:
        *   `"args": ["<path-to-your-project-directory>/run_server.py"]`: Update `<path-to-your-project-directory>` to the absolute path where you have cloned this repository.
        *   `"cwd": "<path-to-your-project-directory>"`: Update `<path-to-your-project-directory>` to the absolute path of this repository.
        *   `"PATH": "<path-to-your-project-directory>/.venv/bin:${PATH}"`: Update `<path-to-your-project-directory>` to the absolute path of this repository.

2.  **Workflow Traces (`workflow_traces/`)**:
    *   **File**: This is a directory where you place your workflow-specific data.
    *   **Values to Edit**: You will add subdirectories here, each representing a workflow. Inside each workflow directory, you'll place your schema (`*_schema.json`) and trace files (e.g., `*.BlockTrace.json`, `*.DatalifeTrace.json`). Refer to the "Available Workflows" section for the expected structure.

### Option 3: MCP Inspector (For Development & Testing)

The MCP Inspector provides a web-based UI for testing your MCP server:

```bash
# Install the MCP Inspector (one-time setup)
npm install -g @modelcontextprotocol/inspector

# Run the inspector with your server
npx @modelcontextprotocol/inspector python run_server.py
```

This opens a browser interface where you can:
- View all registered tools and their schemas
- Test tool calls with custom parameters
- See request/response logs
- Debug tool behavior and outputs

**Useful for:**
- Verifying tool contracts and parameter types
- Testing edge cases without writing code
- Debugging server responses

### Option 4: Python Client (For Automated Testing)

An example Python client is provided for testing:

```bash
python run_client.py ddmd
```

This connects to the server via stdio transport and demonstrates tool usage.

## Available Workflows

Place workflow trace data in the `workflow_traces/` directory with the following structure:

```
workflow_traces/
  ??? <workflow_name>/
      ??? <workflow_name>_4n_pfs_large_schema.json
      ??? <workflow_name>_4n_pfs_large/
          ??? *.BlockTrace.json
          ??? *.DatalifeTrace.json
```

The system automatically discovers all workflows on startup.

## Project Structure

```
flow-viz-mcp/
??? README.md                          # Project overview and usage guide
??? interactive_cli.py                 # Interactive command-line interface
??? run_server.py                      # MCP server launcher
??? run_client.py                      # Example MCP client
??? pyproject.toml                     # Python project configuration
?
??? docs/                              # Documentation
?   ??? FILTERING_GUIDE.md            # Task filtering input format guide
?   ??? spec.md                       # Technical specification
?   ??? plan.md                       # Development plan
?
??? src/dfl_mcp/                      # Main source code
?   ??? server.py                     # MCP server implementation
?   ??? config.py                     # Configuration settings
?   ??? data_parser.py                # Trace and schema parsers
?   ??? graph_builder.py              # DFL-DAG construction
?   ??? models.py                     # Data models
?   ??? analysis/                     # Analysis modules
?       ??? sankey_utils.py           # Sankey diagram generation
?       ??? metrics.py                # Flow statistics
?       ??? critical_path.py          # Critical path analysis
?       ??? pattern_rules.py          # Pattern identification
?       ??? task_ordering.py          # Task ordering utilities
?
??? tests/                            # Unit tests
?   ??? test_parser.py
?   ??? test_builder.py
?   ??? test_sankey.py
?   ??? test_stats.py
?
??? workflow_traces/                  # Workflow trace data
?   ??? ddmd/
?   ?   ??? ddmd_4n_pfs_large_schema.json
?   ?   ??? ddmd_4n_pfs_large/
?   ?       ??? *.BlockTrace.json
?   ?       ??? *.DatalifeTrace.json
?   ??? montage/
?       ??? ...
?
??? output/                           # Generated visualizations
    ??? sankey_*.html
    ??? *_summary.txt
```

## Documentation

- **[Task Filtering Guide](docs/FILTERING_GUIDE.md)** - Comprehensive guide on how to specify tasks for filtering and visualization, including input formats, examples, and common use cases
- **[Workflow Structure Guide](docs/workflow_structure.md)** - Required directory structure and naming conventions for adding new workflow traces
- **[Technical Specification](docs/spec.md)** - Complete technical specification including system architecture, data models, and implementation details
- **[Development Plan](docs/plan.md)** - Project development roadmap and planning documents
- **[Future Enhancements](docs/TODO.md)** - Proposed features and improvements for future development
- **[Original Request](docs/request.md)** - Original project requirements and feature requests
