import os
from app import app, db
from models import SiteSettings

def seed_settings():
    with app.app_context():
        db.create_all()
        # Define default settings
        defaults = [
            {'key': 'site_name', 'value': 'Muhammad Hanzala', 'category': 'General', 'description': 'Full name displayed in branding'},
            {'key': 'tagline', 'value': 'Full Stack Developer & Digital Creator', 'category': 'General', 'description': 'Main headline on homepage'},
            {'key': 'location', 'value': 'Islamabad, Pakistan', 'category': 'Contact', 'description': 'Physical location displayed in footer'},
            {'key': 'phone', 'value': '+92 301 5855940', 'category': 'Contact', 'description': 'Contact phone number'},
            {'key': 'email', 'value': 'hani75384@gmail.com', 'category': 'Contact', 'description': 'Contact email address'},
            {'key': 'education_main', 'value': 'BS Computer Science (6th Semester)', 'category': 'Personal', 'description': 'Current education status'},
            {'key': 'education_institution', 'value': 'KICSIT, Islamabad', 'category': 'Personal', 'description': 'Current university name'},
            {'key': 'experience_years', 'value': '2+', 'category': 'Stats', 'description': 'Years of professional experience'},
            {'key': 'projects_completed', 'value': '50+', 'category': 'Stats', 'description': 'Total projects delivered'},
            {'key': 'bio_lead', 'value': 'I craft high-performance web applications, stunning 3D visuals, and engaging digital experiences. Some people call me Hani.', 'category': 'Personal', 'description': 'Main bio intro on hero section'},
        ]
        
        for d in defaults:
            existing = SiteSettings.query.filter_by(key=d['key']).first()
            if not existing:
                setting = SiteSettings(
                    key=d['key'],
                    value=d['value'],
                    category=d['category'],
                    description=d['description']
                )
                db.session.add(setting)
        
        db.session.commit()
        print("SiteSettings seeded successfully.")

if __name__ == '__main__':
    seed_settings()
