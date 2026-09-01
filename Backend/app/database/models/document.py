import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class DocumentModel(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    filename: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    type: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    path: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True,
    )

    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    title: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    person: Mapped[str | None] = mapped_column(String, nullable=True)
    department: Mapped[str | None] = mapped_column(String, nullable=True)
    document_type: Mapped[str | None] = mapped_column(String, nullable=True)

    tags: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    page_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    chunk_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    ocr_language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="fr",
        server_default="fr",
    )
