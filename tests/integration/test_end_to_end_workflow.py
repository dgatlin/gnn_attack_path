"""
Integration tests for end-to-end workflows.

Tests complete workflows from data generation to attack path analysis.
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

from data.generate_synthetic_data import SyntheticDataGenerator
from scorer.baseline import HybridScorer
from scorer.gnn_model import AttackPathGNN
from agent.mcp_client_simple import SimpleMCPClient, MCPClientConfig, MCPToolWrapper


class TestDataToAnalysisWorkflow:
    """Integration tests for data generation to analysis workflow."""
    
    def setup_method(self):
        """Set up test data and components."""
        self.data_generator = SyntheticDataGenerator()
        self.scorer = HybridScorer()
    
    def test_synthetic_data_generation(self):
        """Test complete synthetic data generation."""
        data = self.data_generator.generate_all()
        
        assert "assets" in data
        assert "edges" in data
        assert "vulnerabilities" in data
        assert "crown_jewels" in data
        
        assert len(data["assets"]) > 0
        assert len(data["edges"]) > 0
        assert len(data["vulnerabilities"]) > 0
        assert len(data["crown_jewels"]) > 0
    
    def test_data_to_scoring_pipeline(self):
        """Test data flows through scoring pipeline."""
        # Generate data
        data = self.data_generator.generate_all()
        
        # Load into scorer
        self.scorer.load_graph(data["assets"], data["edges"])
        
        # Test scoring
        if len(data["assets"]) >= 2:
            source = data["assets"][0]["id"]
            target = data["assets"][-1]["id"]
            
            paths = self.scorer.get_attack_paths(source, target)
            
            assert isinstance(paths, list)
            if paths:  # If paths exist
                for path in paths:
                    assert isinstance(path, list)
                    assert len(path) > 0
    
    def test_crown_jewel_identification(self):
        """Test crown jewel identification in generated data."""
        data = self.data_generator.generate_all()
        
        crown_jewels = data["crown_jewels"]
        assert len(crown_jewels) > 0
        
        # Check that crown jewels are in the assets
        asset_ids = [asset["id"] for asset in data["assets"]]
        for crown_jewel in crown_jewels:
            assert crown_jewel["asset_id"] in asset_ids
    
    def test_vulnerability_assignment(self):
        """Test vulnerability assignment to assets."""
        data = self.data_generator.generate_all()
        
        vulnerabilities = data["vulnerabilities"]
        assert len(vulnerabilities) > 0
        
        # Check that vulnerabilities have required fields
        for vuln in vulnerabilities:
            assert "cve" in vuln
            assert "cvss" in vuln
            assert "exploit_available" in vuln
            assert "description" in vuln


class TestMCPWorkflowIntegration:
    """Integration tests for MCP workflow components."""
    
    def setup_method(self):
        """Set up MCP components."""
        self.client_config = MCPClientConfig()
        self.client = SimpleMCPClient(self.client_config)
        self.wrapper = MCPToolWrapper(self.client)
    
    @pytest.mark.asyncio
    async def test_complete_mcp_workflow(self):
        """Test complete MCP workflow from connection to analysis."""
        # Connect to MCP
        await self.client.connect()
        assert self.client.connected == True
        
        # Test graph statistics
        stats = await self.wrapper.get_graph_overview()
        assert "total_nodes" in stats
        assert stats["total_nodes"] > 0
        
        # Test attack path analysis
        paths = await self.wrapper.find_attack_paths("server1", "database1")
        assert isinstance(paths, list)
        
        # Test risk assessment
        if paths:
            asset_id = paths[0]["path"][0] if paths[0]["path"] else "test_asset"
            assessment = await self.wrapper.assess_asset(asset_id)
            assert "risk_score" in assessment
        
        # Test remediation suggestions
        if paths:
            path_id = "test_path"
            suggestions = await self.wrapper.suggest_fixes(path_id, "patch")
            assert "actions" in suggestions
        
        # Disconnect
        await self.client.disconnect()
        assert self.client.connected == False
    
    @pytest.mark.asyncio
    async def test_mcp_tool_chain(self):
        """Test chaining multiple MCP tools together."""
        await self.client.connect()
        
        # Get risky assets
        risky_assets = await self.wrapper.get_risky_assets(5)
        assert len(risky_assets) > 0
        
        # For each risky asset, assess it
        for asset in risky_assets[:2]:  # Test first 2 assets
            if "path_id" in asset:
                assessment = await self.wrapper.assess_asset(asset["source"])
                assert "risk_score" in assessment
                
                # Suggest fixes
                suggestions = await self.wrapper.suggest_fixes(
                    asset["path_id"], "patch"
                )
                assert "actions" in suggestions
        
        await self.client.disconnect()
    
    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Test error recovery in MCP workflow."""
        await self.client.connect()
        
        # Test with invalid parameters
        try:
            result = await self.wrapper.find_attack_paths("", "")
            # Should handle gracefully
            assert isinstance(result, list)
        except Exception as e:
            # Should not crash the client
            assert "error" in str(e).lower() or "invalid" in str(e).lower()
        
        # Client should still be connected
        assert self.client.connected == True
        
        # Should be able to make valid calls after error
        stats = await self.wrapper.get_graph_overview()
        assert "total_nodes" in stats
        
        await self.client.disconnect()


