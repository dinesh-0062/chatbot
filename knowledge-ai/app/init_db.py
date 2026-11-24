
from sqlalchemy import text

from app.core.database import engine, Base
from app.models import Document, WebSource, Conversation, Message
from sqlalchemy import inspect


def initialize_database():

    print("Connecting to PostgreSQL...")

    with engine.connect() as connection:
        result = connection.execute(text("SELECT version()"))
        print("Database connected successfully!")
        print(result.scalar())

    print("Creating database tables...")

    Base.metadata.create_all(bind=engine)

    # create_all does not alter existing tables. Add columns conservatively.
    inspector = inspect(engine)
    if "documents" in inspector.get_table_names() and engine.dialect.name == "postgresql":
        columns = {column["name"] for column in inspector.get_columns("documents")}
        with engine.begin() as connection:
            if "file_size" not in columns:
                connection.execute(text(
                    "ALTER TABLE documents ADD COLUMN file_size BIGINT NOT NULL DEFAULT 0"
                ))
            if "error_message" not in columns:
                connection.execute(text(
                    "ALTER TABLE documents ADD COLUMN error_message TEXT"
                ))
            if "updated_at" not in columns:
                connection.execute(text(
                    "ALTER TABLE documents ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE "
                    "NOT NULL DEFAULT NOW()"
                ))

    print("Tables created successfully!")
    print("Registered tables:", list(Base.metadata.tables.keys()))


if __name__ == "__main__":
    initialize_database()
