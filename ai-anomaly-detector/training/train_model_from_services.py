import pandas as pd
import numpy as np
from elasticsearch import Elasticsearch
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import joblib
import os
import json
from datetime import datetime, timedelta
import seaborn as sns

print("API Monitoring and Anomaly Detection - Service-Based Model Training")
print("=================================================================")

# Connect to Elasticsearch
print("Connecting to Elasticsearch...")
es = Elasticsearch(["http://localhost:9200"])
print("Connected to Elasticsearch")

# Define the indices to use
indices = ["api-training-data", "api-logs-*"]
print(f"Using indices: {indices}")

# Get all service logs from the last 2 hours
print("Extracting service data from Elasticsearch...")
now = datetime.now()
time_from = now - timedelta(hours=2)

query = {
    "query": {
        "bool": {
            "must": [
                {"range": {"@timestamp": {"gte": time_from.isoformat()}}},
            ]
        }
    },
    "size": 10000
}

# Execute search across multiple indices
response = es.search(index=",".join(indices), body=query)
hits = response["hits"]["hits"]
print(f"Retrieved {len(hits)} records from Elasticsearch")

# Process hits into DataFrame
data = []
for hit in hits:
    source = hit["_source"]
    
    try:
        # Get service info
        if isinstance(source.get("service"), dict):
            service_name = source.get("service", {}).get("name", "unknown")
        else:
            service_name = source.get("service", "unknown")
        
        # Get request info
        if isinstance(source.get("request"), dict):
            request = source.get("request", {})
            endpoint = request.get("endpoint", "/unknown")
            method = request.get("method", "GET")
        else:
            if isinstance(source.get("http"), dict):
                endpoint = source.get("http", {}).get("target", "/unknown")
                method = source.get("http", {}).get("method", "GET")
            else:
                endpoint = "/unknown"
                method = "GET"
        
        # Get response info
        if isinstance(source.get("response"), dict):
            response_data = source.get("response", {})
            status_code = response_data.get("status_code", 200)
            duration_ms = response_data.get("duration_ms", 0)
        else:
            if isinstance(source.get("http"), dict):
                status_code = source.get("http", {}).get("status_code", 200)
                duration_ms = source.get("duration_ms", 0)
            else:
                status_code = 200
                duration_ms = 0
        
        # Determine if it's an error
        is_error = source.get("is_error", status_code >= 400)
        
        # Check if it's an artificial anomaly
        is_artificial_anomaly = source.get("artificial_anomaly", False)
        
        record = {
            "timestamp": source.get("@timestamp"),
            "service": service_name,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "is_error": is_error,
            "is_artificial_anomaly": is_artificial_anomaly
        }
        data.append(record)
    except Exception as e:
        print(f"Error processing record: {e}")
        continue

raw_data = pd.DataFrame(data)

if len(raw_data) == 0:
    print("No data found. Please run 'inject_service_data.py' first to generate training data.")
    exit(1)

# Convert timestamp to datetime
if "timestamp" in raw_data.columns:
    print("Converting timestamps to datetime...")
    # Try to handle different timestamp formats with flexible parsing
    raw_data["timestamp"] = pd.to_datetime(raw_data["timestamp"], errors='coerce')
    # Drop rows with invalid timestamps
    raw_data = raw_data.dropna(subset=["timestamp"])
    print(f"Converted timestamps using flexible parsing. {len(raw_data)} valid records remain.")

print("\nData Sample:")
print(raw_data.head())

print("\nServices found in data:")
print(raw_data["service"].value_counts())

print("\nEndpoints found in data:")
print(raw_data["endpoint"].value_counts())

print("\nData Statistics:")
print(raw_data.describe())

# Create time-based features
print("\nCreating time-based features...")
window_minutes = 1  # 1-minute window for more granular analysis

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
    contamination=0.15,  # Increased to 0.15 to detect more anomalies
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

# Create visualizations
print("\nCreating visualizations...")
plt.figure(figsize=(15, 10))

# Plot 1: Response Time vs Error Rate
plt.subplot(2, 2, 1)
normal = features[~features["is_anomaly"]]
anomalies = features[features["is_anomaly"]]

plt.scatter(normal["duration_ms_mean"], 
            normal["error_rate"],
            c="blue", label="Normal", alpha=0.5, s=50)

plt.scatter(anomalies["duration_ms_mean"], 
            anomalies["error_rate"],
            c="red", label="Anomaly", alpha=0.7, s=70)

plt.xlabel("Mean Response Time (ms)")
plt.ylabel("Error Rate (%)")
plt.title("API Performance Anomaly Detection")
plt.legend()

# Plot 2: Traffic Load vs Response Time
plt.subplot(2, 2, 2)
plt.scatter(normal["requests_per_minute"], 
            normal["duration_ms_mean"],
            c="blue", label="Normal", alpha=0.5, s=50)

plt.scatter(anomalies["requests_per_minute"], 
            anomalies["duration_ms_mean"],
            c="red", label="Anomaly", alpha=0.7, s=70)

plt.xlabel("Requests per Minute")
plt.ylabel("Mean Response Time (ms)")
plt.title("Traffic Load vs Response Time")
plt.legend()

# Plot 3: Anomaly Score Distribution
plt.subplot(2, 2, 3)
sns.histplot(features["anomaly_score"], bins=30, kde=True)
plt.axvline(x=0, color='r', linestyle='--')
plt.title("Anomaly Score Distribution")
plt.xlabel("Anomaly Score")
plt.ylabel("Frequency")

# Plot 4: Service-specific Response Times
plt.subplot(2, 2, 4)
service_endpoints = features.groupby(["service", "endpoint"])["duration_ms_mean"].mean().reset_index()
service_endpoints["label"] = service_endpoints["service"] + ": " + service_endpoints["endpoint"]
service_endpoints = service_endpoints.sort_values("duration_ms_mean", ascending=False)

colors = sns.color_palette("husl", len(service_endpoints))
plt.bar(service_endpoints["label"], service_endpoints["duration_ms_mean"], color=colors)
plt.xticks(rotation=45, ha="right")
plt.title("Average Response Time by Service & Endpoint")
plt.ylabel("Mean Response Time (ms)")
plt.tight_layout()

plt.tight_layout()

# Save the plot
plt.savefig("service_anomaly_detection.png")
print("Visualization saved as 'service_anomaly_detection.png'")

# Save models
print("\nSaving models...")
os.makedirs("./models", exist_ok=True)

joblib.dump(iso_forest, "./models/service_isolation_forest.pkl")
joblib.dump(scaler, "./models/service_isolation_forest_scaler.pkl")
joblib.dump(numeric_cols, "./models/service_isolation_forest_features.pkl")

# Save training metadata
metadata = {
    "training_time": datetime.now().isoformat(),
    "training_records": len(raw_data),
    "feature_records": len(features),
    "features": numeric_cols,
    "anomalies_detected": int(num_anomalies),
    "services": raw_data["service"].unique().tolist(),
    "endpoints": raw_data["endpoint"].unique().tolist()
}

with open("./models/service_model_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print("\nAnomalous service endpoints:")
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