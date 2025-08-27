from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from . import chat_bp
from my_marketplace.models import User, Conversation, Message
from ..database import db
from ..utils.crypto import MessageCrypto


@chat_bp.route('/')
@login_required
def conversations():
    """Display the main chat interface"""
    return render_template('chat/conversations.html')


@chat_bp.route('/conversation/<int:conversation_id>')
@login_required
def conversation_detail(conversation_id):
    """Display a specific conversation"""
    conversation = Conversation.query.get_or_404(conversation_id)
    
    # Check if current user is a participant
    participant_ids = [int(pid.strip()) for pid in conversation.participants.split(',') if pid.strip()]
    if current_user.id not in participant_ids:
        flash('You are not authorized to view this conversation.', 'error')
        return redirect(url_for('chat.conversations'))
    
    return render_template('chat/conversations.html', active_conversation_id=conversation_id)


@chat_bp.route('/api/users/search')
@login_required
def search_users():
    """Search for users to start a conversation with"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify([])
    
    # Search users by name or email (excluding current user)
    users = User.query.filter(
        (User.name.ilike(f'%{query}%') | User.email.ilike(f'%{query}%')) &
        (User.id != current_user.id)
    ).limit(10).all()
    
    return jsonify([{
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'avatar_url': user.avatar_url
    } for user in users])


@chat_bp.route('/api/conversations/<int:conversation_id>/participants')
@login_required
def get_conversation_participants(conversation_id):
    """Get participant information for a conversation"""
    conversation = Conversation.query.get_or_404(conversation_id)
    
    # Check if current user is a participant
    participant_ids = [int(pid.strip()) for pid in conversation.participants.split(',') if pid.strip()]
    if current_user.id not in participant_ids:
        return jsonify(error='Not authorized'), 403
    
    # Get participant details
    participants = User.query.filter(User.id.in_(participant_ids)).all()
    
    return jsonify([{
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'avatar_url': user.avatar_url
    } for user in participants])