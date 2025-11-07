# src/dfl_mcp/uri_utils.py

def parse_uri(uri: str):
    """
    Parses a DFL URI.
    e.g., dfl://my_workflow/task/T1 or dfl://my_workflow/data/file.h5
    """
    parts = uri.replace("dfl://", "").split("/")
    if len(parts) != 3:
        raise ValueError(f"Invalid DFL URI: {uri}")
    
    workflow_name, component_type, component_id = parts
    return workflow_name, component_type, component_id

def create_uri(workflow_name: str, component_type: str, component_id: str) -> str:
    """
    Creates a DFL URI.
    """
    return f"dfl://{workflow_name}/{component_type}/{component_id}"
