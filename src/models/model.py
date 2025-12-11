"""
Model for MBTA Reliability Prediction
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error, accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, mutual_info_regression
import warnings
warnings.filterwarnings('ignore')


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create feature set"""
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime').reset_index(drop=True)
    
    # Temporal
    df['day_of_week'] = df['datetime'].dt.dayofweek
    df['month'] = df['datetime'].dt.month
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['is_monday'] = (df['day_of_week'] == 0).astype(int)
    
    # Class schedules
    from src.mbta.class_schedules import get_class_starts_in_window
    
    df['morning_class_starts'] = df.apply(
        lambda row: get_class_starts_in_window(8, 0, 10, 0, row['day_of_week']) 
        if row['day_of_week'] < 5 else 0, axis=1
    )
    df['afternoon_class_starts'] = df.apply(
        lambda row: get_class_starts_in_window(12, 0, 15, 0, row['day_of_week']) 
        if row['day_of_week'] < 5 else 0, axis=1
    )
    df['total_class_starts'] = df['morning_class_starts'] + df['afternoon_class_starts']
    
    # Time-series
    df['snow_lag_1d'] = df['snow'].shift(1)
    df['snow_lag_7d'] = df['snow'].shift(7)
    df['total_alerts_lag_1d'] = df['total_alerts'].shift(1)
    df['total_alerts_lag_7d'] = df['total_alerts'].shift(7)
    
    # Rolling averages
    df['snow_rolling_3d'] = df['snow'].rolling(window=3, min_periods=1).mean()
    df['snow_rolling_7d'] = df['snow'].rolling(window=7, min_periods=1).mean()
    df['total_alerts_rolling_7d'] = df['total_alerts'].rolling(window=7, min_periods=1).mean()
    df['total_alerts_rolling_14d'] = df['total_alerts'].rolling(window=14, min_periods=1).mean()
    
    # Rolling std
    df['snow_std_7d'] = df['snow'].rolling(window=7, min_periods=1).std()
    
    # Alert patterns
    df['alert_pattern_month'] = df.groupby('month')['total_alerts'].transform(
        lambda x: x.expanding().mean()
    )
    df['days_since_last_alert'] = (
        df.groupby((df['total_alerts'] > 0).cumsum()).cumcount()
    )
    
    # Interactions
    df['snow_x_classes'] = df['snow'] * df['total_class_starts']
    df['alerts_x_classes'] = df['total_alerts'] * df['total_class_starts']
    
    return df


def train_model(df: pd.DataFrame):
    """Train production model with both regression and classification"""
    
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
    
    feature_cols = [col for col in feature_cols if col in df.columns]
    
    X = df[feature_cols].fillna(0).values
    y = df['pct'].values
    
    valid_mask = ~np.isnan(y)
    X = X[valid_mask]
    y = y[valid_mask]
    
    # Feature selection
    selector = SelectKBest(score_func=mutual_info_regression, k=min(20, X.shape[1]))
    X_selected = selector.fit_transform(X, y)
    selected_indices = selector.get_support(indices=True)
    selected_features = [feature_cols[i] for i in selected_indices]
    
    # Split
    split_idx = int(len(X_selected) * 0.8)
    X_train, X_test = X_selected[:split_idx], X_selected[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # Create reliability categories (High/Medium/Low)
    train_mean = np.mean(y_train)
    train_std = np.std(y_train)
    y_train_cat = pd.cut(y_train, 
                        bins=[0, train_mean - train_std, train_mean + train_std, 1.0],
                        labels=['Low', 'Medium', 'High'])
    y_test_cat = pd.cut(y_test,
                       bins=[0, train_mean - train_std, train_mean + train_std, 1.0],
                       labels=['Low', 'Medium', 'High'])
    
    # Scale
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Regression model
    reg_model = RandomForestRegressor(
        n_estimators=300,
        max_depth=6,
        min_samples_split=15,
        min_samples_leaf=8,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1
    )
    
    reg_model.fit(X_train_scaled, y_train)
    y_pred_reg = reg_model.predict(X_test_scaled)
    
    # Classification model
    clf_model = RandomForestClassifier(
        n_estimators=300,
        max_depth=6,
        min_samples_split=15,
        min_samples_leaf=8,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1
    )
    
    clf_model.fit(X_train_scaled, y_train_cat)
    y_pred_clf = clf_model.predict(X_test_scaled)
    
    # Metrics
    reg_r2 = r2_score(y_test, y_pred_reg)
    reg_rmse = np.sqrt(mean_squared_error(y_test, y_pred_reg))
    reg_mae = mean_absolute_error(y_test, y_pred_reg)
    
    clf_accuracy = accuracy_score(y_test_cat, y_pred_clf)
    
    # Baseline
    baseline_pred = np.full_like(y_test, np.mean(y_train))
    baseline_r2 = r2_score(y_test, baseline_pred)
    baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_pred))
    
    # Feature importance
    reg_importances = reg_model.feature_importances_
    clf_importances = clf_model.feature_importances_
    
    return {
        'reg_model': reg_model,
        'clf_model': clf_model,
        'scaler': scaler,
        'feature_names': selected_features,
        'reg_r2': reg_r2,
        'reg_rmse': reg_rmse,
        'reg_mae': reg_mae,
        'clf_accuracy': clf_accuracy,
        'baseline_r2': baseline_r2,
        'baseline_rmse': baseline_rmse,
        'reg_importances': reg_importances,
        'clf_importances': clf_importances,
        'classification_report': classification_report(y_test_cat, y_pred_clf)
    }


