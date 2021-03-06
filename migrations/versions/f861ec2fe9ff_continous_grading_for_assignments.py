"""Continous grading for assignments

Revision ID: f861ec2fe9ff
Revises: 925060c32677
Create Date: 2017-02-24 13:39:32.149251

"""

# revision identifiers, used by Alembic.
revision = 'f861ec2fe9ff'
down_revision = '925060c32677'

from alembic import op
import sqlalchemy as sa
import server


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('assignment', sa.Column('continuous_autograding', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('assignment', 'continuous_autograding')
    # ### end Alembic commands ###
