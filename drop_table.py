import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Drop the table if it exists
cursor.execute("DROP TABLE IF EXISTS reservations_coach;")
print("Table 'reservations_coach' has been dropped.")

# Commit and close the connection
conn.commit()
conn.close()
