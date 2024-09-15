import uvicorn
from pathlib import Path
from fastapi import FastAPI, Request, Body

from opentelemetry import trace, baggage
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.metrics import get_meter_provider

import prometheus_client

app = FastAPI()

trace.set_tracer_provider(TracerProvider())
trace_provider: TracerProvider = trace.get_tracer_provider()
trace_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

tracer = trace.get_tracer(__name__)

resource = Resource(attributes={SERVICE_NAME: "microservice1"})
prometheus_client.start_http_server(port=8002)
reader = PrometheusMetricReader()
meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
get_meter_provider().set_meter_provider(meter_provider)

meter = meter_provider.get_meter(__name__)
request_counter = meter.create_counter(
    "request_count", unit="1", description="Number of request received"
)
error_counter = meter.create_counter(
    "error_count", unit="1", description="Number of error received"
)

@app.post("/add-user")
async def add_user(request: Request, user: dict = Body(...)):
    request_counter.add(1)
    headers = dict(request.headers)
    print(f"Received headers {headers}")
    try:
        carrier = {"traceparent": headers["traceparent"]}
        ctx = TraceContextTextMapPropagator().extract(carrier=carrier)
        print(f"Received context {ctx}")

        b2 = {"baggage": headers["baggage"]}
        ctx2 = W3CBaggagePropagator().extract(b2, context=ctx)
        print(f"Received context2 {ctx2}")

        with tracer.start_span("microservice1_span", context=ctx2):
            print(baggage.get_baggage("hello", ctx2))
            return f"user added from microservice1 {user}"
    except Exception as e:
        error_counter.add(1)
        return {"error": str(e)}, 500


if __name__ == "__main__":
    uvicorn.run(app=f"{Path(__file__).stem}:app", host="0.0.0.0", port=8000)
