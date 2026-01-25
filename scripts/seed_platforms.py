import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import ExternalPlatform

def seed_platforms():
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        print("Seeding External Platforms...")
        
        platforms = [
            {
                "platform_name": "Fiverr",
                "title": "Full Stack Web Developer Gig",
                "url": "https://www.fiverr.com/mr0_0hani",
                "thumbnail": "",  # Link to placeholder if no real img
                "description": "Offering high-end web development services with Flask and React.",
                "service_type": "Web Development",
                "rating": 5.0,
                "reviews_count": 25,
                "order_index": 1
            },
            {
                "platform_name": "Upwork",
                "title": "Senior Python Backend Developer",
                "url": "https://www.upwork.com/",
                "thumbnail": "",
                "description": "Building scalable backend architectures and API integrations.",
                "service_type": "Backend Engineering",
                "rating": 4.9,
                "reviews_count": 12,
                "order_index": 2
            },
            {
                "platform_name": "LinkedIn",
                "title": "Professional Profile & Portfolio",
                "url": "https://www.linkedin.com/in/muhammad-hanzala-47439328a/",
                "thumbnail": "",
                "description": "Connecting with global clients and showcasing digital innovation.",
                "service_type": "Personal Brand",
                "rating": 5.0,
                "reviews_count": 50,
                "order_index": 3
            }
        ]

        for p_data in platforms:
            existing = ExternalPlatform.query.filter_by(platform_name=p_data['platform_name']).first()
            if not existing:
                p = ExternalPlatform(**p_data)
                db.session.add(p)
            else:
                for key, value in p_data.items():
                    setattr(existing, key, value)
        
        db.session.commit()
        print("Platforms Seeded/Updated Successfully!")

if __name__ == '__main__':
    seed_platforms()
