import sqlite3

# Create a new SQLite database (or connect if it exists)
conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()

# Create expenses table
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    month TEXT NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL
)
"""
)

# Create budgets table
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS budgets (
    month TEXT PRIMARY KEY,
    amount REAL NOT NULL
)
"""
)

conn.commit()
conn.close()

print("Database 'expenses.db' created successfully with required tables.")
