"""
Optuna hyperparameter optimization for GNN models.
Optimizes GraphSAGE and GAT models for attack path scoring.
"""
import optuna
import torch
import torch.nn as nn
from torch_geometric.data import Data
from typing import Dict, Any, Tuple, List
import structlog
from .gnn_model import GraphSAGEModel, GATModel, AttackPathGNN

logger = structlog.get_logger(__name__)


class GNNHyperparameterOptimizer:
    """Optuna-based hyperparameter optimization for GNN models."""
    
    def __init__(self, model_type: str = 'graphsage', device: str = 'cpu'):
        self.model_type = model_type
        self.device = device
        self.best_params = None
        self.best_score = float('inf')
        
    def create_objective(self, train_data: Data, val_data: Data, 
                        test_data: Data) -> callable:
        """Create objective function for Optuna optimization."""
        
        def objective(trial):
            try:
                # Suggest hyperparameters based on model type
                if self.model_type == 'graphsage':
                    params = self._suggest_graphsage_params(trial)
                elif self.model_type == 'gat':
                    params = self._suggest_gat_params(trial)
                else:
                    raise ValueError(f"Unknown model type: {self.model_type}")
                
                # Create model with suggested parameters
                model = self._create_model(params)
                
                # Train and evaluate
                score = self._train_and_evaluate(model, train_data, val_data, test_data)
                
                # Report intermediate result
                trial.report(score, step=0)
                
                # Handle pruning
                if trial.should_prune():
                    raise optuna.exceptions.TrialPruned()
                
                return score
                
            except Exception as e:
                logger.error("Trial failed", error=str(e), trial_number=trial.number)
                raise optuna.exceptions.TrialPruned()
        
        return objective
    
    def _suggest_graphsage_params(self, trial) -> Dict[str, Any]:
        """Suggest hyperparameters for GraphSAGE model."""
        return {
            'hidden_dim': trial.suggest_categorical('hidden_dim', [32, 64, 128, 256]),
            'num_layers': trial.suggest_int('num_layers', 2, 5),
            'dropout': trial.suggest_float('dropout', 0.1, 0.5),
            'learning_rate': trial.suggest_float('learning_rate', 1e-4, 1e-2, log=True),
            'weight_decay': trial.suggest_float('weight_decay', 1e-5, 1e-2, log=True),
            'batch_size': trial.suggest_categorical('batch_size', [32, 64, 128, 256]),
            'epochs': trial.suggest_int('epochs', 50, 200),
            'patience': trial.suggest_int('patience', 10, 50)
        }
    
    def _suggest_gat_params(self, trial) -> Dict[str, Any]:
        """Suggest hyperparameters for GAT model."""
        return {
            'hidden_dim': trial.suggest_categorical('hidden_dim', [32, 64, 128, 256]),
            'num_layers': trial.suggest_int('num_layers', 2, 5),
            'num_heads': trial.suggest_categorical('num_heads', [2, 4, 8]),
            'dropout': trial.suggest_float('dropout', 0.1, 0.5),
            'learning_rate': trial.suggest_float('learning_rate', 1e-4, 1e-2, log=True),
            'weight_decay': trial.suggest_float('weight_decay', 1e-5, 1e-2, log=True),
            'batch_size': trial.suggest_categorical('batch_size', [32, 64, 128, 256]),
            'epochs': trial.suggest_int('epochs', 50, 200),
            'patience': trial.suggest_int('patience', 10, 50)
        }
    
    def _create_model(self, params: Dict[str, Any]) -> nn.Module:
        """Create model with given parameters."""
        node_dim = 50  # This should match your actual node feature dimension
        edge_dim = 20  # This should match your actual edge feature dimension
        
        if self.model_type == 'graphsage':
            return GraphSAGEModel(
                node_dim=node_dim,
                edge_dim=edge_dim,
                hidden_dim=params['hidden_dim'],
                num_layers=params['num_layers'],
                dropout=params['dropout']
            )
        elif self.model_type == 'gat':
            return GATModel(
                node_dim=node_dim,
                edge_dim=edge_dim,
                hidden_dim=params['hidden_dim'],
                num_layers=params['num_layers'],
                num_heads=params['num_heads'],
                dropout=params['dropout']
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def _train_and_evaluate(self, model: nn.Module, train_data: Data, 
                           val_data: Data, test_data: Data) -> float:
        """Train model and return validation loss."""
        model = model.to(self.device)
        train_data = train_data.to(self.device)
        val_data = val_data.to(self.device)
        
        # Get hyperparameters from model creation
        optimizer = torch.optim.Adam(
            model.parameters(),
            lr=0.001,  # This should be passed as parameter
            weight_decay=1e-4
        )
        criterion = nn.BCELoss()
        
        best_val_loss = float('inf')
        patience_counter = 0
        patience = 20  # This should be passed as parameter
        
        model.train()
        for epoch in range(100):  # This should be passed as parameter
            optimizer.zero_grad()
            
            # Forward pass
            output = model(train_data.x, train_data.edge_index, train_data.edge_attr)
            
            # Create dummy labels for training
            edge_labels = torch.ones(train_data.edge_index.size(1), device=self.device)
            
            # Calculate loss
            loss = criterion(output['edge_scores'], edge_labels)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            # Validation
            if epoch % 10 == 0:
                val_loss = self._evaluate_model(model, val_data)
                
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                if patience_counter >= patience:
                    break
        
        return best_val_loss
    
    def _evaluate_model(self, model: nn.Module, data: Data) -> float:
        """Evaluate model on validation data."""
        model.eval()
        with torch.no_grad():
            output = model(data.x, data.edge_index, data.edge_attr)
            edge_labels = torch.ones(data.edge_index.size(1), device=self.device)
            criterion = nn.BCELoss()
            loss = criterion(output['edge_scores'], edge_labels)
        return loss.item()
    
    def optimize(self, train_data: Data, val_data: Data, test_data: Data,
                 n_trials: int = 100, study_name: str = None) -> Dict[str, Any]:
        """Run hyperparameter optimization."""
        logger.info("Starting hyperparameter optimization", 
                   model_type=self.model_type, 
                   n_trials=n_trials)
        
        # Create study
        study = optuna.create_study(
            direction='minimize',
            study_name=study_name or f"gnn_{self.model_type}_optimization",
            pruner=optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=10)
        )
        
        # Create objective function
        objective = self.create_objective(train_data, val_data, test_data)
        
        # Run optimization
        study.optimize(objective, n_trials=n_trials)
        
        # Get best parameters
        self.best_params = study.best_params
        self.best_score = study.best_value
        
        logger.info("Hyperparameter optimization completed",
                   best_score=self.best_score,
                   best_params=self.best_params)
        
        return {
            'best_params': self.best_params,
            'best_score': self.best_score,
            'study': study
        }
    
    def get_optimization_report(self, study: optuna.Study) -> Dict[str, Any]:
        """Generate optimization report."""
        trials = study.trials
        
        return {
            'total_trials': len(trials),
            'completed_trials': len([t for t in trials if t.state == optuna.trial.TrialState.COMPLETE]),
            'pruned_trials': len([t for t in trials if t.state == optuna.trial.TrialState.PRUNED]),
            'failed_trials': len([t for t in trials if t.state == optuna.trial.TrialState.FAIL]),
            'best_value': study.best_value,
            'best_params': study.best_params,
            'best_trial': study.best_trial.number,
            'optimization_history': [
                {
                    'trial': trial.number,
                    'value': trial.value,
                    'state': trial.state.name,
                    'params': trial.params
                }
                for trial in trials
            ]
        }


def optimize_gnn_models(train_data: Data, val_data: Data, test_data: Data,
                       model_types: List[str] = ['graphsage', 'gat'],
                       n_trials: int = 50) -> Dict[str, Any]:
    """Optimize multiple GNN model types."""
    results = {}
    
    for model_type in model_types:
        logger.info(f"Optimizing {model_type} model")
        
        optimizer = GNNHyperparameterOptimizer(model_type=model_type)
        result = optimizer.optimize(train_data, val_data, test_data, n_trials)
        
        results[model_type] = {
            'best_params': result['best_params'],
            'best_score': result['best_score'],
            'report': optimizer.get_optimization_report(result['study'])
        }
    
    return results
