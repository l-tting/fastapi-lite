from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from models import Sale,Product


def sales_per_day(db:Session):
    sales_day_day= db.query(func.date(Sale.created_at).label("dates"),
                    func.sum(Sale.quantity * Product.selling_price).label("sales")).join(Product).group_by('dates').all()
    sales_data =[{"date":str(dates),"sales":sales} for dates,sales in sales_day_day]
   
    return sales_data

def sales_per_product(db:Session):
    sales_per_prod = db.query((Product.name).label("product"),
                        func.sum(Product.selling_price * Sale.quantity).label("sales")).join(Sale).group_by("product").all()
    sales_prod =[{"product":product,"sale":sale} for product,sale in sales_per_prod]
    return sales_prod

def profit_per_day(db:Session):
    profit_day = db.query(func.date(Sale.created_at).label("dates"),
                          func.sum(Sale.quantity*(Product.selling_price -Product.buying_price)).label("profit")).join(Product).group_by('dates').all()
    
    profit_data =[{"date":dates,"profit":profit} for dates,profit in profit_day]
    return profit_data

def profit_per_product(db:Session):
    profit_product = db.query((Product.name).label("product"),
                    func.sum(Sale.quantity *(Product.selling_price-Product.buying_price)).label("Profit")).join(Sale).group_by("product").all()
    
    profit_p =[{"product":product,"profit":profit} for product,profit in profit_product]
    return profit_p
