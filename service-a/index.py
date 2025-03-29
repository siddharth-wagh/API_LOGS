from flask import Flask, jsonify, request
import requests
import time
import random
import os
from otel import init_telemetry

app = Flask(__name__)
init_telemetry(app)

SERVICE_B_URL = os.getenv('SERVICE_B_URL', 'http://service-b:5000')

@app.route('/start')
def start():
    # Check for intentional failure
    if request.args.get('fail') == 'true':
        return jsonify({"error": "Intentional failure"}), 500
    
    return jsonify({"message": "Hello from service-a"})

@app.route('/api/users')
def get_users():
    # Add random delay to simulate varying processing times
    delay = random.uniform(0.01, 0.1)
    time.sleep(delay)
    
    # Check for intentional failure
    if request.args.get('fail') == 'true':
        return jsonify({"error": "Failed to retrieve users"}), 500
    
    return jsonify({
        "users": [
            {"id": 1, "name": "Alice Johnson"},
            {"id": 2, "name": "Bob Smith"},
            {"id": 3, "name": "Charlie Brown"}
        ]
    })

@app.route('/api/products')
def get_products():
    # Add random delay to simulate varying processing times
    delay = random.uniform(0.01, 0.2)
    time.sleep(delay)
    
    # Check for intentional failure
    if request.args.get('fail') == 'true':
        return jsonify({"error": "Failed to retrieve products"}), 500
    
    # Call service-b to get the data
    try:
        response = requests.get(f"{SERVICE_B_URL}/api/products", timeout=1)
        if response.status_code == 200:
            return jsonify(response.json())
    except Exception as e:
        # If service-b is unavailable, return fallback data
        pass
    
    # Fallback response
    return jsonify({
        "products": [
            {"id": 1, "name": "Laptop", "price": 999.99},
            {"id": 2, "name": "Smartphone", "price": 699.99},
            {"id": 3, "name": "Headphones", "price": 149.99}
        ]
    })

@app.route('/api/orders', methods=['POST'])
def create_order():
    # Add random delay to simulate varying processing times
    delay = random.uniform(0.05, 0.3)
    time.sleep(delay)
    
    # Check for intentional failure
    if request.args.get('fail') == 'true':
        return jsonify({"error": "Failed to create order"}), 500
    
    data = request.json
    return jsonify({
        "order_id": random.randint(1000, 9999),
        "status": "created",
        "data": data
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)
