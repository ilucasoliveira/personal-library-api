"""add users table and book owner

Revision ID: 4b8e2c1f9a73
Revises: dd97d8e19704
Create Date: 2026-10-13 16:00:00.000000

Livros que já existiam ficam com user_id nulo (invisíveis) até alguém rodar:
    poetry run python -m back_end_library.manage create-user --email ... --claim-orphans
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "4b8e2c1f9a73"
down_revision: Union[str, Sequence[str], None] = "dd97d8e19704"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("photo_url", sa.String(length=1000), nullable=True),
        sa.Column("theme", sa.String(length=20), nullable=False, server_default="twilight"),
        sa.Column("accent", sa.String(length=7), nullable=True),
        sa.Column("language", sa.String(length=5), nullable=False, server_default="pt"),
        sa.Column("is_visitor", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.add_column("livros", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index("ix_livros_user_id", "livros", ["user_id"])
    op.create_foreign_key(
        "fk_livros_user_id_users", "livros", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )


def downgrade() -> None:
    op.drop_constraint("fk_livros_user_id_users", "livros", type_="foreignkey")
    op.drop_index("ix_livros_user_id", table_name="livros")
    op.drop_column("livros", "user_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
