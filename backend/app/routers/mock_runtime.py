import asyncio
from typing import Any
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from .. import crud, models
from ..database import get_db
from ..services.matcher import matches_conditions
from ..services.path_matcher import normalize_path, match_path

router = APIRouter(tags=["mock-runtime"])


def normalize_headers(headers) -> dict[str, str]:
    return {key.lower(): value for key, value in headers.items()}


def flatten_query(request: Request) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in request.query_params.keys():
        values = request.query_params.getlist(key)
        result[key] = values if len(values) > 1 else values[0]
    return result


async def read_body(request: Request) -> Any:
    raw = await request.body()
    if not raw:
        return None
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            return await request.json()
        except Exception:
            return {"_raw": raw.decode("utf-8", errors="replace"), "_json_error": "Invalid JSON body"}
    return raw.decode("utf-8", errors="replace")


def log_request(db: Session, *, project_id, route_id, response_id, method, path, query, headers, body, status_code):
    log = models.MockRequestLog(
        project_id=project_id,
        mock_route_id=route_id,
        matched_response_id=response_id,
        method=method,
        path=path,
        query_json=crud.dumps_json(query),
        headers_json=crud.dumps_json(headers),
        body_json=crud.dumps_json(body),
        status_code=status_code,
    )
    db.add(log)
    db.commit()


def select_response(responses: list[models.MockResponse], context: dict[str, Any]) -> models.MockResponse | None:
    active = [response for response in responses if response.is_active]
    for response in active:
        if matches_conditions(crud.loads_json(response.condition_json), context):
            return response
    for response in active:
        if response.is_default:
            return response
    return active[0] if active else None


@router.api_route("/mock/{project_slug}/{actual_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def handle_mock(project_slug: str, actual_path: str, request: Request, db: Session = Depends(get_db)):
    method = request.method.upper()
    path = normalize_path(actual_path)
    query = flatten_query(request)
    headers = normalize_headers(request.headers)
    body = await read_body(request)

    project = db.query(models.Project).filter_by(slug=project_slug.lower(), is_active=True).first()
    if not project:
        log_request(db, project_id=None, route_id=None, response_id=None, method=method, path=path, query=query, headers=headers, body=body, status_code=404)
        return JSONResponse(status_code=404, content={"detail": "Mock project not found"})

    routes = db.query(models.MockRoute).filter_by(project_id=project.id, method=method, is_active=True).all()
    matched_route = None
    path_params: dict[str, str] = {}
    for route in routes:
        result = match_path(route.path, path)
        if result.matched:
            matched_route = route
            path_params = result.params
            break

    if not matched_route:
        log_request(db, project_id=project.id, route_id=None, response_id=None, method=method, path=path, query=query, headers=headers, body=body, status_code=404)
        return JSONResponse(status_code=404, content={"detail": "No mock route matched", "method": method, "path": path})

    responses = db.query(models.MockResponse).filter_by(mock_route_id=matched_route.id, is_active=True).order_by(models.MockResponse.priority.asc(), models.MockResponse.id.asc()).all()
    context = {"body": body or {}, "headers": headers, "query": query, "params": path_params}
    matched_response = select_response(responses, context)
    if not matched_response:
        log_request(db, project_id=project.id, route_id=matched_route.id, response_id=None, method=method, path=path, query=query, headers=headers, body=body, status_code=404)
        return JSONResponse(status_code=404, content={"detail": "No active responses configured for matched route"})

    delay_ms = matched_response.delay_ms or 0
    if delay_ms > 0:
        await asyncio.sleep(delay_ms / 1000)

    response_body = crud.loads_json(matched_response.body_json)
    response_headers = crud.loads_json(matched_response.headers_json) or {}
    if not isinstance(response_headers, dict):
        response_headers = {}

    log_request(
        db,
        project_id=project.id,
        route_id=matched_route.id,
        response_id=matched_response.id,
        method=method,
        path=path,
        query=query,
        headers=headers,
        body=body,
        status_code=matched_response.status_code,
    )
    return JSONResponse(status_code=matched_response.status_code, content=response_body, headers={str(k): str(v) for k, v in response_headers.items()})
