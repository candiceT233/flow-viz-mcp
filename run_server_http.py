#!/usr/bin/env python3
"""
HTTP/SSE Server for DFL Visualization MCP Server

This script runs the MCP server over HTTP using Server-Sent Events (SSE),
which allows clients to connect via HTTP instead of stdio.
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import uvicorn

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.dfl_mcp.server import DFLVisualizationMCP


class HTTPMCPServer:
    """
    HTTP wrapper for the MCP server that uses Server-Sent Events (SSE)
    for bidirectional communication.
    """
    
    def __init__(self, workflow_name: Optional[str] = None, host: str = "localhost", port: int = 8000):
        self.app = FastAPI(title="DFL Visualization MCP Server")
        self.mcp_server = DFLVisualizationMCP(workflow_name=workflow_name)
        self.host = host
        self.port = port
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup HTTP routes for MCP communication."""
        
        @self.app.get("/")
        async def root():
            return {
                "name": "DFL Visualization MCP Server",
                "version": "0.1.0",
                "protocol": "MCP over HTTP/SSE",
                "endpoints": {
                    "sse": "/sse",
                    "health": "/health",
                    "tools": "/tools"
                }
            }
        
        @self.app.get("/health")
        async def health():
            return {"status": "healthy", "workflows": self.mcp_server.available_workflows}
        
        @self.app.get("/tools")
        async def list_tools():
            """List available MCP tools."""
            # Get tools from the MCP server
            tools = []
            for tool_name in ["get_sankey_data", "get_flow_summary_stats", "analyze_critical_path", "adjust_sankey_canvas_size"]:
                tools.append({
                    "name": tool_name,
                    "description": f"MCP tool: {tool_name}"
                })
            return {"tools": tools}
        
        @self.app.post("/mcp/call")
        async def call_tool(request: Request):
            """Call an MCP tool via HTTP POST."""
            try:
                body = await request.json()
                tool_name = body.get("tool")
                arguments = body.get("arguments", {})
                
                if not tool_name:
                    return {"error": "Missing 'tool' parameter"}, 400
                
                # Call the tool method
                if hasattr(self.mcp_server, tool_name):
                    method = getattr(self.mcp_server, tool_name)
                    result = method(**arguments)
                    return {"result": result, "tool": tool_name}
                else:
                    return {"error": f"Tool '{tool_name}' not found"}, 404
                    
            except Exception as e:
                return {"error": str(e), "type": type(e).__name__}, 500
        
        @self.app.get("/sse")
        async def sse_endpoint(request: Request):
            """Server-Sent Events endpoint for MCP communication."""
            async def event_generator():
                # Send initial connection message
                yield {
                    "event": "connected",
                    "data": json.dumps({
                        "server": "DFL Visualization MCP Server",
                        "workflows": self.mcp_server.available_workflows
                    })
                }
                
                # Keep connection alive and handle requests
                while True:
                    # Check if client disconnected
                    if await request.is_disconnected():
                        break
                    
                    # For now, we'll use POST /mcp/call for actual tool calls
                    # SSE is mainly for server-to-client messages
                    await asyncio.sleep(1)
                    yield {
                        "event": "ping",
                        "data": json.dumps({"status": "alive"})
                    }
            
            return EventSourceResponse(event_generator())
    
    def run(self):
        """Run the HTTP server."""
        print(f"\n{'='*60}")
        print("DFL Visualization MCP Server (HTTP/SSE)")
        print(f"{'='*60}")
        print(f"\nServer starting on http://{self.host}:{self.port}")
        print(f"\nAvailable Endpoints:")
        print(f"  - Health: http://{self.host}:{self.port}/health")
        print(f"  - Tools: http://{self.host}:{self.port}/tools")
        print(f"  - MCP Call: http://{self.host}:{self.port}/mcp/call (POST)")
        print(f"  - SSE: http://{self.host}:{self.port}/sse")
        print(f"\nAvailable Workflows: {', '.join(self.mcp_server.available_workflows)}")
        print(f"{'='*60}\n")
        
        uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")


def main():
    parser = argparse.ArgumentParser(description="Run the DFL Visualization MCP server over HTTP/SSE.")
    parser.add_argument(
        "--workflow-name",
        default=None,
        help="The name of the workflow to trace (optional)."
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host to bind to (default: localhost)."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)."
    )
    args = parser.parse_args()
    
    server = HTTPMCPServer(
        workflow_name=args.workflow_name,
        host=args.host,
        port=args.port
    )
    server.run()


if __name__ == "__main__":
    main()

