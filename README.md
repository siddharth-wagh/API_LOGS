# Distributed Microservices Observability Platform

This repository contains a comprehensive observability platform for distributed microservices, featuring:

1. **Microservices Architecture**: Python and Node.js-based services communicating via HTTP
2. **Observability Infrastructure**: ELK Stack and OpenTelemetry for collecting logs and metrics
3. **AI-Powered Anomaly Detection**: Machine learning models for detecting abnormal service behavior

## Multi-Cloud Deployment Architecture

This platform is designed for deployment across multiple cloud environments with a centralized observability infrastructure:

### Local Collector Agents (Per Cloud/Region)
- OpenTelemetry agent collectors run close to services in each cloud/region
- Collect and preprocess telemetry data (traces, metrics, logs)
- Add cloud-specific metadata and context
- Reduce bandwidth by batching and compressing data

### Gateway Collectors (Per Cloud/Region)
- Aggregate data from multiple agent collectors
- Apply intelligent sampling and filtering
- Process data before forwarding to central ELK stack
- Provide fault tolerance and load balancing

### Centralized ELK Stack
- Single source of truth for all observability data
- Elasticsearch for storage and indexing
- Logstash for data processing and enrichment
- Kibana for visualization and dashboarding

### Data Flow Architecture
```
[Cloud A]                     [Cloud B]                     [Cloud C]
Services → Local Collectors   Services → Local Collectors   Services → Local Collectors
     ↓                             ↓                             ↓
Gateway Collector            Gateway Collector            Gateway Collector
     ↓                             ↓                             ↓
     └─────────────→ Central ELK Stack ←─────────────┘
                          ↑
                    [Security/Access]
                    Kibana Dashboard
```

## Directory Structure

```
project-root/
│
├── service-a/                 # Python-based microservice
├── service-b/                 # Node.js-based microservice
├── frontend/                  # Simple user interface
│
├── otel-collector/            # OpenTelemetry configuration
│   ├── config.yaml            # Agent collector config
│   └── gateway-config.yaml    # Gateway collector config
│
├── elasticsearch/             # Elasticsearch configuration
├── logstash/                  # Logstash configuration
├── kibana/                    # Kibana configuration
│
├── ai-anomaly-detector/       # AI-based monitoring
│   ├── training/              # Model training code
│   ├── monitoring/            # Real-time monitoring
│   └── data_collection/       # Telemetry data collection
│
└── docker-compose.yml         # Local deployment configuration
```

## Deployment Instructions

### Local Development
To run the entire platform locally:

```bash
docker-compose up --build
```

This will start all services, the OpenTelemetry Collectors (agent and gateway), and the ELK stack.

### Cloud Deployment

For multi-cloud deployment:

1. **Deploy Central ELK Stack**
   - Deploy to your primary cloud or use Elastic Cloud
   - Ensure sufficient storage and compute resources
   - Configure networking for cross-cloud access

2. **Deploy Gateway Collectors**
   - One collector cluster per cloud/region
   - Configure to point to the central ELK stack
   - Apply appropriate sampling and filtering

3. **Deploy Agent Collectors**
   - Deploy alongside services (as sidecars or DaemonSets in K8s)
   - Configure to point to the local gateway collector
   - Enable metrics collection for host resources

4. **Deploy Services**
   - Set appropriate environment variables for OpenTelemetry
   - Configure service discovery for local agent collectors

## Service Components

- **service-a**: A Python-based service that processes API requests
- **service-b**: A Node.js service that provides backend functionality
- **frontend**: A simple user interface that interacts with service-a

## Observability Components

- **OpenTelemetry Collector**: Collects, processes, and exports telemetry data
- **ELK Stack**:
  - **Elasticsearch**: Stores and indexes telemetry data
  - **Logstash**: Processes and transforms log data
  - **Kibana**: Basic visualization dashboard

## AI Anomaly Detection

The `ai-anomaly-detector` directory contains components for:
- Training machine learning models on historical telemetry data
- Real-time monitoring of services for anomalies
- Alerting when potential issues are detected

## Accessing the Interfaces

- **Kibana**: http://localhost:5601
- **Jaeger UI**: http://localhost:16686
- **Frontend**: http://localhost:3000

## Metrics and Logs

The system collects various telemetry data, including:
- Request latency and throughput
- Error rates and status codes
- Resource utilization (CPU, memory)
- Custom business metrics

## License

This project is licensed under the MIT License - see the LICENSE file for details.

# Microservices Monitoring with AI Anomaly Detection

This project demonstrates an architecture with three main layers:

1. **Target System**: The microservices being monitored
2. **Observability Infrastructure**: ELK Stack and OpenTelemetry for collecting logs and metrics
3. **AI Anomaly Detector**: Our AI-powered product that identifies unusual behavior

## Project Organization

```
project-root/
├── microservices/                # The services being monitored
│   ├── service-a/                # Python Flask microservice
│   ├── service-b/                # Node.js microservice
│   └── frontend/                 # Frontend application
├── observability/                # Observability infrastructure
│   ├── otel-collector/           # OpenTelemetry collector
│   ├── elasticsearch/            # Elasticsearch configuration
│   ├── logstash/                 # Logstash configuration
│   ├── kibana/                   # Kibana configuration
│   └── docker-compose.yml        # Docker Compose for the infrastructure
└── ai-anomaly-detector/          # Our AI product (separate component)
    ├── data_collection/          # Data collection from observability infra
    ├── training/                 # ML model training modules
    ├── monitoring/               # Real-time monitoring service
    ├── testing/                  # Test utilities and anomaly generators
    ├── docs/                     # Documentation and visualizations
    ├── shared/                   # Shared resources (models, etc.)
    └── main.py                   # Main entry point
```

