from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(prefix="/admin", tags=["admin-projects"])


@router.post("/projects", response_model=schemas.ProjectOut, status_code=201)
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db)):
    return crud.create_project(db, payload)


@router.get("/projects", response_model=list[schemas.ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).order_by(models.Project.created_at.desc()).all()


@router.get("/projects/{project_id}", response_model=schemas.ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    return crud.get_project_or_404(db, project_id)


@router.put("/projects/{project_id}", response_model=schemas.ProjectOut)
def update_project(project_id: int, payload: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    return crud.update_project(db, crud.get_project_or_404(db, project_id), payload)


@router.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = crud.get_project_or_404(db, project_id)
    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}


@router.get("/logs", response_model=list[schemas.MockRequestLogOut])
def list_all_logs(limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    return crud.list_logs(db, limit=limit)


@router.get("/projects/{project_id}/logs", response_model=list[schemas.MockRequestLogOut])
def list_project_logs(project_id: int, limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    crud.get_project_or_404(db, project_id)
    return crud.list_logs(db, project_id=project_id, limit=limit)


@router.get("/dashboard", response_model=schemas.DashboardStats)
def dashboard(db: Session = Depends(get_db)):
    return schemas.DashboardStats(
        total_projects=db.query(func.count(models.Project.id)).scalar() or 0,
        total_routes=db.query(func.count(models.MockRoute.id)).scalar() or 0,
        total_active_routes=db.query(func.count(models.MockRoute.id)).filter(models.MockRoute.is_active.is_(True)).scalar() or 0,
        total_request_logs=db.query(func.count(models.MockRequestLog.id)).scalar() or 0,
        latest_logs=crud.list_logs(db, limit=10),
    )
