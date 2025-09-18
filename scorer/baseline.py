"""
Baseline scoring algorithms for attack path analysis.
Implements Dijkstra, PageRank, and motif-based scoring approaches.
"""
import heapq
import math
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict, deque
import networkx as nx
import structlog

logger = structlog.get_logger(__name__)


class AttackPathScorer:
    """Base class for attack path scoring algorithms."""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.node_features = {}
        self.edge_features = {}
    
    def load_graph(self, nodes: List[Dict], edges: List[Dict]):
        """Load graph data from nodes and edges."""
        # Add nodes
        for node in nodes:
            self.graph.add_node(node['id'], **node)
            self.node_features[node['id']] = node
        
        # Add edges
        for edge in edges:
            self.graph.add_edge(
                edge['source_id'], 
                edge['target_id'], 
                **edge.get('properties', {})
            )
            edge_key = (edge['source_id'], edge['target_id'])
            self.edge_features[edge_key] = edge.get('properties', {})
    
    def calculate_edge_weight(self, source: str, target: str, edge_attrs: Dict) -> float:
        """Calculate edge weight based on attack likelihood."""
        base_weight = 1.0
        
        # Exploitability factor
        exploitability = edge_attrs.get('exploitability', 0.5)
        base_weight *= (1.0 + exploitability)
        
        # Exposure factor (public vs private)
        exposure = edge_attrs.get('exposure', 0.5)
        base_weight *= (1.0 + exposure)
        
        # Privilege gain factor
        privilege_gain = edge_attrs.get('privilege_gain', 0.5)
        base_weight *= (1.0 + privilege_gain)
        
        # Recency factor (more recent = higher weight)
        recency = edge_attrs.get('recency', 0.5)
        base_weight *= (1.0 + recency)
        
        return base_weight
    
    def get_attack_paths(self, source: str, target: str, max_hops: int = 4) -> List[Dict[str, Any]]:
        """Get attack paths from source to target."""
        raise NotImplementedError


class DijkstraScorer(AttackPathScorer):
    """Dijkstra-based attack path scoring using risk-weighted shortest paths."""
    
    def get_attack_paths(self, source: str, target: str, max_hops: int = 4) -> List[Dict[str, Any]]:
        """Find shortest risk-weighted paths using Dijkstra's algorithm."""
        if source not in self.graph or target not in self.graph:
            return []
        
        # Calculate edge weights
        for u, v, data in self.graph.edges(data=True):
            weight = self.calculate_edge_weight(u, v, data)
            self.graph[u][v]['weight'] = weight
        
        try:
            # Find shortest path
            path = nx.shortest_path(self.graph, source, target, weight='weight')
            path_length = nx.shortest_path_length(self.graph, source, target, weight='weight')
            
            # Calculate path score (lower weight = higher risk)
            path_score = 1.0 / (1.0 + path_length)
            
            return [{
                'path': path,
                'score': path_score,
                'length': len(path) - 1,
                'total_weight': path_length,
                'algorithm': 'dijkstra'
            }]
        except nx.NetworkXNoPath:
            return []
    
    def get_top_k_paths(self, source: str, target: str, k: int = 5, max_hops: int = 4) -> List[Dict[str, Any]]:
        """Get top K shortest paths using Yen's algorithm."""
        if source not in self.graph or target not in self.graph:
            return []
        
        # Calculate edge weights
        for u, v, data in self.graph.edges(data=True):
            weight = self.calculate_edge_weight(u, v, data)
            self.graph[u][v]['weight'] = weight
        
        try:
            # Get top K shortest paths
            paths = list(nx.shortest_simple_paths(self.graph, source, target, weight='weight'))
            
            results = []
            for i, path in enumerate(paths[:k]):
                if len(path) - 1 > max_hops:
                    break
                
                # Calculate path weight
                path_weight = sum(
                    self.graph[path[j]][path[j+1]]['weight'] 
                    for j in range(len(path) - 1)
                )
                
                # Calculate path score
                path_score = 1.0 / (1.0 + path_weight)
                
                results.append({
                    'path': path,
                    'score': path_score,
                    'length': len(path) - 1,
                    'total_weight': path_weight,
                    'rank': i + 1,
                    'algorithm': 'dijkstra'
                })
            
            return results
        except nx.NetworkXNoPath:
            return []


