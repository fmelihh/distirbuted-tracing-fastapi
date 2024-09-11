import json
import uvicorn
import requests
from pathlib import Path
from fastapi import FastAPI

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry import trace, propagators, baggage
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor


app = FastAPI()

trace.set_tracer_provider(TracerProvider())
trace_provider: TracerProvider = trace.get_tracer_provider()
trace_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

tracer = trace.get_tracer(__name__)


@app.get("/send-user")
async def add_user(username: str, age: int):
    with tracer.start_as_current_span("microservice2_span") as span:
        ctx = baggage.set_baggage("hello", "world")

        headers = {}
        W3CBaggagePropagator().inject(headers, ctx)
        TraceContextTextMapPropagator().inject(headers, ctx)

        print(headers)
        requests.post(
            "http://localhost:8000/add-user",
            headers=headers,
            data=json.dumps({"user": {"username": username, "age": age}}),
        )


if __name__ == "__main__":
    uvicorn.run(app=f"{Path(__file__).stem}:app", host="0.0.0.0", port=8001)
