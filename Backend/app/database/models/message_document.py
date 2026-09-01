from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.message import MessageModel


class MessageDocumentModel(Base):
    __tablename__ = "message_documents"
    __table_args__ = (
        UniqueConstraint(
            "message_id",
            "position",
            name="uq_message_documents_message_id_position",
        ),
        Index("ix_message_documents_document_id", "document_id"),
    )

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        primary_key=True,
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    message: Mapped[MessageModel] = relationship(
        back_populates="document_links",
    )
