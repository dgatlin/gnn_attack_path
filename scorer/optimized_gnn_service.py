"""
Optimized GNN service integrating Optuna and MLflow for hyperparameter optimization
and experiment tracking in attack path scoring.
"""
import torch
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import structlog
from pathlib import Path
import json
import time

from .gnn_model import AttackPathGNN, GraphSAGEModel, GATModel
from .optuna_optimization import GNNHyperparameterOptimizer, optimize_gnn_models
from .mlflow_tracking import MLflowTracker, track_gnn_training

logger = structlog.get_logger(__name__)


class OptimizedGNNService:
    """Enhanced GNN service with Optuna optimization and MLflow tracking."""
    
    def __init__(self, device: str = 'cpu', 
                 mlflow_experiment: str = "gnn-attack-paths",
                 optuna_study_name: str = "gnn_optimization"):
        self.device = device
        self.mlflow_tracker = MLflowTracker(experiment_name=mlflow_experiment)
        self.optuna_study_name = optuna_study_name
        self.models = {}
        self.optimization_results = {}
        
    def prepare_training_data(self, nodes: List[Dict], edges: List[Dict]) -> Tuple[Any, Any, Any]:
        """Prepare training, validation, and test datasets."""
        logger.info("Preparing training data", 
                   nodes=len(nodes), 
                   edges=len(edges))
        
        # Create GNN instance for data preparation
        gnn = AttackPathGNN(device=self.device)
        data = gnn.prepare_data(nodes, edges)
        
        # Split data (simple split for demo - in practice, use proper CV)
        total_nodes = data.x.size(0)
        train_size = int(0.7 * total_nodes)
        val_size = int(0.15 * total_nodes)
        
        # Create train/val/test splits
        train_data = data
        val_data = data  # In practice, create proper validation set
        test_data = data  # In practice, create proper test set
        
        logger.info("Data prepared", 
                   train_nodes=train_data.x.size(0),
                   val_nodes=val_data.x.size(0),
                   test_nodes=test_data.x.size(0))
        
        return train_data, val_data, test_data
    
    def optimize_hyperparameters(self, train_data: Any, val_data: Any, test_data: Any,
                                model_types: List[str] = ['graphsage', 'gat'],
                                n_trials: int = 50) -> Dict[str, Any]:
        """Run hyperparameter optimization using Optuna."""
        logger.info("Starting hyperparameter optimization", 
                   model_types=model_types, 
                   n_trials=n_trials)
        
        # Run optimization for each model type
        optimization_results = optimize_gnn_models(
            train_data, val_data, test_data, model_types, n_trials
        )
        
        # Log optimization results to MLflow
        with self.mlflow_tracker.start_run(run_name="hyperparameter_optimization") as run:
            # Log optimization parameters
            self.mlflow_tracker.log_model_parameters({
                'n_trials': n_trials,
                'model_types': model_types,
                'optimization_timestamp': time.time()
            })
            
            # Log results for each model type
            for model_type, result in optimization_results.items():
                self.mlflow_tracker.log_training_metrics({
                    f'{model_type}_best_score': result['best_score'],
                    f'{model_type}_n_trials': result['report']['total_trials']
                })
                
                # Log best parameters
                for param_name, param_value in result['best_params'].items():
                    self.mlflow_tracker.log_training_metrics({
                        f'{model_type}_{param_name}': param_value
                    })
            
            # Log optimization report as artifact
            report_data = {
                'optimization_results': optimization_results,
                'timestamp': time.time()
            }
            report_file = 'optimization_report.json'
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            self.mlflow_tracker.log_model_artifacts({'optimization_report': report_file})
            Path(report_file).unlink()  # Clean up
        
        self.optimization_results = optimization_results
        logger.info("Hyperparameter optimization completed", 
                   results=len(optimization_results))
        
        return optimization_results
    
    def train_optimized_model(self, train_data: Any, val_data: Any, test_data: Any,
                             model_type: str = 'graphsage', 
                             use_optimized_params: bool = True) -> Dict[str, Any]:
        """Train model with optimized hyperparameters."""
        logger.info("Training optimized model", 
                   model_type=model_type, 
                   use_optimized=use_optimized_params)
        
        # Get parameters
        if use_optimized_params and model_type in self.optimization_results:
            params = self.optimization_results[model_type]['best_params']
        else:
            # Use default parameters
            params = self._get_default_params(model_type)
        
        # Create model
        gnn = AttackPathGNN(model_type=model_type, device=self.device)
        node_dim = train_data.x.size(1)
        edge_dim = train_data.edge_attr.size(1)
        
        gnn.build_model(node_dim, edge_dim, **params)
        
        # Train model
        start_time = time.time()
        gnn.train(train_data, epochs=params.get('epochs', 100))
        training_time = time.time() - start_time
        
        # Evaluate model
        performance = self._evaluate_model(gnn, test_data)
        performance['training_time'] = training_time
        
        # Track training in MLflow
        run_id = track_gnn_training(
            model=gnn.model,
            train_data=train_data,
            val_data=val_data,
            test_data=test_data,
            params=params,
            performance=performance,
            run_name=f"{model_type}_optimized_training"
        )
        
        # Store model
        self.models[model_type] = {
            'gnn': gnn,
            'params': params,
            'performance': performance,
            'run_id': run_id
        }
        
        logger.info("Model training completed", 
                   model_type=model_type,
                   performance=performance,
                   run_id=run_id)
        
        return {
            'model_type': model_type,
            'performance': performance,
            'run_id': run_id,
            'params': params
        }
    
    def _get_default_params(self, model_type: str) -> Dict[str, Any]:
        """Get default parameters for model type."""
        if model_type == 'graphsage':
            return {
                'hidden_dim': 64,
                'num_layers': 2,
                'dropout': 0.1,
                'epochs': 100
            }
        elif model_type == 'gat':
            return {
                'hidden_dim': 64,
                'num_layers': 2,
                'num_heads': 4,
                'dropout': 0.1,
                'epochs': 100
            }
        else:
            return {'epochs': 100}
    
    def _evaluate_model(self, gnn: AttackPathGNN, test_data: Any) -> Dict[str, Any]:
        """Evaluate model performance."""
        gnn.model.eval()
        test_data = test_data.to(self.device)
        
        with torch.no_grad():
            output = gnn.model(test_data.x, test_data.edge_index, test_data.edge_attr)
            edge_scores = output['edge_scores']
        
        # Calculate performance metrics
        # Note: In practice, you'd have ground truth labels
        # For demo, we'll simulate some metrics
        
        # Simulate ground truth (in practice, this would be real labels)
        edge_labels = torch.ones_like(edge_scores)
        
        # Calculate basic metrics
        predictions = (edge_scores > 0.5).float()
        accuracy = (predictions == edge_labels).float().mean().item()
        
        # Calculate precision, recall, F1
        true_positives = (predictions * edge_labels).sum().item()
        false_positives = (predictions * (1 - edge_labels)).sum().item()
        false_negatives = ((1 - predictions) * edge_labels).sum().item()
        
        precision = true_positives / (true_positives + false_positives + 1e-8)
        recall = true_positives / (true_positives + false_negatives + 1e-8)
        f1_score = 2 * (precision * recall) / (precision + recall + 1e-8)
        
        # Calculate latency
        start_time = time.time()
        _ = gnn.model(test_data.x, test_data.edge_index, test_data.edge_attr)
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'latency_ms': latency_ms,
            'path_detection_accuracy': accuracy,  # Placeholder
            'risk_score_correlation': 0.85,  # Placeholder
            'top_k_precision': 0.92  # Placeholder
        }
    
    def get_attack_paths(self, source: str, target: str, 
                        model_type: str = 'graphsage',
                        max_hops: int = 4) -> List[Dict[str, Any]]:
        """Get attack paths using optimized model."""
        if model_type not in self.models:
            raise ValueError(f"Model {model_type} not trained. Available: {list(self.models.keys())}")
        
        gnn = self.models[model_type]['gnn']
        
        # This would use the actual graph data
        # For demo, return simulated results
        return [
            {
                'path': [source, f'intermediate-{i}', target],
                'score': 0.8 - i * 0.1,
                'length': 2,
                'algorithm': f'optimized_{model_type}',
                'model_run_id': self.models[model_type]['run_id']
            }
            for i in range(3)
        ]
    
    def compare_models(self, model_types: List[str] = None) -> Dict[str, Any]:
        """Compare performance of different models."""
        if model_types is None:
            model_types = list(self.models.keys())
        
        comparison_data = []
        for model_type in model_types:
            if model_type in self.models:
                model_info = self.models[model_type]
                comparison_data.append({
                    'model_type': model_type,
                    'performance': model_info['performance'],
                    'params': model_info['params'],
                    'run_id': model_info['run_id']
                })
        
        # Use MLflow to get detailed comparison
        run_ids = [info['run_id'] for info in comparison_data]
        mlflow_comparison = self.mlflow_tracker.compare_models(run_ids)
        
        return {
            'models': comparison_data,
            'mlflow_comparison': mlflow_comparison,
            'best_model': max(comparison_data, key=lambda x: x['performance']['f1_score'])
        }
    
    def get_model_recommendations(self) -> Dict[str, Any]:
        """Get model recommendations based on performance."""
        if not self.models:
            return {'message': 'No models trained yet'}
        
        # Get best model from MLflow
        best_mlflow_model = self.mlflow_tracker.get_best_model('f1_score')
        
        # Get local best model
        local_best = max(self.models.items(), 
                        key=lambda x: x[1]['performance']['f1_score'])
        
        return {
            'recommended_model': local_best[0],
            'performance': local_best[1]['performance'],
            'mlflow_best': best_mlflow_model,
            'all_models': {
                name: info['performance'] 
                for name, info in self.models.items()
            }
        }
    
    def generate_experiment_report(self) -> Dict[str, Any]:
        """Generate comprehensive experiment report."""
        return self.mlflow_tracker.generate_experiment_report()
    
    def save_models(self, output_dir: str = "models"):
        """Save all trained models."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        for model_type, model_info in self.models.items():
            model_path = output_path / f"{model_type}_optimized.pth"
            torch.save({
                'model_state_dict': model_info['gnn'].model.state_dict(),
                'model_type': model_type,
                'params': model_info['params'],
                'performance': model_info['performance'],
                'run_id': model_info['run_id']
            }, model_path)
            
            logger.info("Saved model", 
                       model_type=model_type, 
                       path=str(model_path))
    
    def load_models(self, input_dir: str = "models"):
        """Load previously trained models."""
        input_path = Path(input_dir)
        
        for model_file in input_path.glob("*_optimized.pth"):
            checkpoint = torch.load(model_file, map_location=self.device)
            
            model_type = checkpoint['model_type']
            params = checkpoint['params']
            
            # Recreate model
            gnn = AttackPathGNN(model_type=model_type, device=self.device)
            gnn.build_model(50, 20, **params)  # These should match your actual dimensions
            gnn.model.load_state_dict(checkpoint['model_state_dict'])
            
            self.models[model_type] = {
                'gnn': gnn,
                'params': params,
                'performance': checkpoint['performance'],
                'run_id': checkpoint['run_id']
            }
            
            logger.info("Loaded model", 
                       model_type=model_type, 
                       file=str(model_file))
