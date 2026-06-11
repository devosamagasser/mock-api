# Developer Documentation

This document explains how Mock API Provider is structured so another developer can continue working on it confidently.

## Technology stack

- **Python 3.12** runtime in Docker
- **FastAPI** for HTTP routing and OpenAPI docs
- **SQLAlchemy** for database models and queries
- **Pydantic v2** for request/response schemas and validation
- **SQLite** as the default local database
- **Native HTML/CSS/JavaScript** for the Admin UI
- **Docker Compose** for local containerized execution

## Repository structure

```text
mock-api-provider/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app setup, router registration, static UI, demo seed
│   │   ├── database.py             # database engine/session/base setup
│   │   ├── models.py               # SQLAlchemy ORM models
│   │   ├── schemas.py              # Pydantic schemas and validators
│   │   ├── crud.py                 # persistence helpers and JSON serialization helpers
│   │   ├── routers/
│   │   │   ├── admin_projects.py   # project, dashboard, and log endpoints
│   │   │   ├── admin_routes.py     # route endpoints
│   │   │   ├── admin_responses.py  # response endpoints
│   │   │   └── mock_runtime.py     # runtime /mock endpoint
│   │   ├── services/
│   │   │   ├── matcher.py          # condition matching logic
│   │   │   └── path_matcher.py     # static/dynamic path matching
│   │   └── static/
│   │       ├── index.html          # Admin UI HTML shell
│   │       ├── app.js              # Admin UI behavior and API calls
│   │       └── style.css           # Admin UI styles
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
├── README.md
├── HOW_TO_USE.md
├── FEATURES.md
└── DEVELOPER_DOCUMENTATION.md
```

## How to run the app

### Docker Compose

```bash
docker compose up --build
```

Docker Compose exposes port `8000`, sets `DATABASE_URL=sqlite:////app/data/mock.db`, and mounts `./data` to `/app/data`.

### Local Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Local default database URL:

```text
sqlite:///./data/mock.db
```

Override it with:

```bash
export DATABASE_URL="sqlite:///./data/mock.db"
```

## Application startup

`backend/app/main.py` performs the main app setup:

1. creates database tables with `Base.metadata.create_all(bind=engine)`
2. creates the FastAPI app with title `Mock API Provider`
3. enables permissive CORS for local development
4. mounts static assets from `backend/app/static` at `/static`
5. includes admin and runtime routers
6. serves `index.html` from `/`
7. exposes `POST /admin/seed/demo` for sample data

There is currently no Alembic migration setup. Schema changes are applied through SQLAlchemy table creation for new databases.

## Data model

### Project

Represents one mock API workspace.

Important fields:

- `id`
- `name`
- `slug`
- `description`
- `is_active`
- `created_at`
- `updated_at`

Relationships:

- one project has many routes
- one project has many request logs

### MockRoute

Represents one mocked method/path combination inside a project.

Important fields:

- `id`
- `project_id`
- `name`
- `method`
- `path`
- `description`
- `expected_headers_json`
- `expected_body_json`
- `is_active`
- `created_at`
- `updated_at`

Database constraint:

- `project_id`, `method`, and `path` must be unique together

Relationships:

- one route belongs to one project
- one route has many responses
- one route has many request logs

### MockResponse

Represents one possible response for a route.

Important fields:

- `id`
- `mock_route_id`
- `name`
- `status_code`
- `headers_json`
- `body_json`
- `condition_json`
- `priority`
- `delay_ms`
- `is_default`
- `is_active`
- `created_at`
- `updated_at`

Relationships:

- one response belongs to one route
- one response can be referenced by many request logs

### MockRequestLog

Represents a recorded runtime request.

Important fields:

- `id`
- `project_id`
- `mock_route_id`
- `matched_response_id`
- `method`
- `path`
- `query_json`
- `headers_json`
- `body_json`
- `status_code`
- `created_at`

Logs can represent successful matches or failures such as missing project, no matching route, or no active response.

## JSON storage pattern

SQLite fields that hold arbitrary JSON are stored as `TEXT` columns. The app serializes/deserializes them in `crud.py`:

- `dumps_json(value)` converts Python data into JSON text.
- `loads_json(value)` converts JSON text back into Python data.
- `apply_json_out(obj, fields)` converts model JSON fields before returning API responses.

The important JSON fields are:

- route: `expected_headers_json`, `expected_body_json`
- response: `headers_json`, `body_json`, `condition_json`
- log: `query_json`, `headers_json`, `body_json`

