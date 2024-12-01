from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLALCHEMY_DATABASE_URL = 'postgresql://fastapi_user:Pass123@localhost/fastapi'
SQLALCHEMY_DATABASE_URL = "sqlite:///./mydatabase.db" 
engine = create_engine(SQLALCHEMY_DATABASE_URL)

sessionlocal = sessionmaker(bind=engine)

Base = declarative_base()

def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()