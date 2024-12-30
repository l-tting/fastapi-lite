from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base
# from database import Base

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    buying_price = Column(Integer, nullable=False)
    selling_price = Column(Integer, nullable=False)
    stock_quantity = Column(Integer, nullable=False)
    sales = relationship("Sale", back_populates='product')

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone_number = Column(String, nullable=False)
    password = Column(String,nullable=False)
    sales = relationship("Sale", back_populates='user')

class Sale(Base):
    __tablename__ = 'sales'
    id = Column(Integer, primary_key=True)
    pid = Column(Integer, ForeignKey('products.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())
    product = relationship("Product", back_populates='sales')
    user = relationship("User", back_populates='sales')
    



