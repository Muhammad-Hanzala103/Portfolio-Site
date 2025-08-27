from flask import render_template
from flask_socketio import emit, join_room
from my_marketplace.app import socketio
from . import webrtc_bp


@webrtc_bp.route("/webrtc")
def webrtc():
    return render_template("webrtc.html")


@socketio.on('join')
def handle_join(room):
    join_room(room)


@socketio.on('offer')
def handle_offer(offer, room):
    emit('offer', offer, room=room, include_self=False)


@socketio.on('answer')
def handle_answer(answer, room):
    emit('answer', answer, room=room, include_self=False)


@socketio.on('candidate')
def handle_candidate(candidate, room):
    emit('candidate', candidate, room=room, include_self=False)