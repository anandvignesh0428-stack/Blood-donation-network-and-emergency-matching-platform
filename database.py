import os
import sqlite3

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "blood_donation.db")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

engine_kwargs = {}
if DATABASE_URL.startswith("mysql"):
    engine_kwargs = {"pool_pre_ping": True, "pool_recycle": 3600}
else:
    engine_kwargs = {"connect_args": {"check_same_thread": False}}

engine = create_engine(
    DATABASE_URL,
    **engine_kwargs
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_safe_migration():
    """Idempotent migration: only add missing columns, never drop or delete data.
    Only runs for SQLite databases."""
    if DATABASE_URL.startswith("mysql"):
        return
    if not os.path.exists(DB_PATH):
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # donors table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='donors'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(donors)")
            donor_cols = [row[1] for row in cursor.fetchall()]
            if "latitude" not in donor_cols:
                cursor.execute("ALTER TABLE donors ADD COLUMN latitude REAL")
            if "longitude" not in donor_cols:
                cursor.execute("ALTER TABLE donors ADD COLUMN longitude REAL")
            if "available" not in donor_cols:
                cursor.execute("ALTER TABLE donors ADD COLUMN available BOOLEAN DEFAULT 1")
            if "name" not in donor_cols:
                cursor.execute("ALTER TABLE donors ADD COLUMN name TEXT")
            if "blood_group" not in donor_cols:
                cursor.execute("ALTER TABLE donors ADD COLUMN blood_group TEXT")
            if "location" not in donor_cols:
                cursor.execute("ALTER TABLE donors ADD COLUMN location TEXT")
            if "phone" not in donor_cols:
                cursor.execute("ALTER TABLE donors ADD COLUMN phone TEXT")

        # emergency_requests table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emergency_requests'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(emergency_requests)")
            emg_cols = [row[1] for row in cursor.fetchall()]
            if "priority" not in emg_cols:
                cursor.execute("ALTER TABLE emergency_requests ADD COLUMN priority TEXT DEFAULT 'Normal'")
            if "latitude" not in emg_cols:
                cursor.execute("ALTER TABLE emergency_requests ADD COLUMN latitude REAL")
            if "longitude" not in emg_cols:
                cursor.execute("ALTER TABLE emergency_requests ADD COLUMN longitude REAL")
            if "status" not in emg_cols:
                cursor.execute("ALTER TABLE emergency_requests ADD COLUMN status TEXT DEFAULT 'Pending'")
            if "patient_name" not in emg_cols:
                cursor.execute("ALTER TABLE emergency_requests ADD COLUMN patient_name TEXT")
            if "blood_group" not in emg_cols:
                cursor.execute("ALTER TABLE emergency_requests ADD COLUMN blood_group TEXT")
            if "location" not in emg_cols:
                cursor.execute("ALTER TABLE emergency_requests ADD COLUMN location TEXT")
            if "hospital" not in emg_cols:
                cursor.execute("ALTER TABLE emergency_requests ADD COLUMN hospital TEXT")
            if "contact" not in emg_cols:
                cursor.execute("ALTER TABLE emergency_requests ADD COLUMN contact TEXT")

        conn.commit()
        conn.close()
    except Exception:
        # Never crash app startup due to migration
        try:
            conn.close()
        except Exception:
            pass