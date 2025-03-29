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