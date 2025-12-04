"""Database migration script to add new columns to project table"""
import sqlite3
import os

# Get the database path
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'portfolio.db')

print(f"Connecting to database: {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Adding new columns to project table...")

# List of columns to add
columns_to_add = [
    ("long_description", "TEXT"),
    ("challenge", "TEXT"),
    ("solution", "TEXT"),
    ("client", "VARCHAR(100)"),
    ("role", "VARCHAR(100)")
]

for column_name, column_type in columns_to_add:
    try:
        cursor.execute(f"ALTER TABLE project ADD COLUMN {column_name} {column_type}")
        print(f"✓ Added column: {column_name}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print(f"⊘ Column {column_name} already exists, skipping")
        else:
            print(f"✗ Error adding column {column_name}: {e}")

# Create ProjectImage table if it doesn't exist
print("\nCreating ProjectImage table...")
try:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_image (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            image VARCHAR(255),
            caption VARCHAR(500),
            order_index INTEGER DEFAULT 0,
            FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE
        )
    ''')
    print("✓ ProjectImage table created/verified")
except Exception as e:
    print(f"✗ Error creating ProjectImage table: {e}")

# Create Technology table if it doesn't exist
print("\nCreating Technology table...")
try:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS technology (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL UNIQUE,
            icon VARCHAR(100)
        )
    ''')
    print("✓ Technology table created/verified")
except Exception as e:
    print(f"✗ Error creating Technology table: {e}")

# Create project_technologies association table if it doesn't exist
print("\nCreating project_technologies association table...")
try:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_technologies (
            project_id INTEGER NOT NULL,
            technology_id INTEGER NOT NULL,
            PRIMARY KEY (project_id, technology_id),
            FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
            FOREIGN KEY (technology_id) REFERENCES technology(id) ON DELETE CASCADE
        )
    ''')
    print("✓ project_technologies table created/verified")
except Exception as e:
    print(f"✗ Error creating project_technologies table: {e}")

# Commit changes
conn.commit()
conn.close()

print("\n" + "="*50)
print("✅ Database migration completed successfully!")
print("="*50)
print("\nNew columns added to project table:")
for column_name, _ in columns_to_add:
    print(f"  - {column_name}")
print("\nNew tables created:")
print("  - project_image")
print("  - technology")
print("  - project_technologies")
