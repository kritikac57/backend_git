# backend/alembic/env.py (continued)
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import Base from models for Alembic to detect
from app.database import Base
from app.models.models import NGO, Donation

# This is the Alembic Config object
config = context.config

# Override the SQLAlchemy URL with environment variable if present
sqlalchemy_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/donation_app")
config.set_main_option("sqlalchemy.url", sqlalchemy_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

# backend/alembic.ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = postgresql://postgres:postgres@db:5432/donation_app

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S

# backend/alembic/versions/initial_migration.py
"""Initial migration

Revision ID: initial_migration
Create Date: 2024-04-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2 as ga

# revision identifiers
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create PostGIS extension if not exists
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    
    # Create NGOs table
    op.create_table(
        'ngos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('location', ga.Geometry('POINT', srid=4326), nullable=False),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('is_available', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on NGO location for spatial queries
    op.create_index('idx_ngo_location', 'ngos', ['location'], unique=False, postgresql_using='gist')
    
    # Create donations table
    op.create_table(
        'donations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('donor_name', sa.String(), nullable=False),
        sa.Column('donor_location', ga.Geometry('POINT', srid=4326), nullable=False),
        sa.Column('donor_address', sa.String(), nullable=True),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('status', sa.String(), server_default=sa.text("'pending'")),
        sa.Column('ngo_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['ngo_id'], ['ngos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on donation location for spatial queries
    op.create_index('idx_donation_location', 'donations', ['donor_location'], unique=False, postgresql_using='gist')

def downgrade():
    op.drop_table('donations')
    op.drop_table('ngos')
    op.execute('DROP EXTENSION IF EXISTS postgis')