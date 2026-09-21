import sqlite3

conn = sqlite3.connect('blood_donation.db')
c = conn.cursor()

# Remove test entries with invalid blood groups
c.execute("DELETE FROM donors WHERE blood_group NOT IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')")
deleted = c.rowcount
print(f"Removed {deleted} donors with invalid blood groups")

# Remove duplicate donors by name/location/phone (keep first)
c.execute("""
    DELETE FROM donors 
    WHERE id NOT IN (
        SELECT MIN(id) 
        FROM donors 
        GROUP BY lower(name), blood_group, lower(location), phone
    )
""")
deleted = c.rowcount
print(f"Removed {deleted} duplicate donors (case-insensitive)")

conn.commit()
conn.close()
print("Database cleanup complete")

# Verify
conn = sqlite3.connect('blood_donation.db')
c = conn.cursor()
c.execute("SELECT * FROM donors")
print("Donors:", c.fetchall())
c.execute("SELECT * FROM emergency_requests")
print("Emergency Requests:", c.fetchall())
conn.close()