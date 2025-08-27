from flask import Blueprint

webrtc_bp = Blueprint('webrtc', __name__)

from . import routes