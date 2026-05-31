from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import *

DATABASE_URL = "postgresql://postgres:password@master-db:5432/master_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)