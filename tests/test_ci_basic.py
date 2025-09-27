"""
Basic CI tests that don't require agent dependencies.
These tests focus on core functionality without langchain/mcp imports.
"""
import pytest
import numpy as np
import networkx as nx
from unittest.mock import Mock, patch
import tempfile
import os


class TestBasicFunctionality:
    """Test basic functionality without external dependencies."""
    
    def test_basic_imports(self):
        """Test that basic imports work."""
        import numpy as np
        import networkx as nx
        import torch
        from sklearn.ensemble import RandomForestClassifier
        
        assert np is not None
        assert nx is not None
        assert torch is not None
        assert RandomForestClassifier is not None
    
    def test_numpy_operations(self):
        """Test basic numpy operations."""
        arr = np.array([1, 2, 3, 4, 5])
        assert arr.sum() == 15
        assert arr.mean() == 3.0
        assert arr.max() == 5
    
    def test_networkx_basic(self):
        """Test basic NetworkX operations."""
        G = nx.Graph()
        G.add_edge(1, 2)
        G.add_edge(2, 3)
        
        assert len(G.nodes()) == 3
        assert len(G.edges()) == 2
        assert nx.has_path(G, 1, 3)
    
    def test_scikit_learn_basic(self):
        """Test basic scikit-learn functionality."""
        from sklearn.datasets import make_classification
        from sklearn.model_selection import train_test_split
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import accuracy_score
        
        # Generate sample data
        X, y = make_classification(n_samples=100, n_features=4, random_state=42)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train a simple model
        clf = RandomForestClassifier(n_estimators=10, random_state=42)
        clf.fit(X_train, y_train)
        
        # Make predictions
        y_pred = clf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        assert accuracy > 0.5  # Should be better than random
    
    def test_pytorch_basic(self):
        """Test basic PyTorch functionality."""
        import torch
        import torch.nn as nn
        
        # Create a simple tensor
        x = torch.randn(5, 3)
        assert x.shape == (5, 3)
        
        # Test basic operations
        y = torch.sum(x, dim=1)
        assert y.shape == (5,)
        
        # Test simple neural network
        model = nn.Linear(3, 1)
        output = model(x)
        assert output.shape == (5, 1)
    
    def test_file_operations(self):
        """Test basic file operations."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_file = f.name
        
        try:
            assert os.path.exists(temp_file)
            with open(temp_file, 'r') as f:
                content = f.read()
            assert content == "test content"
        finally:
            os.unlink(temp_file)


class TestMockDataGeneration:
    """Test mock data generation without external dependencies."""
    
    def test_generate_mock_graph(self):
        """Test generating a mock graph."""
        G = nx.Graph()
        
        # Add nodes
        nodes = ['server1', 'server2', 'database', 'web_app']
        for node in nodes:
            G.add_node(node)
        
        # Add edges
        edges = [
            ('server1', 'web_app'),
            ('server2', 'web_app'),
            ('web_app', 'database')
        ]
        G.add_edges_from(edges)
        
        assert len(G.nodes()) == 4
        assert len(G.edges()) == 3
        assert nx.is_connected(G)
    
    def test_generate_mock_attack_paths(self):
        """Test generating mock attack paths."""
        paths = [
            ['external', 'server1', 'web_app', 'database'],
            ['external', 'server2', 'web_app', 'database'],
            ['external', 'web_app', 'database']
        ]
        
        assert len(paths) == 3
        for path in paths:
            assert isinstance(path, list)
            assert len(path) >= 2
            assert path[0] == 'external'
            assert path[-1] == 'database'
    
    def test_mock_scoring(self):
        """Test mock scoring functionality."""
        # Mock scoring function
        def score_path(path):
            return len(path) * 0.2  # Simple scoring based on path length
        
        paths = [
            ['external', 'web_app', 'database'],
            ['external', 'server1', 'web_app', 'database']
        ]
        
        scores = [score_path(path) for path in paths]
        
        assert len(scores) == 2
        assert abs(scores[0] - 0.6) < 0.001  # 3 * 0.2
        assert abs(scores[1] - 0.8) < 0.001  # 4 * 0.2
        assert scores[1] > scores[0]  # Longer path should have higher score


class TestAPIStructure:
    """Test API structure without starting the server."""
    
    def test_fastapi_imports(self):
        """Test that FastAPI can be imported."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        assert FastAPI is not None
        assert TestClient is not None
    
    def test_api_structure(self):
        """Test basic API structure."""
        # Test that we can create a basic FastAPI app
        from fastapi import FastAPI
        app = FastAPI()
        
        @app.get("/test")
        def test_endpoint():
            return {"message": "test"}
        
        assert app is not None
        
        # Test basic FastAPI functionality without TestClient
        routes = [route.path for route in app.routes]
        assert "/test" in routes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
