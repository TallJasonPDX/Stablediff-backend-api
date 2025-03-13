
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, ForeignKey, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
import uuid

from app.config import settings

# Create SQLite engine
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Database models
class DBUser(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    is_active = Column(Boolean, default=True)
    instagram_connected = Column(Boolean, default=False)
    instagram_token = Column(String, nullable=True)
    instagram_id = Column(String, nullable=True, unique=True, index=True)
    follows_required = Column(Boolean, default=False)
    quota_remaining = Column(Integer, default=10)  # Default image quota
    quota_reset_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    images = relationship("DBImage", back_populates="user")

class DBImage(Base):
    __tablename__ = "images"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    filename = Column(String)
    theme = Column(String)
    original_url = Column(String)
    processed_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    user = relationship("DBUser", back_populates="images")

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