class PageRankScorer(AttackPathScorer):
    """PageRank-based attack surface scoring personalized to crown jewels."""
    
    def __init__(self, alpha: float = 0.85, max_iter: int = 100):
        super().__init__()
        self.alpha = alpha
        self.max_iter = max_iter
    
    def get_attack_paths(self, source: str, target: str, max_hops: int = 4) -> List[Dict[str, Any]]:
        """Get attack paths using personalized PageRank."""
        if source not in self.graph or target not in self.graph:
            return []
        
        # Calculate personalized PageRank
        personalization = {target: 1.0}  # Personalize to target
        pagerank_scores = nx.pagerank(
            self.graph, 
            alpha=self.alpha, 
            max_iter=self.max_iter,
            personalization=personalization
        )
        
        # Find paths from source to target
        try:
            paths = list(nx.all_simple_paths(self.graph, source, target, cutoff=max_hops))
            
            results = []
            for path in paths:
                # Calculate path score based on PageRank scores
                path_score = sum(pagerank_scores.get(node, 0) for node in path)
                path_score = path_score / len(path)  # Normalize by path length
                
                results.append({
                    'path': path,
                    'score': path_score,
                    'length': len(path) - 1,
                    'pagerank_score': path_score,
                    'algorithm': 'pagerank'
                })
            
            # Sort by score descending
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:5]  # Return top 5
            
        except nx.NetworkXNoPath:
            return []


class MotifScorer(AttackPathScorer):
    """Motif-based scoring for attack pattern detection."""
    
    def __init__(self):
        super().__init__()
        self.motif_patterns = {
            'public_vuln_lateral': self._detect_public_vuln_lateral,
            'privilege_escalation': self._detect_privilege_escalation,
            'data_exfiltration': self._detect_data_exfiltration
        }
    
    def get_attack_paths(self, source: str, target: str, max_hops: int = 4) -> List[Dict[str, Any]]:
        """Get attack paths using motif-based scoring."""
        if source not in self.graph or target not in self.graph:
            return []
        
        # Find all paths from source to target
        try:
            paths = list(nx.all_simple_paths(self.graph, source, target, cutoff=max_hops))
            
            results = []
            for path in paths:
                # Calculate motif-based score
                motif_score = self._calculate_motif_score(path)
                
                # Calculate path length penalty
                length_penalty = 1.0 / (1.0 + len(path))
                
                # Combine scores
                path_score = motif_score * length_penalty
                
                results.append({
                    'path': path,
                    'score': path_score,
                    'length': len(path) - 1,
                    'motif_score': motif_score,
                    'algorithm': 'motif'
                })
            
            # Sort by score descending
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:5]  # Return top 5
            
        except nx.NetworkXNoPath:
            return []
    
    def _calculate_motif_score(self, path: List[str]) -> float:
        """Calculate motif-based score for a path."""
        total_score = 0.0
        
        for i in range(len(path) - 1):
            source = path[i]
            target = path[i + 1]
            
            # Check for motif patterns
            for pattern_name, detector in self.motif_patterns.items():
                if detector(source, target):
                    total_score += 1.0
        
        return total_score / max(1, len(path) - 1)  # Normalize by path length
    
    def _detect_public_vuln_lateral(self, source: str, target: str) -> bool:
        """Detect public-facing vulnerability to lateral movement pattern."""
        source_data = self.node_features.get(source, {})
        target_data = self.node_features.get(target, {})
        
        # Check if source is public-facing and has vulnerabilities
        is_public = source_data.get('type') == 'vm' and self._has_public_access(source)
        has_vuln = self._has_exploitable_vulnerability(source)
        is_lateral = target_data.get('type') in ['vm', 'db', 'bucket']
        
        return is_public and has_vuln and is_lateral
    
    def _detect_privilege_escalation(self, source: str, target: str) -> bool:
        """Detect privilege escalation pattern."""
        source_data = self.node_features.get(source, {})
        target_data = self.node_features.get(target, {})
        
        # Check if moving from user to role to policy
        is_privilege_escalation = (
            source_data.get('type') == 'user' and target_data.get('type') == 'role'
        ) or (
            source_data.get('type') == 'role' and target_data.get('type') == 'policy'
        )
        
        return is_privilege_escalation
    
    def _detect_data_exfiltration(self, source: str, target: str) -> bool:
        """Detect data exfiltration pattern."""
        source_data = self.node_features.get(source, {})
        target_data = self.node_features.get(target, {})
        
        # Check if moving from database to external resource
        is_data_exfiltration = (
            source_data.get('type') == 'db' and 
            target_data.get('type') in ['bucket', 'vm'] and
            target_data.get('critical', False)
        )
        
        return is_data_exfiltration
    
    def _has_public_access(self, node_id: str) -> bool:
        """Check if node has public access."""
        # Check for public security group rules
        for u, v, data in self.graph.edges(node_id, data=True):
            if data.get('type') == 'ALLOWS' and data.get('cidr') == '0.0.0.0/0':
                return True
        return False
    
    def _has_exploitable_vulnerability(self, node_id: str) -> bool:
        """Check if node has exploitable vulnerabilities."""
        # Check for vulnerabilities in connected software
        for u, v, data in self.graph.edges(node_id, data=True):
            if data.get('type') == 'RUNS':
                # Check if software has exploitable vulnerabilities
                for u2, v2, data2 in self.graph.edges(v, data=True):
                    if data2.get('type') == 'HAS_VULN' and data2.get('exploit_available', False):
                        return True
        return False


