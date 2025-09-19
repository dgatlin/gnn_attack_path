"""
MCP (Model Context Protocol) Client for AI Agent Communication

This module provides MCP client implementation that allows AI agents
to communicate with the MCP server and access graph operations.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

from mcp.client.session import ClientSession
from mcp import stdio_client
from mcp.types import CallToolRequest, CallToolResult, ListToolsRequest, ListToolsResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MCPClientConfig:
    """Configuration for MCP Client"""
    server_command: List[str] = None
    server_args: List[str] = None


class GNNAttackPathMCPClient:
    """MCP Client for GNN Attack Path Analysis"""
    
    def __init__(self, config: MCPClientConfig):
        self.config = config
        self.client = None
        self.available_tools = []
    
    async def connect(self):
        """Connect to the MCP server"""
        try:
            if self.config.server_command:
                self.client = await stdio_client(
                    self.config.server_command,
                    self.config.server_args or []
                )
            else:
                # Default to running the server as a subprocess
                self.client = await stdio_client(
                    ["python", "-m", "agent.mcp_server"],
                    []
                )
            
            # Initialize the client
            await self.client.initialize()
            
            # Get available tools
            await self._load_available_tools()
            
            logger.info(f"Connected to MCP server with {len(self.available_tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {str(e)}")
            raise
    
    async def _load_available_tools(self):
        """Load available tools from the server"""
        try:
            request = ListToolsRequest()
            response = await self.client.list_tools(request)
            self.available_tools = response.tools
            logger.info(f"Loaded {len(self.available_tools)} tools from server")
        except Exception as e:
            logger.error(f"Failed to load tools: {str(e)}")
            raise
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        try:
            request = CallToolRequest(
                name=tool_name,
                arguments=arguments
            )
            
            response = await self.client.call_tool(request)
            
            if response.isError:
                error_text = ""
                for content in response.content:
                    if hasattr(content, 'text'):
                        error_text += content.text
                raise RuntimeError(f"Tool call failed: {error_text}")
            
            # Extract text content from response
            result_text = ""
            for content in response.content:
                if hasattr(content, 'text'):
                    result_text += content.text
            
            # Try to parse as JSON, fallback to text
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                return {"text": result_text}
                
        except Exception as e:
            logger.error(f"Tool call failed for {tool_name}: {str(e)}")
            raise
    
    async def query_graph(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a Cypher query against the graph database"""
        return await self.call_tool("query_graph", {
            "query": query,
            "parameters": parameters or {}
        })
    
    async def score_attack_paths(self, source_node: str, target_node: str, max_depth: int = 5) -> Dict[str, Any]:
        """Score attack paths between two nodes"""
        return await self.call_tool("score_attack_paths", {
            "source_node": source_node,
            "target_node": target_node,
            "max_depth": max_depth
        })
    
    async def get_top_risky_paths(self, limit: int = 10, min_score: float = 0.5) -> Dict[str, Any]:
        """Get top K most risky attack paths"""
        return await self.call_tool("get_top_risky_paths", {
            "limit": limit,
            "min_score": min_score
        })
    
    async def analyze_asset_risk(self, asset_id: str, include_neighbors: bool = True) -> Dict[str, Any]:
        """Analyze risk for a specific asset"""
        return await self.call_tool("analyze_asset_risk", {
            "asset_id": asset_id,
            "include_neighbors": include_neighbors
        })
    
    async def propose_remediation(self, path_id: str, remediation_type: str, dry_run: bool = True) -> Dict[str, Any]:
        """Propose remediation actions for a security issue"""
        return await self.call_tool("propose_remediation", {
            "path_id": path_id,
            "remediation_type": remediation_type,
            "dry_run": dry_run
        })
    
    async def get_graph_statistics(self, include_risk_metrics: bool = True) -> Dict[str, Any]:
        """Get overall graph statistics"""
        return await self.call_tool("get_graph_statistics", {
            "include_risk_metrics": include_risk_metrics
        })
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Disconnected from MCP server")


class MCPToolWrapper:
    """Wrapper class for easy tool access in AI agents"""
    
    def __init__(self, client: GNNAttackPathMCPClient):
        self.client = client
    
    async def find_attack_paths(self, source: str, target: str) -> List[Dict[str, Any]]:
        """Find and score attack paths between source and target"""
        result = await self.client.score_attack_paths(source, target)
        return result.get("scored_paths", [])
    
    async def get_risky_assets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most risky assets in the graph"""
        result = await self.client.get_top_risky_paths(limit=limit)
        return result.get("risky_paths", [])
    
    async def assess_asset(self, asset_id: str) -> Dict[str, Any]:
        """Assess risk for a specific asset"""
        return await self.client.analyze_asset_risk(asset_id)
    
    async def suggest_fixes(self, path_id: str, issue_type: str) -> Dict[str, Any]:
        """Suggest remediation fixes for a security issue"""
        return await self.client.propose_remediation(path_id, issue_type)
    
    async def get_graph_overview(self) -> Dict[str, Any]:
        """Get high-level overview of the graph"""
        return await self.client.get_graph_statistics()


# Example usage and testing
async def main():
    """Example usage of MCP client"""
    config = MCPClientConfig()
    client = GNNAttackPathMCPClient(config)
    
    try:
        await client.connect()
        
        # Example: Get graph statistics
        stats = await client.get_graph_statistics()
        print("Graph Statistics:")
        print(json.dumps(stats, indent=2))
        
        # Example: Find attack paths
        paths = await client.score_attack_paths("server1", "database1")
        print("\nAttack Paths:")
        print(json.dumps(paths, indent=2))
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
