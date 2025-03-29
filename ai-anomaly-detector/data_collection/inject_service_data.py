import pandas as pd
import numpy as np
from elasticsearch import Elasticsearch
import json
import requests
import random
import time
from datetime import datetime, timedelta
import os

print("Service Log Data Collection and Injection")
print("========================================")

# Connect to Elasticsearch
print("Connecting to Elasticsearch...")
es = Elasticsearch(["http://localhost:9200"])
print("Connected to Elasticsearch")

def get_service_logs(service_name, hours_back=1):
    """Get logs from a specific service from Elasticsearch"""
    now = datetime.now()
    time_from = now - timedelta(hours=hours_back)
    
    print(f"Retrieving logs for {service_name} from the last {hours_back} hour(s)...")
    
    # Query for service logs
    query = {
        "query": {
            "bool": {
                "must": [
                    {"range": {"@timestamp": {"gte": time_from.isoformat()}}},
                    {"match": {"service.name": service_name}}
                ]
            }
        },
        "size": 10000
    }
    
    # Execute search
    response = es.search(index="*", body=query)
    hits = response["hits"]["hits"]
    
    print(f"Retrieved {len(hits)} logs for {service_name}")
    return hits

def generate_artificial_anomalies(service_name, endpoint, count=5):
    """Generate artificial anomalies for training purposes"""
    print(f"Generating {count} artificial anomalies for {service_name} {endpoint}...")
    
    anomalies = []
    timestamp = datetime.now()
    
    for i in range(count):
        # Create timestamp with slight variation
        ts = timestamp - timedelta(minutes=random.randint(1, 30))
        
        # Create anomalous record
        anomaly = {
            "@timestamp": ts.isoformat(),
            "service": {
                "name": service_name
            },
            "request": {
                "method": "GET",
                "endpoint": endpoint
            },
            "response": {
                "status_code": random.choice([500, 503, 504, 429]),
                "duration_ms": random.randint(300, 800)  # High latency
            },
            "is_error": True,
            "artificial_anomaly": True
        }
        
        anomalies.append(anomaly)
    
    return anomalies

def inject_logs_to_elasticsearch(logs, index_name="api-training-data"):
    """Inject logs into Elasticsearch for model training"""
    print(f"Injecting {len(logs)} logs into Elasticsearch index '{index_name}'...")
    
    # Create index if not exists
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name)
    
    # Bulk insert
    bulk_data = []
    for log in logs:
        bulk_data.append({"index": {"_index": index_name}})
        bulk_data.append(log)
    
    if bulk_data:
        es.bulk(body=bulk_data, refresh=True)
    
    print(f"Successfully injected logs into Elasticsearch index '{index_name}'")

def create_service_latency_pattern(service_name, endpoint, duration_minutes=30, 
                                  normal_latency_range=(10, 50), anomaly_latency_range=(200, 500)):
    """Create a pattern of normal and anomalous latency for a service endpoint"""
    print(f"Creating latency pattern for {service_name} {endpoint}...")
    
    logs = []
    now = datetime.now()
    
    # Generate one record per minute for the duration
    for i in range(duration_minutes):
        timestamp = now - timedelta(minutes=i)
        
        # Determine if this minute should have an anomaly (10% chance)
        is_anomaly = random.random() < 0.1
        
        # Create 10-20 requests per minute
        request_count = random.randint(10, 20)
        
        for j in range(request_count):
            # Determine latency based on whether this is an anomaly
            if is_anomaly:
                latency = random.randint(*anomaly_latency_range)
                error = random.random() < 0.3  # 30% chance of error during anomaly
                status_code = 500 if error else 200
            else:
                latency = random.randint(*normal_latency_range)
                error = random.random() < 0.01  # 1% chance of error normally
                status_code = 500 if error else 200
            
            # Create timestamp with slight variation within the minute
            ts = timestamp + timedelta(seconds=random.randint(0, 59))
            
            # Create log record
            log = {
                "@timestamp": ts.isoformat(),
                "service": {
                    "name": service_name
                },
                "request": {
                    "method": "GET",
                    "endpoint": endpoint
                },
                "response": {
                    "status_code": status_code,
                    "duration_ms": latency
                },
                "is_error": error,
                "artificial": True
            }
            
            logs.append(log)
    
    print(f"Created {len(logs)} log records for {service_name} {endpoint}")
    return logs

