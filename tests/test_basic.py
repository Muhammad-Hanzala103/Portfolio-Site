import pytest
from app import app, db
from models import User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_home_page(client):
    """Test that the home page loads."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Muhammad Hanzala" in response.data

def test_admin_login_page(client):
    """Test that the admin login page loads."""
    response = client.get('/admin/login')
    assert response.status_code == 200

def test_strict_name_rule_in_content(client):
    """Ensure Hani is not incorrectly attached to the main name."""
    response = client.get('/')
    content = response.data.decode('utf-8')
    assert "Muhammad Hanzala (Hani)" not in content
    assert "Muhammad Hanzala Hani" not in content