if __name__ == '__main__':
    print("="*70)
    print("MODEL - Pattern Discovery & Prediction")
    print("="*70)
    
    # Load data
    print("\nLoading data...")
    import os
    data_path = os.path.join(os.path.dirname(__file__), '../../data/with_alerts.csv')
    df = pd.read_csv(data_path)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df[df['datetime'] >= '2019-01-01'].copy()
    
    print(f"Dataset: {len(df)} rows")
    print(f"Avg reliability: {df['pct'].mean():.3f} ({df['pct'].mean()*100:.1f}%)")
    
    # Create features
    print("\nCreating features...")
    df_features = create_features(df)
    
    # Train model
    print("\nTraining models...")
    result = train_model(df_features)
    
    # Results
    print("\n" + "="*70)
    print("MODEL RESULTS")
    print("="*70)
    
    print(f"\nBASELINE (predicting mean):")
    print(f"   Test R²:  {result['baseline_r2']:.4f}")
    print(f"   Test RMSE: {result['baseline_rmse']:.4f}")
    
    print(f"\nREGRESSION MODEL (Predicting Reliability %):")
    print(f"   Test R²:  {result['reg_r2']:.4f}")
    print(f"   Test RMSE: {result['reg_rmse']:.4f}")
    print(f"   Test MAE:  {result['reg_mae']:.4f}")
    
    if result['reg_r2'] > result['baseline_r2']:
        print(f"   Model improves over baseline!")
    elif result['reg_rmse'] < result['baseline_rmse']:
        improvement = ((result['baseline_rmse'] - result['reg_rmse']) / result['baseline_rmse']) * 100
        print(f"   Model reduces RMSE by {improvement:.1f}%")
    
    print(f"\n📈 CLASSIFICATION MODEL (High/Medium/Low Reliability):")
    print(f"   Accuracy: {result['clf_accuracy']:.4f} ({result['clf_accuracy']*100:.1f}%)")
    print(f"\n   Classification Report:")
    print(result['classification_report'])
    
    print(f"\nTOP 10 FEATURES (Regression):")
    indices = np.argsort(result['reg_importances'])[-10:][::-1]
    for i, idx in enumerate(indices, 1):
        print(f"   {i:2d}. {result['feature_names'][idx]:<40s} {result['reg_importances'][idx]:>8.4f}")
    
    print(f"\nKEY INSIGHTS:")
    top_features = [result['feature_names'][idx] for idx in np.argsort(result['reg_importances'])[-5:][::-1]]
    print(f"   • Most important factors: {', '.join(top_features[:3])}")
    print(f"   • Model learns patterns in: time-series, alerts, weather")
    print(f"   • Classification accuracy: {result['clf_accuracy']*100:.1f}% for reliability categories")
    
    print(f"\nMODEL SUMMARY:")
    print(f"   Regression: Random Forest (300 trees)")
    print(f"   Classification: Random Forest (300 trees)")
    print(f"   Features: {len(result['feature_names'])}")
    
    print("\nModel ready!")