class HybridScorer(AttackPathScorer):
    """Hybrid scorer combining multiple algorithms."""
    
    def __init__(self, weights: Dict[str, float] = None):
        super().__init__()
        self.weights = weights or {
            'dijkstra': 0.4,
            'pagerank': 0.3,
            'motif': 0.3
        }
        self.dijkstra_scorer = DijkstraScorer()
        self.pagerank_scorer = PageRankScorer()
        self.motif_scorer = MotifScorer()
    
    def load_graph(self, nodes: List[Dict], edges: List[Dict]):
        """Load graph data into all scorers."""
        super().load_graph(nodes, edges)
        self.dijkstra_scorer.load_graph(nodes, edges)
        self.pagerank_scorer.load_graph(nodes, edges)
        self.motif_scorer.load_graph(nodes, edges)
    
    def get_attack_paths(self, source: str, target: str, max_hops: int = 4) -> List[Dict[str, Any]]:
        """Get attack paths using hybrid scoring."""
        # Get results from all scorers
        dijkstra_results = self.dijkstra_scorer.get_attack_paths(source, target, max_hops)
        pagerank_results = self.pagerank_scorer.get_attack_paths(source, target, max_hops)
        motif_results = self.motif_scorer.get_attack_paths(source, target, max_hops)
        
        # Combine results
        all_paths = {}
        
        # Add Dijkstra results
        for result in dijkstra_results:
            path_key = tuple(result['path'])
            if path_key not in all_paths:
                all_paths[path_key] = {
                    'path': result['path'],
                    'scores': {},
                    'length': result['length']
                }
            all_paths[path_key]['scores']['dijkstra'] = result['score']
        
        # Add PageRank results
        for result in pagerank_results:
            path_key = tuple(result['path'])
            if path_key not in all_paths:
                all_paths[path_key] = {
                    'path': result['path'],
                    'scores': {},
                    'length': result['length']
                }
            all_paths[path_key]['scores']['pagerank'] = result['score']
        
        # Add motif results
        for result in motif_results:
            path_key = tuple(result['path'])
            if path_key not in all_paths:
                all_paths[path_key] = {
                    'path': result['path'],
                    'scores': {},
                    'length': result['length']
                }
            all_paths[path_key]['scores']['motif'] = result['score']
        
        # Calculate hybrid scores
        results = []
        for path_data in all_paths.values():
            hybrid_score = 0.0
            for algorithm, weight in self.weights.items():
                if algorithm in path_data['scores']:
                    hybrid_score += weight * path_data['scores'][algorithm]
            
            results.append({
                'path': path_data['path'],
                'score': hybrid_score,
                'length': path_data['length'],
                'scores': path_data['scores'],
                'algorithm': 'hybrid'
            })
        
        # Sort by hybrid score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:5]  # Return top 5
