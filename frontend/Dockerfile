# Use Python base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the frontend code
COPY . .

# Set environment variables for cloud deployment
ENV PYTHONUNBUFFERED=1
ENV SERVICE_NAME=frontend
ENV OTEL_EXPORTER_OTLP_ENDPOINT="http://agent-collector:4318"
ENV OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf"
ENV DEPLOYMENT_ENV=production
ENV CLOUD_PROVIDER=aws
ENV SERVICE_REGION=us-east-1

# Expose the frontend port
EXPOSE 3000

# Start the frontend app
CMD ["python", "main.py"]
