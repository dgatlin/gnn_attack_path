"""
Example script demonstrating Optuna hyperparameter optimization and MLflow tracking
for GNN attack path scoring models.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import numpy as np
from typing import Dict, Any
import structlog

from data.generate_synthetic_data import SyntheticDataGenerator
from scorer.optimized_gnn_service import OptimizedGNNService
from scorer.optuna_optimization import GNNHyperparameterOptimizer
from scorer.mlflow_tracking import MLflowTracker

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


def main():
    """Main example demonstrating GNN optimization with Optuna and MLflow."""
    logger.info("Starting GNN optimization example")
    
    # Step 1: Generate synthetic data
    logger.info("Step 1: Generating synthetic data")
    generator = SyntheticDataGenerator(seed=42)
    data = generator.generate_all()
    
    # Convert to PyTorch Geometric format
    from scorer.gnn_model import AttackPathGNN
    gnn = AttackPathGNN()
    train_data, val_data, test_data = gnn.prepare_data(
        data['assets'], data['relationships']
    )
    
    logger.info("Data generated", 
               nodes=train_data.x.size(0),
               edges=train_data.edge_index.size(1))
    
    # Step 2: Initialize optimized GNN service
    logger.info("Step 2: Initializing optimized GNN service")
    service = OptimizedGNNService(
        device='cpu',
        mlflow_experiment="gnn-attack-paths-demo",
        optuna_study_name="gnn_demo_optimization"
    )
    
    # Step 3: Run hyperparameter optimization
    logger.info("Step 3: Running hyperparameter optimization")
    optimization_results = service.optimize_hyperparameters(
        train_data=train_data,
        val_data=val_data,
        test_data=test_data,
        model_types=['graphsage', 'gat'],
        n_trials=20  # Reduced for demo
    )
    
    # Print optimization results
    logger.info("Optimization results", results=optimization_results)
    
    # Step 4: Train optimized models
    logger.info("Step 4: Training optimized models")
    training_results = {}
    
    for model_type in ['graphsage', 'gat']:
        logger.info(f"Training {model_type} model")
        result = service.train_optimized_model(
            train_data=train_data,
            val_data=val_data,
            test_data=test_data,
            model_type=model_type,
            use_optimized_params=True
        )
        training_results[model_type] = result
        
        logger.info(f"{model_type} training completed", 
                   performance=result['performance'])
    
    # Step 5: Compare models
    logger.info("Step 5: Comparing models")
    comparison = service.compare_models()
    logger.info("Model comparison", comparison=comparison)
    
    # Step 6: Get recommendations
    logger.info("Step 6: Getting model recommendations")
    recommendations = service.get_model_recommendations()
    logger.info("Model recommendations", recommendations=recommendations)
    
    # Step 7: Generate experiment report
    logger.info("Step 7: Generating experiment report")
    report = service.generate_experiment_report()
    logger.info("Experiment report", report=report)
    
    # Step 8: Save models
    logger.info("Step 8: Saving models")
    service.save_models("models/optimized")
    
    # Step 9: Demonstrate attack path prediction
    logger.info("Step 9: Demonstrating attack path prediction")
    best_model_type = recommendations['recommended_model']
    
    attack_paths = service.get_attack_paths(
        source="asset-001",
        target="crown-jewel-db-001",
        model_type=best_model_type,
        max_hops=4
    )
    
    logger.info("Attack paths found", 
               count=len(attack_paths),
               model_type=best_model_type)
    
    for i, path in enumerate(attack_paths):
        logger.info(f"Path {i+1}", 
                   path=path['path'],
                   score=path['score'],
                   algorithm=path['algorithm'])
    
    # Step 10: Show MLflow UI information
    logger.info("Step 10: MLflow tracking information")
    logger.info("MLflow UI available at: http://localhost:5000")
    logger.info("To start MLflow UI: mlflow ui --backend-store-uri sqlite:///mlflow.db")
    
    logger.info("GNN optimization example completed successfully!")


def demonstrate_individual_components():
    """Demonstrate individual Optuna and MLflow components."""
    logger.info("Demonstrating individual components")
    
    # Generate sample data
    generator = SyntheticDataGenerator(seed=42)
    data = generator.generate_all()
    
    # Prepare data
    gnn = AttackPathGNN()
    train_data, val_data, test_data = gnn.prepare_data(
        data['assets'], data['relationships']
    )
    
    # 1. Demonstrate Optuna optimization
    logger.info("1. Demonstrating Optuna optimization")
    optimizer = GNNHyperparameterOptimizer(model_type='graphsage')
    optuna_result = optimizer.optimize(
        train_data=train_data,
        val_data=val_data,
        test_data=test_data,
        n_trials=10
    )
    
    logger.info("Optuna optimization completed", 
               best_params=optuna_result['best_params'],
               best_score=optuna_result['best_score'])
    
    # 2. Demonstrate MLflow tracking
    logger.info("2. Demonstrating MLflow tracking")
    tracker = MLflowTracker(experiment_name="individual_demo")
    
    with tracker.start_run(run_name="demo_run") as run:
        # Log parameters
        tracker.log_model_parameters({
            'model_type': 'graphsage',
            'hidden_dim': 64,
            'num_layers': 2,
            'dropout': 0.1
        })
        
        # Log metrics
        tracker.log_training_metrics({
            'accuracy': 0.85,
            'precision': 0.82,
            'recall': 0.88,
            'f1_score': 0.85
        })
        
        # Log attack path analysis
        tracker.log_attack_path_analysis({
            'total_paths': 15,
            'high_risk_paths': 3,
            'avg_path_length': 2.5,
            'crown_jewels_reachable': 2
        })
        
        logger.info("MLflow tracking completed", run_id=run.info.run_id)
    
    # 3. Demonstrate model comparison
    logger.info("3. Demonstrating model comparison")
    comparison = tracker.compare_models([run.info.run_id])
    logger.info("Model comparison", comparison=comparison)
    
    # 4. Generate experiment report
    logger.info("4. Generating experiment report")
    report = tracker.generate_experiment_report()
    logger.info("Experiment report", report=report)


if __name__ == "__main__":
    print("🛡️ GNN Attack Path Demo - Optuna & MLflow Integration")
    print("=" * 60)
    
    try:
        # Run main example
        main()
        
        print("\n" + "=" * 60)
        print("✅ Main example completed successfully!")
        
        # Run individual components demo
        print("\n🔧 Running individual components demo...")
        demonstrate_individual_components()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("\n📊 Next steps:")
        print("1. Start MLflow UI: mlflow ui --backend-store-uri sqlite:///mlflow.db")
        print("2. View experiments at: http://localhost:5000")
        print("3. Check saved models in: models/optimized/")
        print("4. Review optimization results in: optimization_report.json")
        
    except Exception as e:
        logger.error("Example failed", error=str(e))
        print(f"❌ Example failed: {e}")
        sys.exit(1)
