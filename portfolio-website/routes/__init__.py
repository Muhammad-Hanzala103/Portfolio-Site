from flask import Blueprint

# Initialize the routes blueprint
main_bp = Blueprint('main', __name__)
admin_bp = Blueprint('admin', __name__)
api_bp = Blueprint('api', __name__)

# Import routes to register them with the blueprints
from .main import *
from .admin import *
from .api import *