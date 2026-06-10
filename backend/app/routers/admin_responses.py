from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(prefix="/admin", tags=["admin-responses"])


@router.post("/routes/{route_id}/responses", response_model=schemas.MockResponseOut, status_code=201)
def create_response(route_id: int, payload: schemas.MockResponseCreate, db: Session = Depends(get_db)):
    crud.get_route_or_404(db, route_id)
    return crud.create_response(db, route_id, payload)


@router.get("/routes/{route_id}/responses", response_model=list[schemas.MockResponseOut])
def list_responses(route_id: int, db: Session = Depends(get_db)):
    crud.get_route_or_404(db, route_id)
    responses = db.query(models.MockResponse).filter_by(mock_route_id=route_id).order_by(models.MockResponse.priority.asc(), models.MockResponse.id.asc()).all()
    return [crud.response_out(response) for response in responses]


@router.get("/responses/{response_id}", response_model=schemas.MockResponseOut)
def get_response(response_id: int, db: Session = Depends(get_db)):
    return crud.response_out(crud.get_response_or_404(db, response_id))


@router.put("/responses/{response_id}", response_model=schemas.MockResponseOut)
def update_response(response_id: int, payload: schemas.MockResponseUpdate, db: Session = Depends(get_db)):
    return crud.update_response(db, crud.get_response_or_404(db, response_id), payload)


@router.delete("/responses/{response_id}")
def delete_response(response_id: int, db: Session = Depends(get_db)):
    response = crud.get_response_or_404(db, response_id)
    db.delete(response)
    db.commit()
    return {"message": "Response deleted"}
