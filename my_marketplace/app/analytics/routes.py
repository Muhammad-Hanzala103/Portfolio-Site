from flask import request, jsonify, session
from . import analytics_bp
from my_marketplace.models import Event
from .. import db

@analytics_bp.route('/track', methods=['POST'])
def track_event():
    event_data = request.json
    event = Event(
        event_type=event_data.get('event_type'),
        user_id=event_data.get('user_id'),
        session_id=session.sid,
        meta=event_data.get('meta')
    )
    db.session.add(event)
    db.session.commit()
    return jsonify({'status': 'success'}), 200