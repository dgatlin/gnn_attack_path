"""
Unit tests for baseline scoring algorithms.

Tests individual scoring algorithms in isolation with mocked dependencies.
"""
import pytest
import networkx as nx
from unittest.mock import Mock, patch
from typing import Dict, List, Any

from scorer.baseline import DijkstraScorer, PageRankScorer, MotifScorer, HybridScorer


class TestDijkstraScorer:
    """Unit tests for Dijkstra-based attack path scoring."""
    
    def setup_method(self):
        """Set up test data for each test."""
        self.scorer = DijkstraScorer()
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
    
    def test_dijkstra_scorer_initialization(self):
        """Test Dijkstra scorer initializes correctly."""
        assert isinstance(self.scorer.graph, nx.DiGraph)
        assert self.scorer.node_features == {}
        assert self.scorer.edge_features == {}
    
    def test_load_graph(self):
        """Test graph loading functionality."""
        self.scorer.load_graph(self.sample_nodes, self.sample_edges)
        
        assert self.scorer.graph is not None
        assert len(self.scorer.graph.nodes) == 4
        assert len(self.scorer.graph.edges) == 2
        assert len(self.scorer.node_features) == 4
        assert len(self.scorer.edge_features) == 2
    
    def test_get_attack_paths(self):
        """Test attack path finding."""
        self.scorer.load_graph(self.sample_nodes, self.sample_edges)
        
        paths = self.scorer.get_attack_paths("vm1", "db1", max_hops=3)
        
        assert isinstance(paths, list)
        assert len(paths) > 0
        # Check that paths contain dictionaries with expected structure
        for path in paths:
            assert isinstance(path, dict)
            assert "path" in path
            assert "score" in path  # The actual field name is "score", not "risk_score"
            assert isinstance(path["path"], list)
    
    def test_get_top_k_paths(self):
        """Test getting top K paths."""
        self.scorer.load_graph(self.sample_nodes, self.sample_edges)
        
        paths = self.scorer.get_top_k_paths("vm1", "db1", k=3, max_hops=3)
        
        assert isinstance(paths, list)
        assert len(paths) <= 3
        if paths:
            for path in paths:
                assert isinstance(path, dict)
                assert "path" in path
                assert "score" in path  # The actual field name is "score"
    
    def test_empty_graph(self):
        """Test behavior with empty graph."""
        scorer = DijkstraScorer()
        scorer.load_graph([], [])
        
        paths = scorer.get_attack_paths("source", "target")
        assert paths == []
    
    def test_no_path_exists(self):
        """Test behavior when no path exists."""
        self.scorer.load_graph(self.sample_nodes, self.sample_edges)
        
        paths = self.scorer.get_attack_paths("vm1", "nonexistent")
        assert paths == []


class TestPageRankScorer:
    """Unit tests for PageRank-based scoring."""
    
    def setup_method(self):
        """Set up test data."""
        self.scorer = PageRankScorer()
        self.sample_nodes = [
            {"id": "node1", "type": "server", "critical": False},
            {"id": "node2", "type": "database", "critical": True},
            {"id": "node3", "type": "proxy", "critical": False},
        ]
        
        self.sample_edges = [
            {"source_id": "node1", "target_id": "node2", "type": "CONNECTS_TO"},
            {"source_id": "node2", "target_id": "node3", "type": "CONNECTS_TO"},
        ]
    
    def test_pagerank_scorer_initialization(self):
        """Test PageRank scorer initializes correctly."""
        assert isinstance(self.scorer.graph, nx.DiGraph)
        assert self.scorer.node_features == {}
        assert self.scorer.edge_features == {}
        assert self.scorer.alpha == 0.85
        assert self.scorer.max_iter == 100
    
    def test_load_graph(self):
        """Test graph loading."""
        self.scorer.load_graph(self.sample_nodes, self.sample_edges)
        
        assert self.scorer.graph is not None
        assert len(self.scorer.graph.nodes) == 3
        assert len(self.scorer.node_features) == 3
    
    def test_get_attack_paths(self):
        """Test attack path finding with PageRank."""
        self.scorer.load_graph(self.sample_nodes, self.sample_edges)
        
        paths = self.scorer.get_attack_paths("node1", "node2")
        
        assert isinstance(paths, list)
        if paths:
            for path in paths:
                assert isinstance(path, dict)
                assert "path" in path
                assert "score" in path  # The actual field name is "score"


