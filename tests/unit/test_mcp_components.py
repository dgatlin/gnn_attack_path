"""
Unit tests for MCP (Model Context Protocol) components.

Tests MCP server, client, and agent components in isolation.
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

from agent.mcp_server import GNNAttackPathMCPServer, MCPServerConfig
from agent.mcp_client_simple import SimpleMCPClient, MCPClientConfig, MCPToolWrapper


class TestMCPServer:
    """Unit tests for MCP Server component."""
    
    def setup_method(self):
        """Set up test configuration."""
        self.config = MCPServerConfig(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="test_password"
        )
    
    def test_mcp_server_initialization(self):
        """Test MCP server initializes correctly."""
        server = GNNAttackPathMCPServer(self.config)
        
        assert server.config == self.config
        assert server.neo4j_conn is None
        assert server.scoring_service is None
        assert server.remediation_service is None
        assert server.server is not None
    
    def test_mcp_server_configuration(self):
        """Test MCP server configuration validation."""
        server = GNNAttackPathMCPServer(self.config)
        
        assert server.config.neo4j_uri == "bolt://localhost:7687"
        assert server.config.neo4j_user == "neo4j"
        assert server.config.neo4j_password == "test_password"
    
    def test_tool_handlers_exist(self):
        """Test that all required tool handlers are defined."""
        server = GNNAttackPathMCPServer(self.config)
        
        required_handlers = [
            '_handle_query_graph',
            '_handle_score_attack_paths',
            '_handle_get_top_risky_paths',
            '_handle_analyze_asset_risk',
            '_handle_propose_remediation',
            '_handle_get_graph_statistics'
        ]
        
        for handler_name in required_handlers:
            assert hasattr(server, handler_name)
            assert callable(getattr(server, handler_name))
    
    @pytest.mark.asyncio
    async def test_ensure_connections(self):
        """Test connection establishment."""
        with patch('agent.mcp_server.Neo4jConnection') as mock_neo4j, \
             patch('agent.mcp_server.AttackPathScoringService') as mock_scoring, \
             patch('agent.mcp_server.RemediationAgent') as mock_remediation:
            
            mock_neo4j.return_value.connect = AsyncMock()
            mock_scoring.return_value.initialize = AsyncMock()
            
            server = GNNAttackPathMCPServer(self.config)
            await server._ensure_connections()
            
            assert server.neo4j_conn is not None
            assert server.scoring_service is not None
            assert server.remediation_service is not None
    
    @pytest.mark.asyncio
    async def test_handle_query_graph(self):
        """Test graph query handling."""
        with patch('agent.mcp_server.Neo4jConnection') as mock_neo4j, \
             patch('agent.mcp_server.AttackPathScoringService') as mock_scoring, \
             patch('agent.mcp_server.RemediationAgent') as mock_remediation:
            
            mock_conn = Mock()
            mock_conn.execute_query = AsyncMock(return_value=[{"test": "data"}])
            mock_neo4j.return_value = mock_conn
            mock_scoring.return_value.initialize = AsyncMock()
            
            server = GNNAttackPathMCPServer(self.config)
            
            result = await server._handle_query_graph({
                "query": "MATCH (n) RETURN n LIMIT 1",
                "parameters": {}
            })
            
            assert result.content[0].text is not None
            assert "test" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_handle_score_attack_paths(self):
        """Test attack path scoring handling."""
        with patch('agent.mcp_server.Neo4jConnection') as mock_neo4j, \
             patch('agent.mcp_server.AttackPathScoringService') as mock_scoring, \
             patch('agent.mcp_server.RemediationAgent') as mock_remediation:
            
            mock_conn = Mock()
            mock_conn.execute_query = AsyncMock(return_value=[])
            mock_neo4j.return_value = mock_conn
            mock_scoring.return_value.initialize = AsyncMock()
            mock_scoring.return_value.score_path = AsyncMock(return_value=0.8)
            
            server = GNNAttackPathMCPServer(self.config)
            
            result = await server._handle_score_attack_paths({
                "source_node": "server1",
                "target_node": "database1",
                "max_depth": 5
            })
            
            assert result.content[0].text is not None
            result_data = json.loads(result.content[0].text)
            assert "source_node" in result_data
            assert "target_node" in result_data


class TestMCPClient:
    """Unit tests for MCP Client component."""
    
    def setup_method(self):
        """Set up test configuration."""
        self.config = MCPClientConfig()
    
    def test_mcp_client_initialization(self):
        """Test MCP client initializes correctly."""
        client = SimpleMCPClient(self.config)
        
        assert client.config == self.config
        assert client.connected == False
    
    @pytest.mark.asyncio
    async def test_client_connection(self):
        """Test client connection lifecycle."""
        client = SimpleMCPClient(self.config)
        
        await client.connect()
        assert client.connected == True
        
        await client.disconnect()
        assert client.connected == False
    
    @pytest.mark.asyncio
    async def test_tool_calls(self):
        """Test various tool calls."""
        client = SimpleMCPClient(self.config)
        await client.connect()
        
        # Test query_graph tool
        result = await client.call_tool("query_graph", {
            "query": "MATCH (n) RETURN n LIMIT 5",
            "parameters": {}
        })
        assert "result_count" in result
        assert "results" in result
        
        # Test score_attack_paths tool
        result = await client.call_tool("score_attack_paths", {
            "source_node": "server1",
            "target_node": "database1"
        })
        assert "scored_paths" in result
        assert len(result["scored_paths"]) > 0
        
        # Test get_top_risky_paths tool
        result = await client.call_tool("get_top_risky_paths", {
            "limit": 5
        })
        assert "risky_paths" in result
        
        await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling for invalid tool calls."""
        client = SimpleMCPClient(self.config)
        await client.connect()
        
        # Test unknown tool
        result = await client.call_tool("unknown_tool", {})
        assert "error" in result
        
        await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_connection_required(self):
        """Test that tool calls require connection."""
        client = SimpleMCPClient(self.config)
        
        with pytest.raises(RuntimeError, match="Client not connected"):
            await client.call_tool("query_graph", {})


