import os
from alembic import context
from sqlalchemy import engine_from_config, pool
from database.mocked_models import Base

from logging.config import fileConfig
from dotenv import load_dotenv

load_dotenv()

# Alembic Config object
config = context.config
fileConfig(config.config_file_name)

# Inject .env var into sqlalchemy.url
mocked_url = os.getenv("MOCKED_DB_URL")
if mocked_url:
    config.set_main_option("sqlalchemy.url", mocked_url)

target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
