"""create ai products table

Revision ID: 20260703_0001
Revises:
Create Date: 2026-07-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260703_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_products",
        sa.Column("product_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=True),
        sa.Column("brand", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("specs", postgresql.JSONB(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("source", sa.Text(), nullable=True, server_default="catalog-service"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_synced_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_ai_products_category", "ai_products", ["category"])
    op.create_index("idx_ai_products_brand", "ai_products", ["brand"])
    op.create_index("idx_ai_products_is_active", "ai_products", ["is_active"])


def downgrade() -> None:
    op.drop_index("idx_ai_products_is_active", table_name="ai_products")
    op.drop_index("idx_ai_products_brand", table_name="ai_products")
    op.drop_index("idx_ai_products_category", table_name="ai_products")
    op.drop_table("ai_products")

