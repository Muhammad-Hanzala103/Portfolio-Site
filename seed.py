from app import app, db, bcrypt
from models import User, Project, Service, ServiceTier, BlogPost, BlogCategory, Tag, SiteVisit, Payment, Skill, Testimonial, ProjectCategory
from datetime import datetime, timedelta
import random

def seed_data():
    with app.app_context():
        db.create_all()

        # 1. Admin User (Strict Rules)
        print("Seeding Admin User...")
        if User.query.filter_by(username='hanzala').first():
             print("Admin already exists.")
        else:
            hashed_pw = bcrypt.generate_password_hash('ChangeMe!2025').decode('utf-8')
            admin = User(
                username='hanzala',
                email='hani75384@gmail.com',  # Fixed typo
                password=hashed_pw,
                is_admin=True
            )
            db.session.add(admin)
        
        # 2. Project Categories
        categories = ['Web Development', '3D Design', 'Motion Graphics']
        cat_objs = {}
        for cat_name in categories:
            cat = ProjectCategory.query.filter_by(name=cat_name).first()
            if not cat:
                cat = ProjectCategory(name=cat_name)
                db.session.add(cat)
            cat_objs[cat_name] = cat
        db.session.commit()

        # 3. Projects
        print("Seeding Projects...")
        projects_data = [
            {
                "title": "E-Commerce Titan",
                "description": "A fully scalable e-commerce platform built with Flask and React.",
                "category": "Web Development",
                "tech": "Python, React, AWS",
                "slug": "ecommerce-titan"
            },
            {
                "title": "NeonCity 3D",
                "description": "Cyberpunk inspired 3D environment for a game engine.",
                "category": "3D Design",
                "tech": "Blender, Unreal Engine",
                "slug": "neoncity-3d"
            },
            {
                "title": "CryptoDash",
                "description": "Real-time cryptocurrency dashboard with websocket integration.",
                "category": "Web Development",
                "tech": "Vue.js, Socket.io",
                "slug": "cryptodash"
            },
            {
                "title": "BrandMotion Pack",
                "description": "A collection of high-energy motion graphics for diverse brands.",
                "category": "Motion Graphics",
                "tech": "After Effects",
                "slug": "brandmotion-pack"
            },
            {
                "title": "AI Image Generator",
                "description": "SaaS application leveraging Stable Diffusion for custom image generation.",
                "category": "Web Development",
                "tech": "Python, PyTorch, React",
                "slug": "ai-image-generator"
            },
            {
                "title": "Portfolio V1",
                "description": "Legacy portfolio site showcasing early career work.",
                "category": "Web Development",
                "tech": "HTML, CSS, JS",
                "slug": "portfolio-v1"
            }
        ]

        for p_data in projects_data:
            if not Project.query.filter_by(slug=p_data['slug']).first():
                proj = Project(
                    title=p_data['title'],
                    slug=p_data['slug'],
                    description=p_data['description'],
                    short_description=p_data['description'],
                    technologies=p_data['tech'],
                    category_id=cat_objs[p_data['category']].id,
                    featured=True,
                    order_index=0
                )
                db.session.add(proj)

        # 4. Services & Tiers
        print("Seeding Services...")
        services_data = [
            {
                "title": "Full Stack Development",
                "desc": "Complete web applications from concept to deployment.",
                "icon": "fas fa-code",
                "tiers": [
                    {"name": "Starter", "price": 500, "desc": "Landing page + CMS"},
                    {"name": "Standard", "price": 1500, "desc": "E-commerce or Web App"},
                    {"name": "Premium", "price": 3000, "desc": "Enterprise SaaS Solution"}
                ]
            },
            {
                "title": "3D Visualization",
                "desc": "Photorealistic 3D renders and assets.",
                "icon": "fas fa-cube",
                "tiers": [
                    {"name": "Basic", "price": 300, "desc": "Single asset render"},
                    {"name": "Scene", "price": 800, "desc": "Full environment scene"},
                    {"name": "Animation", "price": 2000, "desc": "30s 3D product animation"}
                ]
            }
        ]

        for s_data in services_data:
            if not Service.query.filter_by(title=s_data['title']).first():
                service = Service(
                    title=s_data['title'],
                    description=s_data['desc'],
                    short_description=s_data['desc'],
                    price="Varies",
                    icon=s_data['icon']
                )
                db.session.add(service)
                db.session.flush() # get ID

                for t_data in s_data['tiers']:
                    tier = ServiceTier(
                        service_id=service.id,
                        name=t_data['name'],
                        price=t_data['price'],
                        description=t_data['desc'],
                        features="Source File, High Res Render, revisions"
                    )
                    db.session.add(tier)

        # 5. Blog Posts
        print("Seeding Blog...")
        blog_data = [
            {"title": "The Future of Flask in 2025", "slug": "flask-future-2025"},
            {"title": "Why Glassmorphism is Here to Stay", "slug": "glassmorphism-ux"},
            {"title": "Optimizing 3D Assets for Web", "slug": "3d-web-optimization"},
            {"title": "My Journey: Muhammad Hanzala", "slug": "my-journey-hanzala"}
        ]
        
        default_cat = BlogCategory(name='Tech', slug='tech')
        db.session.add(default_cat)
        db.session.commit()

        for b_data in blog_data:
            if not BlogPost.query.filter_by(slug=b_data['slug']).first():
                post = BlogPost(
                    title=b_data['title'],
                    slug=b_data['slug'],
                    content=f"Content for {b_data['title']}. strict rule: I am Muhammad Hanzala.",
                    excerpt=f"Read about {b_data['title']}",
                    published=True,
                    category_id=default_cat.id
                )
                db.session.add(post)

        # 6. Analytics (Visits & Payments)
        print("Seeding Analytics...")
        # Visits
        for _ in range(50):
            visit = SiteVisit(
                ip_address=f"192.168.1.{random.randint(1, 255)}",
                page_visited=random.choice(['/', '/about', '/projects', '/contact']),
                visit_date=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            db.session.add(visit)

        # Payments
        for _ in range(5):
            payment = Payment(
                stripe_session_id=f"cs_test_{random.randint(10000,99999)}",
                amount_cents=random.choice([50000, 150000, 300000]),
                status='paid',
                customer_email='client@example.com',
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            db.session.add(payment)

        # 7. Testimonials
        if not Testimonial.query.first():
             t = Testimonial(
                 client_name="John Doe",
                 client_position="CEO, TechCorp",
                 testimonial_text="Muhammad Hanzala delivered an exceptional platform. The design is stunning.",
                 platform="Upwork",
                 rating=5,
                 featured=True
             )
             db.session.add(t)

        db.session.commit()
        print("Seeding Complete. Nickname rule enforced.")

# Alias for CLI command
def run_seed():
    """Alias for seed_data for Flask CLI."""
    seed_data()

if __name__ == '__main__':
    seed_data()