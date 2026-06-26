from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.api.customers import router as customers_router
from app.api.agents import router as agents_router
from app.api.runs import router as runs_router
from app.api.sapcontrol import router as sapcontrol_router
from datetime import datetime

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="OrbitSAP",
    description="The Control Plane for SAP System Refresh",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(runs_router, prefix="/api")
app.include_router(sapcontrol_router, prefix="/api")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/dashboard")
def dashboard():
    return FileResponse("static/index.html")

@app.get("/")
def root():
    return {
        "product": "OrbitSAP",
        "status": "running",
        "time": datetime.utcnow().isoformat()
    }

@app.get("/health")
def health():
    return {"status": "ok"}
