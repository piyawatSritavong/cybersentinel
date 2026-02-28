import os
import logging
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.memory import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_database():
    """Force create/migrate tables to the Replit Managed PostgreSQL database."""
    try:
        db_url = settings.database_url or os.environ.get("DATABASE_URL", "")
        if not db_url:
            logger.error("DATABASE_URL not set. Cannot migrate.")
            return

        engine = create_engine(db_url)

        logger.info("Connecting to Replit Managed PostgreSQL...")

        logger.info("Creating tables from models...")
        Base.metadata.create_all(engine)

        logger.info("Verifying columns and patching...")
        with engine.connect() as conn:
            alter_queries = [
                "ALTER TABLE incidents ADD COLUMN IF NOT EXISTS risk_level TEXT",
                "ALTER TABLE incidents ADD COLUMN IF NOT EXISTS category TEXT",
                "ALTER TABLE incidents ADD COLUMN IF NOT EXISTS summary TEXT",
                "ALTER TABLE incidents ADD COLUMN IF NOT EXISTS source_type TEXT"
            ]
            for query in alter_queries:
                conn.execute(text(query))
                conn.commit()

        logger.info("Database migration completed successfully.")

    except Exception as e:
        logger.error(f"Migration failed: {e}")


if __name__ == "__main__":
    migrate_database()
