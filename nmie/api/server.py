from fastapi import FastAPI
from nmie.api.routes_execution import router as execution_router
from nmie.api.routes_alpaca import router as alpaca_router
from nmie.api.routes_research import router as research_router
from nmie.api.routes_tca import router as tca_router
from nmie.api.routes_graphdash import router as graphdash_router
from nmie.api.routes_control import router as control_router
from nmie.api.routes_artifacts import router as artifacts_router
from nmie.api.routes_strategies import router as strategies_router
from nmie.api.routes_backtest import router as backtest_router
from nmie.api.routes_market import router as market_router
from nmie.api.routes_analytics import router as analytics_router
from nmie.api.routes_intelligence import router as intelligence_router
from nmie.api.routes_nexus import router as nexus_router
from nmie.api.telemetry import app as telemetry_app

app = FastAPI(
    title="NMIE v3++ - Execution Research Platform",
    description="Control Plane + Analysis (No Live Trading)",
    version="3.1.0"
)

# Include routers
app.include_router(control_router)
app.include_router(artifacts_router)
app.include_router(execution_router)
app.include_router(alpaca_router)
app.include_router(research_router)
app.include_router(tca_router)
app.include_router(graphdash_router)
app.include_router(strategies_router)
app.include_router(backtest_router)
app.include_router(market_router)
app.include_router(analytics_router)
app.include_router(intelligence_router)
app.include_router(nexus_router)

@app.middleware("http")
async def add_no_cache_header(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/dashboard"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

@app.on_event("startup")
async def startup_event():
    from nmie.api.routes_control import runner
    runner.start()

@app.on_event("shutdown")
async def shutdown_event():
    from nmie.api.routes_control import runner
    runner.stop()

# Merge telemetry endpoints (or run separately)
from nmie.api.telemetry import app as telemetry_sub
from nmie.api.logging_config import logger

app.mount("/telemetry", telemetry_sub)

# Mount Dashboard UI
from fastapi.staticfiles import StaticFiles
import os
import mimetypes
from pathlib import Path

# Explicitly add mime types to ensure Docker serving works correctly
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")

# Calculate absolute path relative to this file
# server.py is in nmie/nmie/api/
# We want nmie/apps/graphdash_new/dist
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent # nmie/
dashboard_path = project_root / "apps" / "graphdash_new" / "dist"

logger.info(f"Mounting Dashboard from {dashboard_path}")
logger.info(f"Path Exists? {dashboard_path.exists()}")

if dashboard_path.exists():
    app.mount("/dashboard", StaticFiles(directory=str(dashboard_path), html=True), name="dashboard")
else:
    logger.warning(f"Dashboard path {dashboard_path} not found. Ensure 'npm run build' was run.")

@app.get("/")
def root():
    return {
        "message": "Welcome to NMIE - Adaptive Neural Execution Engine",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
