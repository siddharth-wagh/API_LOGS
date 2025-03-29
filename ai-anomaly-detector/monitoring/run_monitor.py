import time
import os
import pandas as pd
import numpy as np
import json
import joblib
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("api_monitor")

class APIMonitor:
    def __init__(self):
        """Initialize the API monitor with Elasticsearch connection and model loading."""
        self.es = Elasticsearch("http://localhost:9200")
        self.model_dir = "./models"
        self.load_models()
        
    def load_models(self):
        """Load the trained models and metadata from the models directory."""
        try:
            # Load model and associated files
            self.model = joblib.load(os.path.join(self.model_dir, "isolation_forest.pkl"))
            self.scaler = joblib.load(os.path.join(self.model_dir, "isolation_forest_scaler.pkl"))
            self.features = joblib.load(os.path.join(self.model_dir, "isolation_forest_features.pkl"))
            
            # Load model metadata or create default if not available
            metadata_path = os.path.join(self.model_dir, "model_metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {
                    "model_type": "IsolationForest",
                    "training_date": datetime.now().isoformat(),
                    "anomalous_endpoints": []
                }
                
            logger.info(f"Successfully loaded model with metadata: {self.metadata}")
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            raise
            
    def get_recent_logs(self, minutes=10):
        """
        Get logs from the last X minutes from Elasticsearch.
        
        Args:
            minutes (int): Number of minutes to look back
            
        Returns:
            pd.DataFrame: DataFrame with the processed logs
        """
        try:
            # Calculate time range
            now = datetime.now()
            time_from = now - timedelta(minutes=minutes)
            
            # Query Elasticsearch
            query = {
                "query": {
                    "match_all": {}
                },
                "size": 10000,
                "sort": [
                    {"@timestamp": {"order": "desc"}}
                ]
            }
            
            # Log the query for debugging
            logger.info(f"Searching for logs in index: api-logs-2025.03.29")
            
            result = self.es.search(
                index="api-logs-2025.03.29",
                body=query
            )
            
            # Process results
            hits = result.get("hits", {}).get("hits", [])
            if not hits:
                logger.warning("No logs found in the specified time range")
                return None
                
            logger.info(f"Retrieved {len(hits)} logs from the last {minutes} minutes")
            
            # Process logs into a DataFrame
            records = []
            for hit in hits:
                source = hit.get("_source", {})
                
                # Extract relevant fields
                timestamp = source.get("@timestamp")
                
                # Handle service field that could be string or object
                service = source.get("service", "unknown")
                if isinstance(service, dict) and "name" in service:
                    service = service["name"]
                elif not isinstance(service, str):
                    service = "unknown"
                
                # Extract other fields
                response = source.get("response", {})
                request = source.get("request", {})
                
                record = {
                    "timestamp": timestamp,
                    "service": service,
                    "endpoint": request.get("url", {}).get("path", "unknown"),
                    "method": request.get("method", "unknown"),
                    "status_code": response.get("status_code", 0),
                    "duration_ms": response.get("duration_ms", 0),
                    "is_error": 1 if response.get("status_code", 200) >= 400 else 0,
                }
                records.append(record)
                
            return pd.DataFrame(records)
            
        except Exception as e:
            logger.error(f"Error retrieving logs: {str(e)}")
            return None
            
    def process_logs(self, logs_df):
        """
        Process logs into features for anomaly detection.
        
        Args:
            logs_df (pd.DataFrame): DataFrame with raw logs
            
        Returns:
            pd.DataFrame: DataFrame with processed features
        """
        if logs_df is None or len(logs_df) == 0:
            logger.warning("No logs to process")
            return None
            
        try:
            # Convert timestamp to datetime
            logs_df["timestamp"] = pd.to_datetime(logs_df["timestamp"])
            
            # Group by service and endpoint and aggregate
            features_df = logs_df.groupby(["service", "endpoint"]).agg({
                "duration_ms": ["count", "mean", "std", "max"],
                "is_error": ["sum", "mean"],
                "timestamp": ["min", "max"]
            }).reset_index()
            
            # Flatten multi-level columns
            features_df.columns = [
                "_".join(col).strip("_") for col in features_df.columns.values
            ]
            
            # Calculate requests per minute
            features_df["time_span_minutes"] = (
                features_df["timestamp_max"] - features_df["timestamp_min"]
            ).dt.total_seconds() / 60
            
            # Handle case where all logs have the same timestamp
            features_df["time_span_minutes"] = features_df["time_span_minutes"].replace(0, 1/60)
            
            features_df["requests_per_minute"] = features_df["duration_ms_count"] / features_df["time_span_minutes"]
            
            # Fill NaN values
            features_df = features_df.fillna({
                "duration_ms_std": 0,
                "is_error_mean": 0
            })
            
            logger.info(f"Processed logs into {len(features_df)} feature records")
            return features_df
            
        except Exception as e:
            logger.error(f"Error processing logs: {str(e)}")
            return None
            
    def detect_anomalies(self, features_df):
        """
        Detect anomalies using the loaded model.
        
        Args:
            features_df (pd.DataFrame): DataFrame with processed features
            
        Returns:
            pd.DataFrame: DataFrame with anomaly predictions
        """
        if features_df is None or len(features_df) == 0:
            logger.warning("No features to analyze")
            return None
            
        try:
            # Prepare features for prediction
            # Ensure all required features are present
            required_features = self.features

            # Add missing features with default values
            for feature in required_features:
                if feature not in features_df.columns:
                    if feature == 'duration_ms_min':
                        features_df[feature] = features_df['duration_ms_mean']
                    elif feature == 'duration_ms_median':
                        features_df[feature] = features_df['duration_ms_mean']
                    elif feature == 'error_rate':
                        features_df[feature] = features_df['is_error_mean'] * 100
                    else:
                        features_df[feature] = 0

            # Create feature matrix
            prediction_features = features_df[required_features].copy()
            
            # Scale features
            scaled_features = self.scaler.transform(prediction_features)
            
            # Predict anomalies
            predictions = self.model.predict(scaled_features)
            scores = self.model.decision_function(scaled_features)
            
            # Add results to DataFrame
            features_df["anomaly"] = predictions
            features_df["anomaly_score"] = scores
            
            # Filter to show only anomalies (where prediction is -1)
            anomalies_df = features_df[features_df["anomaly"] == -1].copy()
            
            # Add current timestamp
            anomalies_df["detection_time"] = datetime.now().isoformat()
            
            anomaly_count = len(anomalies_df)
            logger.info(f"Detected {anomaly_count} anomalies out of {len(features_df)} endpoints")
            
            return anomalies_df
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            return None
            
    def send_alerts(self, anomalies_df):
        """
        Send alerts for detected anomalies.
        
        Args:
            anomalies_df (pd.DataFrame): DataFrame with detected anomalies
            
        Returns:
            bool: True if alerts were sent successfully
        """
        if anomalies_df is None or len(anomalies_df) == 0:
            logger.info("No anomalies to alert on")
            return True
            
        try:
            # Convert DataFrame to list of dictionaries for indexing
            records = anomalies_df.to_dict(orient="records")
            
            # Index anomalies in Elasticsearch
            for record in records:
                # Format all timestamps as ISO strings
                for key, value in record.items():
                    if isinstance(value, pd.Timestamp):
                        record[key] = value.isoformat()
                
                # Add alert metadata
                record["alert_type"] = "api_anomaly"
                record["alert_severity"] = "high" if record.get("anomaly_score", 0) < -0.15 else "medium"
                
                # Index into Elasticsearch
                self.es.index(
                    index="api-anomalies",
                    document=record
                )
                
                # Log alert details
                logger.warning(
                    f"ANOMALY DETECTED: service={record['service']}, "
                    f"endpoint={record['endpoint']}, "
                    f"avg_response_time={record['duration_ms_mean']:.2f}ms, "
                    f"error_rate={record['is_error_mean']*100:.2f}%, "
                    f"score={record['anomaly_score']:.4f}"
                )
                
            # Here you could add other alerting mechanisms (e.g., email, Slack, PagerDuty)
            
            logger.info(f"Successfully sent {len(records)} alerts")
            return True
            
        except Exception as e:
            logger.error(f"Error sending alerts: {str(e)}")
            return False
            
    def run_check(self):
        """Run a complete check for anomalies and send alerts if needed."""
        logger.info("Starting anomaly detection check")
        
        # Get recent logs
        logs_df = self.get_recent_logs()
        if logs_df is None or len(logs_df) == 0:
            logger.warning("No logs found to analyze")
            return
            
        # Process logs into features
        features_df = self.process_logs(logs_df)
        if features_df is None or len(features_df) == 0:
            logger.warning("No features extracted from logs")
            return
            
        # Detect anomalies
        anomalies_df = self.detect_anomalies(features_df)
        
        # Send alerts for anomalies
        if anomalies_df is not None and len(anomalies_df) > 0:
            self.send_alerts(anomalies_df)
        
        logger.info("Completed anomaly detection check")
        
    def start_monitoring(self, check_interval=60):
        """
        Start continuous monitoring for anomalies.
        
        Args:
            check_interval (int): Interval between checks in seconds
        """
        logger.info(f"Starting continuous monitoring with {check_interval}s interval")
        
        try:
            while True:
                self.run_check()
                logger.info(f"Waiting {check_interval} seconds until next check")
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {str(e)}")
            raise
            
if __name__ == "__main__":
    print("Starting API Anomaly Detection Monitor")
    print("======================================")
    print("Press Ctrl+C to stop monitoring")
    print()
    
    monitor = APIMonitor()
    monitor.start_monitoring() 