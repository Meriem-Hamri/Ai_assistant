"""align document columns with application

Revision ID: b4e92f1a6c3d
Revises: 70b781bf1560
Create Date: 2026-08-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b4e92f1a6c3d"
down_revision: Union[str, Sequence[str], None] = "70b781bf1560"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Align database column names with the application contract."""
    op.alter_column("documents", "original_name", new_column_name="filename")
    op.alter_column("documents", "extension", new_column_name="type")
    op.alter_column("documents", "file_size", new_column_name="size")
    op.alter_column("documents", "stored_name", new_column_name="path")

    op.execute(
        sa.text(
            """
            UPDATE documents
            SET type = substring(type from 2)
            WHERE type LIKE '.%'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE documents
            SET path = 'documents/' || path
            WHERE position('/' in path) = 0
              AND position(chr(92) in path) = 0
            """
        )
    )


def downgrade() -> None:
    """Restore the original database column names."""
    op.execute(
        sa.text(
            """
            UPDATE documents
            SET path = substring(path from length('documents/') + 1)
            WHERE path LIKE 'documents/%'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE documents
            SET type = '.' || type
            WHERE type NOT LIKE '.%'
            """
        )
    )

    op.alter_column("documents", "path", new_column_name="stored_name")
    op.alter_column("documents", "size", new_column_name="file_size")
    op.alter_column("documents", "type", new_column_name="extension")
    op.alter_column("documents", "filename", new_column_name="original_name")
