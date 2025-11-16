import argparse
from src.dfl_mcp.server import DFLVisualizationMCP


def main():
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="Run the DFL Visualization MCP server.")
    parser.add_argument(
        "--workflow-name",
        default="ddmd",
        help="The name of the workflow to trace."
    )
    args = parser.parse_args()
    workflow_name = args.workflow_name

    server = DFLVisualizationMCP(workflow_name=workflow_name)
    server.run()


if __name__ == "__main__":
    main()