class TestScoringPipelineIntegration:
    """Integration tests for scoring pipeline components."""
    
    def setup_method(self):
        """Set up scoring components."""
        self.data_generator = SyntheticDataGenerator()
        self.hybrid_scorer = HybridScorer()
    
    def test_hybrid_scoring_pipeline(self):
        """Test hybrid scoring with real data."""
        # Generate realistic data
        data = self.data_generator.generate_all()
        
        # Load into hybrid scorer
        self.hybrid_scorer.load_graph(data["assets"], data["edges"])
        
        # Test scoring with different algorithms
        if len(data["assets"]) >= 2:
            source = data["assets"][0]["id"]
            target = data["assets"][-1]["id"]
            
            # Get paths using hybrid scoring
            paths = self.hybrid_scorer.get_attack_paths(source, target)
            
            if paths:
                # Test individual path scoring
                for path in paths[:3]:  # Test first 3 paths
                    score = self.hybrid_scorer.score_path(path)
                    assert isinstance(score, float)
                    assert 0.0 <= score <= 1.0
    
    def test_scoring_consistency(self):
        """Test that scoring is consistent across multiple runs."""
        data = self.data_generator.generate_all()
        self.hybrid_scorer.load_graph(data["assets"], data["edges"])
        
        if len(data["assets"]) >= 2:
            source = data["assets"][0]["id"]
            target = data["assets"][-1]["id"]
            
            # Run scoring multiple times
            results = []
            for _ in range(3):
                paths = self.hybrid_scorer.get_attack_paths(source, target)
                results.append(len(paths))
            
            # Results should be consistent
            assert all(r == results[0] for r in results)
    
    def test_large_dataset_handling(self):
        """Test handling of larger datasets."""
        # Generate larger dataset
        data_generator = SyntheticDataGenerator()
        data_generator.num_assets = 100
        data_generator.num_vulnerabilities = 50
        
        data = data_generator.generate_all()
        
        # Should handle larger datasets
        assert len(data["assets"]) >= 50  # At least half of requested
        assert len(data["edges"]) > 0
        
        # Load into scorer
        self.hybrid_scorer.load_graph(data["assets"], data["edges"])
        
        # Should be able to score paths
        if len(data["assets"]) >= 2:
            source = data["assets"][0]["id"]
            target = data["assets"][-1]["id"]
            
            paths = self.hybrid_scorer.get_attack_paths(source, target)
            assert isinstance(paths, list)


class TestPerformanceIntegration:
    """Integration tests for performance characteristics."""
    
    def setup_method(self):
        """Set up performance test components."""
        self.data_generator = SyntheticDataGenerator()
        self.scorer = HybridScorer()
    
    def test_scoring_performance(self):
        """Test scoring performance with realistic data."""
        import time
        
        # Generate data
        data = self.data_generator.generate_all()
        self.scorer.load_graph(data["assets"], data["edges"])
        
        if len(data["assets"]) >= 2:
            source = data["assets"][0]["id"]
            target = data["assets"][-1]["id"]
            
            # Measure scoring time
            start_time = time.time()
            paths = self.scorer.get_attack_paths(source, target)
            end_time = time.time()
            
            scoring_time = end_time - start_time
            
            # Should complete within reasonable time (2 seconds)
            assert scoring_time < 2.0
            
            # Should find some paths if they exist
            assert isinstance(paths, list)
    
    def test_memory_usage(self):
        """Test memory usage with larger datasets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Generate larger dataset
        data_generator = SyntheticDataGenerator()
        data_generator.num_assets = 200
        data = data_generator.generate_all()
        
        # Load into scorer
        self.scorer.load_graph(data["assets"], data["edges"])
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024  # 100MB in bytes
    
    def test_concurrent_scoring(self):
        """Test concurrent scoring operations."""
        import threading
        import time
        
        data = self.data_generator.generate_all()
        self.scorer.load_graph(data["assets"], data["edges"])
        
        if len(data["assets"]) >= 4:
            results = []
            errors = []
            
            def score_paths(source, target):
                try:
                    paths = self.scorer.get_attack_paths(source, target)
                    results.append((source, target, len(paths)))
                except Exception as e:
                    errors.append(str(e))
            
            # Start multiple scoring threads
            threads = []
            for i in range(3):
                source = data["assets"][i]["id"]
                target = data["assets"][i + 1]["id"]
                thread = threading.Thread(target=score_paths, args=(source, target))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Should complete without errors
            assert len(errors) == 0
            assert len(results) == 3
