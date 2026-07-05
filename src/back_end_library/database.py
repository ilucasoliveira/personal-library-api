import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DATABASE = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE, poolclass=NullPool)

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    yield db
    db.close()