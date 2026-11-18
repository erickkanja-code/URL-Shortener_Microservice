"""Alembic migration environment.

Alembic runs this file for every command. It points Alembic at the
database (using the same DATABASE_URL as the app) and at the models'
metadata, which `--autogenerate` compares against the database.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

from app.core.config import DATABASE_URL
from app.models import Base

# The Alembic Config object, which gives access to the values in alembic.ini.
config = context.config

# Use the same database URL as the app, read once in app.core.config.
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Set up Python logging from the [loggers] sections of alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The metadata of every model. Importing app.models registers all tables on it.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates the SQL as text instead of connecting to the database,
    so the migration can be reviewed or run by hand.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Connects to the database and applies the migrations directly.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()