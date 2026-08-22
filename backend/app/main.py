from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
from starlette.requests import Request
from app.api import routes_voice, routes_query, routes_health, routes_benchmark

app = FastAPI(title="VaaniRAG Backend")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For hackathon
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Middleware for request latency
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include routers
app.include_router(routes_health.router, prefix="/api", tags=["health"])
app.include_router(routes_voice.router, prefix="/api", tags=["voice"])
app.include_router(routes_query.router, prefix="/api", tags=["query"])
app.include_router(routes_benchmark.router, prefix="/api", tags=["benchmark"])

@app.get("/")
async def root():
    return {"message": "Welcome to VaaniRAG API"}
