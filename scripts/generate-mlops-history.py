#!/usr/bin/env python3
"""
Generate historical MLflow and Optuna experiment data for demo purposes.
This creates realistic-looking experiment history to showcase ML Ops practices.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)

def generate_optuna_history():
    """Generate realistic Optuna optimization history."""
    trials = []
    
    # Simulate 50 trials with hyperparameter optimization
    base_score = 0.65
    best_score = 0.94
    
    for trial_num in range(50):
        # Parameters for this trial
        hidden_dim = random.choice([32, 64, 128, 256])
        num_layers = random.randint(2, 5)
        dropout = round(random.uniform(0.1, 0.5), 2)
        learning_rate = round(10 ** random.uniform(-4, -2), 6)
        
        # Score improves over time with some randomness
        progress = trial_num / 50
        score = base_score + (best_score - base_score) * progress + random.uniform(-0.05, 0.05)
        score = min(max(score, 0.60), 0.95)  # Clamp between 0.60 and 0.95
        
        # Some trials get pruned
        state = 'COMPLETE' if random.random() > 0.15 else 'PRUNED'
        
        trial = {
            'trial_number': trial_num,
            'state': state,
            'value': round(score, 4) if state == 'COMPLETE' else None,
            'params': {
                'hidden_dim': hidden_dim,
                'num_layers': num_layers,
                'dropout': dropout,
                'learning_rate': learning_rate,
                'batch_size': random.choice([32, 64, 128]),
                'epochs': random.randint(50, 200)
            },
            'datetime_start': (datetime.now() - timedelta(days=7) + timedelta(hours=trial_num * 0.5)).isoformat(),
            'datetime_complete': (datetime.now() - timedelta(days=7) + timedelta(hours=trial_num * 0.5 + 0.25)).isoformat() if state == 'COMPLETE' else None,
            'duration': round(random.uniform(120, 600), 2)  # seconds
        }
        trials.append(trial)
    
    # Find best trial
    completed_trials = [t for t in trials if t['state'] == 'COMPLETE' and t['value'] is not None]
    best_trial = max(completed_trials, key=lambda x: x['value'])
    
    optuna_data = {
        'study_name': 'gnn_attack_path_optimization',
        'n_trials': len(trials),
        'completed_trials': len([t for t in trials if t['state'] == 'COMPLETE']),
        'pruned_trials': len([t for t in trials if t['state'] == 'PRUNED']),
        'best_trial': best_trial['trial_number'],
        'best_value': best_trial['value'],
        'best_params': best_trial['params'],
        'trials': trials,
        'optimization_direction': 'maximize',
        'study_created': (datetime.now() - timedelta(days=7)).isoformat(),
        'study_completed': datetime.now().isoformat()
    }
    
    return optuna_data


def generate_mlflow_experiments():
    """Generate realistic MLflow experiment history."""
    experiments = []
    
    models = ['GraphSAGE', 'GAT', 'GCN', 'Hybrid']
    
    experiment_id = 1
    for model_type in models:
        # Generate 3-5 runs per model
        n_runs = random.randint(3, 5)
        
        for run_num in range(n_runs):
            # Base metrics that improve over time
            base_accuracy = 0.75 + (run_num * 0.03)
            
            run = {
                'run_id': f'run_{experiment_id:04d}',
                'experiment_id': f'exp_{model_type.lower()}',
                'run_name': f'{model_type}_run_{run_num + 1}',
                'status': 'FINISHED',
                'start_time': (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                'end_time': (datetime.now() - timedelta(days=random.randint(1, 30)) + timedelta(hours=2)).isoformat(),
                'artifact_uri': f'mlruns/0/{experiment_id}/artifacts',
                'lifecycle_stage': 'active',
                'params': {
                    'model_type': model_type,
                    'hidden_dim': random.choice([64, 128, 256]),
                    'num_layers': random.randint(2, 4),
                    'dropout': round(random.uniform(0.1, 0.4), 2),
                    'learning_rate': round(10 ** random.uniform(-4, -2), 6),
                    'batch_size': random.choice([64, 128, 256]),
                    'optimizer': 'Adam',
                    'loss_function': 'BCELoss'
                },
                'metrics': {
                    'accuracy': round(base_accuracy + random.uniform(-0.02, 0.05), 4),
                    'precision': round(base_accuracy + random.uniform(-0.03, 0.04), 4),
                    'recall': round(base_accuracy + random.uniform(-0.02, 0.06), 4),
                    'f1_score': round(base_accuracy + random.uniform(-0.02, 0.04), 4),
                    'auc_roc': round(min(base_accuracy + random.uniform(0.05, 0.15), 0.98), 4),
                    'train_loss': round(random.uniform(0.1, 0.3), 4),
                    'val_loss': round(random.uniform(0.15, 0.35), 4),
                    'path_detection_accuracy': round(base_accuracy + random.uniform(0.0, 0.08), 4),
                    'top_k_precision': round(base_accuracy + random.uniform(0.02, 0.10), 4),
                    'latency_ms': round(random.uniform(50, 200), 2)
                },
                'tags': {
                    'model_family': 'GNN',
                    'task': 'attack_path_scoring',
                    'framework': 'PyTorch Geometric',
                    'optimization': 'Optuna' if run_num >= 2 else 'Manual'
                }
            }
            experiments.append(run)
            experiment_id += 1
    
    mlflow_data = {
        'experiment_name': 'gnn_attack_paths',
        'total_runs': len(experiments),
        'active_runs': 0,
        'experiments': experiments,
        'artifact_location': './mlruns',
        'tracking_uri': 'sqlite:///mlflow.db',
        'created': (datetime.now() - timedelta(days=30)).isoformat(),
        'last_updated': datetime.now().isoformat()
    }
    
    return mlflow_data


def generate_model_comparison():
    """Generate model comparison data."""
    models = [
        {
            'model_name': 'GraphSAGE',
            'version': 'v2.1',
            'accuracy': 0.94,
            'precision': 0.92,
            'recall': 0.96,
            'f1_score': 0.94,
            'latency_ms': 87,
            'training_time_hours': 2.3,
            'params_count': 45728,
            'best_for': 'Overall accuracy'
        },
        {
            'model_name': 'GAT',
            'version': 'v1.8',
            'accuracy': 0.92,
            'precision': 0.94,
            'recall': 0.90,
            'f1_score': 0.92,
            'latency_ms': 142,
            'training_time_hours': 3.1,
            'params_count': 67392,
            'best_for': 'Precision'
        },
        {
            'model_name': 'Hybrid',
            'version': 'v1.5',
            'accuracy': 0.91,
            'precision': 0.89,
            'recall': 0.93,
            'f1_score': 0.91,
            'latency_ms': 65,
            'training_time_hours': 1.8,
            'params_count': 38144,
            'best_for': 'Speed'
        },
        {
            'model_name': 'Baseline (Dijkstra)',
            'version': 'v1.0',
            'accuracy': 0.82,
            'precision': 0.80,
            'recall': 0.84,
            'f1_score': 0.82,
            'latency_ms': 23,
            'training_time_hours': 0,
            'params_count': 0,
            'best_for': 'Baseline'
        }
    ]
    
    return {
        'comparison_date': datetime.now().isoformat(),
        'models': models,
        'recommended_model': 'GraphSAGE',
        'recommendation_reason': 'Best overall accuracy with acceptable latency'
    }


def generate_optimization_timeline():
    """Generate timeline showing optimization progress."""
    timeline = []
    
    # Week 1: Initial baseline
    timeline.append({
        'date': (datetime.now() - timedelta(days=30)).isoformat(),
        'milestone': 'Initial Baseline',
        'best_accuracy': 0.75,
        'model': 'Dijkstra',
        'notes': 'Traditional shortest path algorithm'
    })
    
    # Week 2: First GNN
    timeline.append({
        'date': (datetime.now() - timedelta(days=23)).isoformat(),
        'milestone': 'First GNN Model',
        'best_accuracy': 0.82,
        'model': 'GraphSAGE',
        'notes': 'Initial GraphSAGE implementation'
    })
    
    # Week 3: Optuna optimization starts
    timeline.append({
        'date': (datetime.now() - timedelta(days=16)).isoformat(),
        'milestone': 'Optuna HPO Started',
        'best_accuracy': 0.87,
        'model': 'GraphSAGE (Optimized)',
        'notes': 'Hyperparameter optimization with Optuna (50 trials)'
    })
    
    # Week 4: GAT experiments
    timeline.append({
        'date': (datetime.now() - timedelta(days=9)).isoformat(),
        'milestone': 'GAT Architecture',
        'best_accuracy': 0.90,
        'model': 'GAT',
        'notes': 'Graph Attention Network with learned attention weights'
    })
    
    # Week 5: Hybrid approach
    timeline.append({
        'date': (datetime.now() - timedelta(days=2)).isoformat(),
        'milestone': 'Hybrid Model',
        'best_accuracy': 0.94,
        'model': 'GraphSAGE + GAT Ensemble',
        'notes': 'Ensemble of GraphSAGE and GAT with optimized hyperparameters'
    })
    
    return {
        'timeline': timeline,
        'total_duration_days': 30,
        'total_experiments': 67,
        'accuracy_improvement': '25.3%'
    }


def save_mlops_data():
    """Generate and save all ML Ops demonstration data."""
    logger.info("Generating ML Ops demonstration data")
    
    # Create data directory
    data_dir = Path('data/mlops_history')
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate Optuna data
    logger.info("Generating Optuna optimization history")
    optuna_data = generate_optuna_history()
    with open(data_dir / 'optuna_history.json', 'w') as f:
        json.dump(optuna_data, f, indent=2)
    
    # Generate MLflow data
    logger.info("Generating MLflow experiment history")
    mlflow_data = generate_mlflow_experiments()
    with open(data_dir / 'mlflow_experiments.json', 'w') as f:
        json.dump(mlflow_data, f, indent=2)
    
    # Generate model comparison
    logger.info("Generating model comparison data")
    comparison_data = generate_model_comparison()
    with open(data_dir / 'model_comparison.json', 'w') as f:
        json.dump(comparison_data, f, indent=2)
    
    # Generate optimization timeline
    logger.info("Generating optimization timeline")
    timeline_data = generate_optimization_timeline()
    with open(data_dir / 'optimization_timeline.json', 'w') as f:
        json.dump(timeline_data, f, indent=2)
    
    # Generate summary
    summary = {
        'generated_at': datetime.now().isoformat(),
        'data_files': [
            'optuna_history.json',
            'mlflow_experiments.json',
            'model_comparison.json',
            'optimization_timeline.json'
        ],
        'statistics': {
            'total_optuna_trials': optuna_data['n_trials'],
            'total_mlflow_runs': mlflow_data['total_runs'],
            'best_model': comparison_data['recommended_model'],
            'best_accuracy': max(m['accuracy'] for m in comparison_data['models']),
            'optimization_duration_days': timeline_data['total_duration_days']
        }
    }
    
    with open(data_dir / 'summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info("ML Ops data generated successfully", 
               output_dir=str(data_dir),
               files=len(summary['data_files']))
    
    return summary


def main():
    """Main entry point."""
    print("🔬 Generating ML Ops Demonstration Data")
    print("=" * 60)
    
    try:
        summary = save_mlops_data()
        
        print("\n✅ Data generation completed successfully!")
        print(f"\n📊 Summary:")
        print(f"  - Optuna trials: {summary['statistics']['total_optuna_trials']}")
        print(f"  - MLflow runs: {summary['statistics']['total_mlflow_runs']}")
        print(f"  - Best model: {summary['statistics']['best_model']}")
        print(f"  - Best accuracy: {summary['statistics']['best_accuracy']:.2%}")
        print(f"  - Optimization period: {summary['statistics']['optimization_duration_days']} days")
        print(f"\n📁 Data saved to: data/mlops_history/")
        print(f"\n🚀 Next step: Start your API server to expose this data")
        print(f"   python -m uvicorn api.main:app --reload")
        
    except Exception as e:
        logger.error("Failed to generate ML Ops data", error=str(e))
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

