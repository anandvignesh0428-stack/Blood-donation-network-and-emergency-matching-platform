import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blood_donation.db")

def migrate():
    if not os.path.exists(DB_PATH):
        print("Database not found. Tables will be created on first run.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(donors)")
    donor_cols = [row[1] for row in cursor.fetchall()]

    if "latitude" not in donor_cols:
        cursor.execute("ALTER TABLE donors ADD COLUMN latitude REAL")
        print("Added latitude to donors table")

    if "longitude" not in donor_cols:
        cursor.execute("ALTER TABLE donors ADD COLUMN longitude REAL")
        print("Added longitude to donors table")

    cursor.execute("PRAGMA table_info(emergency_requests)")
    emg_cols = [row[1] for row in cursor.fetchall()]

    if "priority" not in emg_cols:
        cursor.execute("ALTER TABLE emergency_requests ADD COLUMN priority TEXT DEFAULT 'Normal'")
        print("Added priority to emergency_requests table")

    if "latitude" not in emg_cols:
        cursor.execute("ALTER TABLE emergency_requests ADD COLUMN latitude REAL")
        print("Added latitude to emergency_requests table")

    if "longitude" not in emg_cols:
        cursor.execute("ALTER TABLE emergency_requests ADD COLUMN longitude REAL")
        print("Added longitude to emergency_requests table")

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
