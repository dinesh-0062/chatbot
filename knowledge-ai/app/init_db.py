
from sqlalchemy import text

from app.core.database import engine, Base
from app.models import Document


def initialize_database():

    print("Connecting to PostgreSQL...")

    with engine.connect() as connection:
        result = connection.execute(text("SELECT version()"))
        print("Database connected successfully!")
        print(result.scalar())

    print("Creating database tables...")

    Base.metadata.create_all(bind=engine)

    print("Tables created successfully!")
    print("Registered tables:", list(Base.metadata.tables.keys()))


if __name__ == "__main__":
    initialize_database()
