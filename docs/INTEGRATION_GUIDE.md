# MCP Integration Guide

This guide provides detailed instructions for integrating the DFL Visualization MCP Server with various MCP-compatible clients, including Cursor IDE and terminal agents like Gemini.

## Table of Contents

- [Cursor IDE Integration](#cursor-ide-integration)
- [Gemini Terminal Agent Integration](#gemini-terminal-agent-integration)
- [Common Configuration](#common-configuration)

---

## Cursor IDE Integration

To use the DFL Visualization tools with Cursor IDE's AI agent:

**Quick Reference:**
- **Required Version:** Cursor 0.40.0 or later (MCP support)
- **Config File:** `~/Library/Application Support/Cursor/User/globalStorage/mcp.json` (macOS) or similar location
- **Update Method:** **Cursor** → **Check for Updates**
- **Note:** If "Model Context Protocol" doesn't appear in Settings, you can still configure MCP manually via the config file

### Step 1: Check Cursor Version and Update

**Check Your Current Version:**
- Go to: **Cursor** → **About Cursor** (macOS) or **Help** → **About** (Windows/Linux)
- Note your version number

**Update Cursor IDE:**

**Option A: Automatic Update (Recommended)**
1. Go to: **Cursor** → **Check for Updates** (macOS) or **Help** → **Check for Updates** (Windows/Linux)
2. If an update is available, Cursor will prompt you to download and install it
3. Restart Cursor after the update completes

**Option B: Manual Update**
1. **macOS:**
   - Download the latest version from [cursor.sh](https://cursor.sh)
   - Or use Homebrew: `brew upgrade --cask cursor`
   
2. **Windows:**
   - Download the latest installer from [cursor.sh](https://cursor.sh)
   - Run the installer (it will update your existing installation)
   
3. **Linux:**
   - Download the latest `.deb` or `.rpm` package from [cursor.sh](https://cursor.sh)
   - Install using your package manager:
     ```bash
     # For .deb (Debian/Ubuntu)
     sudo dpkg -i cursor_*.deb
     
     # For .rpm (Fedora/RHEL)
     sudo rpm -i cursor_*.rpm
     ```

**MCP Support Requirements:**
- MCP (Model Context Protocol) support was added in Cursor version 0.40.0 and later
- If you're on an older version, you must update to use MCP features
- You can still configure MCP manually via config files even if the UI doesn't show the option (see Step 2)

### Step 2: Configure the MCP Server

**Note:** Even if the Settings UI doesn't show "Model Context Protocol", you can configure MCP directly by editing the configuration file. This method works for all Cursor versions that support MCP.

**File to Edit:** The MCP configuration file location depends on your Cursor version:

**For Cursor 0.40.0+ (Recommended locations):**
- **macOS:** `~/Library/Application Support/Cursor/User/globalStorage/mcp.json`
- **Linux:** `~/.config/Cursor/User/globalStorage/mcp.json`
- **Windows:** `%APPDATA%\Cursor\User\globalStorage\mcp.json`

**Alternative locations (if above doesn't work):**
- **macOS/Linux:** `~/.cursor/mcp.json`
- **Windows:** `%APPDATA%\Cursor\mcp.json`

**How to Find the Config File:**
1. Open Cursor
2. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux) to open Command Palette
3. Type: "Preferences: Open User Settings (JSON)"
4. This opens your settings file - note the directory it's in
5. The MCP config should be in the same directory or in `globalStorage/mcp.json`

**Create the Config File:**
If the file doesn't exist, create it:
```bash
# macOS/Linux
mkdir -p ~/Library/Application\ Support/Cursor/User/globalStorage
touch ~/Library/Application\ Support/Cursor/User/globalStorage/mcp.json

# Or alternative location
mkdir -p ~/.cursor
touch ~/.cursor/mcp.json

# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path "$env:APPDATA\Cursor\User\globalStorage"
New-Item -ItemType File -Force -Path "$env:APPDATA\Cursor\User\globalStorage\mcp.json"
```

### Step 3: Add the MCP Server Configuration

Open or create the `mcp.json` file and add the following configuration:

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

   **Example with `uv run` (Recommended):**
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
   
   **Alternative using Python directly:**
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

### Step 4: Restart Cursor IDE

Close and reopen Cursor for the changes to take effect.

### Step 5: Verify the Integration

- Open a chat with Cursor's AI agent (Cmd+L or Ctrl+L)
- Ask: "What MCP tools are available?"
- **Expected Output:** The agent should list `get_sankey_data`, `get_flow_summary_stats`, `analyze_critical_path`, and `adjust_sankey_canvas_size`

### Step 6: Expected Output When Using Tools

**Example Request:**
- Ask: "Generate a Sankey diagram for the ddmd workflow"

**Expected Response:**
- The agent will call `get_sankey_data` and respond with: "Sankey diagram saved to output/sankey.html"
- You can then open the HTML file in your browser to view the visualization

**File Created:**
- Location: `<path-to-your-project-directory>/output/sankey.html`
- Format: Interactive HTML file with Plotly Sankey diagram

### Troubleshooting

- **"Model Context Protocol" option not in Settings**: 
  - Your Cursor version may be too old. Check your version: **Cursor** → **About Cursor**
  - MCP support requires Cursor 0.40.0 or later
  - Update Cursor using **Cursor** → **Check for Updates** (see Step 1)
  - **Note:** You can still configure MCP manually via the config file even if the UI option isn't available
  
- **Tools don't appear**: 
  - Check the Cursor output panel (View → Output) for MCP connection errors
  - Verify your Cursor version is 0.40.0 or later
  - Ensure the `mcp.json` file is in the correct location (see Step 2)
  - Check that the JSON syntax is valid (no trailing commas, proper quotes)
  
- **Python path issues**: 
  - Verify the Python path is correct: `which python` (should point to your virtual environment)
  - On macOS/Linux, you may need to use the full path: `"command": "/path/to/.venv/bin/python"`
  
- **Virtual environment**: 
  - Ensure the virtual environment is created: `cd <project-dir> && uv venv`
  - Ensure dependencies are installed: `pip install -e .`
  - The PATH in config should include `.venv/bin`
  
- **File permissions**: 
  - Check that `run_server.py` is executable: `chmod +x run_server.py`
  - Ensure the config file is readable: `chmod 644 mcp.json`
  
- **Path errors**: 
  - Always use absolute paths in configuration, not relative paths
  - Verify paths exist: `ls -la <path-to-your-project-directory>/run_server.py`
  
- **Config file not found**: 
  - Use Command Palette (Cmd+Shift+P) → "Preferences: Open User Settings (JSON)" to find the settings directory
  - Create the `globalStorage` directory if it doesn't exist
  - Create the `mcp.json` file manually if needed (see Step 2)
  
- **Cursor doesn't recognize MCP config**: 
  - Ensure you're using the correct file location (try both `globalStorage/mcp.json` and `~/.cursor/mcp.json`)
  - Restart Cursor completely (quit and reopen, don't just reload)
  - Check Cursor's developer console for errors: **Help** → **Toggle Developer Tools**

---

## Gemini Terminal Agent Integration

To use the DFL Visualization tools with Google's Gemini terminal agent (via `aider` or similar MCP-compatible terminal tools):

### Step 1: Install Required Tools

If not already installed, install your terminal agent:

```bash
# For aider (example MCP-compatible terminal agent)
pip install aider-chat
```

**Note:** The exact installation command depends on your terminal agent. Check your agent's documentation for installation instructions.

### Step 2: Configure the MCP Server

**File to Edit:** `~/.aider/config.json` (or your terminal agent's config file)

**Location in System:**
- **macOS/Linux:** `~/.aider/config.json`
- **Windows:** `%USERPROFILE%\.aider\config.json`

**Note:** The exact location depends on your terminal agent. For `aider`, create the config file if it doesn't exist.

### Step 3: Add the MCP Server Configuration

Open or create the configuration file and add:

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

**Example with `uv run`:**
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

### Step 4: Alternative - HTTP/SSE Connection (Optional)

If your terminal agent supports HTTP connections, you can run the MCP server over HTTP instead of stdio:

**1. Start the HTTP server using `uv run` (Recommended):**
```bash
cd <path-to-your-project-directory>
uv run run_server_http.py --host localhost --port 8000
```

**Or using Python directly:**
```bash
cd <path-to-your-project-directory>
source .venv/bin/activate
python run_server_http.py --host localhost --port 8000
```

**Note:** Using `uv run` automatically manages dependencies. If using Python directly, ensure all dependencies are installed: `pip install -e .`

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

**3. Configure your terminal agent to use HTTP:**

For Gemini terminal agent, update `.gemini/settings.json`:

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

**Note:** Most MCP clients use stdio by default. HTTP/SSE support depends on your specific terminal agent. If HTTP doesn't work, use the stdio configuration (Step 3) instead.

### Step 5: Alternative - Environment Variable Configuration

Some terminal agents allow MCP server configuration via environment variables. Set:

```bash
export MCP_SERVERS='{"flow-viz-mcp": {"command": "python", "args": ["<path-to-your-project-directory>/run_server.py"], "cwd": "<path-to-your-project-directory>", "env": {"PATH": "<path-to-your-project-directory>/.venv/bin:${PATH}"}}}'
```

Add this to your shell configuration file (`~/.zshrc`, `~/.bashrc`, etc.) to make it persistent.

### Step 6: Start Your Terminal Agent

```bash
# Example with aider
aider
```

### Step 7: Verify the Integration

- In the terminal agent, ask: "What tools are available?"
- Or try: "List available MCP tools"
- **Expected Output:** The agent should list the DFL Visualization tools (`get_sankey_data`, `get_flow_summary_stats`, `analyze_critical_path`, `adjust_sankey_canvas_size`)

### Step 7: Expected Output When Using Tools

**Example Request:**
```
Generate a Sankey diagram for the ddmd workflow
```

**Expected Response:**
```
I'll generate a Sankey diagram for the ddmd workflow.
[Calling get_sankey_data tool...]
Sankey diagram saved to output/sankey.html
Full workflow visualized with 12 tasks
```

**File Created:**
- Location: `<path-to-your-project-directory>/output/sankey.html`
- Format: Interactive HTML file with Plotly Sankey diagram
- **To View:** Open the HTML file in a web browser

### Step 8: Example Terminal Session

```bash
$ aider
> Generate a Sankey diagram for the ddmd workflow with critical path highlighted

[Agent calls get_sankey_data tool]
Sankey diagram generated successfully!
File: output/sankey.html

> Analyze the critical path using volume as the metric

[Agent calls analyze_critical_path tool]
Critical path analysis complete:
- Total critical weight: 1,234,567 bytes
- Critical path nodes: ['task_0', 'file_A.h5', 'task_1', ...]
- Optimization opportunities: [...]
```

### Step 9: Testing the Server Directly

Before using with the terminal agent, test the server manually:

**Using `uv run` (Recommended):**
```bash
cd <path-to-your-project-directory>
uv run run_server.py
```

**Or using Python directly:**
```bash
cd <path-to-your-project-directory>
source .venv/bin/activate
python run_server.py
```

**Expected Output:**
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

============================================================
```

Press Ctrl+C to stop the server.

### Troubleshooting

- **Tools not appearing**: Check that your terminal agent supports MCP protocol
- **Connection errors**: Verify Python path: `which python` should show your virtual environment
- **Permission errors**: Ensure `run_server.py` is executable: `chmod +x run_server.py`
- **Path issues**: Use absolute paths in configuration, not relative paths
- **Virtual environment**: Ensure the virtual environment is created and activated, or the PATH includes `.venv/bin`
- **Configuration format**: Verify JSON syntax is correct (no trailing commas, proper quotes)

---

## Common Configuration

### Required Information

For all integrations, you'll need:

1. **Project Directory Path**: The absolute path to your `flow-viz-mcp` directory
   - Example (macOS): `/Users/mengtang/script/flow-viz-mcp`
   - Example (Linux): `/home/username/flow-viz-mcp`
   - Example (Windows): `C:\Users\username\flow-viz-mcp`

2. **Python Executable**: Path to Python in your virtual environment
   - Usually: `<project-directory>/.venv/bin/python`
   - Verify with: `which python` (macOS/Linux) or `where python` (Windows)

3. **Virtual Environment**: Ensure your virtual environment is set up
   ```bash
   cd <path-to-your-project-directory>
   uv venv  # or python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -e .
   ```

### Configuration Template

Use this template for any MCP client:

```json
{
  "mcpServers": {
    "flow-viz-mcp": {
      "command": "python",
      "args": ["<absolute-path-to-project>/run_server.py"],
      "cwd": "<absolute-path-to-project>",
      "env": {
        "PATH": "<absolute-path-to-project>/.venv/bin:${PATH}"
      }
    }
  }
}
```

**Key Points:**
- Use absolute paths, not relative paths
- Include the virtual environment's `bin` directory in PATH
- Ensure `run_server.py` is executable
- The `cwd` should be the project root directory

### Verification Checklist

After configuration, verify:

- [ ] Configuration file exists and has correct JSON syntax
- [ ] All paths are absolute (not relative)
- [ ] Virtual environment is set up and activated
- [ ] Python executable is accessible: `which python` shows `.venv/bin/python`
- [ ] Server starts manually: `python run_server.py` shows startup message
- [ ] Tools appear in the client: Ask "What MCP tools are available?"
- [ ] Tools work: Try generating a Sankey diagram

### Getting Help

If you encounter issues:

1. **Check Server Logs**: Look for error messages in the client's output panel
2. **Test Server Manually**: Run `python run_server.py` directly to see if it starts
3. **Verify Paths**: Use `pwd` to get your current directory and verify all paths
4. **Check Permissions**: Ensure files are readable and executable
5. **Review Configuration**: Double-check JSON syntax and path values

For more information, see:
- [README.md](../README.md) - Main project documentation
- [Task Filtering Guide](FILTERING_GUIDE.md) - How to filter workflows
- [Workflow Structure Guide](workflow_structure.md) - Adding new workflows

