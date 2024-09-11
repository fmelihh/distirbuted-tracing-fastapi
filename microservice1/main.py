import uvicorn
from pathlib import Path
from fastapi import FastAPI, Request, Body

from opentelemetry import trace, baggage
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

app = FastAPI()

trace.set_tracer_provider(TracerProvider())
trace_provider: TracerProvider = trace.get_tracer_provider()
trace_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

tracer = trace.get_tracer(__name__)

@app.post("/add-user")
async def add_user(request: Request, user: dict = Body(...)):
    headers = dict(request.headers)
    print(f"Received headers {headers}")
    carrier = {"traceparent": headers["traceparent"]}
    ctx = TraceContextTextMapPropagator().extract(carrier=carrier)
    print(f"Received context {ctx}")

    b2 = {"baggage": headers["baggage"]}
    ctx2 = W3CBaggagePropagator().extract(b2, context=ctx)
    print(f"Received context2 {ctx2}")

    with tracer.start_span("microservice1_span", context=ctx2):
        print(baggage.get_baggage("hello", ctx2))
        return f"user added from microservice1 {user}"




if __name__ == "__main__":
    uvicorn.run(app=f"{Path(__file__).stem}:app", host="0.0.0.0", port=8000)