# Gemini MCP Integration Guide

This guide provides step-by-step instructions for connecting Google's Gemini to the DFL Visualization MCP Server.

## Overview

There are two main ways to connect Gemini to MCP servers:
1. **Stdio Transport** (Recommended) - Direct process communication
2. **HTTP/SSE Transport** - Web-based communication

## Prerequisites

1. **Project Setup**: Ensure your MCP server is set up and working
   ```bash
   cd /Users/mengtang/script/flow-viz-mcp
   uv sync  # Install dependencies
   ```

2. **Test the Server** (Optional - for verification only):
   ```bash
   uv run run_server.py
   ```
   You should see:
   ```
   ============================================================
   DFL Visualization MCP Server
   ============================================================
   
   Available Workflows:
     - ddmd
     - montage
   
   Available Tools:
     - get_sankey_data
     - get_flow_summary_stats
     - analyze_critical_path
     - adjust_sankey_canvas_size
     - list_workflow_stages
   ```
   **Note**: When you run this manually, the server waits for MCP protocol messages on stdin. Press Ctrl+C to exit. In normal use, Gemini will spawn this automatically.

---

## Method 1: Stdio Transport (Recommended)

This is the standard MCP connection method where Gemini communicates with the server via standard input/output.

**Important**: With stdio transport, you **DO NOT** manually run the server. The Gemini terminal agent will automatically spawn the server process as a child process based on your configuration. The server communicates via stdin/stdout pipes that the client manages.

### How Stdio MCP Works

