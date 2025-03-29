# AI Anomaly Detector

This directory contains our AI-powered anomaly detection product for microservices monitoring. It connects to your observability infrastructure (ELK Stack) to detect anomalies in distributed services.

## Directory Structure

The product is organized into the following components:

```
ai-anomaly-detector/
├── data_collection/     # Data collection from ELK Stack
├── training/            # ML model training modules
├── monitoring/          # Real-time monitoring service
├── testing/             # Test utilities and anomaly generators
├── docs/                # Documentation and visualizations
├── shared/              # Shared resources (models, etc.)
└── main.py              # Main entry point
```

## Complete Step-by-Step Guide

To quickly get started with this API anomaly detection system, follow these steps:

### 1. Ensure Prerequisites

Make sure you have:
- Python 3.7+ installed
- Required Python packages: `pip install elasticsearch pandas numpy scikit-learn matplotlib joblib`
- Running ELK stack (Elasticsearch, Logstash, Kibana)

### 2. Generate Test Data (Optional)

If you don't have actual API logs yet, you can generate test data:

```bash
# Generate test traffic with some anomalies
python load-test.py
```

### 3. Train the Anomaly Detection Model

```bash
# Train the model on data from Elasticsearch
python ai-anomaly-detector/training/train_model.py
```

This will:
- Connect to Elasticsearch
- Extract API logs data
- Create time-based features
- Train an Isolation Forest model
- Save the model to the `models/` directory
- Generate visualizations

### 4. Run the Monitoring Service

```bash
# Start continuous monitoring for anomalies
python ai-anomaly-detector/monitoring/run_monitor.py
```

This will:
- Load the trained model
- Check for new logs every 60 seconds
- Detect anomalies based on response time and error rates
- Send alerts when anomalies are detected
- Store anomaly records in the `api-anomalies` index in Elasticsearch

### 5. View Anomaly Results

Access the results in any of these ways:
- Open Kibana: http://localhost:5601 
- Create an index pattern for `api-anomalies` in Kibana
- Query Elasticsearch directly:
  ```bash
  Invoke-RestMethod -Uri "http://localhost:9200/api-anomalies/_search" -Method GET
  ```

### 6. View API Logs

To see the raw API logs:
- Open Kibana: http://localhost:5601
- Create an index pattern for `api-logs-*` 
- Use the Discover tab to view and filter logs

## Logical Architecture

This product is designed to work with distributed microservices environments. It connects to your ELK Stack, which may be centralized even when your services are distributed across multiple clouds or data centers.

For a detailed explanation of the logical architecture and deployment options, see:
- [Logical Architecture Document](docs/logical_architecture.md)

## Quick Start

You can use our product in one of two ways:

### 1. Using the main entry point

The `main.py` script provides a unified interface to our product:

```bash
# Run the complete pipeline
python main.py --all

# Or run individual steps
python main.py --collect  # Collect data from ELK Stack
python main.py --train    # Train the model
python main.py --monitor  # Start monitoring
python main.py --generate # Generate test anomalies
```

### 2. Using individual modules

You can also use each component independently:

```bash
# Data collection
python data_collection/inject_service_data.py

# Model training
python training/train_model_from_services.py

# Monitoring
python monitoring/monitor_services.py

# Generate test anomalies
python testing/generate_anomalies.py
```

## Module Descriptions

### Data Collection

The data collection module (`data_collection/inject_service_data.py`) connects to your ELK Stack and collects telemetry data for analysis. It can be configured to connect to:

- A local ELK stack (like in this demo)
- A centralized ELK deployment in your infrastructure
- A managed Elastic Cloud instance

### Training

The training module (`training/train_model_from_services.py`) processes the collected data and trains an Isolation Forest model to detect anomalies.

### Monitoring

The monitoring service (`monitoring/monitor_services.py`) continuously checks for anomalies by:
1. Querying your ELK Stack for recent telemetry data
2. Processing the data into features
3. Applying the trained model to detect anomalies
4. Visualizing and alerting on detected anomalies

### Testing

The testing module (`testing/generate_anomalies.py`) allows you to generate artificial anomalies to test the detection capabilities of the system.

## Configuration for Different Environments

To connect to different ELK deployments:

1. Edit `data_collection/inject_service_data.py` and update the Elasticsearch connection settings:

   ```python
   # For local development
   es = Elasticsearch(["http://localhost:9200"])

   # For production environment
   # es = Elasticsearch(
   #     ["https://your-elk-cluster:9200"],
   #     basic_auth=("user", "password"),
   #     ca_certs="path/to/ca.crt"
   # )
   ```

2. For the monitoring service, update the connection settings in `monitoring/monitor_services.py`.


## Documentation

For more detailed information, please refer to the documentation in the `docs/` directory:

- `product_overview.md`: Complete overview of the product
- `logical_architecture.md`: Detailed explanation of the logical architecture
- `anomaly_detection_results.md`: Analysis of detection results

## Visualizations

The system generates several visualizations to help understand and analyze anomalies:

- `service_anomaly_detection.png`: Overview of detected anomalies
- `service_monitor_anomalies.png`: Real-time monitoring results

## Models

Trained models are stored in the `shared/models/` directory and are automatically used by the monitoring service. 