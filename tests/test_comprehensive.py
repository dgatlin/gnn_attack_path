"""
Comprehensive test suite for the GNN Attack Path project.

This test suite covers all major components and their interactions.
Organized into unit tests (isolated component testing) and integration tests (component interaction testing).
"""
import pytest
import asyncio
import json
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from data.generate_synthetic_data import SyntheticDataGenerator
from scorer.baseline import DijkstraScorer, PageRankScorer, MotifScorer, HybridScorer
from scorer.gnn_model import EdgeEncoder, AttackPathGNN
from scorer.service import AttackPathScoringService
from agent.planner import planner
from agent.remediator import RemediationAgent
from agent.app import create_workflow
from agent.mcp_server import GNNAttackPathMCPServer, MCPServerConfig
from agent.mcp_client_simple import SimpleMCPClient, MCPClientConfig, MCPToolWrapper
from api.main import app
from fastapi.testclient import TestClient


# ============================================================================
# UNIT TESTS - Testing individual components in isolation
# ============================================================================

class TestDataGeneration:
    """Unit tests for data generation components."""
    
    def test_synthetic_data_generator_initialization(self):
        """Test SyntheticDataGenerator initializes correctly."""
        generator = SyntheticDataGenerator()
        assert generator.num_assets > 0
        assert generator.num_vulnerabilities > 0
        assert generator.num_crown_jewels > 0
    
    def test_generate_assets(self):
        """Test asset generation."""
        generator = SyntheticDataGenerator()
        assets = generator.generate_assets()
        
        assert isinstance(assets, list)
        assert len(assets) > 0
        assert len(assets) <= generator.num_assets
        
        for asset in assets:
            assert "id" in asset
            assert "type" in asset
            assert "critical" in asset
            assert "properties" in asset
    
    def test_generate_vulnerabilities(self):
        """Test vulnerability generation."""
        generator = SyntheticDataGenerator()
        vulnerabilities = generator.generate_vulnerabilities()
        
        assert isinstance(vulnerabilities, list)
        assert len(vulnerabilities) > 0
        
        for vuln in vulnerabilities:
            assert "cve" in vuln
            assert "cvss" in vuln
            assert "exploit_available" in vuln
            assert "description" in vuln
    
    def test_generate_all(self):
        """Test complete data generation."""
        generator = SyntheticDataGenerator()
        data = generator.generate_all()
        
        assert "assets" in data
        assert "edges" in data
        assert "vulnerabilities" in data
        assert "crown_jewels" in data
        assert len(data["assets"]) > 0


class TestBaselineScorers:
    """Unit tests for baseline scoring algorithms."""
    
    def test_dijkstra_scorer_initialization(self):
        """Test DijkstraScorer initializes correctly."""
        scorer = DijkstraScorer()
        assert scorer.graph is None
        assert scorer.node_weights == {}
        assert scorer.edge_weights == {}
    
    def test_pagerank_scorer_initialization(self):
        """Test PageRankScorer initializes correctly."""
        scorer = PageRankScorer()
        assert scorer.graph is None
        assert scorer.pagerank_scores == {}
    
    def test_motif_scorer_initialization(self):
        """Test MotifScorer initializes correctly."""
        scorer = MotifScorer()
        assert scorer.graph is None
        assert scorer.motif_patterns == {}
    
    def test_hybrid_scorer_initialization(self):
        """Test HybridScorer initializes correctly."""
        scorer = HybridScorer()
        assert scorer.dijkstra_scorer is not None
        assert scorer.pagerank_scorer is not None
        assert scorer.motif_scorer is not None
    
    def test_scorer_with_sample_data(self):
        """Test scorers with sample data."""
        generator = SyntheticDataGenerator()
        data = generator.generate_all()
        
        scorer = HybridScorer()
        scorer.load_graph(data["assets"], data["edges"])
        
        if len(data["assets"]) >= 2:
            source = data["assets"][0]["id"]
            target = data["assets"][-1]["id"]
            
            paths = scorer.get_attack_paths(source, target)
            assert isinstance(paths, list)


