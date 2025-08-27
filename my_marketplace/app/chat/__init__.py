from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from flask_socketio import emit, join_room, leave_room

from models import Message, Conversation, User, db
from ..utils.crypto import MessageCrypto
from .. import socketio


chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

# Import routes after blueprint creation to avoid circular imports
from . import routes


def conversation_to_dict(c: Conversation):
    # Parse participants from comma-separated string
    participant_ids = [int(pid.strip()) for pid in c.participants.split(',') if pid.strip()]
    return {
        'id': c.id,
        'participants': participant_ids,
        'last_message_at': c.last_message_at.isoformat() if c.last_message_at else None,
    }


def message_to_dict(m: Message):
    # Decrypt the message content
    decrypted_content = MessageCrypto.decrypt_message(m.ciphertext)
    return {
        'id': m.id,
        'conversation_id': m.conversation_id,
        'sender_id': m.sender_id,
        'content': decrypted_content,
        'is_read': m.read_at is not None,
        'timestamp': m.timestamp.isoformat() if m.timestamp else None,
        'attachment_url': m.attachment_url,
    }


@chat_bp.get('/ping')
def ping():
    return jsonify(msg='chat ok')


@chat_bp.post('/conversations')
@login_required
def create_conversation():
    """Create a new conversation between two users"""
    data = request.get_json()
    other_user_id = data.get('other_user_id')
    
    if not other_user_id or other_user_id == current_user.id:
        return jsonify(error='Invalid user ID'), 400
    
    # Check if other user exists
    other_user = User.query.get(other_user_id)
    if not other_user:
        return jsonify(error='User not found'), 404
    
    # Check if conversation already exists between these users
    existing_conversations = Conversation.query.filter(
        Conversation.participants.like(f'%{current_user.id}%')
    ).all()
    
    for conv in existing_conversations:
        participant_ids = [int(pid.strip()) for pid in conv.participants.split(',') if pid.strip()]
        if set(participant_ids) == {current_user.id, other_user_id}:
            return jsonify(conversation_to_dict(conv))
    
    # Create new conversation
    participants_str = f'{current_user.id},{other_user_id}'
    conversation = Conversation(participants=participants_str)
    
    try:
        db.session.add(conversation)
        db.session.commit()
        return jsonify(conversation_to_dict(conversation)), 201
    except Exception:
        db.session.rollback()
        return jsonify(error='Failed to create conversation'), 500


@chat_bp.patch('/messages/<int:message_id>/read')
@login_required
def mark_message_read(message_id):
    """Mark a message as read"""
    message = Message.query.get_or_404(message_id)
    
    # Check if current user is authorized to mark this message as read
    conversation = message.conversation
    participant_ids = [int(pid.strip()) for pid in conversation.participants.split(',') if pid.strip()]
    
    if current_user.id not in participant_ids:
        return jsonify(error='Not authorized'), 403
    
    # Only allow marking messages as read if user is not the sender
    if message.sender_id == current_user.id:
        return jsonify(error='Cannot mark own message as read'), 400
    
    try:
        message.read_at = db.func.now()
        db.session.commit()
        return jsonify(message_to_dict(message))
    except Exception:
        db.session.rollback()
        return jsonify(error='Failed to mark message as read'), 500


@chat_bp.get('/conversations')
@login_required
def list_conversations():
    # Find conversations where current user is a participant
    conversations = Conversation.query.filter(
        Conversation.participants.like(f'%{current_user.id}%')
    ).order_by(Conversation.last_message_at.desc()).all()
    
    # Filter to ensure user is actually a participant (not just substring match)
    user_conversations = []
    for conv in conversations:
        participant_ids = [int(pid.strip()) for pid in conv.participants.split(',') if pid.strip()]
        if current_user.id in participant_ids:
            user_conversations.append(conv)
    
    return jsonify([conversation_to_dict(c) for c in user_conversations])


@chat_bp.get('/conversations/<int:conversation_id>/messages')
@login_required
def list_messages(conversation_id):
    conversation = Conversation.query.get_or_404(conversation_id)
    
    # Check if current user is a participant
    participant_ids = [int(pid.strip()) for pid in conversation.participants.split(',') if pid.strip()]
    if current_user.id not in participant_ids:
        return jsonify(error='Not authorized'), 403
    
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp.asc()).all()
    return jsonify([message_to_dict(m) for m in messages])


@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        emit('status', {'msg': f'{current_user.username} connected'})
    else:
        emit('status', {'msg': 'Anonymous user connected'})


@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        emit('status', {'msg': f'{current_user.username} disconnected'})


@socketio.on('join')
def on_join(data):
    if not current_user.is_authenticated:
        return
    conversation_id = data.get('conversation_id')
    if not conversation_id:
        return
    conversation = Conversation.query.get(conversation_id)
    if not conversation:
        return
    
    # Check if current user is a participant
    participant_ids = [int(pid.strip()) for pid in conversation.participants.split(',') if pid.strip()]
    if current_user.id not in participant_ids:
        return
    
    room = f'conversation_{conversation_id}'
    join_room(room)
    emit('status', {'msg': f'{current_user.name} has entered the room.'}, room=room)


@socketio.on('leave')
def on_leave(data):
    if not current_user.is_authenticated:
        return
    conversation_id = data.get('conversation_id')
    if not conversation_id:
        return
    room = f'conversation_{conversation_id}'
    leave_room(room)
    emit('status', {'msg': f'{current_user.username} has left the room.'}, room=room)


@socketio.on('send_message')
def handle_send_message(data):
    if not current_user.is_authenticated:
        return
    conversation_id = data.get('conversation_id')
    content = data.get('content')
    if not conversation_id or not content:
        return

    conversation = Conversation.query.get(conversation_id)
    if not conversation:
        return
    
    # Check if current user is a participant
    participant_ids = [int(pid.strip()) for pid in conversation.participants.split(',') if pid.strip()]
    if current_user.id not in participant_ids:
        return

    try:
        # Encrypt the message content
        encrypted_content = MessageCrypto.encrypt_message(content)
        
        msg = Message(
            conversation_id=conversation_id, 
            sender_id=current_user.id, 
            ciphertext=encrypted_content
        )
        db.session.add(msg)
        
        # Update conversation's last message timestamp
        conversation.last_message_at = db.func.now()
        db.session.commit()
        
        room = f'conversation_{conversation_id}'
        emit('new_message', message_to_dict(msg), room=room)
    except Exception as e:
        db.session.rollback()
        emit('error', {'msg': 'Failed to send message'})