1. **You configure** the Gemini terminal agent with the command to spawn the server
2. **Gemini spawns** the server process automatically when needed
3. **Communication happens** via stdin/stdout pipes (you don't see this)
4. **You interact** with Gemini normally, and it calls the MCP tools behind the scenes

### Step 1: Determine Your Gemini Client

Gemini can be accessed through various clients. Common options:

- **Google AI Studio** (web-based)
- **Gemini API** via Python SDK
- **Terminal agents** that support Gemini (e.g., `aider`, `gpt-engineer`)
- **Custom MCP client** using Google's Gemini API

### Step 2: Configure MCP Server

The configuration depends on your Gemini client. Here are common approaches:

#### Option A: Using `uv run` (Recommended)

Create or edit the MCP configuration file for your Gemini client:

**For most MCP clients, create `~/.config/mcp.json` or client-specific config:**

```json
{
  "mcpServers": {
    "flow-viz-mcp": {
      "command": "uv",
      "args": ["run", "run_server.py"],
      "cwd": "/Users/mengtang/script/flow-viz-mcp"
    }
  }
}
```

#### Option B: Using Python Directly

```json
{
  "mcpServers": {
    "flow-viz-mcp": {
      "command": "python",
      "args": ["/Users/mengtang/script/flow-viz-mcp/run_server.py"],
      "cwd": "/Users/mengtang/script/flow-viz-mcp",
      "env": {
        "PATH": "/Users/mengtang/script/flow-viz-mcp/.venv/bin:${PATH}"
      }
    }
  }
}
```

### Step 3: Client-Specific Configuration

#### For Google AI Studio / Gemini API (Python SDK)

If you're using Gemini via Python, you'll need an MCP client library. Example:

```python
# Example: Using Gemini with MCP (pseudo-code)
from google import generativeai as genai
import subprocess
import json

# Configure MCP server
mcp_config = {
    "command": "uv",
    "args": ["run", "run_server.py"],
    "cwd": "/Users/mengtang/script/flow-viz-mcp"
}

# Start MCP server process
mcp_process = subprocess.Popen(
    [mcp_config["command"]] + mcp_config["args"],
    cwd=mcp_config["cwd"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Use Gemini API with MCP tools
genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel('gemini-pro')
# ... connect MCP tools to Gemini ...
```

---

## Gemini Terminal Agent Integration

This section provides detailed instructions specifically for connecting a **Gemini terminal agent** (a command-line tool that uses Google's Gemini API) to the DFL Visualization MCP Server.

### What is a Gemini Terminal Agent?

A Gemini terminal agent is a command-line application that:
- Uses Google's Gemini API for AI interactions
- Supports MCP (Model Context Protocol) for tool integration
- Runs in your terminal and can execute commands, read files, and use MCP tools
- Examples: `aider`, custom terminal agents using Gemini API, or MCP-compatible CLI tools

### Step 1: Identify Your Terminal Agent's Configuration

Different terminal agents store their configuration in different locations. Common locations:

- **Aider**: `~/.aider/config.json`
- **Custom agents**: `~/.config/<agent-name>/config.json` or `~/.<agent-name>/config.json`
- **Generic MCP clients**: `~/.config/mcp.json`

**To find your agent's config location:**
1. Check your terminal agent's documentation
2. Look for environment variables like `MCP_CONFIG_PATH`
3. Check common locations: `~/.config/`, `~/.<agent-name>/`, or `~/Library/Application Support/<agent-name>/`

### Step 2: Create or Edit Configuration File

Create the configuration file if it doesn't exist, or edit the existing one.

**Example for Aider:**
```bash
mkdir -p ~/.aider
touch ~/.aider/config.json
```

**Example for generic MCP client:**
```bash
mkdir -p ~/.config
touch ~/.config/mcp.json
```

### Step 3: Add MCP Server Configuration

Open your terminal agent's configuration file and add the MCP server configuration.

#### Option A: Using `uv run` (Recommended)

This is the recommended approach as `uv` automatically manages the virtual environment:

```json
{
  "mcpServers": {
    "flow-viz-mcp": {
      "command": "uv",
      "args": ["run", "run_server.py"],
      "cwd": "/Users/mengtang/script/flow-viz-mcp"
    }
  }
}
```

#### Option B: Using Python Directly

If you prefer to use Python directly (requires virtual environment setup):

```json
{
  "mcpServers": {
    "flow-viz-mcp": {
      "command": "python",
      "args": ["/Users/mengtang/script/flow-viz-mcp/run_server.py"],
      "cwd": "/Users/mengtang/script/flow-viz-mcp",
      "env": {
        "PATH": "/Users/mengtang/script/flow-viz-mcp/.venv/bin:${PATH}"
      }
    }
  }
}
```

**Important Notes:**
- Replace `/Users/mengtang/script/flow-viz-mcp` with your actual project path
- Use **absolute paths**, not relative paths
- Ensure the `cwd` (current working directory) points to your project root

### Step 4: Verify Configuration Syntax

Ensure your JSON is valid:

```bash
# Test JSON syntax (macOS/Linux)
python3 -m json.tool ~/.aider/config.json

# Or use jq if installed
jq . ~/.aider/config.json
```

If there are syntax errors, fix them before proceeding.

### Step 5: Start Your Gemini Terminal Agent

**Important**: You do NOT need to manually run `uv run run_server.py`. The terminal agent will automatically spawn the server when needed.

Simply start your terminal agent as you normally would:

```bash
# Example commands (depends on your agent)
aider
# or
gemini-terminal-agent
# or
your-agent-command
```

### Step 6: Verify MCP Connection

Once your terminal agent is running, verify that it can see the MCP tools:

1. **Ask your agent**: "What MCP tools are available?" or "List available MCP servers"
2. **Expected response**: The agent should list:
   - `get_sankey_data`
   - `get_flow_summary_stats`
   - `analyze_critical_path`
   - `adjust_sankey_canvas_size`
   - `list_workflow_stages`

### Step 7: Test Tool Execution

Try a simple command to test the connection:

**Example 1: List workflow stages**
```
List all stages in the ddmd workflow
```

**Expected**: The agent should call `list_workflow_stages` and return stage information.

**Example 2: Generate a diagram**
```
Generate a Sankey diagram for the ddmd workflow
```

**Expected**: The agent should call `get_sankey_data` and inform you that the diagram was saved to `output/sankey.html`.

### How It Works Behind the Scenes

When you ask your terminal agent to use an MCP tool:

1. **Agent reads config**: Your terminal agent reads the MCP configuration from the config file
2. **Agent spawns server**: The agent automatically runs `uv run run_server.py` (or your configured command) as a child process
3. **Communication via pipes**: 
   - Agent sends JSON-RPC requests to the server's stdin
   - Server processes requests and writes responses to stdout
   - Agent reads responses from stdout
4. **You see results**: The agent presents the results in your terminal conversation

### Terminal Agent-Specific Examples

#### Example: Aider Configuration

**File**: `~/.aider/config.json`

```json
{
  "mcpServers": {
    "flow-viz-mcp": {
      "command": "uv",
      "args": ["run", "run_server.py"],
      "cwd": "/Users/mengtang/script/flow-viz-mcp"
    }
  }
}
```

Then use aider normally:
```bash
aider
> Generate a Sankey diagram for the ddmd workflow
```

#### Example: Custom Terminal Agent

If your terminal agent uses a different config format, adapt accordingly. Some agents may require:

```json
{
  "mcp": {
    "servers": {
      "flow-viz-mcp": {
        "command": "uv",
        "args": ["run", "run_server.py"],
        "cwd": "/Users/mengtang/script/flow-viz-mcp"
      }
    }
  }
}
```

Check your agent's documentation for the exact format.

### Troubleshooting Terminal Agent Connection

#### Issue: Agent doesn't recognize MCP config

**Solutions:**
1. Verify config file location matches your agent's expected path
2. Check config file permissions: `chmod 644 ~/.aider/config.json`
3. Ensure JSON syntax is valid (no trailing commas, proper quotes)
4. Restart your terminal agent after making config changes

#### Issue: "Command not found: uv"

**Solutions:**
1. Install `uv`: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Verify `uv` is in PATH: `which uv`
3. Use full path in config: `"command": "/path/to/uv"`
4. Or switch to Python directly (Option B in Step 3)

#### Issue: Agent spawns server but tools don't work

**Solutions:**
1. Check that workflow data exists: `ls workflow_traces/`
2. Verify server can start manually: `uv run run_server.py` (then Ctrl+C)
3. Check agent logs for error messages
4. Test with the Python client: `python run_client.py ddmd`

#### Issue: Server process hangs or doesn't respond

**Solutions:**
1. Ensure the project directory path is correct and accessible
2. Check that `run_server.py` is executable: `chmod +x run_server.py`
3. Verify virtual environment is set up: `ls .venv/bin/python`
4. Check for Python errors: Look at agent's stderr output

### Next Steps

Once connected, you can:

1. **Explore workflows**: "List all stages in the ddmd workflow"
2. **Generate visualizations**: "Create a Sankey diagram for stages 1-2 of ddmd"
3. **Analyze performance**: "Show me I/O statistics for the ddmd workflow"
4. **Find bottlenecks**: "Analyze the critical path using volume as the metric"

---

### Step 4: Start Your Gemini Terminal Agent (General)

**Important**: You do NOT need to run `uv run run_server.py` manually. Just start your Gemini terminal agent normally. The agent will automatically spawn the MCP server process when it needs to use the tools.

For example, if using a terminal agent:
```bash
# Just start your Gemini terminal agent
# (The exact command depends on your agent)
gemini-terminal-agent
# or
aider
# or whatever your agent's command is
```

### Step 5: Verify Connection

Once inside your Gemini terminal agent:

1. **Ask Gemini**: "What MCP tools are available?"
2. **Expected Response**: Should list:
   - `get_sankey_data`
   - `get_flow_summary_stats`
   - `analyze_critical_path`
   - `adjust_sankey_canvas_size`
   - `list_workflow_stages`

**What's happening behind the scenes:**
- Gemini reads your config file
- When you ask for tools, Gemini spawns: `uv run run_server.py` as a child process
- Gemini communicates with the server via stdin/stdout pipes
- The server processes your requests and returns results
- You only see the final results in your Gemini conversation

---

## Method 2: HTTP/SSE Transport

If your Gemini client supports HTTP-based MCP connections:

### Step 1: Start the HTTP Server

```bash
cd /Users/mengtang/script/flow-viz-mcp
uv run run_server_http.py --host localhost --port 8000
```

You should see:
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

### Step 2: Configure Gemini Client for HTTP

**For HTTP-based clients, update your config:**

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

**Note**: Keep the HTTP server running in a separate terminal while using Gemini.

---

## Usage Examples

Once connected, you can ask Gemini to:

### 1. Generate Workflow Diagrams

```
"Generate a Sankey diagram for the ddmd workflow"
```

**Expected**: Gemini calls `get_sankey_data` and returns:
```
Sankey diagram saved to output/sankey.html
Full workflow visualized with X tasks
```

### 2. Get I/O Statistics

```
"Show me the I/O summary statistics for the ddmd workflow"
```

**Expected**: Gemini calls `get_flow_summary_stats` and returns structured data with:
- Total workflow I/O (volume, op_count, bandwidth)
- Total read/write breakdowns
- Per-task statistics

### 3. Analyze Critical Path

```
"Analyze the critical path for the ddmd workflow using volume as the metric"
```

**Expected**: Gemini calls `analyze_critical_path` and returns:
- Critical path nodes
- Total critical weight
- Optimization opportunities

### 4. List Workflow Stages

```
"List all stages in the ddmd workflow"
```

**Expected**: Gemini calls `list_workflow_stages` and returns:
- Total number of stages
- Tasks per stage with instance counts

### 5. Generate Subset Diagrams

```
"Generate a diagram showing only stages 1 and 2 of the ddmd workflow"
```

**Expected**: Gemini calls `get_sankey_data` with `stage_numbers=[0, 1]` (0-based indexing)

---

## Understanding Stdio MCP Communication

### What Happens When You Use Tools

1. **You ask Gemini**: "Generate a Sankey diagram for ddmd workflow"
2. **Gemini reads config**: Finds the MCP server configuration
3. **Gemini spawns process**: Automatically runs `uv run run_server.py` as a child process
4. **Communication via pipes**: 
   - Gemini sends JSON-RPC requests to server's stdin
   - Server reads from stdin, processes request
   - Server writes JSON-RPC responses to stdout
   - Gemini reads from stdout, gets the result
5. **You see the result**: Gemini tells you "Sankey diagram saved to output/sankey.html"

### Why You Can't "Connect" Manually

When you run `uv run run_server.py` manually, it:
- Starts the server process
- Waits for JSON-RPC messages on stdin
- Sends responses on stdout
- But there's no client connected to those pipes

The Gemini terminal agent acts as the client and manages these pipes automatically.

### Testing the Connection

If you want to test that the server works correctly, use the provided test client:

```bash
python run_client.py ddmd
```

This demonstrates how a client spawns and communicates with the server.

## Troubleshooting

### Issue: Gemini doesn't see the tools

**Solutions:**
1. **Check server is running**: Test manually with `uv run run_server.py`
2. **Verify config file location**: Check your Gemini client's documentation for config file location
3. **Check JSON syntax**: Ensure no trailing commas, proper quotes
4. **Verify paths**: Use absolute paths, not relative paths
5. **Check permissions**: Ensure `run_server.py` is executable: `chmod +x run_server.py`

### Issue: "Command not found: uv"

**Solutions:**
1. Install `uv`: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Or use Python directly (see Option B in Step 2)

### Issue: "Python path not found"

**Solutions:**
1. Verify virtual environment exists: `ls -la .venv/bin/python`
2. Use full path in config: `"command": "/Users/mengtang/script/flow-viz-mcp/.venv/bin/python"`
3. Ensure PATH includes `.venv/bin` in the `env` section

### Issue: Server starts but tools don't work

**Solutions:**
1. Check server logs for errors
2. Verify workflow data exists: `ls workflow_traces/`
3. Test tools manually using the Python client: `python run_client.py ddmd`

### Issue: HTTP server connection fails

**Solutions:**
1. Ensure server is running: Check `http://localhost:8000/health`
2. Check firewall settings
3. Verify port 8000 is not in use: `lsof -i :8000`
4. Try a different port: `--port 8001`

---

## Configuration File Locations

Common locations for MCP configuration:

- **Generic MCP clients**: `~/.config/mcp.json`
- **Aider**: `~/.aider/config.json`
- **Custom clients**: Check your client's documentation

---

## Next Steps

1. **Test Basic Functionality**: Start with simple requests like "List workflow stages"
2. **Generate Diagrams**: Create Sankey diagrams for your workflows
3. **Analyze Performance**: Use critical path analysis to identify bottlenecks
4. **Explore Filtering**: Try filtering by stages, tasks, or files

---

## Additional Resources

- **Main README**: [README.md](../README.md)
- **Integration Guide**: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- **Task Filtering**: [FILTERING_GUIDE.md](FILTERING_GUIDE.md)
- **Prompt Templates**: [prompt.json](prompt.json)

---

## Quick Reference

**Project Path**: `/Users/mengtang/script/flow-viz-mcp`

**Start Server (stdio)**: `uv run run_server.py`

**Start Server (HTTP)**: `uv run run_server_http.py --host localhost --port 8000`

**Test Server**: `python run_client.py ddmd`

**Available Tools**:
- `get_sankey_data` - Generate Sankey diagrams
- `get_flow_summary_stats` - I/O statistics
- `analyze_critical_path` - Critical path analysis
- `adjust_sankey_canvas_size` - Resize diagrams
- `list_workflow_stages` - List workflow structure

