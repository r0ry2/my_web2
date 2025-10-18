"""add user_id to order

Revision ID: f4aa09b0685a
Revises: 5cb34457eac1
Create Date: 2025-10-17 21:50:00.815336

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f4aa09b0685a'
down_revision = '5cb34457eac1'
branch_labels = None
depends_on = None


def upgrade():
    # ✅ نضيف الأعمدة ونسمّي الـ foreign key
    with op.batch_alter_table('order', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))
        batch_op.create_foreign_key(
            'fk_order_user_id',  # ← اسم القيّد (إجباري في SQLite)
            'user',              # ← الجدول المرتبط
            ['user_id'],         # ← العمود المحلي
            ['id']               # ← العمود الهدف
        )


def downgrade():
    # ✅ عكس العملية (نحذف القيّد والحقول)
    with op.batch_alter_table('order', schema=None) as batch_op:
        batch_op.drop_constraint('fk_order_user_id', type_='foreignkey')
        batch_op.drop_column('created_at')
        batch_op.drop_column('user_id')
