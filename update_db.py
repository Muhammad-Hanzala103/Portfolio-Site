from app import app, db
from models import Gallery

def update_db():
    with app.app_context():
        # Using db.create_all() will only create NEW tables, 
        # but for existing tables with new columns, we might need to handle it manually or via migrate.
        # Since this is a local setup, if create_all doesn't add the column, we'll try to force it.
        try:
            db.create_all()
            print("Database creation/update attempted.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    update_db()
