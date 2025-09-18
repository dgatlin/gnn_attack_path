"""
Graph Neural Network models for attack path scoring using PyTorch Geometric.
Implements GraphSAGE and GAT-based models for edge likelihood prediction.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv, SAGEConv, global_mean_pool
from torch_geometric.data import Data, DataLoader
from torch_geometric.utils import to_networkx
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import structlog

logger = structlog.get_logger(__name__)


class EdgeEncoder(nn.Module):
    """Encodes node and edge features for GNN input."""
    
    def __init__(self, node_dim: int, edge_dim: int, hidden_dim: int):
        super().__init__()
        self.node_encoder = nn.Linear(node_dim, hidden_dim)
        self.edge_encoder = nn.Linear(edge_dim, hidden_dim)
        self.dropout = nn.Dropout(0.1)
        
    def forward(self, x: torch.Tensor, edge_attr: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Encode node and edge features."""
        x_encoded = F.relu(self.node_encoder(x))
        edge_encoded = F.relu(self.edge_encoder(edge_attr))
        
        x_encoded = self.dropout(x_encoded)
        edge_encoded = self.dropout(edge_encoded)
        
        return x_encoded, edge_encoded


class GraphSAGEModel(nn.Module):
    """GraphSAGE-based model for attack path scoring."""
    
    def __init__(self, node_dim: int, edge_dim: int, hidden_dim: int = 64, 
                 num_layers: int = 2, dropout: float = 0.1):
        super().__init__()
        self.encoder = EdgeEncoder(node_dim, edge_dim, hidden_dim)
        
        # GraphSAGE layers
        self.convs = nn.ModuleList()
        for i in range(num_layers):
            in_channels = hidden_dim if i == 0 else hidden_dim
            self.convs.append(SAGEConv(in_channels, hidden_dim))
        
        # Edge scoring head
        self.edge_head = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1)
        )
        
        # Path scoring head
        self.path_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1)
        )
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, 
                edge_attr: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass through the model."""
        # Encode features
        x, edge_attr = self.encoder(x, edge_attr)
        
        # Apply GraphSAGE layers
        for conv in self.convs:
            x = F.relu(conv(x, edge_index))
            x = self.dropout(x)
        
        # Calculate edge scores
        src, dst = edge_index
        edge_features = torch.cat([x[src], x[dst]], dim=1)
        edge_scores = torch.sigmoid(self.edge_head(edge_features)).squeeze(-1)
        
        # Calculate path scores (mean of edge scores)
        path_scores = self._calculate_path_scores(edge_index, edge_scores)
        
        return {
            'edge_scores': edge_scores,
            'path_scores': path_scores,
            'node_embeddings': x
        }
    
    def _calculate_path_scores(self, edge_index: torch.Tensor, 
                              edge_scores: torch.Tensor) -> torch.Tensor:
        """Calculate path scores from edge scores."""
        # Simple aggregation - can be enhanced with more sophisticated methods
        return edge_scores.mean()


class GATModel(nn.Module):
    """Graph Attention Network-based model for attack path scoring."""
    
    def __init__(self, node_dim: int, edge_dim: int, hidden_dim: int = 64,
                 num_layers: int = 2, num_heads: int = 4, dropout: float = 0.1):
        super().__init__()
        self.encoder = EdgeEncoder(node_dim, edge_dim, hidden_dim)
        
        # GAT layers
        self.convs = nn.ModuleList()
        for i in range(num_layers):
            in_channels = hidden_dim if i == 0 else hidden_dim * num_heads
            self.convs.append(GATConv(in_channels, hidden_dim, heads=num_heads,
                                    dropout=dropout, edge_dim=hidden_dim))
        
        # Edge scoring head
        self.edge_head = nn.Sequential(
            nn.Linear(hidden_dim * num_heads * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1)
        )
        
        # Path scoring head
        self.path_head = nn.Sequential(
            nn.Linear(hidden_dim * num_heads, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1)
        )
        
        self.dropout = nn.Dropout(dropout)
        self.num_heads = num_heads
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor,
                edge_attr: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass through the model."""
        # Encode features
        x, edge_attr = self.encoder(x, edge_attr)
        
        # Apply GAT layers
        for conv in self.convs:
            x = F.relu(conv(x, edge_index, edge_attr))
            x = self.dropout(x)
        
        # Calculate edge scores
        src, dst = edge_index
        edge_features = torch.cat([x[src], x[dst]], dim=1)
        edge_scores = torch.sigmoid(self.edge_head(edge_features)).squeeze(-1)
        
        # Calculate path scores
        path_scores = self._calculate_path_scores(edge_index, edge_scores)
        
        return {
            'edge_scores': edge_scores,
            'path_scores': path_scores,
            'node_embeddings': x
        }
    
    def _calculate_path_scores(self, edge_index: torch.Tensor,
                              edge_scores: torch.Tensor) -> torch.Tensor:
        """Calculate path scores from edge scores."""
        return edge_scores.mean()


