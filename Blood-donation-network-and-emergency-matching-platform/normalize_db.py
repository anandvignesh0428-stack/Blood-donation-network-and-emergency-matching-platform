import sqlite3

conn = sqlite3.connect('blood_donation.db')
c = conn.cursor()

# Normalize blood groups in donors table
c.execute("SELECT id, blood_group FROM donors")
donors = c.fetchall()

for donor_id, bg in donors:
    normalized = bg.strip().upper()
    if normalized != bg:
        c.execute("UPDATE donors SET blood_group = ? WHERE id = ?", (normalized, donor_id))
        print(f"Donor {donor_id}: {bg} -> {normalized}")

# Normalize blood groups in emergency_requests table
c.execute("SELECT id, blood_group FROM emergency_requests")
requests = c.fetchall()

for req_id, bg in requests:
    normalized = bg.strip().upper()
    if normalized != bg:
        c.execute("UPDATE emergency_requests SET blood_group = ? WHERE id = ?", (normalized, req_id))
        print(f"Request {req_id}: {bg} -> {normalized}")

# Remove duplicate donors (keep first occurrence)
c.execute("""
    DELETE FROM donors 
    WHERE id NOT IN (
        SELECT MIN(id) 
        FROM donors 
        GROUP BY name, blood_group, location, phone
    )
""")
deleted = c.rowcount
print(f"Removed {deleted} duplicate donors")

conn.commit()
conn.close()
print("Database normalization complete")