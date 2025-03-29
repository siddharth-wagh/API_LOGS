from flask import Flask
import requests
import logging
from otel import init_telemetry

app = Flask(__name__)
init_telemetry(app)  # Initialize OpenTelemetry right after creating the app

logging.basicConfig(level=logging.INFO)

@app.route("/start")
def start():
    try:
        logging.info("Start endpoint called in service-a")
        return {"message": "Hello from service-a"}, 200
    except Exception as e:
        logging.error(f"Error: {e}")
        return {"error": str(e)}, 500

@app.route("/test")
def test():
    try:
        logging.info("Calling service-b from service-a")
        response = requests.get("http://service-b:5000/ping")
        logging.info("Received response from service-b")
        return {"message": "service-a called service-b", "data": response.json()}, 200
    except Exception as e:
        logging.error(f"Error: {e}")
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000)