class AttackPathGNN:
    """Main GNN class for attack path scoring."""
    
    def __init__(self, model_type: str = 'graphsage', device: str = 'cpu'):
        self.device = torch.device(device)
        self.model_type = model_type
        self.model = None
        self.node_features = {}
        self.edge_features = {}
        self.node_mapping = {}
        self.edge_mapping = {}
        
    def prepare_data(self, nodes: List[Dict], edges: List[Dict]) -> Data:
        """Prepare PyTorch Geometric data from nodes and edges."""
        # Create node mapping
        node_ids = list(set([n['id'] for n in nodes]))
        self.node_mapping = {node_id: idx for idx, node_id in enumerate(node_ids)}
        
        # Prepare node features
        node_features = []
        for node in nodes:
            features = self._extract_node_features(node)
            node_features.append(features)
        
        x = torch.tensor(node_features, dtype=torch.float32)
        
        # Prepare edge indices and features
        edge_indices = []
        edge_features = []
        
        for edge in edges:
            source_idx = self.node_mapping.get(edge['source_id'])
            target_idx = self.node_mapping.get(edge['target_id'])
            
            if source_idx is not None and target_idx is not None:
                edge_indices.append([source_idx, target_idx])
                features = self._extract_edge_features(edge)
                edge_features.append(features)
        
        edge_index = torch.tensor(edge_indices, dtype=torch.long).t().contiguous()
        edge_attr = torch.tensor(edge_features, dtype=torch.float32)
        
        return Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
    
    def _extract_node_features(self, node: Dict) -> List[float]:
        """Extract numerical features from node data."""
        features = []
        
        # Node type (one-hot encoded)
        node_types = ['vm', 'db', 'bucket', 'sg', 'subnet', 'user', 'role', 'policy', 'ci_job', 'vpn', 'domain']
        type_vector = [1.0 if node.get('type') == t else 0.0 for t in node_types]
        features.extend(type_vector)
        
        # Critical flag
        features.append(1.0 if node.get('critical', False) else 0.0)
        
        # Environment (one-hot encoded)
        environments = ['production', 'staging', 'development', 'testing']
        env_vector = [1.0 if node.get('environment') == env else 0.0 for env in environments]
        features.extend(env_vector)
        
        # Status (one-hot encoded)
        statuses = ['active', 'inactive', 'maintenance']
        status_vector = [1.0 if node.get('status') == status else 0.0 for status in statuses]
        features.extend(status_vector)
        
        # IP address (simplified)
        ip = node.get('ip_address', '0.0.0.0')
        ip_parts = ip.split('.')
        if len(ip_parts) == 4:
            features.extend([float(part) / 255.0 for part in ip_parts])
        else:
            features.extend([0.0, 0.0, 0.0, 0.0])
        
        return features
    
    def _extract_edge_features(self, edge: Dict) -> List[float]:
        """Extract numerical features from edge data."""
        features = []
        props = edge.get('properties', {})
        
        # Protocol (one-hot encoded)
        protocols = ['tcp', 'udp', 'icmp', 'http', 'https']
        protocol_vector = [1.0 if props.get('protocol') == p else 0.0 for p in protocols]
        features.extend(protocol_vector)
        
        # Port (normalized)
        port = props.get('port', 0)
        features.append(min(port / 65535.0, 1.0))
        
        # Encrypted flag
        features.append(1.0 if props.get('encrypted', False) else 0.0)
        
        # Direction
        features.append(1.0 if props.get('direction') == 'ingress' else 0.0)
        
        # CIDR (public vs private)
        cidr = props.get('cidr', '')
        features.append(1.0 if cidr == '0.0.0.0/0' else 0.0)
        
        # Exploitability
        features.append(props.get('exploitability', 0.5))
        
        # Exposure
        features.append(props.get('exposure', 0.5))
        
        # Privilege gain
        features.append(props.get('privilege_gain', 0.5))
        
        # Recency
        features.append(props.get('recency', 0.5))
        
        return features
    
    def build_model(self, node_dim: int, edge_dim: int, **kwargs):
        """Build the GNN model."""
        if self.model_type == 'graphsage':
            self.model = GraphSAGEModel(node_dim, edge_dim, **kwargs)
        elif self.model_type == 'gat':
            self.model = GATModel(node_dim, edge_dim, **kwargs)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        self.model = self.model.to(self.device)
        logger.info(f"Built {self.model_type} model", 
                   node_dim=node_dim, edge_dim=edge_dim)
    
    def train(self, data: Data, epochs: int = 100, lr: float = 0.001):
        """Train the GNN model."""
        if self.model is None:
            raise RuntimeError("Model not built. Call build_model() first.")
        
        data = data.to(self.device)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.BCELoss()
        
        self.model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            
            # Forward pass
            output = self.model(data.x, data.edge_index, data.edge_attr)
            
            # Create dummy labels for training (in practice, these would be real labels)
            edge_labels = torch.ones(data.edge_index.size(1), device=self.device)
            
            # Calculate loss
            loss = criterion(output['edge_scores'], edge_labels)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}, Loss: {loss.item():.4f}")
    
    def predict_attack_paths(self, data: Data, source: str, target: str, 
                           max_hops: int = 4) -> List[Dict[str, Any]]:
        """Predict attack paths using the trained model."""
        if self.model is None:
            raise RuntimeError("Model not trained. Call train() first.")
        
        self.model.eval()
        data = data.to(self.device)
        
        with torch.no_grad():
            output = self.model(data.x, data.edge_index, data.edge_attr)
            edge_scores = output['edge_scores'].cpu().numpy()
        
        # Find paths from source to target
        source_idx = self.node_mapping.get(source)
        target_idx = self.node_mapping.get(target)
        
        if source_idx is None or target_idx is None:
            return []
        
        # Use edge scores to find high-probability paths
        paths = self._find_paths_with_scores(data, source_idx, target_idx, 
                                           edge_scores, max_hops)
        
        return paths
    
    def _find_paths_with_scores(self, data: Data, source_idx: int, target_idx: int,
                               edge_scores: np.ndarray, max_hops: int) -> List[Dict[str, Any]]:
        """Find paths using edge scores as weights."""
        # Convert to NetworkX for path finding
        import networkx as nx
        
        G = nx.DiGraph()
        
        # Add edges with scores as weights
        for i, (src, dst) in enumerate(data.edge_index.t().cpu().numpy()):
            G.add_edge(src, dst, weight=edge_scores[i])
        
        # Find shortest paths using edge scores as weights
        try:
            paths = list(nx.shortest_simple_paths(G, source_idx, target_idx, weight='weight'))
            
            results = []
            for i, path in enumerate(paths[:5]):  # Top 5 paths
                if len(path) - 1 > max_hops:
                    break
                
                # Calculate path score
                path_score = 0.0
                for j in range(len(path) - 1):
                    edge_score = G[path[j]][path[j+1]]['weight']
                    path_score += edge_score
                
                path_score = path_score / (len(path) - 1)  # Normalize by path length
                
                # Convert back to node IDs
                node_ids = [list(self.node_mapping.keys())[list(self.node_mapping.values()).index(idx)] 
                           for idx in path]
                
                results.append({
                    'path': node_ids,
                    'score': float(path_score),
                    'length': len(path) - 1,
                    'algorithm': f'gnn_{self.model_type}'
                })
            
            return results
            
        except nx.NetworkXNoPath:
            return []
    
    def save_model(self, path: str):
        """Save the trained model."""
        if self.model is None:
            raise RuntimeError("No model to save")
        
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'model_type': self.model_type,
            'node_mapping': self.node_mapping,
            'edge_mapping': self.edge_mapping
        }, path)
        
        logger.info("Model saved", path=path)
    
    def load_model(self, path: str):
        """Load a trained model."""
        checkpoint = torch.load(path, map_location=self.device)
        
        self.model_type = checkpoint['model_type']
        self.node_mapping = checkpoint['node_mapping']
        self.edge_mapping = checkpoint['edge_mapping']
        
        # Rebuild model (assumes same architecture)
        node_dim = len(self._extract_node_features({'id': 'dummy', 'type': 'vm'}))
        edge_dim = len(self._extract_edge_features({'properties': {}}))
        
        self.build_model(node_dim, edge_dim)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        
        logger.info("Model loaded", path=path)
