from flask import Blueprint

bp = Blueprint('auth', __name__, template_folder='templates')

from my_marketplace.app.auth import routes