"""
MCP (Model Context Protocol) Server for GNN Attack Path Analysis

This module provides MCP server implementation that exposes graph operations
as tools for AI agents to interact with the cybersecurity graph database.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from pydantic import BaseModel

from graph.connection import Neo4jConnection
from scorer.service import AttackPathScoringService
from agent.remediator import RemediationAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GraphQueryRequest(BaseModel):
    """Request model for graph queries"""
    query: str
    parameters: Optional[Dict[str, Any]] = None


class PathScoringRequest(BaseModel):
    """Request model for path scoring"""
    source_node: str
    target_node: str
    max_depth: Optional[int] = 5


class RemediationRequest(BaseModel):
    """Request model for remediation actions"""
    path_id: str
    remediation_type: str
    dry_run: bool = True


@dataclass
class MCPServerConfig:
    """Configuration for MCP Server"""
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    scoring_model_path: Optional[str] = None


class GNNAttackPathMCPServer:
    """MCP Server for GNN Attack Path Analysis Tools"""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.server = Server("gnn-attack-path-server")
        self.neo4j_conn = None
        self.scoring_service = None
        self.remediation_service = None
        
        # Register tool handlers
        self._register_tools()
    
    def _register_tools(self):
        """Register all available MCP tools"""
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List all available tools"""
            tools = [
                Tool(
                    name="query_graph",
                    description="Execute Cypher queries against the Neo4j graph database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Cypher query to execute"
                            },
                            "parameters": {
                                "type": "object",
                                "description": "Query parameters",
                                "additionalProperties": True
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="score_attack_paths",
                    description="Score attack paths between source and target nodes using GNN models",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source_node": {
                                "type": "string",
                                "description": "Source node identifier"
                            },
                            "target_node": {
                                "type": "string",
                                "description": "Target node identifier"
                            },
                            "max_depth": {
                                "type": "integer",
                                "description": "Maximum path depth to explore",
                                "default": 5
                            }
                        },
                        "required": ["source_node", "target_node"]
                    }
                ),
                Tool(
                    name="get_top_risky_paths",
                    description="Get top K most risky attack paths in the graph",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Number of top paths to return",
                                "default": 10
                            },
                            "min_score": {
                                "type": "number",
                                "description": "Minimum risk score threshold",
                                "default": 0.5
                            }
                        }
                    }
                ),
                Tool(
                    name="analyze_asset_risk",
                    description="Analyze risk score and vulnerabilities for a specific asset",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "asset_id": {
                                "type": "string",
                                "description": "Asset identifier to analyze"
                            },
                            "include_neighbors": {
                                "type": "boolean",
                                "description": "Include neighboring assets in analysis",
                                "default": True
                            }
                        },
                        "required": ["asset_id"]
                    }
                ),
                Tool(
                    name="propose_remediation",
                    description="Propose remediation actions for identified security issues",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path_id": {
                                "type": "string",
                                "description": "Attack path identifier"
                            },
                            "remediation_type": {
                                "type": "string",
                                "enum": ["patch", "isolate", "monitor", "access_control"],
                                "description": "Type of remediation to propose"
                            },
                            "dry_run": {
                                "type": "boolean",
                                "description": "Whether to simulate the remediation",
                                "default": True
                            }
                        },
                        "required": ["path_id", "remediation_type"]
                    }
                ),
                Tool(
                    name="get_graph_statistics",
                    description="Get overall statistics about the cybersecurity graph",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_risk_metrics": {
                                "type": "boolean",
                                "description": "Include risk-related statistics",
                                "default": True
                            }
                        }
                    }
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            try:
                if name == "query_graph":
                    return await self._handle_query_graph(arguments)
                elif name == "score_attack_paths":
                    return await self._handle_score_attack_paths(arguments)
                elif name == "get_top_risky_paths":
                    return await self._handle_get_top_risky_paths(arguments)
                elif name == "analyze_asset_risk":
                    return await self._handle_analyze_asset_risk(arguments)
                elif name == "propose_remediation":
                    return await self._handle_propose_remediation(arguments)
                elif name == "get_graph_statistics":
                    return await self._handle_get_graph_statistics(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error executing tool {name}: {str(e)}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )
    
    async def _ensure_connections(self):
        """Ensure database and service connections are established"""
        if self.neo4j_conn is None:
            self.neo4j_conn = Neo4jConnection(
                uri=self.config.neo4j_uri,
                user=self.config.neo4j_user,
                password=self.config.neo4j_password
            )
            await self.neo4j_conn.connect()
        
        if self.scoring_service is None:
            self.scoring_service = AttackPathScoringService()
            await self.scoring_service.initialize()
        
        if self.remediation_service is None:
            self.remediation_service = RemediationAgent()
    
    async def _handle_query_graph(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle graph query tool calls"""
        await self._ensure_connections()
        
        query = arguments.get("query")
        parameters = arguments.get("parameters", {})
        
        if not query:
            raise ValueError("Query is required")
        
        try:
            results = await self.neo4j_conn.execute_query(query, parameters)
            
            # Format results for AI consumption
            formatted_results = {
                "query": query,
                "parameters": parameters,
                "result_count": len(results),
                "results": results[:100]  # Limit to first 100 results
            }
            
            return CallToolResult(
                content=[TextContent(
                    type="text", 
                    text=json.dumps(formatted_results, indent=2, default=str)
                )]
            )
        except Exception as e:
            raise Exception(f"Graph query failed: {str(e)}")
    
    async def _handle_score_attack_paths(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle attack path scoring tool calls"""
        await self._ensure_connections()
        
        source_node = arguments.get("source_node")
        target_node = arguments.get("target_node")
        max_depth = arguments.get("max_depth", 5)
        
        if not source_node or not target_node:
            raise ValueError("Both source_node and target_node are required")
        
        try:
            # Find paths between nodes
            path_query = """
            MATCH path = (source)-[*1..{max_depth}]->(target)
            WHERE source.id = $source_id AND target.id = $target_id
            RETURN path, length(path) as path_length
            ORDER BY path_length
            LIMIT 10
            """
            
            paths = await self.neo4j_conn.execute_query(path_query, {
                "source_id": source_node,
                "target_id": target_node,
                "max_depth": max_depth
            })
            
            # Score each path
            scored_paths = []
            for path_data in paths:
                path = path_data["path"]
                path_length = path_data["path_length"]
                
                # Score using GNN model
                score = await self.scoring_service.score_path(path)
                
                scored_paths.append({
                    "path": [node["id"] for node in path.nodes],
                    "length": path_length,
                    "risk_score": score,
                    "explanation": f"Path with {path_length} hops, risk score: {score:.3f}"
                })
            
            # Sort by risk score
            scored_paths.sort(key=lambda x: x["risk_score"], reverse=True)
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps({
                        "source_node": source_node,
                        "target_node": target_node,
                        "paths_found": len(scored_paths),
                        "scored_paths": scored_paths
                    }, indent=2)
                )]
            )
        except Exception as e:
            raise Exception(f"Path scoring failed: {str(e)}")
    
    async def _handle_get_top_risky_paths(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle top risky paths tool calls"""
        await self._ensure_connections()
        
        limit = arguments.get("limit", 10)
        min_score = arguments.get("min_score", 0.5)
        
        try:
            # Get top risky paths using scoring service
            risky_paths = await self.scoring_service.get_top_risky_paths(
                limit=limit,
                min_score=min_score
            )
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps({
                        "total_paths": len(risky_paths),
                        "min_score_threshold": min_score,
                        "risky_paths": risky_paths
                    }, indent=2, default=str)
                )]
            )
        except Exception as e:
            raise Exception(f"Failed to get risky paths: {str(e)}")
    
    async def _handle_analyze_asset_risk(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle asset risk analysis tool calls"""
        await self._ensure_connections()
        
        asset_id = arguments.get("asset_id")
        include_neighbors = arguments.get("include_neighbors", True)
        
        if not asset_id:
            raise ValueError("asset_id is required")
        
        try:
            # Get asset details
            asset_query = """
            MATCH (asset:Asset {id: $asset_id})
            OPTIONAL MATCH (asset)-[r]-(related)
            RETURN asset, collect(DISTINCT {node: related, relationship: type(r)}) as relationships
            """
            
            asset_data = await self.neo4j_conn.execute_query(asset_query, {"asset_id": asset_id})
            
            if not asset_data:
                raise ValueError(f"Asset {asset_id} not found")
            
            asset_info = asset_data[0]
            asset = asset_info["asset"]
            relationships = asset_info["relationships"]
            
            # Calculate risk score
            risk_score = await self.scoring_service.score_asset(asset_id)
            
            analysis = {
                "asset_id": asset_id,
                "asset_type": asset.get("type", "unknown"),
                "risk_score": risk_score,
                "relationships_count": len(relationships),
                "relationships": relationships[:20] if include_neighbors else [],  # Limit for readability
                "risk_level": "HIGH" if risk_score > 0.8 else "MEDIUM" if risk_score > 0.5 else "LOW"
            }
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(analysis, indent=2, default=str)
                )]
            )
        except Exception as e:
            raise Exception(f"Asset analysis failed: {str(e)}")
    
    async def _handle_propose_remediation(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle remediation proposal tool calls"""
        await self._ensure_connections()
        
        path_id = arguments.get("path_id")
        remediation_type = arguments.get("remediation_type")
        dry_run = arguments.get("dry_run", True)
        
        if not path_id or not remediation_type:
            raise ValueError("path_id and remediation_type are required")
        
        try:
            # Propose remediation using remediation service
            remediation_plan = await self.remediation_service.propose_remediation(
                path_id=path_id,
                remediation_type=remediation_type,
                dry_run=dry_run
            )
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(remediation_plan, indent=2, default=str)
                )]
            )
        except Exception as e:
            raise Exception(f"Remediation proposal failed: {str(e)}")
    
    async def _handle_get_graph_statistics(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle graph statistics tool calls"""
        await self._ensure_connections()
        
        include_risk_metrics = arguments.get("include_risk_metrics", True)
        
        try:
            # Get basic graph statistics
            stats_query = """
            MATCH (n)
            RETURN 
                count(n) as total_nodes,
                count(DISTINCT labels(n)) as node_types,
                count(DISTINCT [r in relationships() | type(r)]) as relationship_types
            """
            
            basic_stats = await self.neo4j_conn.execute_query(stats_query)
            
            # Get relationship count
            rel_query = "MATCH ()-[r]->() RETURN count(r) as total_relationships"
            rel_stats = await self.neo4j_conn.execute_query(rel_query)
            
            statistics = {
                "total_nodes": basic_stats[0]["total_nodes"],
                "node_types": basic_stats[0]["node_types"],
                "relationship_types": basic_stats[0]["relationship_types"],
                "total_relationships": rel_stats[0]["total_relationships"]
            }
            
            if include_risk_metrics:
                # Get risk-related statistics
                risk_query = """
                MATCH (n:Asset)
                WHERE n.risk_score IS NOT NULL
                RETURN 
                    avg(n.risk_score) as avg_risk_score,
                    max(n.risk_score) as max_risk_score,
                    count(n) as assets_with_risk_scores
                """
                
                risk_stats = await self.neo4j_conn.execute_query(risk_query)
                if risk_stats:
                    statistics.update({
                        "avg_risk_score": risk_stats[0]["avg_risk_score"],
                        "max_risk_score": risk_stats[0]["max_risk_score"],
                        "assets_with_risk_scores": risk_stats[0]["assets_with_risk_scores"]
                    })
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(statistics, indent=2, default=str)
                )]
            )
        except Exception as e:
            raise Exception(f"Failed to get graph statistics: {str(e)}")
    
    async def run(self):
        """Run the MCP server"""
        logger.info("Starting GNN Attack Path MCP Server...")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="gnn-attack-path-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities={}
                    )
                )
            )


async def main():
    """Main entry point for MCP server"""
    config = MCPServerConfig()
    server = GNNAttackPathMCPServer(config)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
