from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base

# Usando SQLite local. check_same_thread=False é necessário para FastAPI + SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./central_automacao.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()