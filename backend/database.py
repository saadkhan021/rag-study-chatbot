from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# On Railway, mount a Volume (e.g. at /data) and set DATABASE_URL to
# sqlite:////data/app.db — without a Volume, SQLite lives on the
# container's ephemeral filesystem and resets on every redeploy.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()