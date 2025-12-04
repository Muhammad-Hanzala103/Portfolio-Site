from app import app, db
from models import Service, ServiceTier

services_data = [
    {
        'title': 'Image Editing',
        'icon': 'fas fa-camera-retro',
        'description': 'Professional image editing services using Photoshop, Canva, and Affinity Photo. I enhance photos, remove backgrounds, and create stunning visuals.',
        'short_description': 'Professional image editing using Photoshop, Canva, and Affinity.',
        'features': 'Retouching, Background Removal, Color Correction, Photo Manipulation',
        'price': '$10 - $50',
        'tiers': [
            {'name': 'Basic', 'price': 10.0, 'description': 'Basic retouching and background removal for up to 5 images.', 'features': 'Background Removal, Basic Color Correction, 2 Revisions'},
            {'name': 'Standard', 'price': 30.0, 'description': 'Advanced editing and manipulation for up to 10 images.', 'features': 'Advanced Retouching, Photo Manipulation, Source Files, 5 Revisions'},
            {'name': 'Premium', 'price': 50.0, 'description': 'High-end beauty retouching and complex compositing for up to 20 images.', 'features': 'High-End Retouching, Complex Compositing, VIP Support, Unlimited Revisions'}
        ]
    },
    {
        'title': 'Full Stack Web Development',
        'icon': 'fas fa-code',
        'description': 'Complete web solutions using Python (Flask/Django), JavaScript (React), and modern databases. I build scalable and secure web applications.',
        'short_description': 'Complete web solutions using Python, JavaScript, and modern databases.',
        'features': 'Custom Web Apps, API Development, Database Design, Responsive UI',
        'price': '$500 - $2000',
        'tiers': [
            {'name': 'Basic', 'price': 500.0, 'description': 'Simple landing page or portfolio website.', 'features': 'Responsive Design, Contact Form, 3 Pages, 1 Month Support'},
            {'name': 'Standard', 'price': 1000.0, 'description': 'Dynamic web application with database integration.', 'features': 'User Authentication, Database Integration, Admin Panel, 5 Pages, 3 Months Support'},
            {'name': 'Premium', 'price': 2000.0, 'description': 'Complex full-stack application with advanced features.', 'features': 'E-commerce Functionality, API Integration, Custom Dashboard, Payment Gateway, 6 Months Support'}
        ]
    },
    {
        'title': 'Android App Development',
        'icon': 'fab fa-android',
        'description': 'Native Android application development using Android Studio and Java. I create user-friendly and performant mobile apps.',
        'short_description': 'Native Android app development using Android Studio and Java.',
        'features': 'Native UI/UX, API Integration, Offline Support, Play Store Submission',
        'price': '$800 - $3000',
        'tiers': [
            {'name': 'Basic', 'price': 800.0, 'description': 'Simple utility or informational app.', 'features': 'Basic UI, 3 Screens, Splash Screen, APK Delivery'},
            {'name': 'Standard', 'price': 1500.0, 'description': 'Functional app with local database or API.', 'features': 'Custom UI, API Integration, Local Database, 5-8 Screens, Source Code'},
            {'name': 'Premium', 'price': 3000.0, 'description': 'Complex app with backend integration and advanced features.', 'features': 'User Auth, Push Notifications, Payment Integration, Admin Panel, Play Store Upload'}
        ]
    },
    {
        'title': 'Video Editing',
        'icon': 'fas fa-video',
        'description': 'Professional video editing services using DaVinci Resolve. I can help you create engaging videos for your business, social media, or personal use.',
        'short_description': 'Professional video editing services using DaVinci Resolve.',
        'features': 'Color Grading, Motion Graphics, Sound Design, Visual Effects',
        'price': '$200 - $800',
        'tiers': [
            {'name': 'Basic', 'price': 200.0, 'description': 'Basic cut and trim for up to 5 minutes of footage.', 'features': 'Trimming, Basic Transitions, Text Overlays'},
            {'name': 'Standard', 'price': 400.0, 'description': 'Advanced editing with color grading and sound design.', 'features': 'Color Grading, Sound Mixing, Motion Graphics, up to 15 mins'},
            {'name': 'Premium', 'price': 800.0, 'description': 'Cinematic editing with VFX and custom animations.', 'features': 'Advanced VFX, Custom Animation, 4K Rendering, Unlimited Revisions'}
        ]
    },
    {
        'title': 'UI/UX Design',
        'icon': 'fas fa-pencil-ruler',
        'description': 'User-centered UI/UX design services that focus on creating intuitive and engaging user experiences. I design interfaces that are both beautiful and functional.',
        'short_description': 'User-centered UI/UX design services.',
        'features': 'Wireframing, Prototyping, User Testing, Visual Design',
        'price': '$300 - $1000',
        'tiers': [
            {'name': 'Basic', 'price': 300.0, 'description': 'UI design for a single landing page or mobile screen.', 'features': '1 Page/Screen, Source File (Figma/XD), 2 Revisions'},
            {'name': 'Standard', 'price': 600.0, 'description': 'Complete design system for a small website or app.', 'features': 'Up to 5 Pages/Screens, Interactive Prototype, Style Guide'},
            {'name': 'Premium', 'price': 1000.0, 'description': 'Comprehensive UI/UX solution for complex products.', 'features': 'Full App/Web Design, User Flow, High-Fidelity Prototype, Design System'}
        ]
    }
]

with app.app_context():
    # Clear existing services and tiers to avoid duplicates/conflicts
    print("Clearing existing services and tiers...")
    ServiceTier.query.delete()
    Service.query.delete()
    db.session.commit()

    print("Seeding services and tiers...")
    for data in services_data:
        service = Service(
            title=data['title'],
            icon=data['icon'],
            description=data['description'],
            short_description=data['short_description'],
            features=data['features'],
            price=data['price'],
            featured=True
        )
        db.session.add(service)
        db.session.flush() # Flush to get service.id

        for tier_data in data['tiers']:
            tier = ServiceTier(
                service_id=service.id,
                name=tier_data['name'],
                price=tier_data['price'],
                description=tier_data['description'],
                features=tier_data['features']
            )
            db.session.add(tier)
    
    db.session.commit()
    print("Services and tiers seeded successfully!")
