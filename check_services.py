from app import app, db
from models import Service

with app.app_context():
    services = Service.query.all()
    print(f"Total Services: {len(services)}")
    for service in services:
        print(f"Service: {service.title} (ID: {service.id})")
