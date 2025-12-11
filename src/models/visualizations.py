"""
Create visualizations for model analysis:
1. Feature importance chart
2. SVD/PCA dimensionality reduction visualization
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.preprocessing import StandardScaler
import os


def create_feature_importance_chart(feature_names, importances, top_n=10, save_path='images/feature_importance.png'):
    """
    Create a bar chart showing feature importance.
    
    Args:
        feature_names: List of feature names
        importances: Array of importance values
        top_n: Number of top features to show
        save_path: Path to save the image
    """
    # Get top N features
    top_indices = np.argsort(importances)[-top_n:][::-1]
    top_features = [feature_names[i] for i in top_indices]
    top_importances = [importances[i] for i in top_indices]
    
    # Create figure
    plt.figure(figsize=(10, 6))
    plt.barh(range(len(top_features)), top_importances, color='steelblue')
    plt.yticks(range(len(top_features)), top_features)
    plt.xlabel('Feature Importance', fontsize=12)
    plt.title(f'Top {top_n} Most Important Features', fontsize=14, fontweight='bold')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    
    # Save
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Feature importance chart saved to {save_path}")


def create_svd_visualization(X, y_categories, n_components=2, save_path='images/svd_visualization.png'):
    """
    Create SVD/PCA dimensionality reduction visualization.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y_categories: Category labels (High/Medium/Low)
        n_components: Number of components for SVD (2 or 3)
        save_path: Path to save the image
    """
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Apply SVD (using PCA which uses SVD internally)
    if n_components == 2:
        reducer = PCA(n_components=2)
        X_reduced = reducer.fit_transform(X_scaled)
        
        # Create 2D plot
        plt.figure(figsize=(10, 8))
        
        categories = ['Low', 'Medium', 'High']
        colors = ['red', 'orange', 'green']
        
        for i, (cat, color) in enumerate(zip(categories, colors)):
            mask = y_categories == cat
            plt.scatter(X_reduced[mask, 0], X_reduced[mask, 1], 
                       label=cat, alpha=0.6, s=50, c=color)
        
        plt.xlabel(f'First Principal Component (explains {reducer.explained_variance_ratio_[0]:.1%} variance)', fontsize=11)
        plt.ylabel(f'Second Principal Component (explains {reducer.explained_variance_ratio_[1]:.1%} variance)', fontsize=11)
        plt.title('SVD Dimensionality Reduction: Data Visualization in 2D\n(Colored by Reliability Category)', 
                 fontsize=14, fontweight='bold')
        plt.legend(title='Reliability Category', fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"SVD visualization saved to {save_path}")
        print(f"Explained variance: {reducer.explained_variance_ratio_.sum():.1%}")
        
    elif n_components == 3:
        reducer = PCA(n_components=3)
        X_reduced = reducer.fit_transform(X_scaled)
        
        # Create 3D plot
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        categories = ['Low', 'Medium', 'High']
        colors = ['red', 'orange', 'green']
        
        for cat, color in zip(categories, colors):
            mask = y_categories == cat
            ax.scatter(X_reduced[mask, 0], X_reduced[mask, 1], X_reduced[mask, 2],
                      label=cat, alpha=0.6, s=50, c=color)
        
        ax.set_xlabel(f'PC1 ({reducer.explained_variance_ratio_[0]:.1%} variance)')
        ax.set_ylabel(f'PC2 ({reducer.explained_variance_ratio_[1]:.1%} variance)')
        ax.set_zlabel(f'PC3 ({reducer.explained_variance_ratio_[2]:.1%} variance)')
        ax.set_title('SVD Dimensionality Reduction: Data Visualization in 3D\n(Colored by Reliability Category)')
        ax.legend(title='Reliability Category')
        
        # Save
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"SVD 3D visualization saved to {save_path}")
        print(f"Explained variance: {reducer.explained_variance_ratio_.sum():.1%}")


if __name__ == '__main__':
    # Load data and train model
    from src.models.model import train_model, create_features
    
    print("Loading data...")
    data_path = os.path.join(os.path.dirname(__file__), '../../data/with_alerts.csv')
    df = pd.read_csv(data_path)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df[df['datetime'] >= '2019-01-01'].copy()
    
    print("Creating features...")
    df_features = create_features(df)
    
    print("Training model...")
    result = train_model(df_features)
    
    # Create feature importance chart
    print("\nCreating feature importance chart...")
    create_feature_importance_chart(
        result['feature_names'],
        result['clf_importances'],
        top_n=10,
        save_path='images/feature_importance.png'
    )
    
    # Create SVD visualization
    print("\nCreating SVD visualization...")
    # Get the data used for training
    feature_cols = [
        'precip', 'snow',
        'day_of_week', 'month', 'is_weekend', 'is_monday',
        'morning_class_starts', 'afternoon_class_starts', 'total_class_starts',
        'construction_alerts', 'technical_problem_alerts', 'total_alerts',
        'snow_lag_1d', 'snow_lag_7d',
        'total_alerts_lag_1d', 'total_alerts_lag_7d',
        'snow_rolling_3d', 'snow_rolling_7d',
        'total_alerts_rolling_7d', 'total_alerts_rolling_14d',
        'snow_std_7d',
        'alert_pattern_month',
        'days_since_last_alert',
        'snow_x_classes', 'alerts_x_classes',
    ]
    feature_cols = [col for col in feature_cols if col in df_features.columns]
    
    X = df_features[feature_cols].fillna(0).values
    y = df_features['pct'].values
    valid_mask = ~np.isnan(y)
    X = X[valid_mask]
    y = y[valid_mask]
    
    # Create categories
    train_mean = np.mean(y[:int(len(y)*0.8)])
    train_std = np.std(y[:int(len(y)*0.8)])
    y_cat = pd.cut(y, 
                   bins=[0, train_mean - train_std, train_mean + train_std, 1.0],
                   labels=['Low', 'Medium', 'High'])
    
    # Use subset for visualization (faster)
    sample_size = min(2000, len(X))
    indices = np.random.choice(len(X), sample_size, replace=False)
    X_sample = X[indices]
    y_cat_sample = y_cat[indices]
    
    create_svd_visualization(
        X_sample,
        y_cat_sample,
        n_components=2,
        save_path='images/svd_visualization.png'
    )
    
    print("\nAll visualizations created!")

