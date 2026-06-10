import json
from typing import Any, Iterable
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from . import models, schemas

JSON_FIELDS = {"expected_headers_json", "expected_body_json", "headers_json", "body_json", "condition_json", "query_json"}


def dumps_json(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def loads_json(value: str | None) -> Any:
    if value in (None, ""):
        return None
    return json.loads(value)


def apply_json_out(obj: Any, fields: Iterable[str]) -> Any:
    for field in fields:
        if hasattr(obj, field):
            setattr(obj, field, loads_json(getattr(obj, field)))
    return obj


def route_out(obj: models.MockRoute) -> models.MockRoute:
    return apply_json_out(obj, ["expected_headers_json", "expected_body_json"])


def response_out(obj: models.MockResponse) -> models.MockResponse:
    return apply_json_out(obj, ["headers_json", "body_json", "condition_json"])


def log_to_schema(log: models.MockRequestLog) -> schemas.MockRequestLogOut:
    return schemas.MockRequestLogOut(
        id=log.id,
        project_id=log.project_id,
        mock_route_id=log.mock_route_id,
        matched_response_id=log.matched_response_id,
        method=log.method,
        path=log.path,
        query_json=loads_json(log.query_json),
        headers_json=loads_json(log.headers_json),
        body_json=loads_json(log.body_json),
        status_code=log.status_code,
        created_at=log.created_at,
        project_name=log.project.name if log.project else None,
        route_name=log.mock_route.name if log.mock_route else None,
        response_name=log.matched_response.name if log.matched_response else None,
    )


def commit_or_409(db: Session, message: str):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=message) from exc


def get_project_or_404(db: Session, project_id: int) -> models.Project:
    obj = db.get(models.Project, project_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Project not found")
    return obj


def get_route_or_404(db: Session, route_id: int) -> models.MockRoute:
    obj = db.get(models.MockRoute, route_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Route not found")
    return obj


def get_response_or_404(db: Session, response_id: int) -> models.MockResponse:
    obj = db.get(models.MockResponse, response_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Response not found")
    return obj


def create_project(db: Session, data: schemas.ProjectCreate) -> models.Project:
    obj = models.Project(**data.model_dump())
    db.add(obj)
    commit_or_409(db, "A project with this slug already exists")
    db.refresh(obj)
    return obj


def update_project(db: Session, obj: models.Project, data: schemas.ProjectUpdate) -> models.Project:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    commit_or_409(db, "A project with this slug already exists")
    db.refresh(obj)
    return obj


def create_route(db: Session, project_id: int, data: schemas.MockRouteCreate) -> models.MockRoute:
    payload = data.model_dump()
    for key in ["expected_headers_json", "expected_body_json"]:
        payload[key] = dumps_json(payload.get(key))
    obj = models.MockRoute(project_id=project_id, **payload)
    db.add(obj)
    commit_or_409(db, "A route with this method and path already exists for this project")
    db.refresh(obj)
    return route_out(obj)


def update_route(db: Session, obj: models.MockRoute, data: schemas.MockRouteUpdate) -> models.MockRoute:
    payload = data.model_dump(exclude_unset=True)
    for key, value in payload.items():
        setattr(obj, key, dumps_json(value) if key in ["expected_headers_json", "expected_body_json"] else value)
    commit_or_409(db, "A route with this method and path already exists for this project")
    db.refresh(obj)
    return route_out(obj)


def create_response(db: Session, route_id: int, data: schemas.MockResponseCreate) -> models.MockResponse:
    payload = data.model_dump()
    for key in ["headers_json", "body_json", "condition_json"]:
        payload[key] = dumps_json(payload.get(key))
    obj = models.MockResponse(mock_route_id=route_id, **payload)
    if obj.is_default:
        db.query(models.MockResponse).filter_by(mock_route_id=route_id).update({"is_default": False})
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return response_out(obj)


def update_response(db: Session, obj: models.MockResponse, data: schemas.MockResponseUpdate) -> models.MockResponse:
    payload = data.model_dump(exclude_unset=True)
    if payload.get("is_default") is True:
        db.query(models.MockResponse).filter(models.MockResponse.mock_route_id == obj.mock_route_id, models.MockResponse.id != obj.id).update({"is_default": False})
    for key, value in payload.items():
        setattr(obj, key, dumps_json(value) if key in ["headers_json", "body_json", "condition_json"] else value)
    db.commit()
    db.refresh(obj)
    return response_out(obj)


def list_logs(db: Session, project_id: int | None = None, route_id: int | None = None, limit: int = 100):
    query = db.query(models.MockRequestLog).options(
        joinedload(models.MockRequestLog.project), joinedload(models.MockRequestLog.mock_route), joinedload(models.MockRequestLog.matched_response)
    )
    if project_id is not None:
        query = query.filter(models.MockRequestLog.project_id == project_id)
    if route_id is not None:
        query = query.filter(models.MockRequestLog.mock_route_id == route_id)
    return [log_to_schema(log) for log in query.order_by(models.MockRequestLog.created_at.desc()).limit(limit).all()]
