import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.routers import auth, companies, contacts, leads, deals, tasks, analytics

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Enterprise CRM Platform for managing customers, deals pipeline, contacts, companies, leads, and operational tasks."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
def on_startup():
    init_db()

# Mount Static Files & Templates
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, "static")
templates_dir = os.path.join(base_dir, "templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Routers
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(contacts.router)
app.include_router(leads.router)
app.include_router(deals.router)
app.include_router(tasks.router)
app.include_router(analytics.router)

@app.get("/")
def serve_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "app_name": settings.app_name})

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ApexCRM",
        "environment": settings.app_env,
        "database": "sqlite_connected"
    }