def process_and_inject_service_logs():
    """Main function to process and inject service logs"""
    # Get real logs from services
    service_a_logs = get_service_logs("service-a")
    service_b_logs = get_service_logs("service-b")
    
    # Process logs into a common format
    processed_logs = []
    
    # Process service-a logs
    for hit in service_a_logs:
        source = hit["_source"]
        processed_log = {}
        
        # Extract timestamp
        processed_log["@timestamp"] = source.get("@timestamp", datetime.now().isoformat())
        
        # Set service info
        processed_log["service"] = {"name": "service-a"}
        
        # Extract request info if available
        request = {}
        if "http" in source:
            request["method"] = source.get("http", {}).get("method", "GET")
            request["endpoint"] = source.get("http", {}).get("target", "/unknown")
        processed_log["request"] = request
        
        # Extract response info if available
        response = {}
        if "http" in source:
            response["status_code"] = source.get("http", {}).get("status_code", 200)
            # Add reasonable duration if not available
            response["duration_ms"] = source.get("duration_ms", random.randint(10, 50))
        processed_log["response"] = response
        
        # Determine if it's an error
        processed_log["is_error"] = response.get("status_code", 200) >= 400
        
        processed_logs.append(processed_log)
    
    # Process service-b logs
    for hit in service_b_logs:
        source = hit["_source"]
        processed_log = {}
        
        # Extract timestamp
        processed_log["@timestamp"] = source.get("@timestamp", datetime.now().isoformat())
        
        # Set service info
        processed_log["service"] = {"name": "service-b"}
        
        # Extract request info if available
        request = {}
        if "http" in source:
            request["method"] = source.get("http", {}).get("method", "GET")
            request["endpoint"] = source.get("http", {}).get("target", "/unknown")
        processed_log["request"] = request
        
        # Extract response info if available
        response = {}
        if "http" in source:
            response["status_code"] = source.get("http", {}).get("status_code", 200)
            # Add reasonable duration if not available
            response["duration_ms"] = source.get("duration_ms", random.randint(10, 50))
        processed_log["response"] = response
        
        # Determine if it's an error
        processed_log["is_error"] = response.get("status_code", 200) >= 400
        
        processed_logs.append(processed_log)
    
    print(f"Processed {len(processed_logs)} real service logs")
    
    # Generate artificial patterns to enhance training data
    artificial_logs = []
    
    # Service A patterns
    artificial_logs.extend(create_service_latency_pattern("service-a", "/start", duration_minutes=60))
    artificial_logs.extend(create_service_latency_pattern("service-a", "/test", duration_minutes=60))
    
    # Service B patterns
    artificial_logs.extend(create_service_latency_pattern("service-b", "/ping", duration_minutes=60))
    
    # Generate some anomalies
    artificial_logs.extend(generate_artificial_anomalies("service-a", "/start", count=10))
    artificial_logs.extend(generate_artificial_anomalies("service-a", "/test", count=10))
    artificial_logs.extend(generate_artificial_anomalies("service-b", "/ping", count=10))
    
    print(f"Generated {len(artificial_logs)} artificial log records")
    
    # Combine real and artificial logs
    all_logs = processed_logs + artificial_logs
    print(f"Total logs to inject: {len(all_logs)}")
    
    # Inject into Elasticsearch
    inject_logs_to_elasticsearch(all_logs, index_name="api-training-data")
    
    return len(all_logs)

if __name__ == "__main__":
    try:
        num_logs = process_and_inject_service_logs()
        print(f"Successfully processed and injected {num_logs} log records")
        print("You can now train your model with this data using:")
        print("python train_model_from_services.py")
    except Exception as e:
        print(f"Error processing logs: {e}") 