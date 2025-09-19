#!/usr/bin/env python3
"""
MCP Integration Example

This example demonstrates how to use the MCP (Model Context Protocol) 
integration for seamless tool communication in the GNN Attack Path system.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import MCP components
from agent.mcp_server import GNNAttackPathMCPServer, MCPServerConfig
from agent.mcp_client import GNNAttackPathMCPClient, MCPClientConfig
from agent.mcp_agent import MCPEnhancedAgent


async def example_mcp_server():
    """Example: Running MCP Server"""
    print("🚀 Starting MCP Server Example")
    print("=" * 50)
    
    # Configure server
    config = MCPServerConfig(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password"
    )
    
    # Create and run server
    server = GNNAttackPathMCPServer(config)
    
    print("MCP Server configured with tools:")
    print("- query_graph: Execute Cypher queries")
    print("- score_attack_paths: Score paths between nodes")
    print("- get_top_risky_paths: Get most risky paths")
    print("- analyze_asset_risk: Analyze asset risk")
    print("- propose_remediation: Propose security fixes")
    print("- get_graph_statistics: Get graph overview")
    
    # Note: In production, this would run continuously
    # await server.run()


async def example_mcp_client():
    """Example: Using MCP Client"""
    print("\n🔗 Starting MCP Client Example")
    print("=" * 50)
    
    # Configure client
    config = MCPClientConfig()
    client = GNNAttackPathMCPClient(config)
    
    try:
        # Connect to server (in real usage)
        # await client.connect()
        
        print("MCP Client capabilities:")
        print("- Direct tool calls to graph database")
        print("- Attack path analysis")
        print("- Risk assessment")
        print("- Remediation suggestions")
        
        # Example tool calls (mocked for demo)
        print("\nExample tool calls:")
        
        # Query graph
        print("1. Querying graph for assets...")
        # result = await client.query_graph("MATCH (a:Asset) RETURN a LIMIT 5")
        print("   ✓ Found 5 assets in graph")
        
        # Score attack paths
        print("2. Scoring attack paths...")
        # result = await client.score_attack_paths("server1", "database1")
        print("   ✓ Found 3 attack paths with scores: [0.8, 0.6, 0.4]")
        
        # Get risky assets
        print("3. Getting top risky assets...")
        # result = await client.get_top_risky_paths(limit=5)
        print("   ✓ Found 5 high-risk paths")
        
    except Exception as e:
        print(f"Error in client example: {e}")
    finally:
        # await client.disconnect()
        pass


async def example_mcp_agent():
    """Example: Using MCP Enhanced Agent"""
    print("\n🤖 Starting MCP Enhanced Agent Example")
    print("=" * 50)
    
    # Get OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("⚠️  OPENAI_API_KEY not set. Using mock for demo.")
        openai_api_key = "mock-key"
    
    # Configure agent
    mcp_config = MCPClientConfig()
    agent = MCPEnhancedAgent(openai_api_key, mcp_config)
    
    try:
        # Initialize agent (in real usage)
        # await agent.initialize()
        
        print("MCP Enhanced Agent capabilities:")
        print("- Natural language security queries")
        print("- Graph-aware reasoning")
        print("- Automated tool selection")
        print("- Contextual responses")
        
        # Example queries
        queries = [
            "What are the most risky assets in our network?",
            "Find attack paths from external servers to our database",
            "Assess the risk level of server-001 and suggest fixes",
            "Give me an overview of our security posture"
        ]
        
        print("\nExample security queries:")
        for i, query in enumerate(queries, 1):
            print(f"{i}. {query}")
            # In real usage:
            # response = await agent.analyze_security_query(query)
            # print(f"   Response: {response}")
            print("   → [Would analyze graph and provide detailed response]")
        
    except Exception as e:
        print(f"Error in agent example: {e}")
    finally:
        # await agent.close()
        pass


async def example_integration_workflow():
    """Example: Complete MCP Integration Workflow"""
    print("\n🔄 Starting Complete MCP Integration Workflow")
    print("=" * 50)
    
    print("Complete workflow steps:")
    print("1. 🗄️  MCP Server exposes graph operations as tools")
    print("2. 🔗 MCP Client connects to server and provides tool access")
    print("3. 🤖 AI Agent uses tools for intelligent security analysis")
    print("4. 📊 Results are processed and presented to users")
    
    print("\nBenefits of MCP integration:")
    print("✅ Seamless tool communication")
    print("✅ Standardized protocol")
    print("✅ Language-agnostic tool access")
    print("✅ Easy integration with AI frameworks")
    print("✅ Scalable architecture")
    
    print("\nTool capabilities exposed via MCP:")
    tools = [
        ("query_graph", "Execute Cypher queries against Neo4j"),
        ("score_attack_paths", "Score attack paths using GNN models"),
        ("get_top_risky_paths", "Get most risky paths in the graph"),
        ("analyze_asset_risk", "Analyze risk for specific assets"),
        ("propose_remediation", "Suggest security fixes"),
        ("get_graph_statistics", "Get overall graph metrics")
    ]
    
    for tool_name, description in tools:
        print(f"  • {tool_name}: {description}")


async def main():
    """Run all MCP examples"""
    print("🔧 MCP (Model Context Protocol) Integration Examples")
    print("=" * 60)
    
    await example_mcp_server()
    await example_mcp_client()
    await example_mcp_agent()
    await example_integration_workflow()
    
    print("\n" + "=" * 60)
    print("✅ MCP Integration examples completed!")
    print("\nTo run the actual MCP components:")
    print("1. Start Neo4j database")
    print("2. Run: python -m agent.mcp_server")
    print("3. Run: python -m agent.mcp_client")
    print("4. Run: python -m agent.mcp_agent")


if __name__ == "__main__":
    asyncio.run(main())
