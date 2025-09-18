# 🧠 Optuna & MLflow Integration for GNN Attack Path Scoring

This document explains how Optuna and MLflow are integrated into the GNN Attack Path Demo for hyperparameter optimization and experiment tracking.

## 🎯 Overview

The integration provides:
- **Optuna**: Automated hyperparameter optimization for GraphSAGE and GAT models
- **MLflow**: Experiment tracking, model registry, and performance monitoring
- **Seamless Integration**: Combined workflow for optimal model training and tracking

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Data Layer"
        DATA[Synthetic Data<br/>Neo4j Graph]
    end
    
    subgraph "Optimization Layer"
        OPTUNA[Optuna<br/>Hyperparameter Search]
        PRUNER[Median Pruner<br/>Early Stopping]
    end
    
    subgraph "ML Ops Layer"
        MLFLOW[MLflow<br/>Experiment Tracking]
        REGISTRY[Model Registry<br/>Version Control]
    end
    
    subgraph "Model Layer"
        GNN[GNN Models<br/>GraphSAGE & GAT]
        TRAIN[Training Loop<br/>PyTorch]
    end
    
    subgraph "Evaluation Layer"
        METRICS[Performance Metrics<br/>Attack Path Accuracy]
        VIS[Visualization<br/>Plots & Reports]
    end
    
    DATA --> OPTUNA
    OPTUNA --> PRUNER
    OPTUNA --> GNN
    GNN --> TRAIN
    TRAIN --> METRICS
    METRICS --> MLFLOW
    MLFLOW --> REGISTRY
    MLFLOW --> VIS
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install optuna mlflow plotly matplotlib seaborn
```

### 2. Run Optimization Example
```bash
python examples/gnn_optimization_example.py
```

### 3. Start MLflow UI
```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db
# Open http://localhost:5000
```

## 🔧 Optuna Integration

### Hyperparameter Search Space

#### GraphSAGE Parameters
```python
{
    'hidden_dim': [32, 64, 128, 256],
    'num_layers': [2, 3, 4, 5],
    'dropout': [0.1, 0.2, 0.3, 0.4, 0.5],
    'learning_rate': [1e-4, 1e-3, 1e-2],
    'weight_decay': [1e-5, 1e-4, 1e-3],
    'batch_size': [32, 64, 128, 256],
    'epochs': [50, 100, 150, 200],
    'patience': [10, 20, 30, 50]
}
```

#### GAT Parameters
```python
{
    'hidden_dim': [32, 64, 128, 256],
    'num_layers': [2, 3, 4, 5],
    'num_heads': [2, 4, 8],
    'dropout': [0.1, 0.2, 0.3, 0.4, 0.5],
    'learning_rate': [1e-4, 1e-3, 1e-2],
    'weight_decay': [1e-5, 1e-4, 1e-3],
    'batch_size': [32, 64, 128, 256],
    'epochs': [50, 100, 150, 200],
    'patience': [10, 20, 30, 50]
}
```

### Optimization Process

```python
from scorer.optuna_optimization import GNNHyperparameterOptimizer

# Initialize optimizer
optimizer = GNNHyperparameterOptimizer(model_type='graphsage')

# Run optimization
result = optimizer.optimize(
    train_data=train_data,
    val_data=val_data,
    test_data=test_data,
    n_trials=100
)

# Get best parameters
best_params = result['best_params']
best_score = result['best_score']
```

### Pruning Strategy

- **Median Pruner**: Prunes trials that perform worse than median
- **Startup Trials**: 5 trials before pruning starts
- **Warmup Steps**: 10 steps before pruning evaluation

## 📊 MLflow Integration

### Experiment Tracking

#### Automatic Logging
```python
from scorer.mlflow_tracking import MLflowTracker

tracker = MLflowTracker(experiment_name="gnn-attack-paths")

