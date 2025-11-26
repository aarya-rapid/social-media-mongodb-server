# Social Media MongoDB Server

This is a fully-featured social media backend built using **FastAPI**, **MongoDB**, and an MVC-style architecture. It supports posts, comments, authentication with JWT, real-time email notifications, and an AI image generation pipeline for posts using **Flux MCP → Pollinations → Local fallback**.

---

## ⚙ Tech Stack

| Component           | Technology                                      |
| ------------------- | ----------------------------------------------- |
| Backend             | FastAPI                                         |
| Database            | MongoDB                                         |
| Auth                | JWT                                             |
| Task Queue          | Celery + Redis                                  |
| Email               | SendGrid                                        |
| AI Image Generation | Flux MCP Server → Pollinations → Local fallback |
| Static Files        | Starlette StaticFiles                           |
|



## 📌 Core Features

### 🔐 Authentication

* Register new users
* Login with JWT access tokens
* Protected routes using dependency-based auth

### 📝 Posts

* Create, update, delete posts
* **Aggregation-based listing** for performance
* Fetch all posts or posts by a specific user
* Get a single post **with or without comments**
* **Optional AI image generation** using Flux MCP when creating/updating posts
* Stored image metadata: `image_url`, `image_provider`, `image_prompt`

### 💬 Comments

* Create, edit, delete comments
* List comments for a post using **aggregation**

### 📧 Email Notifications

* When someone comments on a post, the post author receives an **email notification**
* Uses **Celery background tasks + SendGrid**

### 🖼 AI Image Generation Pipeline

When a post is created with `generate_image = true`, the system tries:

1️⃣ **Flux MCP server**
2️⃣ **Pollinations AI** (direct URL API)
3️⃣ **Local fallback** — picks a random image from

```
static/images/fallbacks/
```

This guarantees an image **even when external AI services are down**.

---

## 📁 Project Architecture

```
social_media_mongodb_server/
│
├─ routes/         → API layer (HTTP endpoints)
├─ services/       → Business logic
├─ repositories/   → DB access (Mongo)
├─ models/         → Pydantic models / schemas
├─ tasks/          → Celery background jobs (email)
├─ utils/          → Shared helper utilities
├─ scripts/        → Debug & testing scripts (imagegen tester)
│
static/images/fallbacks/  → local fallback images
```

This structure keeps the system modular and scalable.

---

## 🔗 Postman Collection

A complete collection is included to test:

* Auth (login & register)
* Post CRUD
* Comment CRUD
* Image generation endpoint
* Aggregation queries

⚠ After logging in, the `access_token` is automatically saved as a Collection Variable — no manual copying needed.

---

## ▶ Running the Project Locally

### 1️⃣ Install dependencies

```bash
poetry install
```

### 2️⃣ Start Redis (for Celery)

```bash
redis-server
```

### 3️⃣ Run Celery worker (in a separate command line window)

```bash
poetry run celery -A social_media_mongodb_server.tasks.email_tasks worker --loglevel=INFO
```

### 4️⃣ Run FastAPI backend (in a separate command line window)

```bash
poetry run uvicorn social_media_mongodb_server.main:app --reload
```

Server will start at:

```
http://127.0.0.1:8000
```

Docs:

```
http://127.0.0.1:8000/docs
```

---

## 🔑 Required Environment Variables

Create a `.env` file:

```
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=socialmedia
JWT_SECRET=YOUR_SECRET_KEY
JWT_EXPIRE_MINUTES=43200
SENDGRID_API_KEY=YOUR_KEY
SENDER_EMAIL=YOUR_EMAIL
APP_BASE_URL=http://127.0.0.1:8000
REDIS_URL=redis://localhost:6379/0

# Flux MCP Image Generation
FLUX_MCP_API_KEY=YOUR_KEY
FLUX_MCP_BASE_URL=https://server.smithery.ai/@falahgs/flux-imagegen-mcp-server/mcp

# Pollinations fallback
POLLINATIONS_BASE_URL=https://image.pollinations.ai/prompt
```

Ensure local fallback images directory exists:

```
static/images/fallbacks/
```

---

## 🧪 Image Generator Testing Script (optional)

To test Flux → Pollinations → Local fallback behavior outside the API:

```bash
poetry run python -m social_media_mongodb_server.scripts.test_flux_mcp
```

---
