from sqlalchemy import create_engine, Column, String, Boolean, DateTime, ForeignKey, Float, Integer, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import OperationalError, DBAPIError
import datetime
import uuid
import time

from app.config import settings

def get_engine(url, max_retries=3):
    engine = create_engine(url)
    
    @event.listens_for(engine, 'handle_error')
    def handle_error(context):
        conn_rec = context.connection_invalidated and None or context.connection.connection
        if (isinstance(context.original_exception, (OperationalError, DBAPIError)) and
            "SSL connection has been closed unexpectedly" in str(context.original_exception)):
            for attempt in range(max_retries):
                try:
                    if conn_rec:
                        conn_rec.close()
                    if context.connection:
                        context.connection.close()
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    return  # Connection will be retried automatically
                except Exception:
                    if attempt == max_retries - 1:
                        raise
    
    return engine

# Create PostgreSQL engine with retry handling
engine = get_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Database models
class DBUser(Base):
    __tablename__ = "users"

    id = Column(String,
                primary_key=True,
                index=True,
                default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # Admin flag for unlimited quota
    facebook_connected = Column(Boolean, default=False)
    facebook_token = Column(String, nullable=True)
    facebook_id = Column(String, nullable=True, unique=True, index=True)
    follows_required = Column(Boolean, default=False)
    quota_remaining = Column(Integer, default=10)  # Default image quota
    quota_reset_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    images = relationship("DBImage", back_populates="user")
    runpod_requests = relationship("DBRunPodRequest", back_populates="user")


class DBRunPodRequest(Base):
    __tablename__ = "runpod_requests"

    id = Column(String,
                primary_key=True,
                index=True,
                default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    anonymous_user_id = Column(String, nullable=True, index=True)
    workflow_id = Column(String)
    status = Column(
        String,
        default="pending")  # pending, submitted, processing, completed, failed
    runpod_job_id = Column(String, nullable=True)
    input_image_url = Column(String)
    output_image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("DBUser", back_populates="runpod_requests")


class DBImage(Base):
    __tablename__ = "images"

    id = Column(String,
                primary_key=True,
                index=True,
                default=lambda: str(uuid.uuid4()))
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
