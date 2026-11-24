
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import DATABASE_URL


engine_options = {
    "pool_pre_ping": True,
}

if DATABASE_URL.startswith("postgresql"):
    engine_options.update({
        "pool_size": 5,
        "max_overflow": 5,
        "pool_recycle": 1800,
        "connect_args": {"sslmode": "require"},
    })

engine = create_engine(DATABASE_URL, **engine_options)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


class Base(DeclarativeBase):
    pass


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
