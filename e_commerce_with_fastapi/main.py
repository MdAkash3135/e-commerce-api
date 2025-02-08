from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
import schemas
from database import get_db
from fastapi.security import OAuth2PasswordBearer
from auth import create_access_token, verify_access_token
from crud import UserCRUD, ProductCRUD, CategoryCRUD, CartCRUD, OrderCRUD
from typing import List

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# ----------------------
# AUTH & USER ROUTES
# ----------------------

@app.post("/register", response_model=schemas.UserCreate)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        existing_user = UserCRUD.get_user_by_username(db, user.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")
        
        existing_email = UserCRUD.get_user_by_email(db, user.email)
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already taken")
        
        return UserCRUD.create_user(db, user.username, user.email, user.password)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    try:
        db_user = UserCRUD.get_user_by_username(db, user.username)
        if db_user is None or not db_user.verify_password(user.password):
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
        db_user = UserCRUD.get_user_by_id(db, user_id)
        if db_user is None:
            raise HTTPException(status_code=401, detail="User not found")

        return {"message": f"Hello {db_user.username}, this is a protected route."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}", response_model=schemas.UserInDB)
def get_user_endpoint(user_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    db_user = UserCRUD.get_user_by_id(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.put("/users/{user_id}", response_model=schemas.UserInDB)
def update_user_endpoint(user_id: int, user: schemas.UserUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    db_user = UserCRUD.update_user(db, user_id, username=user.username, email=user.email, password=user.password)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.delete("/users/{user_id}")
def delete_user_endpoint(user_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    db_user = UserCRUD.delete_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


# ----------------------
# CATEGORY ROUTES
# ----------------------

@app.post("/categories/", response_model=schemas.CategoryResponse)
def create_category(category: schemas.CategoryCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return CategoryCRUD.create_category(db, category)


@app.get("/categories/", response_model=List[schemas.CategoryResponse])
def get_categories(token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    return CategoryCRUD.get_categories(db)


@app.put("/categories/{category_id}", response_model=schemas.CategoryResponse)
def update_category(category_id: int, category: schemas.CategoryCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    updated_category = CategoryCRUD.update_category(db, category_id, category)
    if not updated_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated_category


@app.delete("/categories/{category_id}")
def delete_category(category_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    deleted = CategoryCRUD.delete_category(db, category_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}


# ----------------------
# PRODUCT ROUTES
# ----------------------

@app.post("/products/", response_model=schemas.ProductResponse)
def create_product(product: schemas.ProductCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return ProductCRUD.create_product(db, product)


@app.get("/products/", response_model=List[schemas.ProductResponse])
def get_products(
    category_id: int = None, 
    min_price: float = None, 
    max_price: float = None, 
    in_stock: bool = None, 
    skip: int = 0, 
    limit: int = 10, 
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    return ProductCRUD.get_products(db, category_id, min_price, max_price, in_stock, skip, limit)


@app.put("/products/{product_id}", response_model=schemas.ProductResponse)
def update_product(product_id: int, product: schemas.ProductCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    updated_product = ProductCRUD.update_product(db, product_id, product)
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated_product


@app.delete("/products/{product_id}")
def delete_product(product_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        deleted = ProductCRUD.delete_product(db, product_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Product not found")
        return {"message": "Product deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------
# CART ROUTES
# ----------------------

@app.get("/{user_id}/cart", response_model=schemas.CartResponse)
def get_cart(user_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return CartCRUD.get_cart(db, user_id)


@app.post("/{user_id}/cart/add", response_model=schemas.CartItemResponse)
def add_to_cart(user_id: int, item: schemas.CartItemCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return CartCRUD.add_to_cart(db, user_id, item)


@app.put("/{user_id}/cart/update/{cart_item_id}", response_model=schemas.CartItemResponse)
def update_cart_item(user_id: int, cart_item_id: int, quantity: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    cart_item = CartCRUD.update_cart_item(db, cart_item_id, quantity)
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return cart_item


@app.delete("/{user_id}/cart/remove/{cart_item_id}")
def remove_cart_item(user_id: int, cart_item_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    removed = CartCRUD.remove_cart_item(db, cart_item_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return {"message": "Cart item removed"}


# ----------------------
# ORDER ROUTES
# ----------------------

@app.post("/checkout/{user_id}", response_model=schemas.OrderInDB)
def checkout(user_id: int, cart_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        order = OrderCRUD.place_order(db, user_id, cart_id)
        if order is None:
            raise HTTPException(status_code=400, detail="Not enough stock or cart is empty")
        return order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
