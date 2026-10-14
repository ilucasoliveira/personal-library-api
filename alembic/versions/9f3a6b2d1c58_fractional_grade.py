"""grade em quartos de estrela (0.25 a 5)

Revision ID: 9f3a6b2d1c58
Revises: 7c1d9e2a4b60
Create Date: 2026-10-14 17:00:00.000000

- livros.grade: deixa de ser inteiro e passa a aceitar 0.25, 0.5, 0.75 ... 5.
  As notas que já existem (1 a 5) continuam iguais, só mudam de tipo.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "9f3a6b2d1c58"
down_revision: Union[str, Sequence[str], None] = "7c1d9e2a4b60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "livros",
        "grade",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        existing_nullable=True,
        postgresql_using="grade::double precision",
    )


def downgrade() -> None:
    # volta para inteiro arredondando (3.75 vira 4; 0.25 vira 1, o mínimo antigo)
    op.alter_column(
        "livros",
        "grade",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="GREATEST(ROUND(grade), 1)::integer",
    )