## Validation and normalization

Validation lives in `backend/app/schemas.py`.

Important behavior:

- project slugs are stripped and lowercased
- route methods are stripped and uppercased
- route paths are normalized to start with `/`
- empty route paths are rejected
- `status_code` must be between `100` and `599`
- `delay_ms` must be between `0` and `120000`

## Admin API endpoints

### Projects and dashboard

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/admin/projects` | create project |
| `GET` | `/admin/projects` | list projects |
| `GET` | `/admin/projects/{project_id}` | get one project |
| `PUT` | `/admin/projects/{project_id}` | update project |
| `DELETE` | `/admin/projects/{project_id}` | delete project and cascaded child data |
| `GET` | `/admin/dashboard` | dashboard totals and latest logs |
| `GET` | `/admin/logs` | list all logs |
| `GET` | `/admin/projects/{project_id}/logs` | list logs for one project |

### Routes

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/admin/projects/{project_id}/routes` | create route under project |
| `GET` | `/admin/projects/{project_id}/routes` | list project routes |
| `GET` | `/admin/routes/{route_id}` | get one route |
| `PUT` | `/admin/routes/{route_id}` | update route |
| `DELETE` | `/admin/routes/{route_id}` | delete route and cascaded responses |
| `GET` | `/admin/routes/{route_id}/logs` | list logs for one route |

### Responses

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/admin/routes/{route_id}/responses` | create response under route |
| `GET` | `/admin/routes/{route_id}/responses` | list route responses by priority then id |
| `GET` | `/admin/responses/{response_id}` | get one response |
| `PUT` | `/admin/responses/{response_id}` | update response |
| `DELETE` | `/admin/responses/{response_id}` | delete response |

### Demo seed

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/admin/seed/demo` | create/update the LMS login demo data |

## Runtime mock flow

Runtime requests are handled by:

```text
/mock/{project_slug}/{actual_path:path}
```

Supported runtime methods:

- `GET`
- `POST`
- `PUT`
- `PATCH`
- `DELETE`
- `OPTIONS`
- `HEAD`

Request handling flow:

1. Normalize the request method to uppercase.
2. Normalize the requested path to start with `/` and remove trailing slash except for root.
3. Flatten query parameters. Repeated query keys become arrays; single values stay strings.
4. Normalize request header keys to lowercase.
5. Read the body:
   - no body becomes `None`
   - valid `application/json` becomes parsed JSON
   - invalid JSON becomes an object with `_raw` and `_json_error`
   - non-JSON body becomes text
6. Find an active project by `project_slug`.
7. Find active routes in that project with the same HTTP method.
8. Match the saved route path against the requested path.
9. Load active responses for the matched route, ordered by `priority` then `id`.
10. Build matcher context:

```json
{
  "body": {},
  "headers": {},
  "query": {},
  "params": {}
}
```

11. Select the first response whose conditions match.
12. If no conditional response matches, select the default response.
13. If no default exists, select the first active response.
14. Apply `delay_ms` if configured.
15. Return `body_json`, `headers_json`, and `status_code`.
16. Write a request log.

Failure behavior:

| Situation | Status | Body |
| --- | ---: | --- |
| project slug not found or inactive | `404` | `{ "detail": "Mock project not found" }` |
| no route matched | `404` | `{ "detail": "No mock route matched", "method": "...", "path": "..." }` |
| matched route has no active responses | `404` | `{ "detail": "No active responses configured for matched route" }` |

## Path matching

Path matching lives in `backend/app/services/path_matcher.py`.

Behavior:

- paths are normalized to start with `/`
- trailing slash is removed unless the path is `/`
- route path placeholders use `{param_name}`
- placeholder names must start with a letter or underscore
- placeholder values match one URL path segment only

Examples:

| Saved route path | Runtime path | Result |
| --- | --- | --- |
| `/api/login` | `/api/login` | match |
| `/api/users/{id}` | `/api/users/15` | match with `params.id = "15"` |
| `/api/users/{id}` | `/api/users/15/posts` | no match |

## Condition matching

Condition matching lives in `backend/app/services/matcher.py`.

Supported operators:

- `equals`
- `not_equals`
- `exists`
- `missing`
- `contains`
- `greater_than`
- `less_than`
- `in`
- `not_in`
- `starts_with`
- `ends_with`

Conditions use dotted paths into the matcher context:

```json
{
  "body.email": { "operator": "equals", "value": "test@test.com" },
  "headers.authorization": { "operator": "exists" },
  "query.status": { "operator": "equals", "value": "active" },
  "params.id": { "operator": "equals", "value": "15" }
}
```

