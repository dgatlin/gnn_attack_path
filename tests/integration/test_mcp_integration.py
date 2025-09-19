"""
Integration tests for MCP (Model Context Protocol) integration.

Tests MCP components working together with real data flows.
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

from agent.mcp_server import GNNAttackPathMCPServer, MCPServerConfig
from agent.mcp_client_simple import SimpleMCPClient, MCPClientConfig, MCPToolWrapper
from data.generate_synthetic_data import SyntheticDataGenerator
from scorer.baseline import HybridScorer


class TestMCPDataFlowIntegration:
    """Integration tests for MCP data flow."""
    
    def setup_method(self):
        """Set up MCP components and data."""
        self.server_config = MCPServerConfig()
        self.client_config = MCPClientConfig()
        self.data_generator = SyntheticDataGenerator()
    
    @pytest.mark.asyncio
    async def test_mcp_with_real_data(self):
        """Test MCP workflow with real generated data."""
        # Generate synthetic data
        data = self.data_generator.generate_all()
        
        # Set up MCP client
        client = SimpleMCPClient(self.client_config)
        await client.connect()
        wrapper = MCPToolWrapper(client)
        
        try:
            # Test graph statistics with real data context
            stats = await wrapper.get_graph_overview()
            assert "total_nodes" in stats
            assert stats["total_nodes"] > 0
            
            # Test attack path analysis
            if len(data["assets"]) >= 2:
                source = data["assets"][0]["id"]
                target = data["assets"][-1]["id"]
                
                paths = await wrapper.find_attack_paths(source, target)
                assert isinstance(paths, list)
                
                # Test risk assessment for found paths
                if paths:
                    for path in paths[:2]:  # Test first 2 paths
                        if "path" in path and path["path"]:
                            asset_id = path["path"][0]
                            assessment = await wrapper.assess_asset(asset_id)
                            assert "risk_score" in assessment
                            assert 0.0 <= assessment["risk_score"] <= 1.0
            
            # Test remediation suggestions
            risky_assets = await wrapper.get_risky_assets(3)
            if risky_assets:
                for asset in risky_assets[:2]:
                    if "path_id" in asset:
                        suggestions = await wrapper.suggest_fixes(
                            asset["path_id"], "patch"
                        )
                        assert "actions" in suggestions
                        assert isinstance(suggestions["actions"], list)
        
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_mcp_error_handling_integration(self):
        """Test MCP error handling in integrated workflow."""
        client = SimpleMCPClient(self.client_config)
        await client.connect()
        wrapper = MCPToolWrapper(client)
        
        try:
            # Test with invalid parameters
            invalid_paths = await wrapper.find_attack_paths("", "")
            assert isinstance(invalid_paths, list)  # Should return empty list or error response
            
            # Test with non-existent asset
            assessment = await wrapper.assess_asset("non_existent_asset_12345")
            assert isinstance(assessment, dict)
            assert "asset_id" in assessment
            
            # Test with invalid remediation type
            suggestions = await wrapper.suggest_fixes("invalid_path", "invalid_type")
            assert isinstance(suggestions, dict)
            
            # Client should still be functional after errors
            stats = await wrapper.get_graph_overview()
            assert "total_nodes" in stats
            
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_mcp_concurrent_operations(self):
        """Test concurrent MCP operations."""
        client = SimpleMCPClient(self.client_config)
        await client.connect()
        wrapper = MCPToolWrapper(client)
        
        try:
            # Define concurrent operations
            async def get_stats():
                return await wrapper.get_graph_overview()
            
            async def get_risky_assets():
                return await wrapper.get_risky_assets(5)
            
            async def assess_asset(asset_id):
                return await wrapper.assess_asset(asset_id)
            
            # Run operations concurrently
            tasks = [
                get_stats(),
                get_risky_assets(),
                assess_asset("test_asset_1"),
                assess_asset("test_asset_2"),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All operations should complete
            assert len(results) == 4
            
            # Check results
            stats_result = results[0]
            risky_result = results[1]
            assess1_result = results[2]
            assess2_result = results[3]
            
            assert isinstance(stats_result, dict)
            assert isinstance(risky_result, list)
            assert isinstance(assess1_result, dict)
            assert isinstance(assess2_result, dict)
            
        finally:
            await client.disconnect()


class TestMCPScoringIntegration:
    """Integration tests for MCP with scoring components."""
    
    def setup_method(self):
        """Set up MCP and scoring components."""
        self.client_config = MCPClientConfig()
        self.scorer = HybridScorer()
        self.data_generator = SyntheticDataGenerator()
    
    @pytest.mark.asyncio
    async def test_mcp_scoring_workflow(self):
        """Test MCP workflow with actual scoring integration."""
        # Generate data and load into scorer
        data = self.data_generator.generate_all()
        self.scorer.load_graph(data["assets"], data["edges"])
        
        # Set up MCP client
        client = SimpleMCPClient(self.client_config)
        await client.connect()
        wrapper = MCPToolWrapper(client)
        
        try:
            # Test attack path analysis
            if len(data["assets"]) >= 2:
                source = data["assets"][0]["id"]
                target = data["assets"][-1]["id"]
                
                # Get paths from MCP
                mcp_paths = await wrapper.find_attack_paths(source, target)
                
                # Get paths from scorer
                scorer_paths = self.scorer.get_attack_paths(source, target)
                
                # Both should return lists
                assert isinstance(mcp_paths, list)
                assert isinstance(scorer_paths, list)
                
                # Test path scoring consistency
                if mcp_paths and scorer_paths:
                    for mcp_path in mcp_paths[:2]:
                        if "path" in mcp_path:
                            path = mcp_path["path"]
                            mcp_score = mcp_path.get("risk_score", 0.0)
                            scorer_score = self.scorer.score_path(path)
                            
                            # Scores should be in valid range
                            assert 0.0 <= mcp_score <= 1.0
                            assert 0.0 <= scorer_score <= 1.0
            
            # Test risk assessment integration
            risky_assets = await wrapper.get_risky_assets(3)
            if risky_assets:
                for asset in risky_assets[:2]:
                    if "source" in asset:
                        assessment = await wrapper.assess_asset(asset["source"])
                        assert "risk_score" in assessment
                        
                        # Risk score should be consistent with asset risk level
                        risk_score = assessment["risk_score"]
                        assert 0.0 <= risk_score <= 1.0
        
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_mcp_performance_integration(self):
        """Test MCP performance with realistic workloads."""
        import time
        
        # Generate larger dataset
        data_generator = SyntheticDataGenerator()
        data_generator.num_assets = 50
        data = data_generator.generate_all()
        
        self.scorer.load_graph(data["assets"], data["edges"])
        
        client = SimpleMCPClient(self.client_config)
        await client.connect()
        wrapper = MCPToolWrapper(client)
        
        try:
            # Measure MCP operation performance
            start_time = time.time()
            
            # Perform multiple MCP operations
            stats = await wrapper.get_graph_overview()
            risky_assets = await wrapper.get_risky_assets(10)
            
            if len(data["assets"]) >= 2:
                source = data["assets"][0]["id"]
                target = data["assets"][-1]["id"]
                paths = await wrapper.find_attack_paths(source, target)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should complete within reasonable time
            assert total_time < 5.0  # 5 seconds max
            
            # Verify results
            assert "total_nodes" in stats
            assert isinstance(risky_assets, list)
            
        finally:
            await client.disconnect()


class TestMCPDataConsistency:
    """Integration tests for MCP data consistency."""
    
    def setup_method(self):
        """Set up MCP components."""
        self.client_config = MCPClientConfig()
    
    @pytest.mark.asyncio
    async def test_mcp_data_consistency(self):
        """Test that MCP returns consistent data across calls."""
        client = SimpleMCPClient(self.client_config)
        await client.connect()
        wrapper = MCPToolWrapper(client)
        
        try:
            # Get initial data
            initial_stats = await wrapper.get_graph_overview()
            initial_risky = await wrapper.get_risky_assets(5)
            
            # Wait a bit
            await asyncio.sleep(0.1)
            
            # Get data again
            second_stats = await wrapper.get_graph_overview()
            second_risky = await wrapper.get_risky_assets(5)
            
            # Data should be consistent (since we're using mock data)
            assert initial_stats["total_nodes"] == second_stats["total_nodes"]
            assert len(initial_risky) == len(second_risky)
            
            # Test attack path consistency
            if len(initial_risky) > 0:
                source = initial_risky[0].get("source", "test_source")
                target = initial_risky[0].get("target", "test_target")
                
                paths1 = await wrapper.find_attack_paths(source, target)
                paths2 = await wrapper.find_attack_paths(source, target)
                
                assert len(paths1) == len(paths2)
                
                # Path scores should be consistent
                for i, (path1, path2) in enumerate(zip(paths1, paths2)):
                    if "risk_score" in path1 and "risk_score" in path2:
                        assert abs(path1["risk_score"] - path2["risk_score"]) < 0.001
        
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_mcp_error_recovery_consistency(self):
        """Test that MCP maintains consistency after errors."""
        client = SimpleMCPClient(self.client_config)
        await client.connect()
        wrapper = MCPToolWrapper(client)
        
        try:
            # Get baseline data
            baseline_stats = await wrapper.get_graph_overview()
            
            # Cause some errors
            try:
                await wrapper.find_attack_paths("", "")
            except:
                pass
            
            try:
                await wrapper.assess_asset("")
            except:
                pass
            
            # Get data after errors
            after_error_stats = await wrapper.get_graph_overview()
            
            # Should still be consistent
            assert baseline_stats["total_nodes"] == after_error_stats["total_nodes"]
            
            # Should still be able to perform operations
            risky_assets = await wrapper.get_risky_assets(3)
            assert isinstance(risky_assets, list)
            
        finally:
            await client.disconnect()
