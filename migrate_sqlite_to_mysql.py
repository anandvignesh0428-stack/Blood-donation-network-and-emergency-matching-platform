#!/usr/bin/env python
"""
SQLite to MySQL Migration Script
Migrates data from blood_donation.db (SQLite) to MySQL blood_donation database.
Preserves all IDs and data. Idempotent - safe to run multiple times.
"""
import os
import sys
import sqlite3
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blood_donation.db")
MYSQL_URL = os.getenv("DATABASE_URL")

if not MYSQL_URL:
    print("ERROR: DATABASE_URL not set in environment")
    print("Set DATABASE_URL in .env file or environment variable")
    sys.exit(1)

if MYSQL_URL.startswith("sqlite"):
    print("ERROR: DATABASE_URL is set to SQLite, not MySQL")
    print("Set DATABASE_URL to mysql+pymysql://USERNAME:PASSWORD@localhost:3306/blood_donation")
    sys.exit(1)

if not os.path.exists(SQLITE_DB_PATH):
    print(f"SQLite database not found at {SQLITE_DB_PATH}")
    print("Nothing to migrate.")
    sys.exit(0)


def get_sqlite_data():
    """Extract all data from SQLite database."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    data = {"donors": [], "emergency_requests": []}

    # Donors
    cursor.execute("SELECT * FROM donors")
    data["donors"] = [dict(row) for row in cursor.fetchall()]

    # Emergency Requests
    cursor.execute("SELECT * FROM emergency_requests")
    data["emergency_requests"] = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return data


def migrate():
    """Migrate data from SQLite to MySQL."""
    print("=" * 60)
    print("SQLite to MySQL Migration")
    print("=" * 60)
    print(f"Source: {SQLITE_DB_PATH}")
    print(f"Target: {MYSQL_URL.replace(os.getenv('DATABASE_URL', '').split('@')[0], '***') if '@' in MYSQL_URL else MYSQL_URL}")
    print()

    # Get SQLite data
    data = get_sqlite_data()
    donor_count = len(data["donors"])
    request_count = len(data["emergency_requests"])

    print(f"Found {donor_count} donors and {request_count} emergency requests in SQLite")
    print()

    if donor_count == 0 and request_count == 0:
        print("No data to migrate.")
        return

    # Connect to MySQL
    mysql_engine = create_engine(MYSQL_URL, pool_pre_ping=True, pool_recycle=3600)
    Session = sessionmaker(bind=mysql_engine)
    session = Session()

    try:
        # Migrate donors
        migrated_donors = 0
        skipped_donors = 0
        for donor in data["donors"]:
            # Check if donor with same ID already exists
            existing = session.execute(
                text("SELECT id FROM donors WHERE id = :id"),
                {"id": donor["id"]}
            ).fetchone()

            if existing:
                skipped_donors += 1
                continue

            session.execute(
                text("""
                    INSERT INTO donors (id, name, blood_group, location, phone, available, latitude, longitude)
                    VALUES (:id, :name, :blood_group, :location, :phone, :available, :latitude, :longitude)
                """),
                {
                    "id": donor["id"],
                    "name": donor["name"],
                    "blood_group": donor["blood_group"],
                    "location": donor["location"],
                    "phone": donor["phone"],
                    "available": bool(donor["available"]) if donor["available"] is not None else True,
                    "latitude": donor["latitude"],
                    "longitude": donor["longitude"]
                }
            )
            migrated_donors += 1

        # Migrate emergency requests
        migrated_requests = 0
        skipped_requests = 0
        for req in data["emergency_requests"]:
            existing = session.execute(
                text("SELECT id FROM emergency_requests WHERE id = :id"),
                {"id": req["id"]}
            ).fetchone()

            if existing:
                skipped_requests += 1
                continue

            session.execute(
                text("""
                    INSERT INTO emergency_requests (id, patient_name, blood_group, location, hospital, contact, status, priority, latitude, longitude)
                    VALUES (:id, :patient_name, :blood_group, :location, :hospital, :contact, :status, :priority, :latitude, :longitude)
                """),
                {
                    "id": req["id"],
                    "patient_name": req["patient_name"],
                    "blood_group": req["blood_group"],
                    "location": req["location"],
                    "hospital": req["hospital"],
                    "contact": req["contact"],
                    "status": req["status"] if req["status"] else "Pending",
                    "priority": req["priority"] if req["priority"] else "Normal",
                    "latitude": req["latitude"],
                    "longitude": req["longitude"]
                }
            )
            migrated_requests += 1

        session.commit()
        print("Migration completed successfully!")
        print(f"  Donors: {migrated_donors} migrated, {skipped_donors} skipped (already exist)")
        print(f"  Emergency Requests: {migrated_requests} migrated, {skipped_requests} skipped (already exist)")

        # Verify
        donor_total = session.execute(text("SELECT COUNT(*) FROM donors")).scalar()
        req_total = session.execute(text("SELECT COUNT(*) FROM emergency_requests")).scalar()
        print(f"\nMySQL now contains: {donor_total} donors, {req_total} emergency requests")

    except Exception as e:
        session.rollback()
        print(f"ERROR during migration: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    migrate()