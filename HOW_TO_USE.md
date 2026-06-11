# How to Use Mock API Provider

Mock API Provider is a local tool for creating fake API endpoints that return predictable responses. It is useful when a frontend, mobile app, QA environment, or integration test needs an API before the real backend is ready.

## Quick start

### Option 1: Run with Docker Compose

```bash
docker compose up --build
```

Open these URLs after the container starts:

- Admin UI: <http://localhost:8000>
- OpenAPI docs: <http://localhost:8000/docs>
- Mock endpoint base URL: `http://localhost:8000/mock/{project_slug}/{actual_path}`

### Option 2: Run locally with Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

By default, data is saved in `data/mock.db`.

## Main user flow

The app is organized around three simple objects:

1. **Project**: a workspace for one product, client, app, or API group.
2. **Route**: one mocked API path inside a project, such as `POST /api/login`.
3. **Response**: one possible response for a route, such as success, validation error, or unauthorized.

### Step 1: Create a project

In the Admin UI:

1. Open <http://localhost:8000>.
2. Go to **Projects**.
3. Click **Create project**.
4. Fill in:
   - **Name**: human-friendly name, for example `LMS`.
   - **Slug**: URL-safe identifier, for example `lms`.
   - **Description**: optional notes.
   - **Active**: keep enabled if the project should serve mock traffic.

Equivalent API request:

```bash
curl -X POST http://localhost:8000/admin/projects \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "LMS",
    "slug": "lms",
    "description": "Learning management system mocks",
    "is_active": true
  }'
```

### Step 2: Create a route

A route defines the HTTP method and path the mock server should listen for.

In the Admin UI:

1. Open the project.
2. Click **Routes**.
3. Click **Create route**.
4. Fill in:
   - **Name**: for example `Login`.
   - **Method**: `GET`, `POST`, `PUT`, `PATCH`, or `DELETE`.
   - **Path**: for example `/api/login`.
   - **Expected headers JSON**: optional documentation/example data.
   - **Expected body JSON**: optional documentation/example data.
   - **Active**: keep enabled if this route should be matched.

Equivalent API request:

```bash
curl -X POST http://localhost:8000/admin/projects/1/routes \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Login",
    "method": "POST",
    "path": "/api/login",
    "description": "Login endpoint",
    "expected_headers_json": { "content-type": "application/json" },
    "expected_body_json": { "email": "test@test.com", "password": "123456" },
    "is_active": true
  }'
```

The runtime mock URL format is:

```text
/mock/{project_slug}/{actual_path}
```

For the example above, call:

```text
http://localhost:8000/mock/lms/api/login
```

### Step 3: Create one or more responses

A response defines what the mock server returns when a route is called.

In the Admin UI:

1. Open a route.
2. Click **Responses**.
3. Click **Create response**.
4. Fill in:
   - **Name**: for example `Login success`.
   - **Status code**: for example `200`.
   - **Priority**: lower numbers are checked first.
   - **Delay ms**: optional artificial delay in milliseconds.
   - **Headers JSON**: response headers, for example `{ "x-mock": "true" }`.
   - **Body JSON**: response body returned to the caller.
   - **Condition JSON**: optional matching rules.
   - **Default**: fallback response when no condition matches.
   - **Active**: keep enabled if this response can be returned.

Success response example:

```bash
curl -X POST http://localhost:8000/admin/routes/1/responses \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Login Success",
    "status_code": 200,
    "priority": 1,
    "headers_json": { "x-mock-source": "mock-api-provider" },
    "condition_json": {
      "body.email": { "operator": "equals", "value": "test@test.com" },
      "body.password": { "operator": "equals", "value": "123456" }
    },
    "body_json": {
      "message": "Login successful",
      "token": "mock-token-123",
      "user": { "id": 1, "name": "Osama" }
    },
    "delay_ms": 0,
    "is_default": false,
    "is_active": true
  }'
```

Default error response example:

```bash
curl -X POST http://localhost:8000/admin/routes/1/responses \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Invalid Credentials",
    "status_code": 401,
    "priority": 100,
    "is_default": true,
    "body_json": { "message": "Invalid credentials" },
    "is_active": true
  }'
```

### Step 4: Call the mock endpoint

```bash
curl -X POST http://localhost:8000/mock/lms/api/login \
  -H 'Content-Type: application/json' \
  -d '{ "email": "test@test.com", "password": "123456" }'
```

Expected response:

```json
{
  "message": "Login successful",
  "token": "mock-token-123",
  "user": {
    "id": 1,
    "name": "Osama"
  }
}
```

