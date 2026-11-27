
import logging

from fastapi import FastAPI, HTTPException, Response
from prometheus_client import (
    Counter,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST
)

# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("support-monitor")

app = FastAPI(title="Application Support Monitoring Lab")

# Prometheus metrics
REQUESTS = Counter(
    "app_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

ERRORS = Counter(
    "app_errors_total",
    "Total application errors"
)

APP_UP = Gauge(
    "app_up",
    "Application health status"
)

APP_UP.set(1)


@app.middleware("http")
async def monitor_requests(request, call_next):
    response = await call_next(request)

    REQUESTS.labels(
        method=request.method,
        endpoint=request.url.path,
        status=str(response.status_code)
    ).inc()

    return response


@app.get("/")
def home():
    logger.info("Application home endpoint accessed")
    return {"message": "Application is running"}


@app.get("/health")
def health():
    logger.info("Health check successful")
    return {"status": "UP"}


@app.get("/work")
def normal_work():
    logger.info("Application processed a normal request")
    return {"status": "success", "message": "Work completed"}


@app.get("/simulate-error")
def simulate_error():
    ERRORS.inc()
    logger.error("Database connection failed - simulated error")

    raise HTTPException(
        status_code=500,
        detail="Simulated internal server error"
    )


@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
