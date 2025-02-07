# E-Commerce API

## Overview

This is a FastAPI-based E-Commerce API designed to handle user registration, authentication, product management, and shopping cart functionality. The API includes endpoints for creating users, logging in, managing categories and products, and handling a shopping cart.

## Features

- **User Registration and Login** with JWT authentication
- **Category and Product Management**
- **Shopping Cart** with the ability to add, update, or remove items
- **Checkout Functionality**
- **Secured Endpoints** with OAuth2-based access control
- **Database Interaction** through SQLAlchemy ORM

## Libraries and Tools Used

- **FastAPI**: Modern web framework for building APIs with Python 3.7+.
- **SQLAlchemy**: SQL toolkit and ORM for Python.
- **Pydantic**: Data validation and settings management using Python type annotations.
- **OAuth2**: For token-based authentication using JWT.
- **SQLite** (or another database): For persistent storage of users, products, and carts.
- **JWT**: For securely handling authentication and session management.

## Prerequisites

To run this project locally, you will need:

- Python 3.7 or higher
- A virtual environment is recommended for managing dependencies.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/MdAkash3135/e-commerce-api.git
cd e-commerce-api
 ```

### 2. Create a Virtual Environment
```
python3 -m venv venv
```
### 3. Activate the Virtual Environment
```
For Windows:
.\venv\Scripts\activate
```
```
For macOS/Linux:
bash
source venv/bin/activate
```

### 4. Install the Required Dependencies
```
bash
pip install -r requirements.txt
```
### Database configuration 
```
Replace line 7 from database.py with you credential
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/dbname"
```
### use alembic as migration tool 

### to start the application 
```
uvicorn main:app --reload
```


```
Endpoints
Authentication
POST /register: Register a new user.
POST /login: Log in and obtain a JWT token.
GET /protected: Protected route, requires valid JWT token.
Categories
POST /categories/: Create a new product category.
GET /categories/: List all product categories.
Products
POST /products/: Create a new product.
GET /products/: List products with optional filters (category, price range, stock).
Shopping Cart
GET /{user_id}: Get the cart for a user.
POST /{user_id}/add: Add an item to the user's cart.
PUT /{user_id}/update/{cart_item_id}: Update the quantity of a cart item.
DELETE /{user_id}/remove/{cart_item_id}: Remove an item from the cart.
Users
POST /users/: Create a new user (admin only).
GET /users/{user_id}: Get a user's details.
PUT /users/{user_id}: Update a user's details.
DELETE /users/{user_id}: Delete a user (admin only).
Checkout
POST /checkout/{user_id}: Checkout and place an order (process the cart).
```
