from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pathlib import Path
from . import crud, models, schemas
from .database import Base, engine, get_db
from .routers import admin_projects, admin_routes, admin_responses, mock_runtime

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mock API Provider", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(admin_projects.router)
app.include_router(admin_routes.router)
app.include_router(admin_responses.router)
app.include_router(mock_runtime.router)


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/admin/seed/demo")
def seed_demo(db: Session = Depends(get_db)):
    project = db.query(models.Project).filter_by(slug="lms").first()
    if not project:
        project = crud.create_project(db, schemas.ProjectCreate(name="LMS", slug="lms", description="Demo learning management system"))

    route = db.query(models.MockRoute).filter_by(project_id=project.id, method="POST", path="/api/login").first()
    if not route:
        route = crud.create_route(
            db,
            project.id,
            schemas.MockRouteCreate(name="Login", method="POST", path="/api/login", description="Demo login endpoint"),
        )

    existing_count = db.query(models.MockResponse).filter_by(mock_route_id=route.id).count()
    if existing_count == 0:
        crud.create_response(
            db,
            route.id,
            schemas.MockResponseCreate(
                name="Login Success",
                status_code=200,
                priority=1,
                condition_json={
                    "body.email": {"operator": "equals", "value": "[test@test.com](mailto:test@test.com)"},
                    "body.password": {"operator": "equals", "value": "123456"},
                },
                body_json={"message": "Login successful", "token": "mock-token-123", "user": {"id": 1, "name": "Osama"}},
            ),
        )
        crud.create_response(
            db,
            route.id,
            schemas.MockResponseCreate(
                name="Invalid Credentials",
                status_code=401,
                priority=100,
                is_default=True,
                body_json={"message": "Invalid credentials"},
            ),
        )
    return {"message": "Demo seed ready", "mock_url": "/mock/lms/api/login"}
