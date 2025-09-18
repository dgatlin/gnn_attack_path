"""
MLflow integration for GNN model experiment tracking and model registry.
Tracks training runs, model versions, and performance metrics.
"""
import mlflow
import mlflow.pytorch
import mlflow.sklearn
import torch
import numpy as np
from typing import Dict, Any, List, Optional
import structlog
from pathlib import Path
import json
import time

logger = structlog.get_logger(__name__)


class MLflowTracker:
    """MLflow integration for GNN model tracking and registry."""
    
    def __init__(self, experiment_name: str = "gnn-attack-paths", 
                 tracking_uri: str = "sqlite:///mlflow.db"):
        self.experiment_name = experiment_name
        self.tracking_uri = tracking_uri
        self._setup_mlflow()
    
    def _setup_mlflow(self):
        """Setup MLflow tracking."""
        mlflow.set_tracking_uri(self.tracking_uri)
        
        # Create or get experiment
        try:
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(self.experiment_name)
                logger.info("Created new MLflow experiment", 
                           name=self.experiment_name, 
                           id=experiment_id)
            else:
                experiment_id = experiment.experiment_id
                logger.info("Using existing MLflow experiment", 
                           name=self.experiment_name, 
                           id=experiment_id)
        except Exception as e:
            logger.error("Failed to setup MLflow experiment", error=str(e))
            raise
    
    def start_run(self, run_name: str = None, tags: Dict[str, str] = None) -> mlflow.ActiveRun:
        """Start a new MLflow run."""
        return mlflow.start_run(run_name=run_name, tags=tags or {})
    
    def log_model_parameters(self, params: Dict[str, Any]):
        """Log model hyperparameters."""
        mlflow.log_params(params)
        logger.info("Logged model parameters", count=len(params))
    
    def log_training_metrics(self, metrics: Dict[str, float], step: int = None):
        """Log training metrics."""
        for metric_name, value in metrics.items():
            if step is not None:
                mlflow.log_metric(metric_name, value, step=step)
            else:
                mlflow.log_metric(metric_name, value)
        
        logger.info("Logged training metrics", count=len(metrics))
    
    def log_model_artifacts(self, artifacts: Dict[str, str]):
        """Log model artifacts (files, plots, etc.)."""
        for artifact_name, artifact_path in artifacts.items():
            if Path(artifact_path).exists():
                mlflow.log_artifact(artifact_path, artifact_name)
                logger.info("Logged artifact", name=artifact_name, path=artifact_path)
            else:
                logger.warning("Artifact not found", name=artifact_name, path=artifact_path)
    
    def log_pytorch_model(self, model: torch.nn.Module, model_name: str = "gnn_model",
                         signature=None, input_example=None):
        """Log PyTorch model to MLflow."""
        try:
            mlflow.pytorch.log_model(
                pytorch_model=model,
                artifact_path=model_name,
                signature=signature,
                input_example=input_example
            )
            logger.info("Logged PyTorch model", name=model_name)
        except Exception as e:
            logger.error("Failed to log PyTorch model", error=str(e))
            raise
    
    def log_model_performance(self, performance: Dict[str, Any]):
        """Log comprehensive model performance metrics."""
        # Log basic metrics
        basic_metrics = {
            'accuracy': performance.get('accuracy', 0.0),
            'precision': performance.get('precision', 0.0),
            'recall': performance.get('recall', 0.0),
            'f1_score': performance.get('f1_score', 0.0),
            'auc_roc': performance.get('auc_roc', 0.0),
            'auc_pr': performance.get('auc_pr', 0.0)
        }
        self.log_training_metrics(basic_metrics)
        
        # Log attack path specific metrics
        attack_metrics = {
            'path_detection_accuracy': performance.get('path_detection_accuracy', 0.0),
            'risk_score_correlation': performance.get('risk_score_correlation', 0.0),
            'top_k_precision': performance.get('top_k_precision', 0.0),
            'latency_ms': performance.get('latency_ms', 0.0)
        }
        self.log_training_metrics(attack_metrics)
        
        # Log confusion matrix if available
        if 'confusion_matrix' in performance:
            self._log_confusion_matrix(performance['confusion_matrix'])
        
        # Log ROC curve if available
        if 'roc_curve' in performance:
            self._log_roc_curve(performance['roc_curve'])
    
    def _log_confusion_matrix(self, cm: np.ndarray):
        """Log confusion matrix as artifact."""
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        
        cm_path = 'confusion_matrix.png'
        plt.savefig(cm_path)
        plt.close()
        
        mlflow.log_artifact(cm_path)
        Path(cm_path).unlink()  # Clean up
    
    def _log_roc_curve(self, roc_data: Dict[str, np.ndarray]):
        """Log ROC curve as artifact."""
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(8, 6))
        plt.plot(roc_data['fpr'], roc_data['tpr'], 
                label=f'ROC Curve (AUC = {roc_data.get("auc", 0.0):.3f})')
        plt.plot([0, 1], [0, 1], 'k--', label='Random')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curve')
        plt.legend()
        
        roc_path = 'roc_curve.png'
        plt.savefig(roc_path)
        plt.close()
        
        mlflow.log_artifact(roc_path)
        Path(roc_path).unlink()  # Clean up
    
    def log_attack_path_analysis(self, analysis: Dict[str, Any]):
        """Log attack path analysis results."""
        # Log path statistics
        path_stats = {
            'total_paths_found': analysis.get('total_paths', 0),
            'high_risk_paths': analysis.get('high_risk_paths', 0),
            'avg_path_length': analysis.get('avg_path_length', 0.0),
            'max_path_length': analysis.get('max_path_length', 0),
            'crown_jewels_reachable': analysis.get('crown_jewels_reachable', 0)
        }
        self.log_training_metrics(path_stats)
        
        # Log top attack paths as JSON
        if 'top_paths' in analysis:
            paths_data = {
                'top_attack_paths': analysis['top_paths'],
                'timestamp': time.time()
            }
            paths_file = 'top_attack_paths.json'
            with open(paths_file, 'w') as f:
                json.dump(paths_data, f, indent=2)
            mlflow.log_artifact(paths_file)
            Path(paths_file).unlink()  # Clean up
    
    def register_model(self, model_name: str, model_version: str = None,
                      description: str = None, tags: Dict[str, str] = None):
        """Register model in MLflow Model Registry."""
        try:
            model_uri = f"runs:/{mlflow.active_run().info.run_id}/gnn_model"
            
            registered_model = mlflow.register_model(
                model_uri=model_uri,
                name=model_name,
                tags=tags or {}
            )
            
            if description:
                client = mlflow.tracking.MlflowClient()
                client.update_model_version(
                    name=model_name,
                    version=registered_model.version,
                    description=description
                )
            
            logger.info("Registered model", 
                       name=model_name, 
                       version=registered_model.version)
            
            return registered_model
            
        except Exception as e:
            logger.error("Failed to register model", error=str(e))
            raise
    
    def get_best_model(self, metric: str = "f1_score", 
                      ascending: bool = False) -> Optional[Dict[str, Any]]:
        """Get the best model based on a metric."""
        try:
            client = mlflow.tracking.MlflowClient()
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            
            runs = client.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=[f"metrics.{metric} {'ASC' if ascending else 'DESC'}"]
            )
            
            if runs:
                best_run = runs[0]
                return {
                    'run_id': best_run.info.run_id,
                    'metric_value': best_run.data.metrics.get(metric, 0.0),
                    'params': best_run.data.params,
                    'metrics': best_run.data.metrics,
                    'tags': best_run.data.tags
                }
            
            return None
            
        except Exception as e:
            logger.error("Failed to get best model", error=str(e))
            return None
    
    def compare_models(self, run_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple model runs."""
        try:
            client = mlflow.tracking.MlflowClient()
            
            comparison_data = []
            for run_id in run_ids:
                run = client.get_run(run_id)
                comparison_data.append({
                    'run_id': run_id,
                    'params': run.data.params,
                    'metrics': run.data.metrics,
                    'tags': run.data.tags
                })
            
            return {
                'runs': comparison_data,
                'comparison_timestamp': time.time()
            }
            
        except Exception as e:
            logger.error("Failed to compare models", error=str(e))
            return {}
    
    def generate_experiment_report(self) -> Dict[str, Any]:
        """Generate comprehensive experiment report."""
        try:
            client = mlflow.tracking.MlflowClient()
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            
            runs = client.search_runs(experiment_ids=[experiment.experiment_id])
            
            if not runs:
                return {'message': 'No runs found in experiment'}
            
            # Calculate statistics
            metrics = {}
            for run in runs:
                for metric_name, value in run.data.metrics.items():
                    if metric_name not in metrics:
                        metrics[metric_name] = []
                    metrics[metric_name].append(value)
            
            # Generate statistics for each metric
            metric_stats = {}
            for metric_name, values in metrics.items():
                metric_stats[metric_name] = {
                    'count': len(values),
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'median': np.median(values)
                }
            
            return {
                'experiment_name': self.experiment_name,
                'total_runs': len(runs),
                'metric_statistics': metric_stats,
                'best_runs': {
                    metric: max(runs, key=lambda r: r.data.metrics.get(metric, 0))
                    for metric in metrics.keys()
                },
                'generated_at': time.time()
            }
            
        except Exception as e:
            logger.error("Failed to generate experiment report", error=str(e))
            return {}


def track_gnn_training(model: torch.nn.Module, train_data: Any, val_data: Any,
                      test_data: Any, params: Dict[str, Any], 
                      performance: Dict[str, Any], run_name: str = None) -> str:
    """Complete GNN training tracking workflow."""
    tracker = MLflowTracker()
    
    with tracker.start_run(run_name=run_name) as run:
        # Log parameters
        tracker.log_model_parameters(params)
        
        # Log model
        tracker.log_pytorch_model(model, "gnn_model")
        
        # Log performance
        tracker.log_model_performance(performance)
        
        # Log training artifacts
        artifacts = {
            'training_config': 'training_config.json',
            'model_architecture': 'model_architecture.txt'
        }
        tracker.log_model_artifacts(artifacts)
        
        logger.info("Completed GNN training tracking", run_id=run.info.run_id)
        return run.info.run_id
