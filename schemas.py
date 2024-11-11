from pydantic import BaseModel

class Product(BaseModel):
    name:str
    buying_price:int
    selling_price:int
    stock_quantity:int

class Sale(BaseModel):
    pid: int
    quantity: int

class User(BaseModel):
    first_name:str
    last_name:str
    email:str
    phone_number:str
    password:str

class UserLogin(BaseModel):
    email:str
    password:str

