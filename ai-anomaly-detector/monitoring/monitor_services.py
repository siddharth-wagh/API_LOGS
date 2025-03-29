import pandas as pd
import numpy as np
from elasticsearch import Elasticsearch
import joblib
import time
import os
import json
from datetime import datetime, timedelta
import colorama
from colorama import Fore, Style
import matplotlib.pyplot as plt
import seaborn as sns

# Initialize colorama
colorama.init()

class ServiceMonitor:
    def __init__(self, es_host="http://localhost:9200", check_interval=30, 
                 model_path="./models/service_isolation_forest.pkl"):
        """Initialize the service monitor"""
        print(f"{Fore.CYAN}Service Performance Monitor{Style.RESET_ALL}")
        print(f"{Fore.CYAN}========================={Style.RESET_ALL}")
        
        # Connect to Elasticsearch
        print("Connecting to Elasticsearch...")
        self.es = Elasticsearch([es_host])
        print("Connected to Elasticsearch")
        
        # Set check interval
        self.check_interval = check_interval
        print(f"Check interval set to {check_interval} seconds")
        
        # Set model path
        self.model_path = model_path
        
        # Load models if they exist
        self.model = None
        self.scaler = None
        self.features = None
        self.load_models()
        
        # Initialize state
        self.last_check = datetime.now() - timedelta(minutes=5)
        self.anomaly_history = []
        self.service_stats = {}
        
        print(f"{Fore.GREEN}Monitor initialized successfully{Style.RESET_ALL}")
    
    def load_models(self):
        """Load the trained models"""
        print("Loading machine learning models...")
        
        # Check if models exist
        if not os.path.exists(self.model_path):
            print(f"{Fore.RED}Model not found at {self.model_path}. Please run train_model_from_services.py first.{Style.RESET_ALL}")
            return False
        
        try:
            # Load model, scaler, and features
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.model_path.replace(".pkl", "_scaler.pkl"))
            self.features = joblib.load(self.model_path.replace(".pkl", "_features.pkl"))
            
            # Load metadata
            with open(self.model_path.replace(".pkl", "_metadata.json"), "r") as f:
                self.metadata = json.load(f)
            
            print(f"Models loaded successfully (trained on {self.metadata['training_records']} records)")
            return True
        except Exception as e:
            print(f"{Fore.RED}Error loading models: {e}{Style.RESET_ALL}")
            return False
    
    def get_recent_logs(self, minutes_back=5):
        """Get recent logs from Elasticsearch"""
        now = datetime.now()
        time_from = now - timedelta(minutes=minutes_back)
        
        # Query for recent logs
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": time_from.isoformat(), "lt": now.isoformat()}}},
                    ]
                }
            },
            "size": 10000
        }
        
        # Execute search
        indices = ["api-training-data", "api-logs-*"]
        response = self.es.search(index=",".join(indices), body=query)
        hits = response["hits"]["hits"]
        
        print(f"Retrieved {len(hits)} log records from the last {minutes_back} minutes")
        
        return hits
    
    def process_logs(self, hits):
        """Process logs into features for anomaly detection"""
        # Process hits into DataFrame
        data = []
        for hit in hits:
            source = hit["_source"]
            
            # Get service info
            service_name = source.get("service", {}).get("name", 
                        source.get("labels", {}).get("service", "unknown"))
            
            # Get request info
            request = source.get("request", {})
            endpoint = request.get("endpoint", 
                        source.get("http", {}).get("target", "/unknown"))
            method = request.get("method", 
                    source.get("http", {}).get("method", "GET"))
            
            # Get response info
            response_data = source.get("response", {})
            status_code = response_data.get("status_code", 
                        source.get("http", {}).get("status_code", 200))
            duration_ms = response_data.get("duration_ms", 
                        source.get("duration_ms", 0))
            
            # Determine if it's an error
            is_error = source.get("is_error", status_code >= 400)
            
            record = {
                "timestamp": source.get("@timestamp"),
                "service": service_name,
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "is_error": is_error
            }
            data.append(record)
        
        # If no data, return empty DataFrame
        if not data:
            return pd.DataFrame()
        
        raw_data = pd.DataFrame(data)
        
        # Convert timestamp to datetime
        if "timestamp" in raw_data.columns:
            raw_data["timestamp"] = pd.to_datetime(raw_data["timestamp"])
        
        # Create time-based features
        window_minutes = 1
        
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
        
        # Update service stats
        for _, row in features.iterrows():
            service_key = f"{row['service']}:{row['endpoint']}"
            if service_key not in self.service_stats:
                self.service_stats[service_key] = {
                    "service": row["service"],
                    "endpoint": row["endpoint"],
                    "request_count": 0,
                    "avg_duration": 0,
                    "error_count": 0,
                    "anomaly_count": 0,
                    "last_anomaly": None
                }
            
            # Update stats
            stats = self.service_stats[service_key]
            stats["request_count"] += row["duration_ms_count"]
            stats["avg_duration"] = (stats["avg_duration"] + row["duration_ms_mean"]) / 2
            stats["error_count"] += row["is_error_sum"]
        
        return features
    
    def detect_anomalies(self, features):
        """Detect anomalies in the features"""
        if self.model is None or features.empty:
            return features
        
        # Select only the columns used during training
        feature_cols = [col for col in self.features if col in features.columns]
        
        if not feature_cols:
            print(f"{Fore.YELLOW}Warning: No matching features found for anomaly detection{Style.RESET_ALL}")
            return features
        
        # Create feature matrix
        X = features[feature_cols].copy()
        X.fillna(0, inplace=True)
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Detect anomalies
        predictions = self.model.predict(X_scaled)
        anomaly_scores = self.model.decision_function(X_scaled)
        
        # Add predictions to features
        features["is_anomaly"] = predictions == -1
        features["anomaly_score"] = anomaly_scores
        
        # Record anomalies
        anomalies = features[features["is_anomaly"]]
        if not anomalies.empty:
            for _, row in anomalies.iterrows():
                # Update service stats
                service_key = f"{row['service']}:{row['endpoint']}"
                if service_key in self.service_stats:
                    self.service_stats[service_key]["anomaly_count"] += 1
                    self.service_stats[service_key]["last_anomaly"] = row["timestamp"]
                
                # Add to anomaly history
                self.anomaly_history.append({
                    "timestamp": row["timestamp"],
                    "service": row["service"],
                    "endpoint": row["endpoint"],
                    "duration_ms": row["duration_ms_mean"],
                    "error_rate": row["error_rate"],
                    "anomaly_score": row["anomaly_score"],
                    "requests_per_minute": row["requests_per_minute"]
                })
        
        return features
    
    def report_anomalies(self, anomalies):
        """Report detected anomalies"""
        if anomalies.empty:
            print(f"{Fore.GREEN}No anomalies detected{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.RED}Detected {len(anomalies)} anomalies:{Style.RESET_ALL}")
        
        # Group anomalies by service and endpoint
        anomaly_summary = anomalies.groupby(["service", "endpoint"]).agg({
            "is_anomaly": "count",
            "duration_ms_mean": "mean",
            "error_rate": "mean",
            "anomaly_score": "mean"
        }).reset_index()
        
        # Print summary
        for _, row in anomaly_summary.iterrows():
            service = row["service"]
            endpoint = row["endpoint"]
            count = row["is_anomaly"]
            duration = row["duration_ms_mean"]
            error_rate = row["error_rate"]
            score = row["anomaly_score"]
            
            print(f"{Fore.RED}⚠️ {service}:{endpoint} - {count} anomalies{Style.RESET_ALL}")
            print(f"   Response Time: {duration:.2f}ms")
            print(f"   Error Rate: {error_rate:.2f}%")
            print(f"   Anomaly Score: {score:.4f}")
    
    def create_visualization(self):
        """Create visualization of recent anomalies"""
        if not self.anomaly_history:
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(self.anomaly_history)
        
        # Only keep the last 100 anomalies
        if len(df) > 100:
            df = df.iloc[-100:]
        
        # Create plot
        plt.figure(figsize=(12, 8))
        
        # Plot 1: Anomalies over time
        plt.subplot(2, 1, 1)
        for service in df["service"].unique():
            service_df = df[df["service"] == service]
            plt.scatter(service_df["timestamp"], service_df["duration_ms"], 
                       label=service, s=100, alpha=0.7)
        
        plt.xlabel("Time")
        plt.ylabel("Response Time (ms)")
        plt.title("Anomalies Over Time")
        plt.legend()
        
        # Plot 2: Service stats
        plt.subplot(2, 1, 2)
        service_stats_df = pd.DataFrame(list(self.service_stats.values()))
        
        if not service_stats_df.empty:
            service_stats_df["error_rate"] = (service_stats_df["error_count"] / 
                                           service_stats_df["request_count"]) * 100
            service_stats_df["label"] = service_stats_df["service"] + ": " + service_stats_df["endpoint"]
            
            # Sort by anomaly count
            service_stats_df = service_stats_df.sort_values("anomaly_count", ascending=False)
            
            colors = sns.color_palette("coolwarm", len(service_stats_df))
            plt.bar(service_stats_df["label"], service_stats_df["anomaly_count"], color=colors)
            plt.xticks(rotation=45, ha="right")
            plt.title("Anomaly Count by Service & Endpoint")
            plt.ylabel("Anomaly Count")
        
        plt.tight_layout()
        plt.savefig("service_monitor_anomalies.png")
        print(f"Visualization saved as 'service_monitor_anomalies.png'")
    
    def run_check(self):
        """Run a single monitoring check"""
        print(f"\n{Fore.CYAN}--- Running check at {datetime.now().strftime('%H:%M:%S')} ---{Style.RESET_ALL}")
        
        # Check if models are loaded
        if self.model is None and not self.load_models():
            print(f"{Fore.RED}Cannot run check: Models not loaded.{Style.RESET_ALL}")
            return
        
        # Get recent logs
        minutes_back = int((datetime.now() - self.last_check).total_seconds() / 60) + 1
        hits = self.get_recent_logs(minutes_back=minutes_back)
        
        if not hits:
            print(f"{Fore.YELLOW}No logs to analyze{Style.RESET_ALL}")
            return
        
        # Process logs into features
        features = self.process_logs(hits)
        
        if features.empty:
            print(f"{Fore.YELLOW}No features extracted from logs{Style.RESET_ALL}")
            return
        
        # Detect anomalies
        features = self.detect_anomalies(features)
        
        # Report anomalies
        anomalies = features[features["is_anomaly"]]
        self.report_anomalies(anomalies)
        
        # Create visualization
        if not anomalies.empty:
            self.create_visualization()
        
        # Update last check time
        self.last_check = datetime.now()
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        print(f"{Fore.GREEN}Starting continuous monitoring...{Style.RESET_ALL}")
        print(f"Press Ctrl+C to stop")
        
        try:
            while True:
                self.run_check()
                print(f"\nNext check in {self.check_interval} seconds...")
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Monitoring stopped by user{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        monitor = ServiceMonitor(check_interval=30)
        monitor.start_monitoring()
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}") 