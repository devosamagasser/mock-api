# Mock API Provider

A local-first Mock API Provider built with FastAPI, SQLite, SQLAlchemy, and a native HTML/CSS/JavaScript admin UI. It lets you create projects, mock routes, multiple response cases, priority/default matching, artificial delays, and request logs. The frontend is served by FastAPI at <http://localhost:8000>, and OpenAPI docs are available at <http://localhost:8000/docs>.

## Features

- Project-based mock route organization.
- Static and dynamic route paths such as `/api/login` and `/api/users/{id}`.
- Response cases with status code, headers, JSON body, conditions, priority, default flag, and delay.
- Runtime mock endpoint pattern: `/mock/{project_slug}/{actual_path}`.
- Request logging for matched and unmatched mock calls.
- Local SQLite persistence in `data/mock.db`.
- Docker Compose setup with a persistent `./data` volume.

## Project structure

```text
mock-api-provider/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── crud.py
│   │   ├── routers/
│   │   ├── services/
│   │   └── static/
│   ├── requirements.txt
│   └── Dockerfile
├── data/
├── docker-compose.yml
└── README.md
```

## Local setup

```bash
cd mock-api-provider
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

By default the app uses `sqlite:///./data/mock.db`. Override it with:

```bash
export DATABASE_URL="sqlite:///./data/mock.db"
```

## Docker setup

```bash
docker compose up --build
```

The app will be available at:

- Admin UI: <http://localhost:8000>
- API docs: <http://localhost:8000/docs>
- Runtime mocks: `http://localhost:8000/mock/{project_slug}/{actual_path}`

## Admin API examples

Create a project:

```bash
curl -X POST http://localhost:8000/admin/projects \
  -H 'Content-Type: application/json' \
  -d '{"name":"LMS","slug":"lms","description":"Learning platform","is_active":true}'
```

Create a route:

```bash
curl -X POST http://localhost:8000/admin/projects/1/routes \
  -H 'Content-Type: application/json' \
  -d '{"name":"Login","method":"POST","path":"/api/login","is_active":true}'
```

Create a response:

```bash
curl -X POST http://localhost:8000/admin/routes/1/responses \
  -H 'Content-Type: application/json' \
  -d '{
    "name":"Login Success",
    "status_code":200,
    "priority":1,
    "condition_json":{
      "body.email":{"operator":"equals","value":"[test@test.com](mailto:test@test.com)"},
      "body.password":{"operator":"equals","value":"123456"}
    },
    "body_json":{"message":"Login successful","token":"mock-token-123"}
  }'
```

Call the mock route:

```bash
curl -X POST http://localhost:8000/mock/lms/api/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"[test@test.com](mailto:test@test.com)","password":"123456"}'
```

## Demo seed

Create the LMS project, `POST /api/login` route, success response, and default invalid-credentials response:

```bash
curl -X POST http://localhost:8000/admin/seed/demo
```

Then call:

```bash
curl -X POST http://localhost:8000/mock/lms/api/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"[test@test.com](mailto:test@test.com)","password":"123456"}'
```

Expected response:

```json
{
  "message": "Login successful",
  "token": "mock-token-123",
  "user": { "id": 1, "name": "Osama" }
}
```

## `condition_json`

Conditions are an object where each key is a dotted path into the matcher context and each value defines an operator and optional value:

```json
{
  "body.email": { "operator": "equals", "value": "[test@test.com](mailto:test@test.com)" },
  "headers.authorization": { "operator": "exists" },
  "query.status": { "operator": "equals", "value": "active" },
  "params.id": { "operator": "equals", "value": "15" }
}
```

Matcher context:

```json
{
  "body": "incoming JSON request body or raw text",
  "headers": "incoming headers normalized to lowercase",
  "query": "query parameters",
  "params": "dynamic path parameters"
}
```

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

Responses are evaluated by ascending `priority`. The first matching response is returned. If none match, the default response is returned. If no default exists, the first active response is returned.

## Dynamic routes

Saved route paths can include `{param}` placeholders:

- `/api/users/{id}` matches `/mock/mobile-app/api/users/15` and exposes `params.id = "15"`.
- `/api/orders/{order_id}/items/{item_id}` exposes both `params.order_id` and `params.item_id`.

Example condition for a dynamic route:

```json
{
  "params.id": { "operator": "equals", "value": "15" }
}
```

## Notes

- Tables are created automatically on startup with `Base.metadata.create_all`.
- JSON fields are stored as SQLite `TEXT` but exposed as JSON through the admin API.
- HTTP methods are normalized to uppercase and route paths are normalized to start with `/`.
