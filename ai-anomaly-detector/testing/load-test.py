import requests
import time
import random
import threading
import uuid
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Service endpoints
SERVICE_A_URL = "http://localhost:4000"
SERVICE_B_URL = "http://localhost:5000"
LOGSTASH_URL = "http://localhost:8086"

# Traffic patterns
PATTERNS = {
    "normal": {
        "requests_per_minute": 60,  # 1 per second
        "error_rate": 0.01,         # 1% errors
        "latency_addition": 0,      # No added latency
    },
    "high_traffic": {
        "requests_per_minute": 300,  # 5 per second
        "error_rate": 0.02,          # 2% errors
        "latency_addition": 0,       # No added latency
    },
    "high_latency": {
        "requests_per_minute": 60,   # 1 per second
        "error_rate": 0.01,          # 1% errors
        "latency_addition": 500,     # Add 500ms latency
    },
    "high_error": {
        "requests_per_minute": 60,   # 1 per second
        "error_rate": 0.15,          # 15% errors
        "latency_addition": 0,       # No added latency
    },
    "degrading": {
        "requests_per_minute": 60,   # 1 per second
        "error_rate": 0.01,          # Start with 1% errors
        "latency_addition": 0,       # Start with no added latency
        "degradation_rate": 0.05,    # Increase latency by 5% each minute
    }
}

# Endpoints to test
ENDPOINTS = [
    "/start",
    "/test",
    "/api/v1/users",
    "/api/v1/products",
    "/api/v1/orders",
]

def log_to_console(message):
    """Log a message to the console"""
    logging.info(message)

def send_log_to_elk(log_data):
    """Send a log directly to ELK via Logstash"""
    try:
        response = requests.post(LOGSTASH_URL, json=log_data, timeout=1)
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Failed to send log to ELK: {e}")
        return False

def make_request(endpoint, pattern_name, pattern):
    """Make a request to the specified endpoint with the given pattern"""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    url = f"{SERVICE_A_URL}{endpoint}"
    headers = {
        "X-Request-ID": request_id,
        "User-Agent": "LoadTest/1.0"
    }
    
    # Add artificial latency if specified
    if pattern.get("latency_addition", 0) > 0:
        time.sleep(pattern["latency_addition"] / 1000)  # Convert ms to seconds
    
    # Determine if this request should simulate an error
    should_error = random.random() < pattern.get("error_rate", 0)
    
    # Initialize status_code outside the try block
    status_code = 500  # Default to error
    
    try:
        if should_error:
            # Simulate a bad request or use a non-existent endpoint
            if random.random() < 0.5:
                url = f"{SERVICE_A_URL}/non-existent-endpoint"
                response = requests.get(url, headers=headers, timeout=5)
                status_code = response.status_code
            else:
                # Send invalid data to trigger a 400 error
                response = requests.post(url, json={"invalid": "data"}, headers=headers, timeout=5)
                status_code = response.status_code
        else:
            # Normal request
            response = requests.get(url, headers=headers, timeout=5)
            status_code = response.status_code
    except requests.exceptions.RequestException as e:
        log_to_console(f"Request error: {e}")
        # status_code remains 500
    
    duration_ms = (time.time() - start_time) * 1000
    
    # Log detailed information
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "service": "load-generator",
        "pattern": pattern_name,
        "request": {
            "method": "GET" if not should_error else "POST",
            "endpoint": endpoint,
            "id": request_id
        },
        "response": {
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2)
        },
        "is_error": status_code >= 400,
        "artificial_latency": pattern.get("latency_addition", 0)
    }
    
    log_to_console(f"Pattern: {pattern_name}, Endpoint: {endpoint}, Status: {status_code}, Duration: {round(duration_ms, 2)}ms")
    send_log_to_elk(log_data)

def run_traffic_pattern(pattern_name):
    """Run a traffic pattern continuously"""
    pattern = PATTERNS[pattern_name]
    base_latency_addition = pattern.get("latency_addition", 0)
    base_error_rate = pattern.get("error_rate", 0)
    degradation_rate = pattern.get("degradation_rate", 0)
    
    iteration = 0
    
    while True:
        # Calculate time between requests based on requests per minute
        sleep_time = 60 / pattern["requests_per_minute"]
        
        # Apply degradation if applicable
        if degradation_rate > 0:
            # Increase latency by degradation rate each minute
            current_latency = base_latency_addition + (iteration * degradation_rate * base_latency_addition)
            current_error_rate = base_error_rate + (iteration * degradation_rate * base_error_rate)
            
            # Update pattern with degraded values
            pattern["latency_addition"] = current_latency
            pattern["error_rate"] = min(current_error_rate, 0.5)  # Cap at 50% error rate
            
            if iteration % 10 == 0:  # Log every 10 iterations
                log_to_console(f"Degradation applied: Latency now {current_latency}ms, Error rate now {current_error_rate:.2%}")
        
        # Select a random endpoint
        endpoint = random.choice(ENDPOINTS)
        
        # Make the request
        make_request(endpoint, pattern_name, pattern)
        
        # Sleep until next request
        jitter = random.uniform(0.8, 1.2)  # Add 20% jitter
        time.sleep(sleep_time * jitter)
        
        iteration += 1

def main():
    """Start all traffic patterns in separate threads"""
    log_to_console("Starting load testing...")
    
    # Start each pattern in its own thread
    threads = []
    for pattern_name in PATTERNS:
        thread = threading.Thread(target=run_traffic_pattern, args=(pattern_name,))
        thread.daemon = True
        threads.append(thread)
        thread.start()
        log_to_console(f"Started '{pattern_name}' traffic pattern")
    
    # Keep the main thread running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log_to_console("Load testing stopped by user")

if __name__ == "__main__":
    main() 