Important details:

- empty or missing `condition_json` means the response matches
- invalid condition shapes do not match
- unsupported operators do not match
- `equals` compares both native equality and string equality
- numeric comparisons convert values with `float(...)`
- numeric conversion failures cause the condition not to match

## Response selection behavior

`select_response` in `mock_runtime.py` receives responses already sorted by priority and id.

Selection order:

1. first active response whose `condition_json` matches
2. first active response marked `is_default`
3. first active response
4. `None` if there are no active responses

Because empty `condition_json` matches immediately, developers should be careful with priority. A response with no condition and low priority can prevent later conditional responses from being reached.

Recommended practice:

- put specific conditional responses at low priority numbers, such as `1`, `2`, `3`
- put broad/default responses at higher priority numbers, such as `100`
- mark exactly one fallback response as `is_default`

## Default response handling

When a response is created or updated with `is_default=true`, `crud.py` clears `is_default` from other responses on the same route. This keeps default behavior deterministic.

## Admin UI architecture

The Admin UI is intentionally simple and framework-free.

Important files:

- `backend/app/static/index.html`: layout shell, navigation, view containers, modal, toast
- `backend/app/static/app.js`: state management, API calls, rendering, forms, logs, demo seed
- `backend/app/static/style.css`: styles

`app.js` keeps client state in a single object:

```js
const state = {
  view: 'dashboard',
  projects: [],
  routes: [],
  responses: [],
  selectedProject: null,
  selectedRoute: null
};
```

The UI uses `fetch` through a small `api(url, options)` helper. Forms serialize data to JSON and call the admin endpoints.

## Error handling

Backend admin helper functions raise `HTTPException` for not-found and duplicate resources. Runtime routes return JSON `404` responses for unmatched project, route, or response cases and still write logs where possible.

Frontend errors are displayed with the toast helper.

## Database notes

- tables are created automatically on startup
- SQLite is the default database
- Docker persists database data under `./data`
- JSON data is stored as text rather than native JSON columns
- cascade delete is configured for project routes, route responses, and related logs where relationships define `cascade="all, delete-orphan"`

## Development guidelines

When adding features:

1. Add or update SQLAlchemy models in `models.py`.
2. Add or update Pydantic schemas in `schemas.py`.
3. Add persistence logic in `crud.py` when serialization, validation, or default-response behavior is needed.
4. Add or update endpoints in the appropriate router.
5. Update the Admin UI if the feature is user-facing.
6. Update documentation examples.
7. Add tests if a test suite is introduced.

When changing matcher behavior:

1. Update `services/matcher.py` or `services/path_matcher.py`.
2. Add examples to `HOW_TO_USE.md`.
3. Consider backwards compatibility with existing `condition_json` stored in SQLite.

When changing JSON fields:

1. Update `JSON_FIELDS` and relevant helpers in `crud.py` if needed.
2. Update schemas so API inputs/outputs stay consistent.
3. Consider data migration because existing SQLite values are stored as text.

## Known limitations and improvement ideas

### No authentication

The Admin UI and admin API are open. Add authentication before exposing the app outside trusted local/dev networks.

### No migration system

The app uses `Base.metadata.create_all`. For production-like use, add Alembic migrations.

### No automated test suite yet

There are no test files in the repository. Good first tests would cover:

- condition operators
- dynamic path matching
- response selection order
- CRUD serialization/deserialization
- runtime 404 cases

### Minimal frontend structure

The UI is a compact vanilla JavaScript app. If it grows, consider splitting `app.js` by domain or introducing a frontend build system.

### No import/export feature

A useful future feature would be exporting/importing projects, routes, and responses as JSON files.

### No response templating

Response bodies are static JSON. A future improvement could support templating values from `body`, `query`, `headers`, or `params`.

## Useful manual checks

Create demo data:

```bash
curl -X POST http://localhost:8000/admin/seed/demo
```

Call a successful login mock:

```bash
curl -X POST http://localhost:8000/mock/lms/api/login \
  -H 'Content-Type: application/json' \
  -d '{ "email": "test@test.com", "password": "123456" }'
```

Call the default invalid login mock:

```bash
curl -X POST http://localhost:8000/mock/lms/api/login \
  -H 'Content-Type: application/json' \
  -d '{ "email": "wrong@example.com", "password": "bad" }'
```

Check logs:

```bash
curl http://localhost:8000/admin/logs
```
