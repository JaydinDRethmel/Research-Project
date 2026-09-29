from fastapi import FastAPI, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import math

# Create FastAPI app
app = FastAPI()

# Define Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
LATENCY = Histogram('http_request_duration_seconds', 'HTTp request duration in seconds', ['endpoint'])

# Define a sample endpoint
@app.get("/")
def read_root():
    start_time = time.time() # Start measuring time

    _ = [math.sin(i) for i in range(10_000)] # Simulate some processing

    duration = time.time() - start_time # Calculate duration
    LATENCY.labels(endpoint="/process").observe(duration) # Record the duration in the histogram
    REQUEST_COUNT.labels(method="GET", endpoint="/process", status="200").inc() # Increment the request count

    # Return the response with processing time
    return{
        "status":"success",
        "processing_time_ms": round(duration * 1000, 2)
    }

# Define the metrics endpoint
@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)