import os
import sys
import re

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import Project, Service, BlogPost, Testimonial

def sanitize_text(text):
    if not text:
        return text
    # Remove single dashes/underscores if they are between letters in a suspicious way
    text = re.sub(r'\s+[-_]\s+', ' ', text)
    # Generic cleanup of extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def sanitize_title(text):
    if not text:
        return text
    text = sanitize_text(text)
    # Ensure titles are capitalized professionally (Title Case)
    return text.title()

def run_cleanup():
    with app.app_context():
        # Ensure new tables are created
        db.create_all()
        print("Database tables verified/created.")
        
        print("Starting AI Artifact Cleanup...")
        
        # 1. Projects
        projects = Project.query.all()
        for p in projects:
            p.title = sanitize_title(p.title)
            p.description = sanitize_text(p.description)
            p.short_description = sanitize_text(p.short_description)
            if p.long_description:
                p.long_description = sanitize_text(p.long_description)
        
        # 2. Services
        services = Service.query.all()
        for s in services:
            s.title = sanitize_text(s.title)
            s.description = sanitize_text(s.description)
            s.short_description = sanitize_text(s.short_description)
            
        # 3. Blog Posts
        posts = BlogPost.query.all()
        for post in posts:
            post.title = sanitize_text(post.title)
            post.content = sanitize_text(post.content)
            post.excerpt = sanitize_text(post.excerpt)
            
        # 4. Testimonials
        testimonials = Testimonial.query.all()
        for t in testimonials:
            t.testimonial_text = sanitize_text(t.testimonial_text)
            
        db.session.commit()
        print("Cleanup Complete! Database corrected.")

if __name__ == '__main__':
    run_cleanup()
