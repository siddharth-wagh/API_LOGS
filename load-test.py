import requests
import random
import time
import logging
import json
from datetime import datetime
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# Configuration
SERVICE_A_URL = "http://localhost:4000"
LOGSTASH_URL = "http://localhost:8086"
REQUEST_PATTERNS = [
    {"endpoint": "/start", "method": "GET", "weight": 5},
    {"endpoint": "/api/users", "method": "GET", "weight": 3},
    {"endpoint": "/api/products", "method": "GET", "weight": 2},
    {"endpoint": "/api/orders", "method": "POST", "weight": 1}
]

# Define traffic patterns
TRAFFIC_PATTERNS = [
    {"name": "normal", "rate": 5, "error_rate": 0.01, "latency_range": (10, 50)},
    {"name": "high_volume", "rate": 20, "error_rate": 0.02, "latency_range": (20, 100)},
    {"name": "slow", "rate": 2, "error_rate": 0.05, "latency_range": (200, 500)},
    {"name": "error_spike", "rate": 10, "error_rate": 0.30, "latency_range": (50, 150)}
]

def make_request(endpoint, method, should_fail=False, artificial_latency=0):
    """Make a request to the service"""
    url = f"{SERVICE_A_URL}{endpoint}"
    
    # Add artificial latency if specified
    if artificial_latency > 0:
        time.sleep(artificial_latency / 1000)  # Convert ms to seconds
    
    try:
        if should_fail:
            # Simulate a request that will cause a 500 error
            url = f"{url}?fail=true"
        
        status_code = 0
        if method == "GET":
            response = requests.get(url, timeout=2)
            status_code = response.status_code
        elif method == "POST":
            response = requests.post(url, json={"data": "test"}, timeout=2)
            status_code = response.status_code
        
        # Log the request
        log_request(endpoint, method, status_code, artificial_latency, should_fail)
        
        return status_code
        
    except Exception as e:
        logging.error(f"Request failed: {e}")
        log_request(endpoint, method, 500, artificial_latency, True)
        return 500

def log_request(endpoint, method, status_code, latency, is_error):
    """Log the request to the console and Logstash"""
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "service": "load-generator",
        "pattern": "test",
        "request": {
            "method": method,
            "endpoint": endpoint
        },
        "response": {
            "status_code": status_code,
            "duration_ms": latency
        },
        "is_error": is_error or status_code >= 400,
        "artificial_latency": latency
    }
    
    logging.info(f"{method} {endpoint} - Status: {status_code} - Latency: {latency}ms")
    
    # Send to Logstash
    try:
        send_log_to_elk(log_data)
    except Exception as e:
        logging.error(f"Failed to send log to ELK: {e}")

def send_log_to_elk(log_data):
    """Send a log directly to ELK via Logstash"""
    try:
        response = requests.post(LOGSTASH_URL, json=log_data, timeout=1)
        if response.status_code not in [200, 201]:
            logging.warning(f"Log sending to Logstash failed: {response.status_code}")
    except Exception as e:
        logging.error(f"Failed to send log to ELK: {e}")

def run_traffic_pattern(pattern, duration=60):
    """Run a specific traffic pattern for a duration in seconds"""
    logging.info(f"Starting traffic pattern: {pattern['name']} for {duration} seconds")
    
    end_time = time.time() + duration
    while time.time() < end_time:
        # Choose endpoint based on weights
        endpoints = []
        weights = []
        for rp in REQUEST_PATTERNS:
            endpoints.append(rp)
            weights.append(rp["weight"])
        
        selected = random.choices(endpoints, weights=weights, k=1)[0]
        
        # Determine if this request should fail
        should_fail = random.random() < pattern["error_rate"]
        
        # Determine latency
        latency = random.randint(pattern["latency_range"][0], pattern["latency_range"][1])
        
        # Make the request
        make_request(selected["endpoint"], selected["method"], should_fail, latency)
        
        # Sleep based on rate
        time.sleep(1 / pattern["rate"])
    
    logging.info(f"Finished traffic pattern: {pattern['name']}")

def main():
    """Main function to run the load test"""
    logging.info("Starting load test")
    
    try:
        # Run normal traffic for 60 seconds
        run_traffic_pattern(TRAFFIC_PATTERNS[0], 60)
        
        # Run high volume traffic for 30 seconds
        run_traffic_pattern(TRAFFIC_PATTERNS[1], 30)
        
        # Run slow traffic for 15 seconds (anomaly)
        run_traffic_pattern(TRAFFIC_PATTERNS[2], 15)
        
        # Run error spike for 10 seconds (anomaly)
        run_traffic_pattern(TRAFFIC_PATTERNS[3], 10)
        
        # Back to normal traffic
        run_traffic_pattern(TRAFFIC_PATTERNS[0], 60)
        
    except KeyboardInterrupt:
        logging.info("Load test interrupted by user")
    
    logging.info("Load test completed")

if __name__ == "__main__":
    main() 