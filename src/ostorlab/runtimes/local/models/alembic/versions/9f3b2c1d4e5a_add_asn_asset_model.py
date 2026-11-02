"""Add ASN asset model

Revision ID: 9f3b2c1d4e5a
Revises: c3231845f850
Create Date: 2026-11-02 14:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9f3b2c1d4e5a"
down_revision = "c3231845f850"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "asn_asset",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asn", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(
            ["id"], ["asset.id"], name=op.f("fk_asn_asset_id_asset")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_asn_asset")),
    )


def downgrade() -> None:
    op.drop_table("asn_asset")
