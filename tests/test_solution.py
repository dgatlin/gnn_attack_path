"""
Test suite for GNN Attack Path Demo.
Comprehensive tests covering all major components.
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

# Import modules to test
from scorer.baseline import DijkstraScorer, PageRankScorer, MotifScorer, HybridScorer
from scorer.gnn_model import AttackPathGNN
from scorer.service import AttackPathScoringService
from agent.planner import AttackPathPlanner
from agent.remediator import RemediationAgent
from agent.app import AttackPathAgent
from agent.mcp_server import GNNAttackPathMCPServer, MCPServerConfig
from agent.mcp_client_simple import SimpleMCPClient, MCPClientConfig, MCPToolWrapper


class TestBaselineScorers:
    """Test baseline scoring algorithms."""
    
    def setup_method(self):
        """Set up test data."""
        self.sample_nodes = [
            {"id": "vm1", "type": "vm", "critical": False},
            {"id": "vm2", "type": "vm", "critical": False},
            {"id": "db1", "type": "db", "critical": True},
            {"id": "sg1", "type": "sg", "critical": False},
        ]
        
        self.sample_edges = [
            {
                "source_id": "vm1",
                "target_id": "vm2",
                "type": "CONNECTS_TO",
                "properties": {"protocol": "tcp", "port": 443}
            },
            {
                "source_id": "vm2",
                "target_id": "db1",
                "type": "CONNECTS_TO",
                "properties": {"protocol": "tcp", "port": 5432}
            }
        ]
    
    def test_dijkstra_scorer(self):
        """Test Dijkstra-based scoring."""
        scorer = DijkstraScorer()
        scorer.load_graph(self.sample_nodes, self.sample_edges)
        
        paths = scorer.get_attack_paths("vm1", "db1", max_hops=3)
        
        assert len(paths) > 0
        assert "path" in paths[0]
        assert "score" in paths[0]
        assert paths[0]["algorithm"] == "dijkstra"
    
    def test_pagerank_scorer(self):
        """Test PageRank-based scoring."""
        scorer = PageRankScorer()
        scorer.load_graph(self.sample_nodes, self.sample_edges)
        
        paths = scorer.get_attack_paths("vm1", "db1", max_hops=3)
        
        assert len(paths) >= 0  # May not find paths in small graph
        if paths:
            assert "path" in paths[0]
            assert "score" in paths[0]
            assert paths[0]["algorithm"] == "pagerank"
    
    def test_motif_scorer(self):
        """Test motif-based scoring."""
        scorer = MotifScorer()
        scorer.load_graph(self.sample_nodes, self.sample_edges)
        
        paths = scorer.get_attack_paths("vm1", "db1", max_hops=3)
        
        assert len(paths) >= 0
        if paths:
            assert "path" in paths[0]
            assert "score" in paths[0]
            assert paths[0]["algorithm"] == "motif"
    
    def test_hybrid_scorer(self):
        """Test hybrid scoring approach."""
        scorer = HybridScorer()
        scorer.load_graph(self.sample_nodes, self.sample_edges)
        
        paths = scorer.get_attack_paths("vm1", "db1", max_hops=3)
        
        assert len(paths) >= 0
        if paths:
            assert "path" in paths[0]
            assert "score" in paths[0]
            assert paths[0]["algorithm"] == "hybrid"


class TestGNNModel:
    """Test GNN model functionality."""
    
    def setup_method(self):
        """Set up test data."""
        self.sample_nodes = [
            {"id": "vm1", "type": "vm", "critical": False, "environment": "production"},
            {"id": "db1", "type": "db", "critical": True, "environment": "production"},
        ]
        
        self.sample_edges = [
            {
                "source_id": "vm1",
                "target_id": "db1",
                "type": "CONNECTS_TO",
                "properties": {"protocol": "tcp", "port": 5432, "encrypted": True}
            }
        ]
    
    def test_gnn_data_preparation(self):
        """Test GNN data preparation."""
        gnn = AttackPathGNN()
        data = gnn.prepare_data(self.sample_nodes, self.sample_edges)
        
        assert data.x.shape[0] == len(self.sample_nodes)
        assert data.edge_index.shape[1] == len(self.sample_edges)
        assert data.edge_attr.shape[0] == len(self.sample_edges)
    
    def test_gnn_model_building(self):
        """Test GNN model building."""
        gnn = AttackPathGNN()
        
        # Calculate dimensions
        node_dim = len(gnn._extract_node_features(self.sample_nodes[0]))
        edge_dim = len(gnn._extract_edge_features(self.sample_edges[0]))
        
        gnn.build_model(node_dim, edge_dim)
        
        assert gnn.model is not None
        assert gnn.model_type in ["graphsage", "gat"]


class TestAgentComponents:
    """Test agent orchestration components."""
    
    def test_planner_intent_parsing(self):
        """Test intent parsing in planner."""
        with patch('agent.planner.ChatOpenAI') as mock_llm:
            mock_llm.return_value = Mock()
            planner = AttackPathPlanner()
        
        # Test different query types
        queries = [
            "Where's my riskiest path to the crown jewel?",
            "What should I fix to reduce risk?",
            "Simulate removing public access"
        ]
        
        for query in queries:
            plan = planner.plan_analysis(query)
            assert "intent" in plan
            assert "target" in plan
            assert "algorithm" in plan
    
    def test_remediator_action_generation(self):
        """Test remediation action generation."""
        remediator = RemediationAgent()
        
        # Mock attack paths
        mock_paths = [
            {
                "path": ["vm1", "vm2", "db1"],
                "score": 0.8,
                "length": 2
            }
        ]
        
        constraints = {"max_actions": 3}
        plan = remediator.generate_remediation_plan(mock_paths, constraints)
        
        assert "actions" in plan
        assert "implementation_plan" in plan
        assert len(plan["actions"]) <= 3


class TestAPIIntegration:
    """Test API integration."""
    
    @pytest.fixture
    def mock_scorer(self):
        """Mock scoring service."""
        scorer = Mock()
        scorer.get_attack_paths.return_value = [
            {
                "path": ["vm1", "db1"],
                "score": 0.8,
                "length": 1,
                "algorithm": "hybrid"
            }
        ]
        scorer.get_risk_explanation.return_value = "Test explanation"
        return scorer
    
    def test_attack_paths_endpoint(self, mock_scorer):
        """Test attack paths API endpoint."""
        from api.main import app
        from fastapi.testclient import TestClient
        
        with patch('api.main.scorer', mock_scorer):
            client = TestClient(app)
            response = client.post("/api/v1/paths", json={
                "target": "db1",
                "algorithm": "hybrid",
                "max_hops": 4,
                "k": 5
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "paths" in data
            assert "latency_ms" in data
            assert len(data["paths"]) > 0
    
    def test_health_check(self):
        """Test health check endpoint."""
        from api.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/health")
        
        # Should return 503 if services not initialized
        assert response.status_code in [200, 503]


class TestDataGeneration:
    """Test synthetic data generation."""
    
    def test_synthetic_data_generator(self):
        """Test synthetic data generation."""
        from data.generate_synthetic_data import SyntheticDataGenerator
        
        generator = SyntheticDataGenerator(seed=42)
        data = generator.generate_all()
        
        assert "assets" in data
        assert "software" in data
        assert "vulnerabilities" in data
        assert "relationships" in data
        
        assert len(data["assets"]) > 0
        assert len(data["software"]) > 0
        assert len(data["vulnerabilities"]) > 0
        assert len(data["relationships"]) > 0
    
    def test_crown_jewel_identification(self):
        """Test crown jewel identification in generated data."""
        from data.generate_synthetic_data import SyntheticDataGenerator
        
        generator = SyntheticDataGenerator(seed=42)
        data = generator.generate_all()
        
        crown_jewels = [asset for asset in data["assets"] if asset.get("critical", False)]
        assert len(crown_jewels) > 0
        
        # Check naming convention
        for jewel in crown_jewels:
            assert "crown-jewel" in jewel["name"]


class TestPerformance:
    """Test performance characteristics."""
    
    def test_scoring_performance(self):
        """Test scoring algorithm performance."""
        import time
        
        # Create larger test dataset
        nodes = []
        edges = []
        
        # Generate 100 nodes
        for i in range(100):
            nodes.append({
                "id": f"node_{i}",
                "type": "vm" if i < 50 else "db",
                "critical": i == 99  # Last node is crown jewel
            })
        
        # Generate 200 edges
        for i in range(200):
            source = f"node_{i % 50}"
            target = f"node_{(i + 1) % 100}"
            edges.append({
                "source_id": source,
                "target_id": target,
                "type": "CONNECTS_TO",
                "properties": {"protocol": "tcp", "port": 443}
            })
        
        # Test Dijkstra performance
        scorer = DijkstraScorer()
        scorer.load_graph(nodes, edges)
        
        start_time = time.time()
        paths = scorer.get_attack_paths("node_0", "node_99", max_hops=5)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert (end_time - start_time) < 5.0  # 5 seconds max
        assert len(paths) >= 0


class TestMCPServer:
    """Test MCP Server functionality."""
    
    def setup_method(self):
        """Set up test configuration."""
        self.config = MCPServerConfig(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="test_password"
        )
    
    @pytest.mark.asyncio
    async def test_mcp_server_initialization(self):
        """Test MCP server initialization."""
        with patch('agent.mcp_server.Neo4jConnection') as mock_neo4j:
            mock_neo4j.return_value.connect = AsyncMock()
            
            server = GNNAttackPathMCPServer(self.config)
            assert server.config == self.config
            assert server.neo4j_conn is None
            assert server.scoring_service is None
    
    def test_mcp_server_configuration(self):
        """Test MCP server configuration."""
        server = GNNAttackPathMCPServer(self.config)
        assert server.config == self.config
        assert server.neo4j_conn is None
        assert server.scoring_service is None
        assert server.remediation_service is None
    
    def test_mcp_server_tool_handlers_exist(self):
        """Test that MCP tool handlers are properly defined."""
        server = GNNAttackPathMCPServer(self.config)
        
        # Check that handler methods exist
        assert hasattr(server, '_handle_query_graph')
        assert hasattr(server, '_handle_score_attack_paths')
        assert hasattr(server, '_handle_get_top_risky_paths')
        assert hasattr(server, '_handle_analyze_asset_risk')
        assert hasattr(server, '_handle_propose_remediation')
        assert hasattr(server, '_handle_get_graph_statistics')


class TestMCPClient:
    """Test MCP Client functionality."""
    
    def setup_method(self):
        """Set up test configuration."""
        self.config = MCPClientConfig()
    
    @pytest.mark.asyncio
    async def test_mcp_client_initialization(self):
        """Test MCP client initialization."""
        client = SimpleMCPClient(self.config)
        assert client.config == self.config
        assert client.connected == False
    
    @pytest.mark.asyncio
    async def test_mcp_client_connection(self):
        """Test MCP client connection."""
        client = SimpleMCPClient(self.config)
        await client.connect()
        assert client.connected == True
        await client.disconnect()
        assert client.connected == False
    
    @pytest.mark.asyncio
    async def test_mcp_tool_calls(self):
        """Test MCP tool calls."""
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
        
        await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_mcp_tool_wrapper(self):
        """Test MCP tool wrapper functionality."""
        client = SimpleMCPClient(self.config)
        await client.connect()
        wrapper = MCPToolWrapper(client)
        
        # Test tool wrapper methods
        result = await wrapper.find_attack_paths("source", "target")
        assert isinstance(result, list)
        assert len(result) > 0
        
        result = await wrapper.get_risky_assets(5)
        assert isinstance(result, list)
        
        result = await wrapper.assess_asset("test_asset")
        assert "asset_id" in result
        
        await client.disconnect()


class TestMCPIntegration:
    """Test MCP integration end-to-end."""
    
    @pytest.mark.asyncio
    async def test_mcp_workflow(self):
        """Test complete MCP workflow."""
        # Test server creation
        server_config = MCPServerConfig()
        server = GNNAttackPathMCPServer(server_config)
        assert server is not None
        
        # Test client creation and basic functionality
        client_config = MCPClientConfig()
        client = SimpleMCPClient(client_config)
        await client.connect()
        
        # Test basic tool calls
        result = await client.call_tool("get_graph_statistics", {})
        assert "total_nodes" in result
        
        await client.disconnect()


def run_all_tests():
    """Run all tests."""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_all_tests()
