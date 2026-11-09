# URL Shortener Microservice

A REST API built with **FastAPI** and **Redis** that generates short codes for long URLs and redirects users to their original destinations.

## Features

- Create short URLs through a POST endpoint.
- Retrieve original URLs through HTTP redirects.
- Validate submitted URLs using Pydantic.
- Store URL mappings in Redis.
- Prevent duplicate submissions.
- Handle missing URLs and invalid requests.
- Automatically generated OpenAPI documentation through Swagger UI.
- Docker-based application and Redis deployment.

## Tech Stack

- Python 3.11+
- FastAPI
- Pydantic
- Redis
- redis-py (asyncio)
- Uvicorn
- Docker and Docker Compose

## Project Structure

```text
url_shortener_microservice/
├── app/
│   ├── routers/
│   │   └── url.py
│   ├── dependency.py
│   └── main.py
├── .env.example
├── .gitignore
├── compose.yaml
├── Dockerfile
├── pyproject.toml
├── requirements.txt
└── uv.lock
```

## Setup and Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd url_shortener_microservice
```

### 2. Configure environment variables

Create a `.env` file using `.env.example`:

```env
REDIS_HOST=redis
REDIS_PORT=6379
```

### 3. Run with Docker Compose

```bash
docker compose up --build
```

The application and Redis will start as separate containers.

### 4. Access API documentation

Open:

```text
http://localhost:8000/docs
```

Swagger UI allows you to interact with and test the API.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/` | Generate a short URL |
| GET | `/api/{short_code}` | Redirect to the original URL |

### Create a short URL

**Request:**

```json
{
  "url": "https://www.example.com"
}
```

**Successful response:** `201 Created`

```json
{
  "url": "example-short-code"
}
```

### Retrieve a short URL

Access:

```text
http://localhost:8000/api/example-short-code
```

A successful lookup returns an HTTP redirect to the original URL.

**Possible status codes:**

- `201` – Short URL created.
- `302` – Redirect to original URL.
- `404` – Short code not found.
- `409` – URL has already been shortened.
- `422` – Invalid request data.

## Architecture

- **FastAPI:** Handles HTTP requests, routing and API documentation.
- **APIRouter:** Separates URL-shortening endpoints from the main application.
- **Dependency Injection:** Uses FastAPI's `Depends` to provide a shared Redis client to endpoints.
- **Pydantic:** Validates incoming URL data.
- **Redis:** Stores original-to-short and short-to-original URL mappings.
- **Docker Compose:** Orchestrates the API and Redis services.