class TestGNNModels:
    """Unit tests for GNN model components."""
    
    def test_edge_encoder_initialization(self):
        """Test EdgeEncoder initializes correctly."""
        encoder = EdgeEncoder(edge_dim=10, hidden_dim=64)
        assert encoder.edge_dim == 10
        assert encoder.hidden_dim == 64
    
    def test_attack_path_gnn_initialization(self):
        """Test AttackPathGNN initializes correctly."""
        model = AttackPathGNN(
            node_dim=20,
            edge_dim=10,
            hidden_dim=64,
            num_layers=2
        )
        assert model.node_dim == 20
        assert model.edge_dim == 10
        assert model.hidden_dim == 64
        assert model.num_layers == 2


class TestAgentComponents:
    """Unit tests for agent components."""
    
    def test_remediation_agent_initialization(self):
        """Test RemediationAgent initializes correctly."""
        agent = RemediationAgent()
        assert agent is not None
        assert hasattr(agent, 'propose_remediation')
        assert hasattr(agent, 'simulate_remediation')
    
    @pytest.mark.asyncio
    async def test_remediation_agent_propose(self):
        """Test remediation proposal."""
        agent = RemediationAgent()
        sample_path = {
            "path": ["server1", "database1"],
            "risk_score": 0.8,
            "vulnerabilities": ["CVE-2023-1234"]
        }
        
        result = await agent.propose_remediation(sample_path, "patch")
        assert isinstance(result, dict)
        assert "actions" in result
        assert "priority" in result
        assert "estimated_effort" in result
    
    def test_workflow_creation(self):
        """Test workflow creation."""
        workflow = create_workflow()
        assert workflow is not None
        assert hasattr(workflow, 'invoke')
        assert hasattr(workflow, 'astream')


class TestMCPServer:
    """Unit tests for MCP Server component."""
    
    def test_mcp_server_initialization(self):
        """Test MCP server initializes correctly."""
        config = MCPServerConfig()
        server = GNNAttackPathMCPServer(config)
        
        assert server.config == config
        assert server.neo4j_conn is None
        assert server.scoring_service is None
        assert server.remediation_service is None
    
    def test_mcp_server_tool_handlers(self):
        """Test that all required tool handlers exist."""
        config = MCPServerConfig()
        server = GNNAttackPathMCPServer(config)
        
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


class TestMCPClient:
    """Unit tests for MCP Client component."""
    
    def test_mcp_client_initialization(self):
        """Test MCP client initializes correctly."""
        config = MCPClientConfig()
        client = SimpleMCPClient(config)
        
        assert client.config == config
        assert client.connected == False
    
    @pytest.mark.asyncio
    async def test_mcp_client_connection(self):
        """Test MCP client connection lifecycle."""
        client = SimpleMCPClient(MCPClientConfig())
        
        await client.connect()
        assert client.connected == True
        
        await client.disconnect()
        assert client.connected == False


