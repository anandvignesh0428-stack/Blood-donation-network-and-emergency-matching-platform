import sqlite3

conn = sqlite3.connect('blood_donation.db')
c = conn.cursor()

# Get tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", c.fetchall())

# Check donors
c.execute("SELECT * FROM donors")
print("Donors:", c.fetchall())

# Check emergency_requests
c.execute("SELECT * FROM emergency_requests")
print("Emergency Requests:", c.fetchall())

conn.close()