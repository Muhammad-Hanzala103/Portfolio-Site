import sqlite3
import os
from app import app

def final_db_fix():
    # Path to your database
    db_path = os.path.join(app.root_path, 'instance', 'portfolio.db')
    if not os.path.exists(db_path):
        db_path = os.path.join(app.root_path, 'portfolio.db')
        
    print(f"Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Define required columns for Gallery table
    gallery_columns = [
        ("video_url", "TEXT"),
        ("is_video", "BOOLEAN DEFAULT 0"),
        ("featured", "BOOLEAN DEFAULT 0"),
        ("order_index", "INTEGER DEFAULT 0"),
        ("category_id", "INTEGER"),
        ("created_at", "DATETIME"),
        ("updated_at", "DATETIME")
    ]

    # Get existing columns
    cursor.execute("PRAGMA table_info(gallery)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    print(f"Current columns in gallery: {existing_columns}")

    for col_name, col_type in gallery_columns:
        if col_name not in existing_columns:
            try:
                query = f"ALTER TABLE gallery ADD COLUMN {col_name} {col_type}"
                cursor.execute(query)
                print(f"Successfully added column: {col_name}")
            except sqlite3.OperationalError as e:
                print(f"Error adding {col_name}: {e}")
        else:
            print(f"Column already exists: {col_name}")

    conn.commit()
    conn.close()
    print("Database migration complete.")

if __name__ == '__main__':
    final_db_fix()
