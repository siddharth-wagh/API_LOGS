const express = require('express');
const axios = require('axios');
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');
const { SimpleSpanProcessor } = require('@opentelemetry/sdk-trace-base');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');
const { ExpressInstrumentation } = require('@opentelemetry/instrumentation-express');
const { HttpInstrumentation } = require('@opentelemetry/instrumentation-http');
const { registerInstrumentations } = require('@opentelemetry/instrumentation');
const { trace } = require('@opentelemetry/api');

// Function to send log to Logstash
async function sendLogToELK(logData) {
  try {
    await axios.post('http://logstash:8086', {
      ...logData,
      timestamp: new Date().toISOString(),
      service: {
        name: process.env.SERVICE_NAME || 'service-b'
      }
    });
  } catch (error) {
    console.error('Failed to send log to ELK:', error.message);
  }
}

// Initialize OpenTelemetry
function initTracing() {
  const provider = new NodeTracerProvider({
    resource: new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: process.env.SERVICE_NAME || 'service-b',
      [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: process.env.DEPLOYMENT_ENV || 'production',
      [SemanticResourceAttributes.CLOUD_PROVIDER]: process.env.CLOUD_PROVIDER || 'aws'
    }),
  });

  const endpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://agent-collector:4318';
  const exporter = new OTLPTraceExporter({
    url: `${endpoint}/v1/traces`
  });

  provider.addSpanProcessor(new SimpleSpanProcessor(exporter));
  provider.register();

  registerInstrumentations({
    instrumentations: [
      new HttpInstrumentation(),
      new ExpressInstrumentation(),
    ],
  });

  console.log(`Tracing initialized with endpoint: ${endpoint}/v1/traces`);
  return trace.getTracer('service-b-tracer');
}

// Initialize tracing
const tracer = initTracing();

const app = express();
app.use(express.json());

// Add logging middleware
app.use((req, res, next) => {
  const startTime = Date.now();
  
  // Process the request
  next();
  
  // After response is sent
  res.on('finish', () => {
    const duration = Date.now() - startTime;
    const logData = {
      request: {
        method: req.method,
        endpoint: req.path,
        remote_addr: req.ip,
        user_agent: req.get('user-agent')
      },
      response: {
        status_code: res.statusCode,
        duration_ms: duration
      },
      is_error: res.statusCode >= 400
    };
    
    // Send to ELK
    sendLogToELK(logData);
    
    console.log(`${req.method} ${req.path} - ${res.statusCode} - ${duration}ms`);
  });
});

// Routes
app.get('/ping', (req, res) => {
  sendLogToELK({
    message: 'Ping received',
    request: { method: 'GET', endpoint: '/ping' },
    response: { status_code: 200 }
  });
  res.json({ message: 'pong from service-b' });
});

app.get('/api/products', (req, res) => {
  // Add random delay (20-80ms)
  const delay = Math.floor(Math.random() * 60) + 20;
  
  // Check for intentional failure
  const shouldFail = req.query.fail === 'true';
  
  setTimeout(() => {
    if (shouldFail) {
      sendLogToELK({
        message: 'Products request failed',
        request: { method: 'GET', endpoint: '/api/products' },
        response: { status_code: 500 },
        is_error: true
      });
      return res.status(500).json({ error: 'Failed to retrieve products' });
    }
    
    sendLogToELK({
      message: 'Products request successful',
      request: { method: 'GET', endpoint: '/api/products' },
      response: { status_code: 200, duration_ms: delay }
    });
    
    res.json({
      products: [
        { id: 1, name: 'Laptop Pro', price: 1299.99, stock: 15 },
        { id: 2, name: 'Smartphone X', price: 899.99, stock: 28 },
        { id: 3, name: 'Wireless Headphones', price: 199.99, stock: 42 },
        { id: 4, name: 'Smart Watch', price: 249.99, stock: 10 },
        { id: 5, name: 'Tablet Mini', price: 399.99, stock: 22 }
      ]
    });
  }, delay);
});

// Start the server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Service B listening on port ${PORT}`);
  sendLogToELK({
    message: 'Service started',
    service: { name: 'service-b' },
    response: { status_code: 200 }
  });
});