with tracker.start_run(run_name="graphsage_optimization"):
    # Log parameters
    tracker.log_model_parameters({
        'hidden_dim': 64,
        'num_layers': 2,
        'dropout': 0.1
    })
    
    # Log metrics
    tracker.log_training_metrics({
        'accuracy': 0.85,
        'f1_score': 0.82,
        'latency_ms': 1200
    })
    
    # Log model
    tracker.log_pytorch_model(model, "gnn_model")
```

#### Custom Metrics
```python
# Attack path specific metrics
tracker.log_training_metrics({
    'path_detection_accuracy': 0.92,
    'risk_score_correlation': 0.87,
    'top_k_precision': 0.89,
    'crown_jewels_reachable': 3
})
```

### Model Registry

#### Registering Models
```python
# Register best model
registered_model = tracker.register_model(
    model_name="attack_path_scorer",
    description="Optimized GNN for attack path scoring",
    tags={"environment": "production", "version": "1.0"}
)
```

#### Model Versioning
```python
# Get model versions
client = mlflow.tracking.MlflowClient()
versions = client.get_latest_versions("attack_path_scorer")

# Load specific version
model = mlflow.pytorch.load_model(
    f"models:/attack_path_scorer/{version}"
)
```

### Artifacts and Visualizations

#### Automatic Artifacts
- **Confusion Matrix**: ROC curve plots
- **Training Curves**: Loss and accuracy over time
- **Attack Path Analysis**: Top paths and risk scores
- **Optimization Reports**: Hyperparameter search results

#### Custom Artifacts
```python
# Log custom plots
tracker.log_model_artifacts({
    'attack_path_visualization': 'path_plot.png',
    'hyperparameter_importance': 'param_importance.png',
    'model_architecture': 'architecture.txt'
})
```

## 🎯 Complete Workflow

### 1. Data Preparation
```python
from data.generate_synthetic_data import SyntheticDataGenerator
from scorer.optimized_gnn_service import OptimizedGNNService

# Generate data
generator = SyntheticDataGenerator(seed=42)
data = generator.generate_all()

# Prepare for training
service = OptimizedGNNService()
train_data, val_data, test_data = service.prepare_training_data(
    data['assets'], data['relationships']
)
```

### 2. Hyperparameter Optimization
```python
# Run optimization for multiple model types
optimization_results = service.optimize_hyperparameters(
    train_data=train_data,
    val_data=val_data,
    test_data=test_data,
    model_types=['graphsage', 'gat'],
    n_trials=100
)
```

### 3. Model Training
```python
# Train optimized models
for model_type in ['graphsage', 'gat']:
    result = service.train_optimized_model(
        train_data=train_data,
        val_data=val_data,
        test_data=test_data,
        model_type=model_type,
        use_optimized_params=True
    )
```

### 4. Model Comparison
```python
# Compare all models
comparison = service.compare_models()
best_model = comparison['best_model']

# Get recommendations
recommendations = service.get_model_recommendations()
```

### 5. Production Deployment
```python
# Save best model
service.save_models("models/production")

# Load for inference
service.load_models("models/production")
attack_paths = service.get_attack_paths(
    source="public-vm-001",
    target="crown-jewel-db",
    model_type=recommendations['recommended_model']
)
```

## 📈 Performance Monitoring

### Key Metrics Tracked

#### Model Performance
- **Accuracy**: Overall prediction accuracy
- **Precision/Recall/F1**: Classification metrics
- **AUC-ROC**: Area under ROC curve
- **AUC-PR**: Area under Precision-Recall curve

#### Attack Path Specific
- **Path Detection Accuracy**: Correctly identified attack paths
- **Risk Score Correlation**: Correlation with ground truth risk
- **Top-K Precision**: Precision for top-K recommendations
- **Latency**: Inference time in milliseconds

#### Training Metrics
- **Training Time**: Total training duration
- **Convergence**: Epochs to convergence
- **Loss Curves**: Training and validation loss
- **Learning Rate**: Optimal learning rate found

### Monitoring Dashboard

Access the MLflow UI to view:
- **Experiment Overview**: All runs and their performance
- **Parameter Importance**: Which hyperparameters matter most
- **Model Comparison**: Side-by-side performance comparison
- **Artifact Browser**: Plots, models, and reports
- **Model Registry**: Versioned models ready for deployment

## 🔍 Advanced Features

### Multi-Objective Optimization
```python
# Optimize for both accuracy and latency
def multi_objective(trial):
    accuracy = train_and_evaluate(trial)
    latency = measure_inference_time(trial)
    return accuracy, -latency  # Minimize latency