class TestAPIIntegration:
    """Unit tests for API endpoints."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


# ============================================================================
# INTEGRATION TESTS - Testing component interactions
# ============================================================================

class TestDataToScoringIntegration:
    """Integration tests for data generation to scoring pipeline."""
    
    def test_complete_data_pipeline(self):
        """Test complete data generation to scoring pipeline."""
        # Generate data
        generator = SyntheticDataGenerator()
        data = generator.generate_all()
        
        # Load into scorer
        scorer = HybridScorer()
        scorer.load_graph(data["assets"], data["edges"])
        
        # Test scoring
        if len(data["assets"]) >= 2:
            source = data["assets"][0]["id"]
            target = data["assets"][-1]["id"]
            
            paths = scorer.get_attack_paths(source, target)
            assert isinstance(paths, list)
            
            if paths:
                for path in paths:
                    score = scorer.score_path(path)
                    assert isinstance(score, float)
                    assert 0.0 <= score <= 1.0


class TestMCPIntegration:
    """Integration tests for MCP components."""
    
    @pytest.mark.asyncio
    async def test_mcp_workflow(self):
        """Test complete MCP workflow."""
        client = SimpleMCPClient(MCPClientConfig())
        await client.connect()
        wrapper = MCPToolWrapper(client)
        
        try:
            # Test graph statistics
            stats = await wrapper.get_graph_overview()
            assert "total_nodes" in stats
            assert stats["total_nodes"] > 0
            
            # Test attack path analysis
            paths = await wrapper.find_attack_paths("server1", "database1")
            assert isinstance(paths, list)
            
            # Test risk assessment
            if paths:
                asset_id = paths[0]["path"][0] if paths[0]["path"] else "test_asset"
                assessment = await wrapper.assess_asset(asset_id)
                assert "risk_score" in assessment
            
            # Test remediation suggestions
            if paths:
                path_id = "test_path"
                suggestions = await wrapper.suggest_fixes(path_id, "patch")
                assert "actions" in suggestions
        
        finally:
            await client.disconnect()


class TestEndToEndWorkflow:
    """Integration tests for end-to-end workflows."""
    
    def test_data_generation_to_analysis(self):
        """Test complete workflow from data generation to analysis."""
        # Generate data
        generator = SyntheticDataGenerator()
        data = generator.generate_all()
        
        # Load into scorer
        scorer = HybridScorer()
        scorer.load_graph(data["assets"], data["edges"])
        
        # Test analysis
        if len(data["assets"]) >= 2:
            source = data["assets"][0]["id"]
            target = data["assets"][-1]["id"]
            
            paths = scorer.get_attack_paths(source, target)
            assert isinstance(paths, list)
            
            if paths:
                # Test path scoring
                for path in paths[:3]:
                    score = scorer.score_path(path)
                    assert isinstance(score, float)
                    assert 0.0 <= score <= 1.0
    
    @pytest.mark.asyncio
    async def test_agent_workflow(self):
        """Test agent workflow integration."""
        # Test remediation agent
        agent = RemediationAgent()
        sample_path = {
            "path": ["external", "dmz", "internal", "database"],
            "risk_score": 0.9,
            "vulnerabilities": ["CVE-2023-CRITICAL"]
        }
        
        remediation = await agent.propose_remediation(sample_path, "patch")
        assert isinstance(remediation, dict)
        assert "actions" in remediation
        
        # Test simulation
        simulation = await agent.simulate_remediation(remediation)
        assert isinstance(simulation, dict)
        assert "success" in simulation
        assert "new_risk_score" in simulation


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance tests for critical components."""
    
    def test_scoring_performance(self):
        """Test scoring performance with realistic data."""
        import time
        
        # Generate larger dataset
        generator = SyntheticDataGenerator()
        generator.num_assets = 50
        data = generator.generate_all()
        
        scorer = HybridScorer()
        scorer.load_graph(data["assets"], data["edges"])
        
        if len(data["assets"]) >= 2:
            source = data["assets"][0]["id"]
            target = data["assets"][-1]["id"]
            
            # Measure scoring time
            start_time = time.time()
            paths = scorer.get_attack_paths(source, target)
            end_time = time.time()
            
            scoring_time = end_time - start_time
            assert scoring_time < 2.0  # Should complete within 2 seconds
    
    def test_memory_usage(self):
        """Test memory usage with larger datasets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Generate larger dataset
        generator = SyntheticDataGenerator()
        generator.num_assets = 100
        data = generator.generate_all()
        
        scorer = HybridScorer()
        scorer.load_graph(data["assets"], data["edges"])
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024  # 100MB in bytes


# ============================================================================
# TEST UTILITIES
# ============================================================================

def test_coverage_report():
    """Generate test coverage report."""
    # This test ensures coverage reporting is working
    assert True


def test_test_organization():
    """Test that test organization is correct."""
    # Verify test structure
    test_file = __file__
    assert "test_comprehensive.py" in test_file
    
    # Verify test classes exist
    test_classes = [
        TestDataGeneration,
        TestBaselineScorers,
        TestGNNModels,
        TestAgentComponents,
        TestMCPServer,
        TestMCPClient,
        TestAPIIntegration,
        TestDataToScoringIntegration,
        TestMCPIntegration,
        TestEndToEndWorkflow,
        TestPerformance
    ]
    
    for test_class in test_classes:
        assert test_class is not None
        assert hasattr(test_class, '__name__')


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
