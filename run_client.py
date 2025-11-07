import asyncio
from fastmcp.client import Client
from fastmcp.client.transports import PythonStdioTransport
import json
import argparse
import os
import sys

async def main():
    """
    Main function to run the MCP client and test the tools.
    """
    parser = argparse.ArgumentParser(description="Run the MCP client.")
    parser.add_argument(
        "workflow_name",
        nargs="?",
        default="ddmd",
        help="The name of the workflow to trace. Defaults to 'ddmd'.",
    )
    args = parser.parse_args()
    workflow_name = args.workflow_name

    # Check if the workflow exists
    trace_dir = "workflow_traces"
    available_workflows = [
        d
        for d in os.listdir(trace_dir)
        if os.path.isdir(os.path.join(trace_dir, d))
    ]
    if workflow_name not in available_workflows:
        print(f"Workflow '{workflow_name}' not found in '{trace_dir}'.")
        print("Available workflows:")
        for d in available_workflows:
            print(f"- {d}")
        sys.exit(1)

    print(f"Using workflow: {workflow_name}")

    transport = PythonStdioTransport(script_path="run_server.py")
    async with Client(transport) as client:
        # Test get_sankey_data for the full workflow
        print("--- Testing get_sankey_data for the full workflow ---")
        sankey_data = await client.call_tool("get_sankey_data", {
            "workflow_name": workflow_name,
            "output_file": "sankey_full_workflow.html"})
        print(sankey_data)

        # Test get_flow_summary_stats
        print("\n--- Testing get_flow_summary_stats ---")
        summary_stats = await client.call_tool("get_flow_summary_stats", {
            "workflow_name": workflow_name,
            "selected_tasks": ["training_0"], 
            "output_file": "summary_test.txt"})
        print(summary_stats)

if __name__ == "__main__":
    asyncio.run(main())