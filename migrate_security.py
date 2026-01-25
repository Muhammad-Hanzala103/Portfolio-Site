import sqlite3
import os
from app import app, db

def migrate():
    # Path to your database
    db_path = os.path.join(app.root_path, 'instance', 'portfolio.db')
    if not os.path.exists(db_path):
        db_path = os.path.join(app.root_path, 'portfolio.db')
        
    print(f"Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Add columns to User table
    columns_to_add = [
        ("google_id", "STRING(100)"),
        ("email_verified", "BOOLEAN DEFAULT 0"),
        ("two_factor_enabled", "BOOLEAN DEFAULT 0")
    ]

    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name} to user table.")
        except sqlite3.OperationalError:
            print(f"Column {col_name} already exists in user table.")

    conn.commit()
    conn.close()

    # Create new tables
    with app.app_context():
        db.create_all()
        print("Created all new tables if they didn't exist.")

if __name__ == '__main__':
    migrate()
