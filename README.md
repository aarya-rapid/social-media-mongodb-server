# Social Media MongoDB Server
A FastAPI-based backend server that provides basic social media functionality, including creating posts and comments, retrieving data, updating content, and deleting entries. MongoDB is used as the data store, accessed asynchronously via Motor. The project is built and managed using Poetry.

## Features

- Create, read, update, and delete posts
- Create, read, update, and delete comments
- Each post can have multiple comments
- Fully asynchronous implementation
- MongoDB backend
- Automatically generated interactive API documentation using FastAPI
- Clean project structure using Poetry environment management

## Tech Stack

- FastAPI – Web framework for building APIs
- Uvicorn – ASGI server
- MongoDB – NoSQL database
- Motor – Asynchronous MongoDB driver
- Pydantic – Data validation and serialization
- Poetry – Dependency and environment management
- python-dotenv – Environment variable handling

## Project Structure

```
social-media-mongodb-server/
├── pyproject.toml
├── .env
└── social_media_mongodb_server/
    ├── __init__.py
    ├── main.py
    ├── db.py
    ├── models.py
    └── routes_posts.py
```

- **main.py** – FastAPI app initialization and router registration  
- **db.py** – MongoDB connection handling  
- **models.py** – Pydantic models and helper functions  
- **routes_posts.py** – Routes for posts and comments  

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/aarya-rapid/social-media-mongodb-server.git
cd social-media-mongodb-server
```

### 2. Install dependencies via Poetry

```bash
poetry install
```

### 3. Create a `.env` file in the project root

```
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=social_media_db
```

Ensure a MongoDB instance is running locally:

```bash
docker run -d --name mongodb -p 27017:27017 mongo:7
```

(or use a native MongoDB installation)

### 4. Run the FastAPI server

```bash
poetry run uvicorn social_media_mongodb_server.main:app --reload
```

The server will start at:

```
http://127.0.0.1:8000
```

## API Documentation

FastAPI automatically generates interactive documentation:

- Swagger UI:
  ```
  http://127.0.0.1:8000/docs
  ```
- ReDoc:
  ```
  http://127.0.0.1:8000/redoc
  ```

## Example Endpoints

### Create a Post

POST `/posts/`
```json
{
  "title": "My first post",
  "content": "Hello world"
}
```

### Create a Comment for a Post

POST `/posts/{post_id}/comments`
```json
{
  "author": "John Doe",
  "content": "Nice post!"
}
```

Use the Swagger or Postman collection to test full CRUD functionality.

## Postman Collection

A Postman collection file (`social_media_api.postman_collection.json`) can be imported into Postman to test all endpoints easily.

## License

This repository is intended for internal development and learning purposes. You may add a formal license if needed.