class TestMotifScorer:
    """Unit tests for motif-based scoring."""
    
    def setup_method(self):
        """Set up test data."""
        self.scorer = MotifScorer()
        self.sample_nodes = [
            {"id": "web1", "type": "web", "critical": False},
            {"id": "app1", "type": "app", "critical": False},
            {"id": "db1", "type": "db", "critical": True},
        ]
        
        self.sample_edges = [
            {"source_id": "web1", "target_id": "app1", "type": "CONNECTS_TO"},
            {"source_id": "app1", "target_id": "db1", "type": "CONNECTS_TO"},
        ]
    
    def test_motif_scorer_initialization(self):
        """Test Motif scorer initializes correctly."""
        assert isinstance(self.scorer.graph, nx.DiGraph)
        assert self.scorer.node_features == {}
        assert self.scorer.edge_features == {}
        assert hasattr(self.scorer, 'motif_patterns')
    
    def test_load_graph(self):
        """Test graph loading."""
        self.scorer.load_graph(self.sample_nodes, self.sample_edges)
        
        assert self.scorer.graph is not None
        assert len(self.scorer.graph.nodes) == 3
        assert len(self.scorer.node_features) == 3
    
    def test_get_attack_paths(self):
        """Test attack path finding with motifs."""
        self.scorer.load_graph(self.sample_nodes, self.sample_edges)
        
        paths = self.scorer.get_attack_paths("web1", "db1")
        
        assert isinstance(paths, list)
        if paths:
            for path in paths:
                assert isinstance(path, dict)
                assert "path" in path
                assert "score" in path  # The actual field name is "score"


class TestHybridScorer:
    """Unit tests for hybrid scoring algorithm."""
    
    def setup_method(self):
        """Set up test data."""
        self.scorer = HybridScorer()
        self.sample_nodes = [
            {"id": "server1", "type": "server", "critical": False},
            {"id": "database1", "type": "database", "critical": True},
        ]
        
        self.sample_edges = [
            {"source_id": "server1", "target_id": "database1", "type": "CONNECTS_TO"},
        ]
    
    def test_hybrid_scorer_initialization(self):
        """Test Hybrid scorer initializes correctly."""
        assert isinstance(self.scorer.graph, nx.DiGraph)
        assert self.scorer.node_features == {}
        assert self.scorer.edge_features == {}
        assert hasattr(self.scorer, 'weights')
        assert self.scorer.weights is not None
    
    def test_load_graph(self):
        """Test graph loading delegates to base class."""
        self.scorer.load_graph(self.sample_nodes, self.sample_edges)
        
        assert self.scorer.graph is not None
        assert len(self.scorer.graph.nodes) == 2
        assert len(self.scorer.node_features) == 2
    
    def test_get_attack_paths(self):
        """Test hybrid attack path finding."""
        self.scorer.load_graph(self.sample_nodes, self.sample_edges)
        
        paths = self.scorer.get_attack_paths("server1", "database1")
        
        assert isinstance(paths, list)
        if paths:
            for path in paths:
                assert isinstance(path, dict)
                assert "path" in path
                assert "score" in path  # The actual field name is "score"
    
    def test_custom_weights(self):
        """Test custom weight configuration."""
        custom_weights = {"dijkstra": 0.5, "pagerank": 0.3, "motif": 0.2}
        scorer = HybridScorer(weights=custom_weights)
        
        assert scorer.weights == custom_weights


class TestScorerIntegration:
    """Integration tests for scorer components."""
    
    def test_scorer_with_real_data(self):
        """Test scorers with realistic data."""
        from data.generate_synthetic_data import SyntheticDataGenerator
        
        # Generate realistic data
        generator = SyntheticDataGenerator()
        data = generator.generate_all()
        
        # Test each scorer
        scorers = [DijkstraScorer(), PageRankScorer(), MotifScorer(), HybridScorer()]
        
        for scorer in scorers:
            scorer.load_graph(data["assets"], data["relationships"])
            
            if len(data["assets"]) >= 2:
                source = data["assets"][0]["id"]
                target = data["assets"][-1]["id"]
                
                paths = scorer.get_attack_paths(source, target)
                assert isinstance(paths, list)
    
    def test_scorer_performance(self):
        """Test scorer performance with larger datasets."""
        import time
        
        from data.generate_synthetic_data import SyntheticDataGenerator
        
        # Generate larger dataset
        generator = SyntheticDataGenerator()
        generator.generate_assets(count=100)
        generator.generate_software(count=20)
        data = generator.generate_all()
        
        scorer = HybridScorer()
        scorer.load_graph(data["assets"], data["relationships"])
        
        if len(data["assets"]) >= 2:
            source = data["assets"][0]["id"]
            target = data["assets"][-1]["id"]
            
            # Measure performance
            start_time = time.time()
            paths = scorer.get_attack_paths(source, target)
            end_time = time.time()
            
            # Should complete within reasonable time
            assert (end_time - start_time) < 5.0
            assert isinstance(paths, list)