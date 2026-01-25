import sqlite3
import os
from app import app

def add_full_name():
    # Path to your database
    db_path = os.path.join(app.root_path, 'instance', 'portfolio.db')
    if not os.path.exists(db_path):
        db_path = os.path.join(app.root_path, 'portfolio.db')
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE user ADD COLUMN full_name STRING(100)")
        print("Added column full_name to user table.")
    except sqlite3.OperationalError:
        print("Column full_name already exists.")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    add_full_name()
