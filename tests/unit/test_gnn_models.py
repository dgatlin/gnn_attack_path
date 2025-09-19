"""
Unit tests for Graph Neural Network models.

Tests GNN model components in isolation with mocked dependencies.
"""
import pytest
import torch
import numpy as np
from unittest.mock import Mock, patch
from typing import Dict, List, Any

from scorer.gnn_model import EdgeEncoder, AttackPathGNN


class TestEdgeEncoder:
    """Unit tests for EdgeEncoder component."""
    
    def setup_method(self):
        """Set up test data."""
        self.node_dim = 20
        self.edge_dim = 10
        self.hidden_dim = 64
        self.encoder = EdgeEncoder(self.node_dim, self.edge_dim, self.hidden_dim)
    
    def test_edge_encoder_initialization(self):
        """Test EdgeEncoder initializes correctly."""
        assert self.encoder.node_encoder is not None
        assert self.encoder.edge_encoder is not None
        assert self.encoder.dropout is not None
    
    def test_forward_pass(self):
        """Test forward pass through EdgeEncoder."""
        batch_size = 5
        node_features = torch.randn(batch_size, self.node_dim)
        edge_features = torch.randn(batch_size, self.edge_dim)
        
        node_output, edge_output = self.encoder(node_features, edge_features)
        
        assert node_output.shape == (batch_size, self.hidden_dim)
        assert edge_output.shape == (batch_size, self.hidden_dim)
        assert not torch.isnan(node_output).any()
        assert not torch.isnan(edge_output).any()
        assert not torch.isinf(node_output).any()
        assert not torch.isinf(edge_output).any()
    
    def test_different_input_sizes(self):
        """Test EdgeEncoder with different input sizes."""
        for batch_size in [1, 10, 100]:
            node_features = torch.randn(batch_size, self.node_dim)
            edge_features = torch.randn(batch_size, self.edge_dim)
            node_output, edge_output = self.encoder(node_features, edge_features)
            assert node_output.shape == (batch_size, self.hidden_dim)
            assert edge_output.shape == (batch_size, self.hidden_dim)
    
    def test_gradient_flow(self):
        """Test that gradients flow through EdgeEncoder."""
        node_features = torch.randn(5, self.node_dim, requires_grad=True)
        edge_features = torch.randn(5, self.edge_dim, requires_grad=True)
        node_output, edge_output = self.encoder(node_features, edge_features)
        loss = node_output.sum() + edge_output.sum()
        loss.backward()
        
        assert node_features.grad is not None
        assert edge_features.grad is not None
        assert not torch.isnan(node_features.grad).any()
        assert not torch.isnan(edge_features.grad).any()


class TestAttackPathGNN:
    """Unit tests for AttackPathGNN model."""
    
    def setup_method(self):
        """Set up test data."""
        self.model_type = 'graphsage'
        self.device = 'cpu'
        self.model = AttackPathGNN(
            model_type=self.model_type,
            device=self.device
        )
    
    def test_gnn_initialization(self):
        """Test AttackPathGNN initializes correctly."""
        assert self.model.model_type == self.model_type
        assert self.model.device == torch.device(self.device)
        assert self.model.model is None  # Model is created when needed
        assert self.model.node_features == {}
        assert self.model.edge_features == {}
        assert self.model.node_mapping == {}
        assert self.model.edge_mapping == {}
    
    def test_prepare_data(self):
        """Test data preparation for AttackPathGNN."""
        sample_nodes = [
            {"id": "node1", "type": "server", "critical": False},
            {"id": "node2", "type": "database", "critical": True},
        ]
        
        sample_edges = [
            {"source_id": "node1", "target_id": "node2", "type": "CONNECTS_TO"},
        ]
        
        data = self.model.prepare_data(sample_nodes, sample_edges)
        
        assert data is not None
        assert hasattr(data, 'x')
        assert hasattr(data, 'edge_index')
        assert hasattr(data, 'edge_attr')
    
    def test_model_creation(self):
        """Test model creation with different types."""
        # Test GraphSAGE model
        model_sage = AttackPathGNN(model_type='graphsage')
        assert model_sage.model_type == 'graphsage'
        
        # Test GAT model
        model_gat = AttackPathGNN(model_type='gat')
        assert model_gat.model_type == 'gat'
    
    def test_device_handling(self):
        """Test model handles different devices correctly."""
        # Test CPU device
        model_cpu = AttackPathGNN(device='cpu')
        assert model_cpu.device == torch.device('cpu')
        
        # Test CUDA device if available
        if torch.cuda.is_available():
            model_cuda = AttackPathGNN(device='cuda')
            assert model_cuda.device == torch.device('cuda')
    
    def test_data_preparation_with_larger_dataset(self):
        """Test data preparation with larger dataset."""
        # Generate more complex data
        nodes = []
        edges = []
        
        for i in range(10):
            nodes.append({
                "id": f"node{i}",
                "type": "server" if i % 2 == 0 else "database",
                "critical": i % 3 == 0
            })
        
        for i in range(15):
            source = f"node{i % 10}"
            target = f"node{(i + 1) % 10}"
            edges.append({
                "source_id": source,
                "target_id": target,
                "type": "CONNECTS_TO"
            })
        
        data = self.model.prepare_data(nodes, edges)
        
        assert data is not None
        assert data.x.shape[0] == 10  # 10 nodes
        assert data.edge_index.shape[1] == 15  # 15 edges
