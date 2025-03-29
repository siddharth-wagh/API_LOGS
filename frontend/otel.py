from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import set_tracer_provider
import logging
import os
import app

logging.basicConfig(level=logging.INFO)

try:
    resource = Resource(attributes={
        SERVICE_NAME: os.getenv('SERVICE_NAME', 'frontend')
    })

    provider = TracerProvider(resource=resource)

    # Add console exporter for debugging
    console_processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(console_processor)

    # Try to add OTLP exporter
    try:
        otlp_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://otel-collector:4318')
        otlp_processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
        provider.add_span_processor(otlp_processor)
        logging.info(f"Successfully initialized OTLP exporter with endpoint: {otlp_endpoint}")
    except Exception as e:
        logging.warning(f"Failed to initialize OTLP exporter: {e}")
        logging.warning("Continuing with console exporter only")

    set_tracer_provider(provider)

    FlaskInstrumentor().instrument_app(app.app)
    RequestsInstrumentor().instrument()

    logging.info("Telemetry initialization completed successfully")
except Exception as e:
    logging.error(f"Failed to initialize telemetry: {e}")
    # Continue without telemetry rather than failing the app

app.app.run(host="0.0.0.0", port=3000)
