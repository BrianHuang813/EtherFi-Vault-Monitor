from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base
import config  # Import config instead of dotenv

if not config.DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in config.py")

db_url = config.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    db_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()