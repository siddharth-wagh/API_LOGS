import requests
import random
import time
import json
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch

print("API Anomaly Generator")
print("====================")

# Configuration
BASE_URL = "http://localhost:4000"  # service-a runs on port 4000
ENDPOINTS = ["/start", "/test"]
NUM_ANOMALIES = 20
ANOMALY_INTERVAL_SEC = 10  # Generate an anomaly every X seconds
NORMAL_LATENCY_RANGE = (10, 50)  # Normal latency range in milliseconds
ANOMALY_LATENCY_RANGE = (400, 800)  # Anomalous latency range
NORMAL_ERROR_RATE = 0.01  # 1% normal error rate
ANOMALY_ERROR_RATE = 0.30  # 30% anomalous error rate

# Connect to Elasticsearch for direct logging
es = Elasticsearch(["http://localhost:9200"])

def generate_normal_request(endpoint):
    """Generate a normal API request"""
    try:
        # Add random parameters
        params = {
            "timestamp": datetime.now().isoformat(),
            "user_id": random.randint(1000, 9999),
            "session": f"session-{random.randint(1, 1000)}"
        }
        
        # Decide if this should be an error (rare for normal traffic)
        should_error = random.random() < NORMAL_ERROR_RATE
        
        # Send request
        if should_error:
            # Simulate error by using invalid endpoint
            url = f"{BASE_URL}{endpoint}-invalid"
        else:
            url = f"{BASE_URL}{endpoint}"
            
        # Random latency simulation
        latency = random.randint(*NORMAL_LATENCY_RANGE)
        
        start_time = time.time()
        response = requests.get(url, params=params, timeout=5)
        actual_latency = (time.time() - start_time) * 1000  # Convert to ms
        
        status_code = response.status_code
        
        print(f"Normal request to {endpoint}: latency={actual_latency:.2f}ms, status={status_code}")
        
        # Log to Elasticsearch
        log_to_elasticsearch(endpoint, status_code, actual_latency, is_anomaly=False)
        
        return True
    except requests.RequestException as e:
        print(f"Error in normal request: {e}")
        return False

def generate_anomalous_request(endpoint):
    """Generate an anomalous API request"""
    try:
        print(f"⚠️ Generating ANOMALY for {endpoint}")
        
        # Add random parameters
        params = {
            "timestamp": datetime.now().isoformat(),
            "user_id": random.randint(1000, 9999),
            "session": f"anomaly-{random.randint(1, 1000)}",
            "artificial_latency": random.randint(*ANOMALY_LATENCY_RANGE)
        }
        
        # Anomalous traffic has higher error rate
        should_error = random.random() < ANOMALY_ERROR_RATE
        
        # Send request
        if should_error:
            # Simulate error by using invalid endpoint or adding error param
            if random.random() < 0.5:
                url = f"{BASE_URL}{endpoint}-invalid"
            else:
                url = f"{BASE_URL}{endpoint}"
                params["force_error"] = True
        else:
            url = f"{BASE_URL}{endpoint}"
            
        # Anomalous latency
        latency = random.randint(*ANOMALY_LATENCY_RANGE)
        
        # Time the request
        start_time = time.time()
        
        # Sleep to simulate backend latency issue
        time.sleep(latency / 1000)  # Convert ms to seconds
        
        try:
            response = requests.get(url, params=params, timeout=5)
            status_code = response.status_code
        except requests.RequestException:
            status_code = 500
            
        actual_latency = (time.time() - start_time) * 1000  # Convert to ms
        
        print(f"⚠️ Anomalous request to {endpoint}: latency={actual_latency:.2f}ms, status={status_code}")
        
        # Log to Elasticsearch
        log_to_elasticsearch(endpoint, status_code, actual_latency, is_anomaly=True)
        
        return True
    except Exception as e:
        print(f"Error in anomalous request: {e}")
        return False

def log_to_elasticsearch(endpoint, status_code, duration_ms, is_anomaly=False):
    """Log request directly to Elasticsearch"""
    try:
        # Create log document
        now = datetime.now()
        doc = {
            "@timestamp": now.isoformat(),
            "service": {
                "name": "service-a"
            },
            "request": {
                "method": "GET",
                "endpoint": endpoint
            },
            "response": {
                "status_code": status_code,
                "duration_ms": duration_ms
            },
            "is_error": status_code >= 400,
            "is_artificial_anomaly": is_anomaly
        }
        
        # Index document
        es.index(index="api-training-data", document=doc)
    except Exception as e:
        print(f"Error logging to Elasticsearch: {e}")

def generate_traffic_burst(endpoint, count=20):
    """Generate a burst of traffic to a specific endpoint"""
    print(f"🔥 Generating traffic burst for {endpoint} ({count} requests)")
    
    for i in range(count):
        generate_normal_request(endpoint)
        time.sleep(0.1)  # 100ms between requests in a burst

def generate_mixed_anomaly_pattern():
    """Generate a mix of normal and anomalous traffic"""
    anomalies_generated = 0
    
    try:
        while anomalies_generated < NUM_ANOMALIES:
            # Generate mostly normal traffic
            for _ in range(random.randint(3, 8)):
                endpoint = random.choice(ENDPOINTS)
                generate_normal_request(endpoint)
                time.sleep(random.uniform(0.2, 1.0))
            
            # Occasionally generate a traffic burst
            if random.random() < 0.2:  # 20% chance
                endpoint = random.choice(ENDPOINTS)
                generate_traffic_burst(endpoint, count=random.randint(10, 30))
            
            # Generate an anomaly
            endpoint = random.choice(ENDPOINTS)
            if generate_anomalous_request(endpoint):
                anomalies_generated += 1
            
            print(f"Progress: {anomalies_generated}/{NUM_ANOMALIES} anomalies generated")
            
            # Wait before next anomaly
            time.sleep(ANOMALY_INTERVAL_SEC)
            
    except KeyboardInterrupt:
        print("\nStopped by user")
        
    print(f"Generated {anomalies_generated} anomalies")

if __name__ == "__main__":
    print(f"Starting anomaly generator. Will generate {NUM_ANOMALIES} anomalies.")
    print(f"Normal latency: {NORMAL_LATENCY_RANGE[0]}-{NORMAL_LATENCY_RANGE[1]}ms")
    print(f"Anomaly latency: {ANOMALY_LATENCY_RANGE[0]}-{ANOMALY_LATENCY_RANGE[1]}ms")
    print(f"Normal error rate: {NORMAL_ERROR_RATE*100}%")
    print(f"Anomaly error rate: {ANOMALY_ERROR_RATE*100}%")
    
    generate_mixed_anomaly_pattern() 