class TestMCPToolWrapper:
    """Unit tests for MCP Tool Wrapper."""
    
    def setup_method(self):
        """Set up test client and wrapper."""
        self.config = MCPClientConfig()
        self.client = SimpleMCPClient(self.config)
        self.wrapper = MCPToolWrapper(self.client)
    
    @pytest.mark.asyncio
    async def test_find_attack_paths(self):
        """Test attack path finding wrapper."""
        await self.client.connect()
        
        result = await self.wrapper.find_attack_paths("source", "target")
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("path" in path for path in result)
        
        await self.client.disconnect()
    
    @pytest.mark.asyncio
    async def test_get_risky_assets(self):
        """Test risky assets retrieval wrapper."""
        await self.client.connect()
        
        result = await self.wrapper.get_risky_assets(5)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        await self.client.disconnect()
    
    @pytest.mark.asyncio
    async def test_assess_asset(self):
        """Test asset assessment wrapper."""
        await self.client.connect()
        
        result = await self.wrapper.assess_asset("test_asset")
        
        assert isinstance(result, dict)
        assert "asset_id" in result
        assert "risk_score" in result
        
        await self.client.disconnect()
    
    @pytest.mark.asyncio
    async def test_suggest_fixes(self):
        """Test remediation suggestion wrapper."""
        await self.client.connect()
        
        result = await self.wrapper.suggest_fixes("path1", "patch")
        
        assert isinstance(result, dict)
        assert "actions" in result
        
        await self.client.disconnect()
    
    @pytest.mark.asyncio
    async def test_get_graph_overview(self):
        """Test graph overview wrapper."""
        await self.client.connect()
        
        result = await self.wrapper.get_graph_overview()
        
        assert isinstance(result, dict)
        assert "total_nodes" in result
        
        await self.client.disconnect()


class TestMCPIntegration:
    """Unit tests for MCP integration components."""
    
    def test_server_client_compatibility(self):
        """Test that server and client are compatible."""
        server_config = MCPServerConfig()
        client_config = MCPClientConfig()
        
        server = GNNAttackPathMCPServer(server_config)
        client = SimpleMCPClient(client_config)
        
        # Both should initialize without errors
        assert server is not None
        assert client is not None
    
    def test_tool_interface_consistency(self):
        """Test that tool interfaces are consistent."""
        server = GNNAttackPathMCPServer(MCPServerConfig())
        
        # Get available tools from server
        tools = server.server._tools
        
        expected_tools = [
            "query_graph",
            "score_attack_paths",
            "get_top_risky_paths",
            "analyze_asset_risk",
            "propose_remediation",
            "get_graph_statistics"
        ]
        
        # Check that all expected tools are available
        tool_names = [tool.name for tool in tools]
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
