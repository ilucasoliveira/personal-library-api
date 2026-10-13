"""token_version on users and only valid reading statuses

Revision ID: 7c1d9e2a4b60
Revises: 4b8e2c1f9a73
Create Date: 2026-10-13 19:30:00.000000

- users.token_version: sobe a cada troca de senha; tokens com versão antiga deixam de valer.
- livros.reading_status: a API passa a aceitar só toRead, reading e read; qualquer valor
  diferente que já esteja no banco vira toRead, para não quebrar as respostas.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "7c1d9e2a4b60"
down_revision: Union[str, Sequence[str], None] = "4b8e2c1f9a73"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))
    op.execute(
        "UPDATE livros SET reading_status = 'toRead' "
        "WHERE reading_status IS NULL OR reading_status NOT IN ('toRead', 'reading', 'read')"
    )


def downgrade() -> None:
    op.drop_column("users", "token_version")
