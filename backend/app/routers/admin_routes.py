from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(prefix="/admin", tags=["admin-routes"])


@router.post("/projects/{project_id}/routes", response_model=schemas.MockRouteOut, status_code=201)
def create_route(project_id: int, payload: schemas.MockRouteCreate, db: Session = Depends(get_db)):
    crud.get_project_or_404(db, project_id)
    return crud.create_route(db, project_id, payload)


@router.get("/projects/{project_id}/routes", response_model=list[schemas.MockRouteOut])
def list_routes(project_id: int, db: Session = Depends(get_db)):
    crud.get_project_or_404(db, project_id)
    routes = db.query(models.MockRoute).filter_by(project_id=project_id).order_by(models.MockRoute.created_at.desc()).all()
    return [crud.route_out(route) for route in routes]


@router.get("/routes/{route_id}", response_model=schemas.MockRouteOut)
def get_route(route_id: int, db: Session = Depends(get_db)):
    return crud.route_out(crud.get_route_or_404(db, route_id))


@router.put("/routes/{route_id}", response_model=schemas.MockRouteOut)
def update_route(route_id: int, payload: schemas.MockRouteUpdate, db: Session = Depends(get_db)):
    return crud.update_route(db, crud.get_route_or_404(db, route_id), payload)


@router.delete("/routes/{route_id}")
def delete_route(route_id: int, db: Session = Depends(get_db)):
    route = crud.get_route_or_404(db, route_id)
    db.delete(route)
    db.commit()
    return {"message": "Route deleted"}


@router.get("/routes/{route_id}/logs", response_model=list[schemas.MockRequestLogOut])
def list_route_logs(route_id: int, limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    crud.get_route_or_404(db, route_id)
    return crud.list_logs(db, route_id=route_id, limit=limit)
