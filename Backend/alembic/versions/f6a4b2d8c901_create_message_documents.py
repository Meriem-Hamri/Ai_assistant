"""create message documents

Revision ID: f6a4b2d8c901
Revises: d2f7c9a81e4b
Create Date: 2026-09-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f6a4b2d8c901"
down_revision: Union[str, Sequence[str], None] = "d2f7c9a81e4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create immutable document snapshots for messages."""
    op.create_table(
        "message_documents",
        sa.Column(
            "message_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["messages.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("message_id", "document_id"),
        sa.UniqueConstraint(
            "message_id",
            "position",
            name="uq_message_documents_message_id_position",
        ),
    )
    op.create_index(
        "ix_message_documents_document_id",
        "message_documents",
        ["document_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop immutable document snapshots for messages."""
    op.drop_index(
        "ix_message_documents_document_id",
        table_name="message_documents",
    )
    op.drop_table("message_documents")
