from typing import List, Union
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas
import crud
import models
from fastapi import APIRouter, Depends, HTTPException
from crud import create_user, get_user_by_username, update_user, delete_user, get_user_by_id
from crud import *
from models import *
from schemas import *
from database import engine, SessionLocal, get_db
from fastapi.security import OAuth2PasswordBearer
from auth import create_access_token, verify_access_token


app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@app.post("/register", response_model=UserCreate)
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = db.query(User).filter(User.username == user.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Username already taken")

        db_user_by_email = db.query(User).filter(User.email == user.email).first()
        if db_user_by_email:
            raise HTTPException(status_code=400, detail="Email already taken")

        new_user = create_user(db, user.username, user.email, user.password)
        return new_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    try:
        db_user = authenticate_user(db, user.username, user.password)
        if db_user is None:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        access_token = create_access_token(data={"sub": str(db_user.id)})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/protected")
def protected_route(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = verify_access_token(token)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user_id = payload.get("sub")
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user is None:
            raise HTTPException(status_code=401, detail="User not found")

        return {"message": f"Hello {db_user.username}, this is a protected route."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/categories/", response_model=schemas.CategoryResponse)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_category(db, category)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/categories/", response_model=List[schemas.CategoryResponse])
def get_categories(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        return crud.get_categories(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------
# PRODUCT ROUTES
# ----------------------

@app.post("/products/", response_model=schemas.ProductResponse)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_product(db, product)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/", response_model=List[schemas.ProductResponse])
def get_products(
    category_id: int = None, 
    min_price: float = None, 
    max_price: float = None, 
    in_stock: bool = None, 
    skip: int = 0, 
    limit: int = 10, 
    db: Session = Depends(get_db)
):
    try:
        return crud.get_products(db, category_id, min_price, max_price, in_stock, skip, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get Cart for a User
@app.get("/{user_id}", response_model=schemas.CartResponse)
def get_cart(user_id: int, db: Session = Depends(get_db)):
    try:
        cart = db.query(Cart).filter(Cart.user_id == user_id).first()
        if not cart:
            cart = Cart(user_id=user_id)
            db.add(cart)
            db.commit()
            db.refresh(cart)
        return cart
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add Item to Cart
@app.post("/{user_id}/add", response_model=schemas.CartItemResponse)
def add_to_cart(user_id: int, item: schemas.CartItemCreate, db: Session = Depends(get_db)):
    try:
        cart = db.query(Cart).filter(Cart.user_id == user_id).first()
        if not cart:
            cart = Cart(user_id=user_id)
            db.add(cart)
            db.commit()
            db.refresh(cart)

        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        cart_item = db.query(CartItem).filter(
            CartItem.cart_id == cart.id, CartItem.product_id == item.product_id
        ).first()

        if cart_item:
            cart_item.quantity += item.quantity
        else:
            cart_item = CartItem(cart_id=cart.id, product_id=item.product_id, quantity=item.quantity)
            db.add(cart_item)

        db.commit()
        db.refresh(cart_item)
        return cart_item
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update Cart Item Quantity
@app.put("/{user_id}/update/{cart_item_id}", response_model=schemas.CartItemResponse)
def update_cart_item(user_id: int, cart_item_id: int, quantity: int, db: Session = Depends(get_db)):
    try:
        cart_item = db.query(CartItem).filter(CartItem.id == cart_item_id).first()
        if not cart_item:
            raise HTTPException(status_code=404, detail="Cart item not found")

        cart_item.quantity = quantity
        db.commit()
        db.refresh(cart_item)
        return cart_item
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Remove Item from Cart
@app.delete("/{user_id}/remove/{cart_item_id}")
def remove_cart_item(user_id: int, cart_item_id: int, db: Session = Depends(get_db)):
    try:
        cart_item = db.query(CartItem).filter(CartItem.id == cart_item_id).first()
        if not cart_item:
            raise HTTPException(status_code=404, detail="Cart item not found")

        db.delete(cart_item)
        db.commit()
        return {"message": "Cart item removed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users/", response_model=UserInDB)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = get_user_by_username(db, user.username)
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        return create_user(db=db, username=user.username, email=user.email, password=user.password)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}", response_model=UserInDB)
def get_user_endpoint(user_id: int, db: Session = Depends(get_db)):
    try:
        db_user = get_user_by_id(db, user_id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return db_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/users/{user_id}", response_model=UserInDB)
def update_user_endpoint(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    try:
        db_user = update_user(db, user_id=user_id, username=user.username, email=user.email, password=user.password)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return db_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/users/{user_id}", response_model=UserInDB)
def delete_user_endpoint(user_id: int, db: Session = Depends(get_db)):
    try:
        db_user = delete_user(db, user_id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return db_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/checkout/{user_id}", response_model=OrderInDB)
def checkout(user_id: int, cart_id: int, db: Session = Depends(get_db)):
    try:
        order = place_order(db, user_id, cart_id)
        if order is None:
            raise HTTPException(status_code=400, detail="Not enough stock or cart is empty")
        return order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
