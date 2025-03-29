# Use official Node.js LTS image
FROM node:16-slim

# Set working directory
WORKDIR /app

# Copy package.json and install dependencies
COPY package*.json ./
RUN npm install

# Copy app source code
COPY . .

# Set environment variables
ENV NODE_OPTIONS=--enable-source-maps
ENV SERVICE_NAME=service-b
ENV OTEL_EXPORTER_OTLP_ENDPOINT="http://agent-collector:4318"
ENV OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf"
ENV DEPLOYMENT_ENV=production 
ENV CLOUD_PROVIDER=aws
ENV SERVICE_REGION=us-east-1

# Expose port (change if needed)
EXPOSE 5000

# Start the service using npm start to ensure proper initialization
CMD ["node", "index.js"]
