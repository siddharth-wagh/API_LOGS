# Use a lightweight Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the service code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SERVICE_NAME=service-a
ENV OTEL_EXPORTER_OTLP_ENDPOINT="http://agent-collector:4318"
ENV OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf"
ENV DEPLOYMENT_ENV=production
ENV CLOUD_PROVIDER=aws
ENV SERVICE_REGION=us-east-1

# Expose the app port
EXPOSE 4000

# Start the service
CMD ["python", "index.py"]
