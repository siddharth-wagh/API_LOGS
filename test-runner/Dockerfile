FROM node:18-alpine

# Install curl for healthcheck
RUN apk add --no-cache curl

WORKDIR /app
COPY package.json ./
RUN npm install
COPY index.js ./

# Add a script to wait for service-a
COPY <<EOF /wait-for-service.sh
#!/bin/sh
until curl -s http://service-a:4000/start > /dev/null; do
  echo "Waiting for service-a..."
  sleep 2
done
echo "service-a is up - starting test runner"
exec "$@"
EOF

RUN chmod +x /wait-for-service.sh

CMD ["/wait-for-service.sh", "npm", "start"]