## Logical Architecture

In a real-world deployment scenario, these components would be distributed as follows:

1. **Microservices Layer**: 
   - Services deployed across different servers or cloud environments
   - Each service instrumented with OpenTelemetry SDKs
   - Service owners maintain their own services

2. **Observability Infrastructure**:
   - **OpenTelemetry Collectors**: Deployed close to services (same cluster or network)
   - **ELK Stack**: 
     - Can be deployed as a centralized service (maintained by platform team)
     - Or as a managed service (e.g., Elastic Cloud)
     - Collects data from all environments

3. **AI Anomaly Detector**:
   - Deployed independently of the services it monitors
   - Connects to the observability infrastructure (ELK)
   - Can monitor multiple environments simultaneously

![Logical Architecture](ai-anomaly-detector/docs/logical_architecture.png)

## Target System

The target system is a typical microservices architecture:

- **Service A**: Python Flask service that exposes endpoints: `/start` and `/test`
- **Service B**: Node.js service that is called by Service A
- Each service is instrumented with OpenTelemetry for tracing and metrics

### Starting the Target System

```bash
docker-compose up -d
```

## Observability Infrastructure

The observability infrastructure consists of:

- **OpenTelemetry Collector**: 
  - Collects traces, metrics, and logs from services
  - Processes and transforms telemetry data
  - Exports data to various backends (including ELK)

- **ELK Stack**:
  - **Elasticsearch**: Stores and indexes telemetry data
  - **Logstash**: Processes and transforms log data
  - **Kibana**: Basic visualization dashboard

This infrastructure allows for collecting and storing telemetry data from all services, regardless of where they are deployed.

## AI Anomaly Detector

Our AI product sits in the `ai-anomaly-detector/` directory and is completely separate from both the target services and the observability infrastructure. It can be used to monitor any microservices architecture that has proper observability set up.

### Using the AI Product

```bash
cd ai-anomaly-detector

# Run the complete pipeline
python main.py --all

# Or run individual steps
python main.py --collect  # Collect data from the observability layer
python main.py --train    # Train the model
python main.py --monitor  # Start monitoring
python main.py --generate # Generate test anomalies
```

For more details about our AI product, see the [AI Anomaly Detector README](ai-anomaly-detector/README.md).

## Results and Visualizations

During testing, our AI product successfully detected anomalies in the target system.

- All visualizations are stored in the `ai-anomaly-detector/docs/` directory
- The analysis report is available at `ai-anomaly-detector/docs/anomaly_detection_results.md`

## Technologies Used

### Target System:
- Docker & Docker Compose
- Python Flask
- Node.js
- OpenTelemetry SDKs

### Observability Infrastructure:
- OpenTelemetry Collector
- Elasticsearch
- Logstash
- Kibana

### AI Anomaly Detector:
- Python
- Pandas
- NumPy
- Scikit-learn (Isolation Forest)
- Matplotlib
- Seaborn

## License

[MIT License](LICENSE)

# API Observability Platform with ML-based Anomaly Detection

This project implements a complete API observability platform with real-time anomaly detection capabilities. The system uses the ELK stack (Elasticsearch, Logstash, Kibana) along with OpenTelemetry collectors to monitor distributed microservices.

## Running the Complete System

To run the entire system including all services, ELK stack, and anomaly detection:

```bash
# Step 1: Start all microservices and the ELK stack
docker-compose up -d

# Step 2: Wait for the services to initialize
Start-Sleep -Seconds 30  # PowerShell
# OR
sleep 30  # Linux/Mac

# Step 3: Generate test traffic to create both normal patterns and anomalies
python load-test.py &

# Step 4: Train the anomaly detection model using data from Elasticsearch
python ai-anomaly-detector/training/train_model.py

# Step 5: Start the anomaly detection monitoring service
python ai-anomaly-detector/monitoring/run_monitor.py &

# Step 6: Open Kibana to view API logs and detected anomalies
Start-Process "http://localhost:5601"  # PowerShell
# OR
xdg-open http://localhost:5601  # Linux
# OR
open http://localhost:5601  # Mac
```

## Components

### Infrastructure
- **Elasticsearch**: Stores API logs and anomaly detection results
- **Logstash**: Collects and processes logs from services
- **Kibana**: Visualizes logs and anomalies

### Microservices
- **service-a**: Example REST API service
- **service-b**: Secondary service that communicates with service-a

### Telemetry Collection
- **agent-collector**: OpenTelemetry Collector for local service telemetry
- **gateway-collector**: Central collector that aggregates telemetry

### Anomaly Detection
- **ai-anomaly-detector**: ML-based system for detecting API anomalies
  - Uses Isolation Forest algorithm to detect abnormal response times and error rates
  - Processes time-series data from API logs
  - Sends alerts when anomalies are detected

## Monitoring and Alerting

The anomaly detection system monitors for:
1. Abnormal response times
2. Unusual error rates
3. Traffic pattern changes

When an anomaly is detected, it:
1. Logs a warning with details about the anomaly
2. Stores the anomaly record in Elasticsearch
3. Makes the anomaly available for visualization in Kibana

## Accessing Results

### View API Logs
- In Kibana, create an index pattern for `api-logs-*`
- Use the Discover tab to explore raw API logs

### View Detected Anomalies
- In Kibana, create an index pattern for `api-anomalies`
- Create visualizations to display anomalies over time

## For More Details

See the full documentation in the `ai-anomaly-detector` directory. 