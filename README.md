# Social Media MongoDB Server

A FastAPI-based backend server with full user authentication, JWT-based security, and CRUD operations for posts and comments.  
MongoDB (running locally) is used as the database, with Motor as the async driver and Poetry for dependency management.

## Features

### User Authentication
- Secure user registration
- Password hashing using Passlib
- Login using OAuth2 password form
- JWT-based authentication (Bearer `<token>`)
- Protected endpoints require valid tokens
- Ownership enforcement (users can edit/delete only their own content)

### Posts
- Create posts (authenticated)
- Publicly list all posts
- Retrieve a post by ID
- Update & delete posts (owner only)

Each post includes:
- title
- content
- timestamps
- author_id
- author_username

### Comments
- Add comments to any post (authenticated)
- Publicly list comments for a post
- Update & delete comments (owner only)

Each comment includes:
- post_id
- content
- timestamps
- author_id
- author_username

## Database Schema (MongoDB)

### users collection
```json
{
  "_id": "ObjectId",
  "email": "string",
  "username": "string",
  "password": "string (hashed)"
}
```

### posts collection
```json
{
  "_id": "ObjectId",
  "title": "string",
  "content": "string",
  "created_at": "datetime",
  "updated_at": "datetime",
  "author_id": "ObjectId",
  "author_username": "string"
}
```

### comments collection
```json
{
  "_id": "ObjectId",
  "post_id": "ObjectId",
  "content": "string",
  "created_at": "datetime",
  "updated_at": "datetime",
  "author_id": "ObjectId",
  "author_username": "string"
}
```

### Indexes Created
- users.email → unique index  
- posts.created_at → for sorting  
- comments(post_id, created_at) → for fast comment retrieval

## Running the Server

1. Install dependencies
```bash
poetry install
```

2. Start MongoDB

    Run it locally through MongoDB Compass or:
```bash
mongod
```

3. Start the FastAPI server
```bash
poetry run uvicorn social_media_mongodb_server.main:app --reload
```

## Environment Variables

Create a `.env` file in the project root:
```
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=social_media_db
SECRET_KEY=YOUR_SECRET_KEY_HERE
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Generate a strong secret key via an online tool or:
```bash
openssl rand -hex 32
```

## Authentication Workflow

### Register
`POST /auth/register`  
Content-Type: `application/json`
```json
{
  "email": "user@example.com",
  "username": "testuser",
  "password": "mypassword"
}
```

### Login
`POST /auth/login`  
Content-Type: `application/x-www-form-urlencoded`
```
username=user@example.com
password=mypassword
```

Response:
```json
{
  "access_token": "<JWT>",
  "token_type": "bearer"
}
```

Use the token for all protected routes:
```
Authorization: Bearer <JWT>
```

## Postman Collection

A Postman collection is included containing:
- Register user
- Login
- Create Post
- List Posts
- Create Comment
- List Comments
- Update/Delete Post
- Update/Delete Comment

## Project Structure
```
social_media_mongodb_server/
├── main.py
├── db.py
├── auth.py
├── users.py
├── models.py
└── routes_posts.py
```
