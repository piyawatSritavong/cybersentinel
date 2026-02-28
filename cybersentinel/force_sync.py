import os
import sqlalchemy
from sqlalchemy import text
from app.core.config import settings


def check_and_force():
    try:
        db_url = settings.database_url or os.environ.get("DATABASE_URL", "")
        if not db_url:
            print("DATABASE_URL not set. Cannot sync.")
            return

        engine = sqlalchemy.create_engine(db_url)
        with engine.connect() as conn:
            db_name = conn.execute(
                text("SELECT current_database();")).fetchone()[0]
            print(f"Connected to database: {db_name}")

            print("Forcing table creation...")
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id SERIAL PRIMARY KEY,
                    alert_id TEXT UNIQUE,
                    org_id TEXT DEFAULT 'default_org',
                    user_id TEXT DEFAULT 'default_user',
                    raw_log TEXT,
                    source_type TEXT,
                    risk_level TEXT,
                    category TEXT,
                    summary TEXT,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    alert_id TEXT,
                    org_id TEXT DEFAULT 'default_org',
                    verdict TEXT,
                    is_correct BOOLEAN,
                    reason TEXT,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.commit()
            print("Tables synced successfully.")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    check_and_force()
