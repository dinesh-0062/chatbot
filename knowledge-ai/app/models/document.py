
from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    func,
    Text,
    BigInteger
)

from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Document(Base):

    __tablename__ = "documents"

    document_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        index=True
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    stored_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    total_pages: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    total_chunks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="completed"
    )

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
