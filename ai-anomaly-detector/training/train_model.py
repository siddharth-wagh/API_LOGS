import pandas as pd
import numpy as np
from elasticsearch import Elasticsearch
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
import matplotlib.pyplot as plt
import joblib
import os
import json
from datetime import datetime, timedelta

print("API Monitoring and Anomaly Detection - Model Training")
print("====================================================")

# Connect to Elasticsearch
print("Connecting to Elasticsearch...")
es = Elasticsearch(["http://localhost:9200"])
print("Connected to Elasticsearch")

# Define the time range for training data
hours_back = 1  # Use data from the last hour
now = datetime.now()
time_from = now - timedelta(hours=hours_back)

# Query for training data
print(f"Extracting data from the last {hours_back} hour(s)...")
query = {
    "query": {
        "bool": {
            "must": [
                {"range": {"@timestamp": {"gte": time_from.isoformat()}}},
                {"exists": {"field": "response.duration_ms"}}
            ]
        }
    },
    "size": 10000
}

# Execute search
response = es.search(index="api-logs-*", body=query)
hits = response["hits"]["hits"]
print(f"Retrieved {len(hits)} records from Elasticsearch")

# Process hits into DataFrame
data = []
for hit in hits:
    source = hit["_source"]
    
    # Extract nested fields
    record = {
        "timestamp": source.get("@timestamp"),
        "service": source.get("service", "unknown"),
        "pattern": source.get("pattern", "unknown"),
        "endpoint": source.get("request", {}).get("endpoint", "/unknown"),
        "method": source.get("request", {}).get("method", "GET"),
        "status_code": source.get("response", {}).get("status_code", 0),
        "duration_ms": source.get("response", {}).get("duration_ms", 0),
        "is_error": source.get("is_error", False),
        "artificial_latency": source.get("artificial_latency", 0)
    }
    data.append(record)

raw_data = pd.DataFrame(data)

# Convert timestamp to datetime
if "timestamp" in raw_data.columns:
    raw_data["timestamp"] = pd.to_datetime(raw_data["timestamp"])

print("\nData Sample:")
print(raw_data.head())

print("\nData Statistics:")
print(raw_data.describe())

# Create time-based features
print("\nCreating time-based features...")
window_minutes = 1  # Reduced from 5 to 1 for more granular data points

# Set timestamp as index
df_copy = raw_data.copy()
df_copy.set_index("timestamp", inplace=True)

# Group by service, endpoint and time window
grouped = df_copy.groupby([
    pd.Grouper(freq=f"{window_minutes}min"),
    "service",
    "endpoint"
])

# Calculate aggregates
aggregates = grouped.agg({
    "duration_ms": ["count", "mean", "std", "min", "max", "median"],
    "is_error": ["sum", "mean"],
    "status_code": ["nunique"]
})

# Flatten column names
aggregates.columns = ["_".join(col).strip() for col in aggregates.columns.values]

# Calculate error rate
aggregates["error_rate"] = aggregates["is_error_mean"] * 100

# Calculate request rate (requests per minute)
aggregates["requests_per_minute"] = aggregates["duration_ms_count"] / window_minutes

# Reset index to make timestamp a column again
features = aggregates.reset_index()

# Fill NaN values
features.fillna({
    "duration_ms_std": 0,
    "duration_ms_median": features["duration_ms_mean"],
    "error_rate": 0
}, inplace=True)

print(f"Created {len(features)} feature records from {len(raw_data)} raw records")

# Select numeric columns for training
numeric_cols = features.select_dtypes(include=[np.number]).columns.tolist()
numeric_cols = [col for col in numeric_cols if col not in ["timestamp", "status_code_nunique"]]

print(f"\nTraining features: {numeric_cols}")

# Create feature matrix
X = features[numeric_cols].copy()
X.fillna(0, inplace=True)

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train Isolation Forest
print("\nTraining Isolation Forest model...")
iso_forest = IsolationForest(
    contamination=0.10,  # Increased from 0.05 to 0.10 to detect more anomalies
    n_estimators=100,
    max_samples="auto",
    random_state=42
)
iso_forest.fit(X_scaled)

# Detect anomalies
print("Detecting anomalies...")
predictions = iso_forest.predict(X_scaled)
anomaly_scores = iso_forest.decision_function(X_scaled)

# Add predictions to features
features["is_anomaly"] = predictions == -1
features["anomaly_score"] = anomaly_scores

num_anomalies = np.sum(predictions == -1)
print(f"Detected {num_anomalies} anomalies out of {len(features)} records")

# Create visualization
print("\nCreating visualizations...")
plt.figure(figsize=(12, 8))

# Plot normal vs anomalous points
plt.subplot(1, 2, 1)
plt.scatter(features[~features["is_anomaly"]]["duration_ms_mean"], 
            features[~features["is_anomaly"]]["error_rate"],
            c="blue", label="Normal", alpha=0.5)

plt.scatter(features[features["is_anomaly"]]["duration_ms_mean"], 
            features[features["is_anomaly"]]["error_rate"],
            c="red", label="Anomaly", alpha=0.7)

plt.xlabel("Mean Response Time (ms)")
plt.ylabel("Error Rate (%)")
plt.title("API Performance Anomaly Detection")
plt.legend()

# Add another plot showing response time over requests/minute
plt.subplot(1, 2, 2)
plt.scatter(features[~features["is_anomaly"]]["requests_per_minute"], 
            features[~features["is_anomaly"]]["duration_ms_mean"],
            c="blue", label="Normal", alpha=0.5)

plt.scatter(features[features["is_anomaly"]]["requests_per_minute"], 
            features[features["is_anomaly"]]["duration_ms_mean"],
            c="red", label="Anomaly", alpha=0.7)

plt.xlabel("Requests per Minute")
plt.ylabel("Mean Response Time (ms)")
plt.title("Traffic Load vs Response Time")
plt.legend()

plt.tight_layout()

# Save the plot
plt.savefig("anomaly_detection.png")
print("Visualization saved as 'anomaly_detection.png'")

# Save models
print("\nSaving models...")
os.makedirs("./models", exist_ok=True)

joblib.dump(iso_forest, "./models/isolation_forest.pkl")
joblib.dump(scaler, "./models/isolation_forest_scaler.pkl")
joblib.dump(numeric_cols, "./models/isolation_forest_features.pkl")

# Save training metadata
metadata = {
    "training_time": datetime.now().isoformat(),
    "training_records": len(raw_data),
    "feature_records": len(features),
    "features": numeric_cols,
    "anomalies_detected": int(num_anomalies)
}

with open("./models/model_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print("\nAnomalous endpoints:")
anomalies = features[features["is_anomaly"]]
if not anomalies.empty:
    anomaly_summary = anomalies.groupby(["service", "endpoint"]).agg({
        "is_anomaly": "count",
        "duration_ms_mean": "mean",
        "error_rate": "mean"
    }).reset_index()
    
    anomaly_summary.columns = ["Service", "Endpoint", "Anomaly Count", "Avg Response Time", "Avg Error Rate"]
    print(anomaly_summary.to_string(index=False))
else:
    print("No anomalies detected in this dataset")

print("\nModel training complete!") 