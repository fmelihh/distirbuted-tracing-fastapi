import json
import uvicorn
import requests
from pathlib import Path
from fastapi import FastAPI

import prometheus_client
from opentelemetry import metrics
from opentelemetry import trace, baggage
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor


app = FastAPI()

trace.set_tracer_provider(TracerProvider())
trace_provider: TracerProvider = trace.get_tracer_provider()
trace_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

tracer = trace.get_tracer(__name__)

resource = Resource(attributes={SERVICE_NAME: "microservice2"})

prometheus_client.start_http_server(port=8003)
reader = PrometheusMetricReader()
provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(provider)

meter = provider.get_meter(__name__)
request_counter = meter.create_counter(
    "request_counter", unit="1", description="Number of requests sent to microservice1"
)
error_counter = meter.create_counter(
    "error_count", unit="1", description="Number of errors encountered during microservice1"
)

@app.get("/send-user")
async def add_user(username: str, age: int):
    request_counter.add(1)
    with tracer.start_as_current_span("microservice2_span"):
        ctx = baggage.set_baggage("hello", "world")

        headers = {}
        W3CBaggagePropagator().inject(headers, ctx)
        TraceContextTextMapPropagator().inject(headers, ctx)

        try:
            print(headers)
            response = requests.post(
                "http://localhost:8000/add-user",
                headers=headers,
                data=json.dumps({"user": {"username": username, "age": age}}),
            )
            response.raise_for_status()
            return "hello from microservice2"
        except Exception as e:
            error_counter.add(1)
            return {"error": str(e)}, 500

if __name__ == "__main__":
    uvicorn.run(app=f"{Path(__file__).stem}:app", host="0.0.0.0", port=8001)
