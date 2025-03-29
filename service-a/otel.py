from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
import opentelemetry.trace as trace
import logging
import requests
import os
import time
import json
from datetime import datetime
from flask import request, g

def init_telemetry(app):
    try:
        resource = Resource(attributes={
            SERVICE_NAME: os.getenv('SERVICE_NAME', 'service-a')
        })

        provider = TracerProvider(resource=resource)
        
        # Add console exporter for debugging
        console_processor = BatchSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(console_processor)

        # Try to add OTLP exporter
        try:
            otlp_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://otel-collector:4318')
            otlp_exporter = OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces")
            otlp_processor = BatchSpanProcessor(otlp_exporter)
            provider.add_span_processor(otlp_processor)
            logging.info(f"Successfully initialized OTLP exporter with endpoint: {otlp_endpoint}/v1/traces")
        except Exception as e:
            logging.warning(f"Failed to initialize OTLP exporter: {e}")
            logging.warning("Continuing with console exporter only")

        trace.set_tracer_provider(provider)

        FlaskInstrumentor().instrument_app(app)
        RequestsInstrumentor().instrument()
        
        # Add detailed request logging middleware
        @app.before_request
        def before_request():
            g.start_time = time.time()
            g.request_id = request.headers.get('X-Request-ID', '')
            
            # Get trace information from current span
            current_span = trace.get_current_span()
            span_context = current_span.get_span_context()
            if span_context.is_valid:
                g.trace_id = format(span_context.trace_id, '032x')
                g.span_id = format(span_context.span_id, '016x')
            else:
                g.trace_id = None
                g.span_id = None
        
        @app.after_request
        def after_request(response):
            if hasattr(g, 'start_time'):
                duration_ms = (time.time() - g.start_time) * 1000
                
                log_data = {
                    "timestamp": datetime.now().isoformat(),
                    "service": os.getenv('SERVICE_NAME', 'service-a'),
                    "request": {
                        "method": request.method,
                        "path": request.path,
                        "remote_addr": request.remote_addr,
                        "user_agent": request.user_agent.string if request.user_agent else None
                    },
                    "response": {
                        "status_code": response.status_code,
                        "content_length": response.content_length
                    },
                    "performance": {
                        "duration_ms": round(duration_ms, 2),
                        "response_time_category": categorize_response_time(duration_ms)
                    },
                    "tracing": {
                        "trace_id": g.trace_id if hasattr(g, 'trace_id') else None,
                        "span_id": g.span_id if hasattr(g, 'span_id') else None,
                        "request_id": g.request_id if hasattr(g, 'request_id') else None
                    },
                    "is_error": response.status_code >= 400
                }
                
                # Log to stdout (will be captured by Docker)
                logging.info(json.dumps(log_data))
                
                # Also send to Logstash if available
                try:
                    logstash_url = "http://logstash:8086"
                    requests.post(logstash_url, json=log_data, timeout=0.5)
                except Exception:
                    pass  # Fail silently if Logstash is not available
            
            return response
        
        logging.info("Telemetry initialization completed successfully")
    except Exception as e:
        logging.error(f"Failed to initialize telemetry: {e}")
        # Continue without telemetry rather than failing the app

def categorize_response_time(duration_ms):
    """Categorize response time for easier analysis"""
    if duration_ms < 100:
        return "fast"
    elif duration_ms < 300:
        return "normal"
    elif duration_ms < 1000:
        return "slow"
    else:
        return "very_slow"
