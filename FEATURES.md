# Mock API Provider Features

Mock API Provider helps teams create and manage local mock APIs without writing custom server code for every endpoint.

## Main features

### 1. Project-based organization

Group related mock routes under a project. Each project has a unique slug that becomes part of the runtime URL:

```text
/mock/{project_slug}/{actual_path}
```

Example:

```text
/mock/lms/api/login
```

This makes it easy to keep mocks separated by product, client, service, or testing scenario.

### 2. Built-in Admin UI

The app includes a browser-based Admin UI at:

```text
http://localhost:8000
```

From the UI, users can:

- view dashboard metrics
- create, edit, and delete projects
- create, edit, and delete routes
- create, edit, mark default, and delete responses
- seed demo data
- inspect request logs
- open the generated OpenAPI docs

### 3. Runtime mock endpoints

All configured routes are served under the `/mock` URL prefix:

```text
/mock/{project_slug}/{actual_path}
```

If a project has slug `mobile-app` and a route path `/api/users`, the callable mock URL is:

```text
http://localhost:8000/mock/mobile-app/api/users
```

### 4. Multiple HTTP methods

Routes can be configured for common API methods:

- `GET`
- `POST`
- `PUT`
- `PATCH`
- `DELETE`
- runtime handler also accepts `OPTIONS` and `HEAD`

Methods are normalized to uppercase.

### 5. Static and dynamic paths

Routes can be static:

```text
/api/login
```

Or dynamic:

```text
/api/users/{id}
/api/orders/{order_id}/items/{item_id}
```

Dynamic values are available in response conditions through `params`, for example:

```json
{
  "params.id": { "operator": "equals", "value": "15" }
}
```

### 6. Multiple responses per route

A single route can have many possible responses. For example, `POST /api/login` can return:

- `200` for valid credentials
- `401` for invalid credentials
- `429` for rate limiting
- `500` for server-error testing

This allows frontend and QA teams to test success and failure flows from one mock route.

### 7. Condition-based matching

Responses can be selected based on request data:

- JSON body values
- request headers
- query parameters
- dynamic path parameters

Example:

```json
{
  "body.email": { "operator": "equals", "value": "test@test.com" },
  "headers.authorization": { "operator": "starts_with", "value": "Bearer " }
}
```

### 8. Priority-based response selection

Responses are evaluated in ascending priority order. Lower priority numbers run first.

Example:

| Response | Priority | Result |
| --- | ---: | --- |
| Login success | `1` | checked first |
| Locked account | `5` | checked second |
| Default invalid credentials | `100` | fallback |

Priority makes matching predictable when multiple responses could match the same request.

### 9. Default fallback response

A response can be marked as the default for a route. If no conditional response matches, the default response is returned.

This is useful for fallback errors such as:

```json
{
  "message": "Invalid credentials"
}
```

### 10. Custom response headers

Each response can include JSON-defined headers:

```json
{
  "x-mock-source": "mock-api-provider",
  "cache-control": "no-store"
}
```

Headers are returned with the response to simulate realistic APIs.

### 11. Custom JSON response bodies

Each response can return any JSON-compatible value:

- object
- array
- string
- number
- boolean
- `null`

Example:

```json
{
  "data": [
    { "id": 1, "name": "First item" },
    { "id": 2, "name": "Second item" }
  ],
  "meta": { "total": 2 }
}
```

### 12. Artificial response delays

Responses can be delayed using `delay_ms`.

Use this to test:

- loading indicators
- timeout behavior
- retry logic
- slow network experiences

Example:

```json
{
  "delay_ms": 1500
}
```

### 13. Request logging

Every runtime mock request is logged, including matched and unmatched requests.

Logs include:

- request time
- HTTP method
- path
- query parameters
- headers
- request body
- status code
- matched project, route, and response names when available

This helps users debug what the client actually sent.

### 14. Dashboard metrics

The dashboard summarizes:

- total projects
- total routes
- active routes
- total request logs
- latest request logs

### 15. Demo seed endpoint

A seed endpoint creates a ready-to-use login demo:

```bash
curl -X POST http://localhost:8000/admin/seed/demo
```

The demo includes:

- project: `LMS`
- slug: `lms`
- route: `POST /api/login`
- success response for known credentials
- default invalid-credentials response

### 16. Local persistence with SQLite

The default database is SQLite at:

```text
data/mock.db
```

Docker Compose mounts `./data` into the container so data can persist across restarts.

### 17. OpenAPI documentation

FastAPI automatically provides API documentation at:

```text
http://localhost:8000/docs
```

Use it to explore and test admin endpoints directly from the browser.

### 18. CORS enabled for local development

The API allows cross-origin requests, which makes it easy to connect a local frontend or mobile development environment to the mock server.

## Common use cases

### Frontend development before backend completion

Frontend teams can build screens against realistic API responses before backend endpoints are finished.

### QA scenario testing

QA teams can create different responses for edge cases:

- empty states
- validation errors
- authentication failures
- permission errors
- server errors
- slow responses

### Mobile app development

Mobile apps can point their API base URL to the local mock server during development.

### Integration demos

Teams can create stable demo data for presentations, sales demos, stakeholder reviews, or design validation.

### Contract discussion

The project, route, expected request JSON, and response JSON fields can act as a lightweight API contract while teams discuss the final backend design.

## Feature summary table

| Feature | Benefit |
| --- | --- |
| Projects | separate mocks by app or domain |
| Routes | define mock method/path combinations |
| Dynamic paths | support IDs and nested resources |
| Multiple responses | simulate many scenarios per endpoint |
| Conditions | match request body, headers, query, and params |
| Priority | choose deterministic response order |
| Default response | safe fallback when no condition matches |
| Custom headers | simulate production-like response metadata |
| Delay | test slow network behavior |
| Logs | debug client requests and matcher results |
| Dashboard | quick overview of usage and activity |
| Docker Compose | run with one command |
| SQLite persistence | keep mock data locally |
| OpenAPI docs | inspect and test admin API endpoints |
