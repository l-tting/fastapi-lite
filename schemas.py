from pydantic import BaseModel

class Product(BaseModel):
    name:str
    buying_price:int
    selling_price:int
    stock_quantity:int

class Sale(BaseModel):
    pid: int
    user_id:int
    quantity: int

class User(BaseModel):
    first_name:str
    last_name:str
    email:str
    phone_number:str
    password:str

