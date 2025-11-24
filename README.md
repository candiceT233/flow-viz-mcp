# DFL Visualization MCP Server

This project implements a Model Context Protocol (MCP) server for visualizing and analyzing Data Flow Lifecycle (DFL) data from scientific workflows. It provides tools to generate interactive Sankey diagrams, calculate flow statistics, and identify critical paths in workflow execution traces.

## Installation

**Prerequisites:**
- Python 3.10 or higher (required by fastmcp)
- `uv` package manager (recommended) - Install with: `curl -LsSf https://astral.sh/uv/install.sh | sh`

**Option 1: Using `uv` (Recommended)**

`uv` automatically manages the virtual environment and dependencies:

```bash
# Install dependencies (uv will create venv automatically)
uv sync

# Or install in development mode
uv pip install -e .
```

**Option 2: Using traditional Python tools**

1.  Create a virtual environment:
    ```bash
    python -m venv .venv
    # or with uv:
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

The MCP server can be used in several ways. The recommended approach is to integrate it with MCP-compatible clients (like Gemini, Claude Desktop, or Cursor IDE) using stdio transport.

### Option 1: MCP Client Integration via Stdio (Recommended)

This is the standard and recommended way to use the MCP server. The server communicates with clients via standard input/output (stdio), and the client automatically manages the server process.

**Important**: With stdio transport, you **DO NOT** manually run the server. Your MCP client will automatically spawn the server process when needed.

#### How Stdio MCP Works

1. **You configure** your MCP client with the command to spawn the server
2. **Client spawns** the server process automatically when you use tools
3. **Communication happens** via stdin/stdout pipes (managed by the client)
4. **You interact** with your client normally, and it calls the MCP tools behind the scenes

#### Available Tools

The server exposes the following tools:

- `get_sankey_data` - Generate interactive Sankey diagram HTML (supports filtering by stage numbers, task IDs, or task ranges)
- `get_flow_summary_stats` - Calculate comprehensive workflow I/O statistics
- `analyze_critical_path` - Identify critical path and optimization opportunities
- `adjust_sankey_canvas_size` - Adjust the canvas size of the last generated Sankey diagram
- `list_workflow_stages` - List all stages in a workflow with their tasks

#### Configuration

Configure your MCP client to use the server. The configuration depends on your client:

**Using `uv run` (Recommended):**
```json
{
  "mcpServers": {
    "flow-viz-mcp": {
      "command": "uv",
      "args": ["run", "run_server.py"],
      "cwd": "<path-to-your-project-directory>"
    }
  }
}
```

**Alternative using Python directly:**
```json
{
  "mcpServers": {
    "flow-viz-mcp": {
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

#### Client-Specific Integration

**Claude Desktop**

1. **Install Claude Desktop** from [claude.ai](https://claude.ai/download)

2. **Configure the MCP Server** by adding to your Claude Desktop config file:
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

3. **Restart Claude Desktop** - The tools will appear in your conversations

4. **Use Natural Language** to request analyses:
   - "Generate a Sankey diagram for the ddmd workflow"
   - "Generate a Sankey diagram for the ddmd workflow with only stage 1 and 2 tasks"
   - "Analyze the critical path using volume as the metric"
   - "Show me flow statistics for tasks openmm_0 through openmm_3"
   - "List all stages in the ddmd workflow"

**Cursor IDE**

To use the DFL Visualization tools with Cursor IDE's AI agent, see the **[Integration Guide](docs/INTEGRATION_GUIDE.md#cursor-ide-integration)** for detailed step-by-step instructions.

**Quick Summary:**
- **File to Edit:** `~/.cursor/mcp.json` (or Cursor's globalStorage location)
- **Configuration:** Add MCP server configuration with absolute paths
- **Expected Output:** Tools available in Cursor's AI chat (Cmd+L or Ctrl+L)

**Gemini Terminal Agent**

To use the DFL Visualization tools with terminal agents like Gemini, see the **[Gemini Integration Guide](docs/GEMINI_INTEGRATION.md)** for detailed step-by-step instructions.

**Quick Summary:**
- **File to Edit:** `~/.config/mcp.json` or your terminal agent's config file
- **Configuration:** Add MCP server configuration
- **Expected Output:** Tools available when querying the terminal agent

**Example Prompts:**

Here are some example prompts you can use with your terminal agent:

**Q: What are the available workflows and what are the tasks for each workflow.**

**A:** The agent will call `list_workflow_stages` for each workflow and return:
```
✦ Available workflows are ddmd and montage.

  Workflow: ddmd
   * Stage 1: openmm (12 instances)
   * Stage 2: aggregate (1 instance), training (1 instance)
   * Stage 3: inference (1 instance)

  Workflow: montage
   * Stage 1: mConcatFit (1 instance), mProject (26 instances)
   * Stage 2: mBgModel (1 instance), mDiffFit (179 instances)
   * Stage 3: mBackground (25 instances)
   * Stage 4: mImgtbl (2 instances)
   * Stage 5: mAdd (2 instances)
   * Stage 6: mViewer (1 instance)
```

**Q: Show me the I/O statistics of task training in ddmd**

**A:** The agent will call `get_flow_summary_stats` with the specific task and return:
```
✦ Here are the I/O statistics for the training_0 task in the ddmd workflow:

   * Combined I/O:
       * Volume: 4.8878 GiB (5,248,236,152 bytes)
       * Operations: 3,706,214
       * Average Bandwidth: 370.58 MB/s
   * Read I/O:
       * Volume: 0.5417 GiB (581,657,336 bytes)
       * Operations: 3,698,942
       * Average Bandwidth: 48.02 MB/s
   * Write I/O:
       * Volume: 4.3461 GiB (4,666,578,816 bytes)
       * Operations: 7,272
       * Average Bandwidth: 2,276.73 MB/s
```

**Q: Please plot dataflow diagram of all tasks in workflow ddmd, save to a file named ddmd_workflow**

**A:** The agent will call `get_sankey_data` and generate:
```
✓  get_sankey_data (flow-viz-mcp MCP Server) {"workflow_name":"ddmd","output_file":"ddmd_workflow.html"}

Sankey diagram saved to output/ddmd_workflow.html
Full workflow visualized with 15 tasks

✦ The Sankey diagram has been saved to output/ddmd_workflow.html.
```

**View the generated diagram:** [Preview ddmd_workflow.html](https://htmlpreview.github.io/?https://github.com/yourusername/flow-viz-mcp/blob/main/output/ddmd_workflow.html)

*Note: Replace `yourusername` with your actual GitHub username or organization name in the link above.*

**Other MCP-Compatible Tools**

The server also works with:
- **Cline** - VS Code extension for Claude
- **Any MCP client** - Any tool supporting the Model Context Protocol (stdio transport)

For detailed integration instructions, see the **[Integration Guide](docs/INTEGRATION_GUIDE.md)**.

### Option 2: MCP Client Integration via HTTP/SSE

If your MCP client supports HTTP-based connections, you can run the server over HTTP using Server-Sent Events (SSE).

#### Step 1: Start the HTTP Server

**Using `uv run` (Recommended):**
```bash
uv run run_server_http.py --host localhost --port 8000
```

**Or using Python directly:**
```bash
python run_server_http.py --host localhost --port 8000
```

The server will start on `http://localhost:8000`. You'll see:
```
============================================================
DFL Visualization MCP Server (HTTP/SSE)
============================================================

Server starting on http://localhost:8000

Available Endpoints:
  - Health: http://localhost:8000/health
  - Tools: http://localhost:8000/tools
  - MCP Call: http://localhost:8000/mcp/call (POST)
  - SSE: http://localhost:8000/sse
```

#### Step 2: Configure Your Client for HTTP

Update your MCP client configuration to use HTTP:

```json
{
  "mcpServers": {
    "flow-viz-mcp": {
      "url": "http://localhost:8000",
      "transport": "http"
    }
  }
}
```

**Note**: Keep the HTTP server running in a separate terminal while using your MCP client.

### Option 3: Interactive CLI (For Direct Use)

The interactive command-line interface provides a user-friendly way to use the tools directly without an MCP client:

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

### Option 4: MCP Inspector (For Development & Testing)

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

## Available Workflows

Place workflow trace data in the `workflow_traces/` directory with the following structure:

```
workflow_traces/
   <workflow_name>/
       <workflow_name>_4n_pfs_large_schema.json
       <workflow_name>_4n_pfs_large/
           *.BlockTrace.json
           *.DatalifeTrace.json
```

The system automatically discovers all workflows on startup.

## Configuration

To use this tool effectively, you may need to edit the following files and values:

1.  **MCP Client Configuration Files**:
    *   For detailed configuration instructions for each client, see the **[Integration Guide](docs/INTEGRATION_GUIDE.md)**.
    *   **Claude Desktop**: `claude_desktop_config.json` (see Claude Desktop Integration section above)
    *   **Cursor IDE**: `mcp.json` (see [Integration Guide - Cursor IDE](docs/INTEGRATION_GUIDE.md#cursor-ide-integration))
    *   **Terminal Agents**: Agent-specific config files (see [Integration Guide - Gemini Terminal Agent](docs/INTEGRATION_GUIDE.md#gemini-terminal-agent-integration))
    *   **Common Values to Edit**:
        *   `"args": ["<path-to-your-project-directory>/run_server.py"]`: Update `<path-to-your-project-directory>` to the absolute path where you have cloned this repository.
        *   `"cwd": "<path-to-your-project-directory>"`: Update `<path-to-your-project-directory>` to the absolute path of this repository.
        *   `"PATH": "<path-to-your-project-directory>/.venv/bin:${PATH}"`: Update `<path-to-your-project-directory>` to the absolute path of this repository.

2.  **Workflow Traces (`workflow_traces/`)**:
    *   **File**: This is a directory where you place your workflow-specific data.
    *   **Location**: `<path-to-your-project-directory>/workflow_traces/`
    *   **Values to Edit**: You will add subdirectories here, each representing a workflow. Inside each workflow directory, you'll place your schema (`*_schema.json`) and trace files (e.g., `*.BlockTrace.json`, `*.DatalifeTrace.json`). Refer to the "Available Workflows" section for the expected structure.

## Project Structure

```
flow-viz-mcp/
 README.md                          # Project overview and usage guide
 interactive_cli.py                 # Interactive command-line interface
 run_server.py                      # MCP server launcher (stdio)
 run_server_http.py                 # MCP server launcher (HTTP/SSE)
 pyproject.toml                     # Python project configuration

 docs/                              # Documentation
    INTEGRATION_GUIDE.md            # Integration instructions for various clients
    GEMINI_INTEGRATION.md           # Detailed Gemini terminal agent integration
    FILTERING_GUIDE.md              # Task filtering input format guide
    workflow_structure.md           # Required directory structure
    prompt.json                     # MCP prompt templates

 src/dfl_mcp/                      # Main source code
    server.py                     # MCP server implementation
    config.py                     # Configuration settings
    data_parser.py                # Trace and schema parsers
    graph_builder.py              # DFL-DAG construction
    models.py                     # Data models
    analysis/                     # Analysis modules
        sankey_utils.py           # Sankey diagram generation
        metrics.py                # Flow statistics
        critical_path.py          # Critical path analysis
        pattern_rules.py          # Pattern identification
        task_ordering.py          # Task ordering utilities

 tests/                            # Unit tests
    test_parser.py
    test_builder.py
    test_sankey.py
    test_stats.py

 workflow_traces/                  # Workflow trace data
    ddmd/
       ddmd_4n_pfs_large_schema.json
       ddmd_4n_pfs_large/
           *.BlockTrace.json
           *.DatalifeTrace.json
    montage/
        ...

 output/                           # Generated visualizations
    sankey_*.html
    *_summary.txt
```

## Documentation

- **[Integration Guide](docs/INTEGRATION_GUIDE.md)** - Step-by-step instructions for integrating with Cursor IDE, Gemini terminal agents, and other MCP-compatible clients
- **[Gemini Integration Guide](docs/GEMINI_INTEGRATION.md)** - Detailed guide for connecting Gemini terminal agents to the MCP server
- **[Task Filtering Guide](docs/FILTERING_GUIDE.md)** - Comprehensive guide on how to specify tasks for filtering and visualization, including input formats, examples, and common use cases
- **[Workflow Structure Guide](docs/workflow_structure.md)** - Required directory structure and naming conventions for adding new workflow traces
- **[Prompt Templates](docs/prompt.json)** - MCP prompt definitions for workflow visualization and analysis
- **[Future Enhancements](docs/TODO.md)** - Proposed features and improvements for future development
- **[Original Request](docs/request.md)** - Original project requirements and feature requests
