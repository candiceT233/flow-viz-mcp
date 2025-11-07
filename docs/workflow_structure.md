# Workflow Traces Directory Structure

This document describes the required directory structure for adding workflow traces to the DFL Visualization MCP Server.

## Directory Structure

Workflows must be organized in the `workflow_traces/` directory following this structure:

```
workflow_traces/
??? <workflow_name>/
    ??? <variant_name>_schema.json        # Workflow schema (required)
    ??? <variant_name>/                   # Trace files directory (required)
        ??? *.BlockTrace.json              # Block-level I/O traces
        ??? *.DatalifeTrace.json           # Application-level I/O traces
```

## Naming Conventions

- **`<workflow_name>`**: Top-level workflow identifier (e.g., `ddmd`, `montage`)
- **`<variant_name>`**: Specific workflow variant/configuration (e.g., `ddmd_4n_pfs_large`, `montage_2n_16blue`)
- Schema file **must** end with `_schema.json`
- Trace directory name **should** match the schema filename (without `_schema.json`)

## Examples

### Example 1: DDMD Workflow
```
workflow_traces/ddmd/
??? ddmd_4n_pfs_large_schema.json
??? ddmd_4n_pfs_large/
    ??? file1.BlockTrace.json
    ??? file1.DatalifeTrace.json
    ??? file2.BlockTrace.json
    ??? file2.DatalifeTrace.json
```

### Example 2: Montage Workflow
```
workflow_traces/montage/
??? montage_2n_16blue_schema.json
??? montage_2n_16blue/
    ??? task1.BlockTrace.json
    ??? task1.DatalifeTrace.json
    ??? task2.BlockTrace.json
    ??? task2.DatalifeTrace.json
```

## Auto-Detection Logic

The server automatically detects workflow files using the following strategy:

1. **Schema Detection**: 
   - Searches for any file ending with `_schema.json` in the workflow directory
   - Example: Finds `ddmd_4n_pfs_large_schema.json`

2. **Trace Directory Detection** (two-step approach):
   - **Step 1 (Primary)**: Infers trace directory from schema filename
     - Schema: `ddmd_4n_pfs_large_schema.json` ? Trace directory: `ddmd_4n_pfs_large/`
     - Schema: `montage_2n_16blue_schema.json` ? Trace directory: `montage_2n_16blue/`
   
   - **Step 2 (Fallback)**: If Step 1 fails, searches for any subdirectory containing trace JSON files
     - Looks for files ending with `.json`
     - Checks if filenames contain `BlockTrace` or `DatalifeTrace`
     - Uses the first matching directory found

This flexible approach supports various naming conventions without requiring manual configuration.

## Adding New Workflows

To add a new workflow:

1. Create a directory under `workflow_traces/` with your workflow name:
   ```bash
   mkdir -p workflow_traces/myworkflow
   ```

2. Add your schema file (must end with `_schema.json`):
   ```bash
   # Example: myworkflow_config_v1_schema.json
   cp myschema.json workflow_traces/myworkflow/myworkflow_config_v1_schema.json
   ```

3. Create a trace directory matching your schema filename (without `_schema.json`):
   ```bash
   mkdir workflow_traces/myworkflow/myworkflow_config_v1
   ```

4. Copy your trace files into the trace directory:
   ```bash
   cp *.BlockTrace.json workflow_traces/myworkflow/myworkflow_config_v1/
   cp *.DatalifeTrace.json workflow_traces/myworkflow/myworkflow_config_v1/
   ```

5. Restart the server or refresh workflow list - your workflow will be automatically discovered!

## Validation

The server validates workflows on load:

- ? Schema file must exist and end with `_schema.json`
- ? Trace directory must exist and contain trace files
- ? At least one `*.BlockTrace.json` or `*.DatalifeTrace.json` file must be present
- ? If validation fails, a descriptive error message is shown

## Troubleshooting

**Problem**: Workflow not appearing in available workflows list

**Solutions**:
1. Check directory exists: `ls workflow_traces/`
2. Check for schema file: `ls workflow_traces/myworkflow/*_schema.json`
3. Check for trace directory: `ls workflow_traces/myworkflow/*/`
4. Check for trace files: `ls workflow_traces/myworkflow/*/*.json | grep -E "BlockTrace|DatalifeTrace"`

**Problem**: Error loading workflow

**Solutions**:
1. Verify schema file is valid JSON: `python -m json.tool workflow_traces/myworkflow/*_schema.json`
2. Verify trace files are valid JSON
3. Check file permissions (must be readable)
4. Check trace directory name matches schema name (without `_schema.json`)

## Future Enhancements

Planned improvements for workflow management:

- MCP tool to upload/add new workflows via API
- Workflow validation tool
- Automatic workflow refresh without server restart
- Multi-version support for same workflow
- Workflow metadata and descriptions
