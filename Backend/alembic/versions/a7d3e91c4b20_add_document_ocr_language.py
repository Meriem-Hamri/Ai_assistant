"""add document OCR language

Revision ID: a7d3e91c4b20
Revises: f6a4b2d8c901
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7d3e91c4b20"
down_revision: Union[str, Sequence[str], None] = "f6a4b2d8c901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "ocr_language",
            sa.String(length=10),
            nullable=False,
            server_default="fr",
        ),
    )


def downgrade() -> None:
    op.drop_column("documents", "ocr_language")
