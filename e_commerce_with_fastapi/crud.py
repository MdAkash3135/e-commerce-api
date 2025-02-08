from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
from passlib.context import CryptContext
import models, schemas
 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
 
 
class UserCRUD:
    @staticmethod
    def create_user(db: Session, username: str, email: str, password: str):
        hashed_password = pwd_context.hash(password)
        db_user = models.User(username=username, email=email, password=hashed_password)
        db.add(db_user)
        try:
            db.commit()
            db.refresh(db_user)
            return db_user
        except IntegrityError:
            db.rollback()
            return None  
 
    @staticmethod
    def get_user_by_id(db: Session, user_id: int):
        return db.query(models.User).filter(models.User.id == user_id).first()
 
    @staticmethod
    def get_user_by_username(db: Session, username: str):
        return db.query(models.User).filter(models.User.username == username).first()
 
    @staticmethod
    def get_user_by_email(db: Session, email: str):
        return db.query(models.User).filter(models.User.email == email).first()
 
    @staticmethod
    def update_user(db: Session, user_id: int, username: str = None, email: str = None, password: str = None):
        db_user = db.query(models.User).filter(models.User.id == user_id).first()
        if db_user:
            if username:
                db_user.username = username
            if email:
                db_user.email = email
            if password:
                db_user.password = pwd_context.hash(password)  
            db.commit()
            db.refresh(db_user)
            return db_user
        return None
 
    @staticmethod
    def delete_user(db: Session, user_id: int):
        db_user = db.query(models.User).filter(models.User.id == user_id).first()
        if db_user:
            db.delete(db_user)
            db.commit()
            return db_user
        return None
 
 
class CategoryCRUD:
    @staticmethod
    def create_category(db: Session, category: schemas.CategoryCreate):
        new_category = models.Category(name=category.name)
        db.add(new_category)
        db.commit()
        db.refresh(new_category)
        return new_category
 
    @staticmethod
    def get_categories(db: Session):
        return db.query(models.Category).all()
 
    @staticmethod
    def update_category(db: Session, category_id: int, category_update: schemas.CategoryCreate):
        category = db.query(models.Category).filter(models.Category.id == category_id).first()
        if category:
            category.name = category_update.name
            db.commit()
            db.refresh(category)
            return category
        return None
 
    @staticmethod
    def delete_category(db: Session, category_id: int):
        category = db.query(models.Category).filter(models.Category.id == category_id).first()
        if category:
            db.delete(category)
            db.commit()
            return True
        return False
 
 
class ProductCRUD:
    @staticmethod
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
 
    @staticmethod
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
 
    @staticmethod
    def update_product(db: Session, product_id: int, product_update: schemas.ProductCreate):
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if product:
            product.name = product_update.name
            product.price = product_update.price
            product.stock = product_update.stock
            product.category_id = product_update.category_id
            db.commit()
            db.refresh(product)
            return product
        return None
 
    @staticmethod
    def delete_product(db: Session, product_id: int):
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if product:
            db.delete(product)
            db.commit()
            return True
        return False
 
 
class CartCRUD:
    @staticmethod
    def get_cart(db: Session, user_id: int):
        cart = db.query(models.Cart).filter(models.Cart.user_id == user_id).first()
        if not cart:
            cart = models.Cart(user_id=user_id)
            db.add(cart)
            db.commit()
            db.refresh(cart)
        return cart
 
    @staticmethod
    def add_to_cart(db: Session, user_id: int, item: schemas.CartItemCreate):
        cart = db.query(models.Cart).filter(models.Cart.user_id == user_id).first()
        if not cart:
            cart = models.Cart(user_id=user_id)
            db.add(cart)
            db.commit()
            db.refresh(cart)
 
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            raise ValueError("Product not found")
 
        cart_item = db.query(models.CartItem).filter(
            models.CartItem.cart_id == cart.id, models.CartItem.product_id == item.product_id
        ).first()
 
        if cart_item:
            cart_item.quantity += item.quantity
        else:
            cart_item = models.CartItem(cart_id=cart.id, product_id=item.product_id, quantity=item.quantity)
            db.add(cart_item)
 
        db.commit()
        db.refresh(cart_item)
        return cart_item
 
    @staticmethod
    def update_cart_item(db: Session, cart_item_id: int, quantity: int):
        cart_item = db.query(models.CartItem).filter(models.CartItem.id == cart_item_id).first()
        if not cart_item:
            return None
 
        cart_item.quantity = quantity
        db.commit()
        db.refresh(cart_item)
        return cart_item
 
    @staticmethod
    def remove_cart_item(db: Session, cart_item_id: int):
        cart_item = db.query(models.CartItem).filter(models.CartItem.id == cart_item_id).first()
        if cart_item:
            db.delete(cart_item)
            db.commit()
            return True
        return False
 
 
class OrderCRUD:
    @staticmethod
    def place_order(db: Session, user_id: int, cart_id: int):
        cart_items = db.query(models.CartItem).filter(models.CartItem.cart_id == cart_id).all()
        if not cart_items:
            return None  
 
        total_price = Decimal(0)
        for item in cart_items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            if product is None or product.stock < item.quantity:
                return None  
            total_price += product.price * item.quantity
 
        order = models.Order(user_id=user_id, total_price=total_price)
        db.add(order)
        db.commit()
        db.refresh(order)
 
        for item in cart_items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            order_item = models.OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=product.price
            )
            db.add(order_item)
            product.stock -= item.quantity
 
        db.commit()
        db.query(models.CartItem).filter(models.CartItem.cart_id == cart_id).delete()
        db.commit()
        return order
 
