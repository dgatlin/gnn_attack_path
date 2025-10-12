"""
Scoring service that combines baseline and GNN approaches for attack path analysis.
Provides a unified interface for all scoring algorithms.
"""
import os
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import torch
import structlog

from .baseline import DijkstraScorer, PageRankScorer, MotifScorer, HybridScorer
from .gnn_model import AttackPathGNN
from graph.connection import get_connection

logger = structlog.get_logger(__name__)


class AttackPathScoringService:
    """Main service for attack path scoring with multiple algorithms."""
    
    def __init__(self, gnn_model_path: Optional[str] = None, device: str = 'cpu'):
        self.device = device
        self.conn = get_connection()
        
        # Initialize scorers
        self.dijkstra_scorer = DijkstraScorer()
        self.pagerank_scorer = PageRankScorer()
        self.motif_scorer = MotifScorer()
        self.hybrid_scorer = HybridScorer()
        
        # Initialize GNN
        self.gnn_scorer = AttackPathGNN(device=device)
        self.gnn_loaded = False
        
        # Try to load model from MLflow first
        mlflow_uri = os.getenv('MLFLOW_TRACKING_URI')
        model_run_id = os.getenv('MLFLOW_MODEL_RUN_ID', 'latest')  # Default to 'latest'
        
        if mlflow_uri:
            try:
                if model_run_id == 'latest':
                    # Get the latest successful model from MLflow
                    actual_run_id = self._get_latest_model_run_id(mlflow_uri)
                    if actual_run_id:
                        self.load_gnn_model_from_mlflow(actual_run_id)
                    else:
                        logger.warning("No trained models found in MLflow")
                else:
                    # Use specific run ID
                    self.load_gnn_model_from_mlflow(model_run_id)
            except Exception as e:
                logger.warning("Failed to load model from MLflow, will use local path", error=str(e))
                if gnn_model_path and Path(gnn_model_path).exists():
                    self.load_gnn_model(gnn_model_path)
        elif gnn_model_path and Path(gnn_model_path).exists():
            self.load_gnn_model(gnn_model_path)
        
        # Cache for performance
        self.path_cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def load_graph_data(self):
        """Load graph data from Neo4j into all scorers."""
        logger.info("Loading graph data from Neo4j")
        
        # Load nodes
        nodes_query = """
        MATCH (n)
        WHERE n.id IS NOT NULL
        RETURN n.id as id, labels(n) as labels, properties(n) as properties
        """
        node_results = self.conn.execute_query(nodes_query)
        
        nodes = []
        for result in node_results:
            if result['id'] is None:
                continue  # Skip nodes without IDs
            node = result['properties']
            node['id'] = result['id']
            node['labels'] = result['labels']
            nodes.append(node)
        
        # Load edges
        edges_query = """
        MATCH (a)-[r]->(b)
        WHERE a.id IS NOT NULL AND b.id IS NOT NULL
        RETURN a.id as source_id, b.id as target_id, type(r) as type, properties(r) as properties
        """
        edge_results = self.conn.execute_query(edges_query)
        
        edges = []
        for result in edge_results:
            if result['source_id'] is None or result['target_id'] is None:
                continue  # Skip edges with missing node IDs
            edge = {
                'source_id': result['source_id'],
                'target_id': result['target_id'],
                'type': result['type'],
                'properties': result['properties']
            }
            edges.append(edge)
        
        # Load data into all scorers
        self.dijkstra_scorer.load_graph(nodes, edges)
        self.pagerank_scorer.load_graph(nodes, edges)
        self.motif_scorer.load_graph(nodes, edges)
        self.hybrid_scorer.load_graph(nodes, edges)
        
        # Prepare GNN data
        if not self.gnn_loaded:
            gnn_data = self.gnn_scorer.prepare_data(nodes, edges)
            self.gnn_data = gnn_data
        
        logger.info("Graph data loaded", 
                   nodes=len(nodes), 
                   edges=len(edges))
    
    def load_gnn_model(self, model_path: str):
        """Load a pre-trained GNN model."""
        try:
            self.gnn_scorer.load_model(model_path)
            self.gnn_loaded = True
            logger.info("GNN model loaded", path=model_path)
        except Exception as e:
            logger.error("Failed to load GNN model", error=str(e))
            self.gnn_loaded = False
    
    def _get_latest_model_run_id(self, mlflow_uri: str) -> Optional[str]:
        """Get the latest successful model run ID from MLflow."""
        try:
            import mlflow
            from mlflow.tracking import MlflowClient
            
            mlflow.set_tracking_uri(mlflow_uri)
            client = MlflowClient()
            
            # Get the gnn-attack-paths experiment
            experiment = client.get_experiment_by_name('gnn-attack-paths')
            if not experiment:
                logger.warning("Experiment 'gnn-attack-paths' not found in MLflow")
                return None
            
            # Search for successful runs with model artifacts
            runs = client.search_runs(
                experiment.experiment_id,
                filter_string="status = 'FINISHED'",
                order_by=["start_time DESC"],
                max_results=10
            )
            
            # Find first run with model artifacts
            for run in runs:
                artifacts = client.list_artifacts(run.info.run_id)
                has_model = any('model' in a.path.lower() for a in artifacts)
                if has_model:
                    logger.info("Found latest model", run_id=run.info.run_id, 
                               run_name=run.data.tags.get('mlflow.runName', 'unnamed'))
                    return run.info.run_id
            
            logger.warning("No runs with model artifacts found")
            return None
            
        except Exception as e:
            logger.error("Failed to get latest model from MLflow", error=str(e))
            return None
    
    def load_gnn_model_from_mlflow(self, run_id: str):
        """Load a GNN model from MLflow."""
        try:
            import mlflow
            
            # Set MLflow tracking URI
            mlflow_uri = os.getenv('MLFLOW_TRACKING_URI')
            if mlflow_uri:
                mlflow.set_tracking_uri(mlflow_uri)
            
            # Load model from MLflow
            model_uri = f"runs:/{run_id}/model_checkpoint/gnn_model.pth"
            logger.info("Loading GNN model from MLflow", run_id=run_id, uri=model_uri)
            
            # Download the model artifact
            local_path = mlflow.artifacts.download_artifacts(model_uri)
            
            # Load the model checkpoint
            checkpoint = torch.load(local_path, map_location=self.device)
            
            # Build model with saved architecture
            node_dim = checkpoint['node_dim']
            edge_dim = checkpoint['edge_dim']
            self.gnn_scorer.build_model(
                node_dim, 
                edge_dim, 
                hidden_dim=checkpoint.get('hidden_dim', 64),
                num_layers=checkpoint.get('num_layers', 2),
                dropout=checkpoint.get('dropout', 0.1)
            )
            
            # Load weights
            self.gnn_scorer.model.load_state_dict(checkpoint['model_state_dict'])
            self.gnn_scorer.model.eval()
            self.gnn_loaded = True
            
            logger.info("GNN model loaded from MLflow successfully", run_id=run_id)
        except Exception as e:
            logger.error("Failed to load GNN model from MLflow", error=str(e), run_id=run_id)
            self.gnn_loaded = False
            raise
    
    def get_attack_paths(self, target: str, algorithm: str = 'hybrid', 
                        max_hops: int = 4, k: int = 5) -> List[Dict[str, Any]]:
        """Get attack paths to a target using specified algorithm."""
        start_time = time.time()
        
        # Check cache first
        cache_key = f"{target}_{algorithm}_{max_hops}_{k}"
        if cache_key in self.path_cache:
            cached_time, cached_result = self.path_cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                logger.info("Returning cached result", target=target, algorithm=algorithm)
                return cached_result
        
        # Find public entry points
        entry_points = self._find_public_entry_points()
        
        if not entry_points:
            logger.warning("No public entry points found")
            return []
        
        # Get paths from each entry point
        all_paths = []
        for entry_point in entry_points:
            paths = self._get_paths_from_entry(entry_point, target, algorithm, max_hops)
            all_paths.extend(paths)
        
        # Sort by score and return top K
        all_paths.sort(key=lambda x: x['score'], reverse=True)
        result = all_paths[:k]
        
        # Cache result
        self.path_cache[cache_key] = (time.time(), result)
        
        latency_ms = (time.time() - start_time) * 1000
        logger.info("Attack paths retrieved", 
                   target=target, 
                   algorithm=algorithm, 
                   count=len(result),
                   latency_ms=latency_ms)
        
        return result
    
    def _find_public_entry_points(self) -> List[str]:
        """Find public-facing entry points in the graph."""
        query = """
        MATCH (vm:Asset {type: "vm"})<-[:APPLIES_TO]-(sg:Asset {type: "sg"})-[:ALLOWS]->(ingress {cidr: "0.0.0.0/0"})
        RETURN DISTINCT vm.id as entry_point
        """
        
        results = self.conn.execute_query(query)
        return [result['entry_point'] for result in results]
    
    def _get_paths_from_entry(self, entry_point: str, target: str, 
                             algorithm: str, max_hops: int) -> List[Dict[str, Any]]:
        """Get paths from a specific entry point to target."""
        try:
            if algorithm == 'dijkstra':
                return self.dijkstra_scorer.get_attack_paths(entry_point, target, max_hops)
            elif algorithm == 'pagerank':
                return self.pagerank_scorer.get_attack_paths(entry_point, target, max_hops)
            elif algorithm == 'motif':
                return self.motif_scorer.get_attack_paths(entry_point, target, max_hops)
            elif algorithm == 'hybrid':
                return self.hybrid_scorer.get_attack_paths(entry_point, target, max_hops)
            elif algorithm == 'gnn' and self.gnn_loaded:
                return self.gnn_scorer.predict_attack_paths(
                    self.gnn_data, entry_point, target, max_hops
                )
            else:
                logger.warning("Unknown algorithm or GNN not loaded", algorithm=algorithm)
                return []
        except Exception as e:
            logger.error("Error getting paths", 
                        entry_point=entry_point, 
                        target=target, 
                        algorithm=algorithm,
                        error=str(e))
            return []
    
    def get_risk_explanation(self, path: List[str]) -> str:
        """Generate human-readable explanation for an attack path."""
        if not path:
            return "No attack path found."
        
        # Get path details from Neo4j
        path_details = self._get_path_details(path)
        
        # Generate explanation
        explanation_parts = []
        
        # Entry point
        entry = path_details[0] if path_details else {}
        if entry.get('type') == 'vm':
            explanation_parts.append(f"Public-facing VM '{entry.get('name', 'unknown')}'")
        
        # Vulnerabilities
        vulns = self._get_vulnerabilities_in_path(path)
        if vulns:
            vuln_desc = ", ".join([f"{v['cve']} (CVSS: {v['cvss']})" for v in vulns[:3]])
            explanation_parts.append(f"with exploitable vulnerabilities: {vuln_desc}")
        
        # Lateral movement
        if len(path) > 2:
            explanation_parts.append(f"enables lateral movement through {len(path)-2} hops")
        
        # Target
        target = path_details[-1] if path_details else {}
        if target.get('critical'):
            explanation_parts.append(f"to reach critical asset '{target.get('name', 'unknown')}'")
        
        return " → ".join(explanation_parts) + "."
    
    def _get_path_details(self, path: List[str]) -> List[Dict[str, Any]]:
        """Get detailed information about nodes in a path."""
        if not path:
            return []
        
        placeholders = ", ".join([f"'{node_id}'" for node_id in path])
        query = f"""
        MATCH (n)
        WHERE n.id IN [{placeholders}]
        RETURN n.id as id, n.type as type, n.name as name, n.critical as critical
        ORDER BY n.id
        """
        
        results = self.conn.execute_query(query)
        return list(results)
    
    def _get_vulnerabilities_in_path(self, path: List[str]) -> List[Dict[str, Any]]:
        """Get vulnerabilities associated with nodes in a path."""
        if not path:
            return []
        
        placeholders = ", ".join([f"'{node_id}'" for node_id in path])
        query = f"""
        MATCH (n)-[:RUNS]->(s)-[:HAS_VULN]->(v)
        WHERE n.id IN [{placeholders}]
        RETURN v.cve as cve, v.cvss as cvss, v.exploit_available as exploit_available
        ORDER BY v.cvss DESC
        """
        
        results = self.conn.execute_query(query)
        return list(results)
    
    def simulate_remediation(self, actions: List[str]) -> Dict[str, Any]:
        """Simulate the effect of remediation actions on attack paths."""
        logger.info("Simulating remediation", actions=actions)
        
        # This is a simplified simulation - in practice, you'd modify the graph
        # and re-run the scoring algorithms
        
        simulation_results = {
            'original_risk': 0.8,  # Placeholder
            'new_risk': 0.3,       # Placeholder
            'risk_reduction': 0.5,
            'actions_applied': actions,
            'affected_assets': len(actions) * 2,  # Placeholder
            'simulation_time': time.time()
        }
        
        return simulation_results
    
    def get_crown_jewels(self) -> List[Dict[str, Any]]:
        """Get all crown jewel assets."""
        query = """
        MATCH (n:Asset {critical: true})
        RETURN n.id as id, n.name as name, n.type as type, n.environment as environment
        """
        
        results = self.conn.execute_query(query)
        return list(results)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return {
            'cache_size': len(self.path_cache),
            'gnn_loaded': self.gnn_loaded,
            'device': self.device,
            'algorithms_available': ['dijkstra', 'pagerank', 'motif', 'hybrid'] + (['gnn'] if self.gnn_loaded else [])
        }
    
    def clear_cache(self):
        """Clear the path cache."""
        self.path_cache.clear()
        logger.info("Path cache cleared")
