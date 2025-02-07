from sqlalchemy.orm import Session
import models, schemas
from sqlalchemy.orm import Session
from models import *
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
from sqlalchemy import func

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create user (for registration)
def create_user(db: Session, username: str, email: str, password: str):
    hashed_password = pwd_context.hash(password)  # Hash the password before storing
    db_user = User(username=username, email=email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# User login (for authentication)
def authenticate_user(db: Session, username: str, password: str):
    db_user = db.query(User).filter(User.username == username).first()
    if db_user is None or not db_user.verify_password(password):
        return None
    return db_user


def create_category(db: Session, category: schemas.CategoryCreate):
    new_category = models.Category(name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

# Get all categories
def get_categories(db: Session):
    return db.query(models.Category).all()

# Create a new product
def create_product(db: Session, product: schemas.ProductCreate):
    new_product = models.Product(
        name=product.name,
        price=product.price,
        stock=product.stock,
        category_id=product.category_id
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

# Get all products with filtering and pagination
def get_products(db: Session, category_id: int = None, min_price: float = None, max_price: float = None, in_stock: bool = None, skip: int = 0, limit: int = 10):
    query = db.query(models.Product)
    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    
    if min_price:
        query = query.filter(models.Product.price >= min_price)
    
    if max_price:
        query = query.filter(models.Product.price <= max_price)
    
    if in_stock is not None:
        query = query.filter(models.Product.stock > 0 if in_stock else models.Product.stock == 0)

    return query.offset(skip).limit(limit).all()


# def create_user(db: Session, username: str, email: str, password: str):
#     hashed_password = pwd_context.hash(password)  # Hash the password before storing
#     db_user = User(username=username, email=email, password=hashed_password)  # Don't forget to hash the password
#     db.add(db_user)
#     try:
#         db.commit()
#         db.refresh(db_user)
#     except IntegrityError:
#         db.rollback()
#         return None  # Or you can return a custom error message
#     return db_user

# Get User by ID
def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

# Get User by Username
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

# Get User by Email
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# Update User (e.g., update password or email)
def update_user(db: Session, user_id: int, username: str = None, email: str = None, password: str = None):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        if username:
            db_user.username = username
        if email:
            db_user.email = email
        if password:
            db_user.password = password  # Hash password before saving in a real app
        db.commit()
        db.refresh(db_user)
        return db_user
    return None

# Delete User
def delete_user(db: Session, user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return db_user
    return None

def place_order(db: Session, user_id: int, cart_id: int):
    # Step 1: Get the cart items
    cart_items = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()
    if not cart_items:
        return None  # Cart is empty
    
    total_price = Decimal(0)  # Initialize total price
    
    # Step 2: Check if there is enough stock for all items and calculate total price
    for item in cart_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product is None or product.stock < item.quantity:
            return None  # Not enough stock for one or more products
        total_price += product.price * item.quantity

    # Step 3: Create an Order
    order = Order(user_id=user_id, total_price=total_price)
    db.add(order)
    db.commit()
    db.refresh(order)

    # Step 4: Add OrderItems and reduce stock
    for item in cart_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        
        # Add item to the order
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=product.price
        )
        db.add(order_item)
        
        # Reduce stock of the product
        product.stock -= item.quantity

    # Step 5: Commit and return order
    db.commit()

    # Clear the cart (since items are now ordered)
    db.query(CartItem).filter(CartItem.cart_id == cart_id).delete()
    db.commit()

    return order