### Step 5: Review request logs

Use **Logs** in the Admin UI to inspect recent mock calls. Logs show:

- Time
- HTTP method
- Requested path
- Returned status code
- Matched response name
- Query parameters
- Request body
- Request headers

Logs are helpful for debugging why a request matched a specific response, or why it returned `404`.

## Data formats

### Project format

```json
{
  "name": "LMS",
  "slug": "lms",
  "description": "Learning platform mocks",
  "is_active": true
}
```

Rules:

- `name` is required.
- `slug` is required and is normalized to lowercase.
- `slug` can contain letters, numbers, underscores, and hyphens.
- inactive projects do not serve mock responses.

### Route format

```json
{
  "name": "Get User",
  "method": "GET",
  "path": "/api/users/{id}",
  "description": "Returns a single user by id",
  "expected_headers_json": { "authorization": "Bearer example-token" },
  "expected_body_json": null,
  "is_active": true
}
```

Rules:

- `method` is normalized to uppercase.
- `path` is normalized to start with `/`.
- dynamic path parameters use `{param_name}`, for example `/api/users/{id}`.
- inactive routes are ignored by the runtime matcher.

### Response format

```json
{
  "name": "User found",
  "status_code": 200,
  "headers_json": { "cache-control": "no-store" },
  "body_json": {
    "id": 15,
    "name": "Test User"
  },
  "condition_json": {
    "params.id": { "operator": "equals", "value": "15" }
  },
  "priority": 1,
  "delay_ms": 200,
  "is_default": false,
  "is_active": true
}
```

Rules:

- `status_code` must be between `100` and `599`.
- `delay_ms` can be `0` to `120000`.
- lower `priority` values are evaluated first.
- only active responses can be returned.
- only one response per route should be marked as default; when a response is marked default, other responses on the same route are unmarked.

## Condition JSON guide

`condition_json` lets one route return different responses based on the incoming request.

The condition object uses this shape:

```json
{
  "context.path": {
    "operator": "operator_name",
    "value": "expected value when needed"
  }
}
```

Available context roots:

| Root | Meaning | Example key |
| --- | --- | --- |
| `body` | JSON body or raw request body | `body.email` |
| `headers` | request headers normalized to lowercase | `headers.authorization` |
| `query` | query string values | `query.status` |
| `params` | dynamic path parameters | `params.id` |

Supported operators:

| Operator | Meaning | Example |
| --- | --- | --- |
| `equals` | actual value equals expected value | `{ "operator": "equals", "value": "active" }` |
| `not_equals` | actual value does not equal expected value | `{ "operator": "not_equals", "value": "blocked" }` |
| `exists` | field exists | `{ "operator": "exists" }` |
| `missing` | field does not exist | `{ "operator": "missing" }` |
| `contains` | string/list contains expected value | `{ "operator": "contains", "value": "admin" }` |
| `greater_than` | actual number is greater than expected number | `{ "operator": "greater_than", "value": 10 }` |
| `less_than` | actual number is less than expected number | `{ "operator": "less_than", "value": 100 }` |
| `in` | actual value is inside expected list/string | `{ "operator": "in", "value": ["new", "active"] }` |
| `not_in` | actual value is not inside expected list/string | `{ "operator": "not_in", "value": ["deleted"] }` |
| `starts_with` | actual string starts with expected value | `{ "operator": "starts_with", "value": "Bearer " }` |
| `ends_with` | actual string ends with expected value | `{ "operator": "ends_with", "value": ".com" }` |

## Dynamic routes

Use `{param}` placeholders in a saved route path:

```text
/api/users/{id}
```

Then call:

```bash
curl http://localhost:8000/mock/lms/api/users/15
```

The matcher exposes this condition context:

```json
{
  "params": {
    "id": "15"
  }
}
```

You can match a response with:

```json
{
  "params.id": { "operator": "equals", "value": "15" }
}
```

## Demo seed

To create a ready-made login example:

```bash
curl -X POST http://localhost:8000/admin/seed/demo
```

Then call:

```bash
curl -X POST http://localhost:8000/mock/lms/api/login \
  -H 'Content-Type: application/json' \
  -d '{ "email": "test@test.com", "password": "123456" }'
```

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `Mock project not found` | project slug in the URL, and project is active |
| `No mock route matched` | HTTP method, route path, project slug, and route active status |
| `No active responses configured` | route has at least one active response |
| wrong response returned | response priorities and conditions |
| condition does not match | header keys are lowercase, path params are strings, JSON body is valid |
