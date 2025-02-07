from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
from passlib.context import CryptContext


Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    carts = relationship("Cart", back_populates="user")
    orders = relationship("Order", back_populates="user")

     # Method to hash password
    def set_password(self, password: str):
        self.password = pwd_context.hash(password)

    # Method to check if the provided password is correct
    def verify_password(self, password: str):
        return pwd_context.verify(password, self.password)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    # One-to-many relationship (A category can have many products)
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Numeric, nullable=False)
    stock = Column(Integer, nullable=False)
    
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    
    # Relationship with Category
    category = relationship("Category", back_populates="products")
class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Added foreign key to User
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

    user = relationship("User", back_populates="carts")  # Link back to the User model

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"))
    product_id = Column(Integer, ForeignKey("products.id"))  # Linking to products
    quantity = Column(Integer, default=1)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")  # Linking to Product Model

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_price = Column(Numeric, nullable=False)
    status = Column(String, default="Pending")  # Order status (e.g., Pending, Completed, Canceled)
    created_at = Column(String, default=datetime.utcnow().isoformat())

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric, nullable=False)  # The price at the time of purchase

    order = relationship("Order", back_populates="items")
    product = relationship("Product")