study = optuna.create_study(directions=['maximize', 'minimize'])
study.optimize(multi_objective, n_trials=100)
```

### Custom Pruners
```python
# Custom pruner for attack path models
class AttackPathPruner(optuna.pruners.BasePruner):
    def prune(self, study, trial):
        # Custom pruning logic based on attack path metrics
        return should_prune(trial)
```

### Model A/B Testing
```python
# Compare models in production
def ab_test_models(model_a, model_b, test_data):
    results_a = evaluate_model(model_a, test_data)
    results_b = evaluate_model(model_b, test_data)
    
    # Log comparison to MLflow
    tracker.log_training_metrics({
        'model_a_f1': results_a['f1_score'],
        'model_b_f1': results_b['f1_score'],
        'improvement': results_b['f1_score'] - results_a['f1_score']
    })
```

## 🛠️ Configuration

### Optuna Configuration
```python
# Custom study configuration
study = optuna.create_study(
    direction='maximize',
    pruner=optuna.pruners.MedianPruner(
        n_startup_trials=10,
        n_warmup_steps=20,
        interval_steps=10
    ),
    sampler=optuna.samplers.TPESampler(
        n_startup_trials=20,
        n_ei_candidates=24
    )
)
```

### MLflow Configuration
```python
# Custom tracking configuration
mlflow.set_tracking_uri("postgresql://user:pass@localhost/mlflow")
mlflow.set_experiment("production_models")

# Custom model logging
mlflow.pytorch.log_model(
    pytorch_model=model,
    artifact_path="attack_path_model",
    signature=signature,
    input_example=input_example,
    registered_model_name="attack_path_scorer"
)
```

## 📚 Best Practices

### 1. Hyperparameter Search
- Start with wide search space, then narrow down
- Use pruning to avoid wasting time on poor trials
- Consider multi-objective optimization for production constraints
- Validate on holdout test set after optimization

### 2. Experiment Tracking
- Use descriptive run names and tags
- Log all relevant metrics, not just final performance
- Include data versioning and preprocessing steps
- Document model architecture and training procedure

### 3. Model Registry
- Use semantic versioning for model releases
- Add comprehensive model descriptions
- Tag models by environment and use case
- Implement model validation before promotion

### 4. Production Deployment
- Monitor model performance in production
- Set up alerts for performance degradation
- Implement model rollback procedures
- Track business impact of model changes

## 🚨 Troubleshooting

### Common Issues

#### Optuna Optimization
- **Slow convergence**: Increase n_trials or adjust search space
- **Memory issues**: Reduce batch size or use gradient accumulation
- **Pruning too aggressive**: Adjust pruner parameters

#### MLflow Tracking
- **Database connection**: Check tracking URI and credentials
- **Artifact storage**: Ensure sufficient disk space
- **Model loading**: Verify model signature and dependencies

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with verbose output
python examples/gnn_optimization_example.py --verbose
```

## 📖 Further Reading

- [Optuna Documentation](https://optuna.readthedocs.io/)
- [MLflow Documentation](https://mlflow.org/docs/)
- [PyTorch Geometric](https://pytorch-geometric.readthedocs.io/)
- [Graph Neural Networks for Cybersecurity](https://arxiv.org/abs/2006.16955)

---

**Built with ❤️ for the cybersecurity community**

For questions or issues, please open an issue on GitHub or check the [Demo Guide](DEMO_GUIDE.md).
