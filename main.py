from fastapi import FastAPI,Depends,status,HTTPException,BackgroundTasks
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash,check_password_hash
import models, database,schemas
from datetime import datetime,timedelta
from auth import get_current_user,create_token
from fastapi.middleware.cors import CORSMiddleware
from services import sales_per_day,profit_per_day,profit_per_product,sales_per_product
import jwt
import os
import time

app = FastAPI()

# secret_key = os.getenv("SECRET_KEY")
# print(secret_key)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



models.Base.metadata.create_all(database.engine)

@app.get('/')
def index():
    return {"message":"MyDuka FASTAPI"}


@app.post('/products',status_code=status.HTTP_201_CREATED)
def add_product(request:schemas.Product,db:Session=Depends(database.get_db)):
    new_product = models.Product(name=request.name,buying_price=request.buying_price,selling_price=request.selling_price,stock_quantity=request.stock_quantity)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return {"message":"product added sucessfully"}


@app.get('/products',status_code=status.HTTP_200_OK)
def fetch_products(user=Depends(get_current_user),db:Session=Depends(database.get_db)):
    products = db.query(models.Product).all()
    return {"products":products}
          

@app.get('/products/{product_id}', status_code=status.HTTP_200_OK)
def fetch_one_product(product_id: int,user=Depends(get_current_user), db: Session = Depends(database.get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.put('/products/{product_id}',status_code=status.HTTP_200_OK)
def update_product(product_id : int,request: schemas.Product,user=Depends(get_current_user),db: Session = Depends(database.get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    product.name = request.name
    product.buying_price = request.buying_price
    product.selling_price = request.selling_price
    product.stock_quantity = request.stock_quantity
    db.commit()
    db.refresh(product)
    return {"message": "Product updated successfully", "product": product}


@app.delete('/products/{product_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, user=Depends(get_current_user),db: Session = Depends(database.get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}


@app.post('/sales',status_code=status.HTTP_201_CREATED)
def make_sale(request:schemas.Sale,user=Depends(get_current_user), db: Session = Depends(database.get_db)):
    product = db.query(models.Product).filter(models.Product.id == request.pid).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    user = db.query(models.User).filter(models.User.id == user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User  not found")
    
    if product.stock_quantity < request.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock available")
    
    new_sale = models.Sale(pid=request.pid, user_id=user.id, quantity=request.quantity)
    product.stock_quantity -= request.quantity

    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)

    db.commit()
    return {"message":"Sale made successfully", "sale_id": new_sale.id}



@app.get("/sales", status_code=status.HTTP_200_OK)
def fetch_sales(user=Depends(get_current_user),db: Session = Depends(database.get_db)):
    sales = db.query(models.Sale).join(models.User).all()
    return {"sales_data":sales}


@app.get("/sales/{id}", status_code=status.HTTP_200_OK)
def fetch_sale(id: int,user=Depends(get_current_user), db: Session = Depends(database.get_db)):
    sale = (
        db.query(models.Sale).join(models.User).join(models.Product).filter(models.Sale.id == id).first()
    )
    if sale:
        return {
            "id": sale.id,
            "pid": sale.pid,
            "user_id": user.id, 
            "product_name": sale.product.name,
            "quantity": sale.quantity
        }
    raise HTTPException(status_code=404, detail="Sale not found")

@app.put("/sales/{id}", status_code=status.HTTP_202_ACCEPTED)
def update_sale(id: int, request: schemas.Sale,user=Depends(get_current_user), db: Session = Depends(database.get_db)):
    
    sale = db.query(models.Sale).filter(models.Sale.id == id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    product = db.query(models.Product).filter(models.Product.id == sale.pid).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    quantity_difference = request.quantity - sale.quantity
    sale.quantity = request.quantity

    product.stock_quantity -= quantity_difference
    db.commit()
    
    return {"message": "Sale updated successfully"}


@app.get("/sales/user/{user_id}", status_code=status.HTTP_200_OK)
def fetch_sales_by_user(user_id: int, db: Session = Depends(database.get_db)):
    sales = db.query(models.Sale).filter(models.Sale.user_id == user_id).join(models.User).all()
    
    if not sales:
        raise HTTPException(status_code=404, detail="No sales found for this user")
    
    return [{
        "id": sale.id,
        "pid": sale.pid,
        "user_id": sale.user_id,
        "first_name": sale.user.first_name,
        "quantity": sale.quantity
    } for sale in sales]

@app.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.User,bg_task:BackgroundTasks, db: Session = Depends(database.get_db)):
    start_time = time.time()
    existing_user = db.query(models.User).filter(models.User.email==user.email).first()
    if existing_user:
        print(existing_user.email)
        raise HTTPException(status_code=400, detail="User already exists,please login")
    hashed_password = generate_password_hash(user.password)
    new_user = models.User(
        first_name=user.first_name,last_name=user.last_name,
        email=user.email,phone_number=user.phone_number,password=hashed_password)
   
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    process_time = time.time() - start_time
    print(f"Prrocess took {process_time}")
    return{"message":"User created successfully"}  

@app.get('/users', status_code=status.HTTP_200_OK)
def get_users(db: Session = Depends(database.get_db)):
    try:
        users = db.query(models.User).all()
        user_list = [
            {
                "user_id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone_number": user.phone_number
            } 
            for user in users
        ]
        return {"users": user_list}
    except Exception as e:  
        raise HTTPException(status_code=500, detail=str(e) or "Error fetching users")

@app.get('/users/{user_id}',status_code=status.HTTP_200_OK)
def fetch_user(user_id:int,db:Session=Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id==user_id).first()
    return user

@app.get('/users/email/{email}', status_code=status.HTTP_200_OK)
def fetch_user_by_email(email: str, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone_number": user.phone_number
    }

@app.put('/users/',status_code=status.HTTP_202_ACCEPTED)
def update_user_info(request:schemas.User,current_user=Depends(get_current_user) ,db:Session =Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id==current_user.id).first()
    print("User",user)
    print(user.email)
    if user is None:
        raise HTTPException(status_code=404,detail="User not found")
    user.first_name = request.first_name
    user.last_name = request.last_name
    user.email = request.email
    user.phone_number = request.phone_number
    user.password = generate_password_hash(request.password)
    try:
        db.commit()
        db.refresh(user)
        return {"message":"updated user info successfully"}
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Error updating user info...{e}")


@app.delete('/users/{user_id}',status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id:int,db:Session=Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id==user_id).first()
    if user is None:
        raise HTTPException(status_code=404,detail='User not found')
    db.delete(user)
    db.commit()
    return {"message":"User deleted successfully"}





@app.post('/login',status_code=status.HTTP_201_CREATED)
def login_user(user:schemas.UserLogin,db:Session=Depends(database.get_db)):
    registered_user = db.query(models.User).filter(models.User.email==user.email).first()
    if registered_user is None:
        raise HTTPException(status_code=404,detail="User does nor exist,please register")
    try:
        if check_password_hash(registered_user.password,user.password):

            token = create_token(data={"user":user.email},expries_delta=timedelta(minutes=30))
            return {"access_token":token}
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Error creating token: {e}")
    
# @app.post("/refresh")
# def refresh_token():


@app.get("/dashboard/sales_per_day")
def sales_day(db: Session = Depends(database.get_db)):
    sales_data = sales_per_day(db)
    return {"sales_per_day":sales_data}

@app.get("/dashboard/profit_per_day")
def profit_day(db:Session=Depends(database.get_db)):
    profit_data = profit_per_day(db)
    return {"Profit_per_day":profit_data}

@app.get("/dashboard/profit_per_product")
def profit_prod(db:Session=Depends(database.get_db)):
    prof_prod = profit_per_product(db)
    return {"profit per product":prof_prod}

@app.get("/dashboard/sales_per_product")
def sales_product(db:Session=Depends(database.get_db)):
    sales_prod =sales_per_product(db)
    return {"sales per product":sales_prod}




 

    




