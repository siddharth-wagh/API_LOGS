import requests
import random
import time
import threading
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:4000"  # Updated to service-a's actual port (4000)
ENDPOINTS = ["/start", "/test"]  # Updated to use only the actual endpoints service-a has
NUM_REQUESTS = 1000  # Total number of requests to generate
NORMAL_LATENCY_RANGE = (10, 50)  # Normal latency range in milliseconds
ANOMALY_LATENCY_RANGE = (200, 500)  # Anomalous latency range
ERROR_PROBABILITY = 0.02  # Normal error rate (2%)
ANOMALY_ERROR_PROBABILITY = 0.15  # Anomalous error rate (15%)
ANOMALY_PROBABILITY = 0.05  # 5% chance of generating anomalous traffic

# Traffic patterns
def generate_normal_traffic(endpoint, batch_size=10):
    """Generate normal traffic pattern"""
    print(f"Generating normal traffic for {endpoint}")
    
    for _ in range(batch_size):
        try:
            # Add random parameters
            params = {
                "timestamp": datetime.now().isoformat(),
                "user_id": random.randint(1000, 9999),
                "session": f"session-{random.randint(1, 1000)}"
            }
            
            # Decide if this should be an error
            should_error = random.random() < ERROR_PROBABILITY
            
            # Send request
            if should_error:
                # Simulate error by using invalid endpoint
                url = f"{BASE_URL}{endpoint}-invalid"
            else:
                url = f"{BASE_URL}{endpoint}"
                
            # Random latency simulation
            latency = random.randint(*NORMAL_LATENCY_RANGE)
            
            if "latency" in params:
                params["latency"] = latency
                
            requests.get(url, params=params, timeout=5)
            print(f"Normal request to {endpoint}: latency={latency}ms, error={should_error}")
            
            # Sleep to space out requests
            time.sleep(random.uniform(0.05, 0.2))
            
        except requests.RequestException as e:
            print(f"Request error (expected): {e}")

def generate_anomalous_traffic(endpoint, batch_size=5):
    """Generate anomalous traffic pattern"""
    print(f"⚠️ Generating ANOMALOUS traffic for {endpoint}")
    
    for _ in range(batch_size):
        try:
            # Add random parameters with potential anomalies
            params = {
                "timestamp": datetime.now().isoformat(),
                "user_id": random.randint(1000, 9999),
                "session": f"anomaly-{random.randint(1, 1000)}",
                "artificial_latency": random.randint(*ANOMALY_LATENCY_RANGE)
            }
            
            # Higher error probability for anomalous traffic
            should_error = random.random() < ANOMALY_ERROR_PROBABILITY
            
            # Send request
            if should_error:
                # Simulate error by using invalid endpoint
                url = f"{BASE_URL}{endpoint}-invalid"
            else:
                url = f"{BASE_URL}{endpoint}"
                
            requests.get(url, params=params, timeout=5)
            print(f"⚠️ Anomalous request to {endpoint}: latency={params['artificial_latency']}ms, error={should_error}")
            
            # Sleep to space out requests
            time.sleep(random.uniform(0.05, 0.2))
            
        except requests.RequestException as e:
            print(f"Request error (expected): {e}")

def generate_burst_traffic(endpoint, burst_size=30):
    """Generate a sudden burst of traffic"""
    print(f"🔥 Generating BURST traffic for {endpoint}")
    
    for _ in range(burst_size):
        try:
            params = {
                "timestamp": datetime.now().isoformat(),
                "user_id": random.randint(1000, 9999),
                "session": f"burst-{random.randint(1, 1000)}"
            }
            
            url = f"{BASE_URL}{endpoint}"
            
            requests.get(url, params=params, timeout=5)
            print(f"🔥 Burst request to {endpoint}")
            
            # Very small delay between requests in a burst
            time.sleep(random.uniform(0.01, 0.05))
            
        except requests.RequestException as e:
            print(f"Request error (burst): {e}")

def traffic_generator():
    """Generate mixed traffic patterns"""
    requests_sent = 0
    
    while requests_sent < NUM_REQUESTS:
        # Select random endpoint
        endpoint = random.choice(ENDPOINTS)
        
        # Decide traffic pattern
        pattern_type = random.random()
        
        if pattern_type < ANOMALY_PROBABILITY:
            # Generate anomalous traffic
            batch_size = random.randint(3, 8)
            generate_anomalous_traffic(endpoint, batch_size)
            requests_sent += batch_size
        elif pattern_type < 0.15:  # 10% chance of burst after accounting for anomalies
            # Generate burst traffic
            burst_size = random.randint(20, 40)
            generate_burst_traffic(endpoint, burst_size)
            requests_sent += burst_size
        else:
            # Generate normal traffic
            batch_size = random.randint(5, 15)
            generate_normal_traffic(endpoint, batch_size)
            requests_sent += batch_size
            
        # Add a pause between batches
        pause_time = random.uniform(0.5, 2.0)
        print(f"Pausing for {pause_time:.2f}s between batches (sent {requests_sent}/{NUM_REQUESTS} requests)")
        time.sleep(pause_time)

if __name__ == "__main__":
    print(f"Starting API traffic generator - will generate {NUM_REQUESTS} requests")
    print(f"Normal latency: {NORMAL_LATENCY_RANGE[0]}-{NORMAL_LATENCY_RANGE[1]}ms")
    print(f"Anomaly latency: {ANOMALY_LATENCY_RANGE[0]}-{ANOMALY_LATENCY_RANGE[1]}ms")
    print(f"Normal error rate: {ERROR_PROBABILITY*100}%")
    print(f"Anomaly error rate: {ANOMALY_ERROR_PROBABILITY*100}%")
    print(f"Anomaly probability: {ANOMALY_PROBABILITY*100}%")
    print("-" * 50)
    
    try:
        traffic_generator()
    except KeyboardInterrupt:
        print("\nTraffic generation stopped by user")
    except Exception as e:
        print(f"Error generating traffic: {e}")
    finally:
        print(f"Traffic generation completed. Sent approximately {NUM_REQUESTS} requests.") 