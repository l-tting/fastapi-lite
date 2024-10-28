from fastapi import FastAPI,Depends,status,HTTPException
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash,check_password_hash
import models, database,schemas
from datetime import datetime,timedelta
import jwt

app = FastAPI()

models.Base.metadata.create_all(database.engine)

@app.get('/')
def index():
    return {"message":"Hello world"}


@app.post('/products',status_code=status.HTTP_201_CREATED)
def add_product(request:schemas.Product,db:Session=Depends(database.get_db)):
    new_product = models.Product(name=request.name,buying_price=request.buying_price,selling_price=request.selling_price,stock_quantity=request.stock_quantity)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return {"message":"product added sucessfully"}


@app.get('/products',status_code=status.HTTP_200_OK)
def fetch_products(db:Session=Depends(database.get_db)):
    products = db.query(models.Product).all()
    return products
          

@app.get('/products/{product_id}', status_code=status.HTTP_200_OK)
def fetch_one_product(product_id: int, db: Session = Depends(database.get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.put('/products/{product_id}',status_code=status.HTTP_200_OK)
def update_product(product_id : int,request: schemas.Product,db: Session = Depends(database.get_db)):
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
def delete_product(product_id: int, db: Session = Depends(database.get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}


@app.post('/sales/',status_code=status.HTTP_201_CREATED)
def make_sale(request:schemas.Sale, db: Session = Depends(database.get_db)):
    product = db.query(models.Products).filter(models.Products.id == request.pid).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    user = db.query(models.Users).filter(models.Users.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User  not found")
    
    if product.stock_quantity < request.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock available")
    
    new_sale = models.Sale(pid=request.pid, user_id=request.user_id, quantity=request.quantity)
    product.stock_quantity -= request.quantity

    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)

    db.commit()
    return {"message":"Sale made successfully", "sale_id": new_sale.id}



@app.get("/sales", status_code=status.HTTP_200_OK)
def fetch_sales(db: Session = Depends(database.get_db)):
    sales = db.query(models.Sales).join(models.Users).all()
    return [{"id": sale.id, "pid": sale.pid, "user_id": sale.user_id, "first name": sale.users.first_name, "quantity": sale.quantity} for sale in sales]


@app.get("/sales/{id}", status_code=status.HTTP_200_OK)
def fetch_sale(id: int, db: Session = Depends(database.get_db)):
    sale = (
        db.query(models.Sales).join(models.Users).join(models.Products).filter(models.Sales.id == id).first()
    )
    if sale:
        return {
            "id": sale.id,
            "pid": sale.pid,
            "user_id": sale.users.id, 
            "product_name": sale.products.name,
            "quantity": sale.quantity
        }
    raise HTTPException(status_code=404, detail="Sale not found")

@app.put("/sales/{id}", status_code=status.HTTP_202_ACCEPTED)
def update_sale(id: int, request: schemas.Sale, db: Session = Depends(database.get_db)):
    
    sale = db.query(models.Sales).filter(models.Sales.id == id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    product = db.query(models.Products).filter(models.Products.id == sale.pid).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    quantity_difference = request.quantity - sale.quantity
    sale.quantity = request.quantity

    product.stock_quantity -= quantity_difference
    db.commit()
    
    return {"message": "Sale updated successfully"}


@app.get("/sales/user/{user_id}", status_code=status.HTTP_200_OK)
def fetch_sales_by_user(user_id: int, db: Session = Depends(database.get_db)):
    sales = db.query(models.Sale).filter(models.Sales.user_id == user_id).join(models.Users).all()
    
    if not sales:
        raise HTTPException(status_code=404, detail="No sales found for this user")
    
    return [{
        "id": sale.id,
        "pid": sale.pid,
        "user_id": sale.user_id,
        "first_name": sale.users.first_name,
        "quantity": sale.quantity
    } for sale in sales]

@app.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.User, db: Session = Depends(database.get_db)):
    existing_user = db.query(models.User).filter(models.User.email==user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists,please login")
    hashed_password = generate_password_hash(user.password)
    new_user = models.User(
        first_name=user.first_name,last_name=user.last_name,
        email=user.email,phone_number=user.password,password=hashed_password)
   
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return{"message":"User created successfully"}  

@app.get('/users',status_code=status.HTTP_200_OK)
def get_users(db:Session =Depends(database.get_db())):
    users = db.query(models.User).all()
    user = [{"user_id":user.id,"first_name":user.first_name,
             "last_name":user.last_name,"email":user.email,"phone_number":user.phone_number} for user in users]
    return {"users":user}

@app.get('/users/{user_id}')
def fetch_user(user_id:int,db:Session=Depends(database.get_db())):
    user = db.query(models.User).filter(models.User.id==user_id).first()
    return user

@app.put('/users/{user_id}',status_code=status.HTTP_202_ACCEPTED)
def update_user_info(request:schemas.User ,db:Session =Depends(database.get_db())):


@app.post('/login',status_code=status.HTTP_201_CREATED)
def login_user(user:schemas.User,db:Session=Depends(database.get_db())):
    registered_user = db.query(models.User).filter(models.User.email==user.email).first()
    if not registered_user:
        raise HTTPException(status_code=404,detail="User does nor exist,please register")
    try:
        if check_password_hash(registered_user.password,user.password):
            access_token = jwt.encode({"sub":registered_user.email,"exp":datetime.utcnow()+timedelta(minutes=10)},algorithm='HS256')
            return {"access_token":access_token}
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Error creating token: {e}")

    






