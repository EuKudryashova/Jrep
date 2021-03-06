"""test1

Revision ID: 85fc306e71
Revises: 44140f691e1a
Create Date: 2013-09-12 18:22:09.178061

"""

# revision identifiers, used by Alembic.
revision = '85fc306e71'
down_revision = '44140f691e1a'

from alembic import op
import sqlalchemy as sa
from DB import Enum


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('vms',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=True),
    sa.Column('state', Enum(length=50), nullable=True),
    sa.Column('os_id', sa.Integer(), nullable=True),
    sa.Column('br_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['br_id'], ['bridges.id'], ),
    sa.ForeignKeyConstraint(['os_id'], ['os.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('vms')
    ### end Alembic commands ###
