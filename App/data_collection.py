import os
import pandas as pd
import numpy as np
from datetime import timedelta
from flask import jsonify, request
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer  # Handle missing values
import joblib
import matplotlib.pyplot as plt


# Define the new CSV file path
CSV_FILE_PATH = "data.csv"

# Load the CSV data into a DataFrame
df = pd.read_csv(CSV_FILE_PATH)

# Convert 'datetime' to UNIX timestamp and add features
df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')

# Drop rows where 'datetime' conversion failed (NaT values)
df = df.dropna(subset=['datetime'])

df['timestamp'] = df['datetime'].astype('int64') // 10**9  # Convert to UNIX timestamp
df['hour'] = df['datetime'].dt.hour
df['day_of_week'] = df['datetime'].dt.dayofweek

# Normalize 'duration' to minutes (if required)
df['duration'] = df['duration'] / 60

# Ensure necessary columns exist
required_columns = ['timestamp', 'duration', 'hour', 'day_of_week', 'remainingFuel']
missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    raise ValueError(f"Missing columns in dataset: {missing_columns}")

# Handle NaN values in X and y
X = df[['timestamp', 'duration', 'hour', 'day_of_week', 'remainingFuel']]
y = df['remainingFuel']

# Drop rows where 'remainingFuel' is NaN
df = df.dropna(subset=['remainingFuel'])

# Use an imputer to fill NaN values in X
imputer = SimpleImputer(strategy="mean")
X_imputed = imputer.fit_transform(X)

# Pipeline: Imputation -> Scaling -> Gradient Boosting Regressor
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('regressor', GradientBoostingRegressor())
])

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X_imputed, y, test_size=0.3, random_state=42)

# Hyperparameter tuning using GridSearchCV
param_grid = {
    'regressor__n_estimators': [100, 200, 300],
    'regressor__learning_rate': [0.01, 0.05, 0.1],
    'regressor__max_depth': [3, 5, 7],
    'regressor__min_samples_split': [2, 5, 10],
    'regressor__subsample': [0.8, 1.0]
}

grid_search = GridSearchCV(pipeline, param_grid, cv=5, scoring='neg_mean_squared_error', n_jobs=-1)
grid_search.fit(X_train, y_train)

# Best model from GridSearchCV
best_pipeline = grid_search.best_estimator_

# Save the trained model pipeline
MODEL_FILE_PATH = "gradient_boosting_pipeline.pkl"
joblib.dump(best_pipeline, MODEL_FILE_PATH)

# Predict on the test set
y_pred = best_pipeline.predict(X_test)

# Evaluation metrics
mse = mean_squared_error(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Gradient Boosting - MSE: {mse}, MAE: {mae}, R^2: {r2}")

# Visualization: Actual vs Predicted Fuel Consumption
plt.figure(figsize=(8, 6))
plt.scatter(y_test, y_pred, color='green', label='Predicted vs Actual')
plt.plot([min(y_test), max(y_test)], [min(y_test), max(y_test)], color='red', linestyle='--', label='Perfect Prediction (y=x)')
plt.xlabel('Actual Remaining Fuel')
plt.ylabel('Predicted Remaining Fuel')
plt.title('Actual vs Predicted Remaining Fuel (Gradient Boosting Regression)')
plt.legend()
plt.grid(True)
plt.show()
