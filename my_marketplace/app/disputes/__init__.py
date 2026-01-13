from flask import Blueprint

disputes_bp = Blueprint('disputes', __name__, template_folder='templates')

from . import routes