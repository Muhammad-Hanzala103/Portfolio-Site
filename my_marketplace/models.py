from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer as Serializer
from sqlalchemy import Enum
from werkzeug.security import generate_password_hash, check_password_hash

from my_marketplace.app.database import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    role = db.Column(Enum('buyer', 'seller', 'both', 'admin', name='user_roles'), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_suspended = db.Column(db.Boolean, default=False)
    bio = db.Column(db.Text, nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    languages = db.Column(db.String(255), nullable=True) # Storing as a comma-separated string
    wallet_balance = db.Column(db.Numeric(10, 2), default=0.00)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def has_reviewed_order(self, order_id):
        """Check if user has already reviewed a specific order"""
        return Review.query.filter_by(order_id=order_id, reviewer_id=self.id).first() is not None

    @property
    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.name}>'

class Gig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(255), nullable=False)
    tags = db.Column(db.Text, nullable=True) # Storing as a comma-separated string
    price_basic = db.Column(db.Numeric(10, 2), nullable=False)
    price_standard = db.Column(db.Numeric(10, 2), nullable=True)
    price_premium = db.Column(db.Numeric(10, 2), nullable=True)
    delivery_days_basic = db.Column(db.Integer, nullable=False)
    delivery_days_standard = db.Column(db.Integer, nullable=True)
    delivery_days_premium = db.Column(db.Integer, nullable=True)
    revisions_allowed = db.Column(db.Integer, default=0)
    thumbnail_url = db.Column(db.String(255), nullable=True)
    attachments = db.Column(db.Text, nullable=True) # Storing as a comma-separated list of URLs
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    seller = db.relationship('User', backref='gigs')

    def __repr__(self):
        return f'<Gig {self.title}>'

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    budget_min = db.Column(db.Numeric(10, 2), nullable=True)
    budget_max = db.Column(db.Numeric(10, 2), nullable=True)
    deadline = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default='open') # open, in_progress, closed
    
    buyer = db.relationship('User', backref='jobs')

    def __repr__(self):
        return f'<Job {self.title}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    gig_id = db.Column(db.Integer, db.ForeignKey('gig.id'), nullable=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    commission = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(Enum('pending', 'active', 'delivered', 'disputed', 'completed', 'cancelled', name='order_statuses'), nullable=False)
    milestone_json = db.Column(db.Text, nullable=True) # Storing as a JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    buyer = db.relationship('User', foreign_keys=[buyer_id], backref='bought_orders')
    seller = db.relationship('User', foreign_keys=[seller_id], backref='sold_orders')
    gig = db.relationship('Gig', backref='orders')
    job = db.relationship('Job', backref='orders')

    def __repr__(self):
        return f'<Order {self.id}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ciphertext = db.Column(db.Text, nullable=False)
    attachment_url = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)

    sender = db.relationship('User', backref='sent_messages')
    conversation = db.relationship('Conversation', backref='messages')

    def __repr__(self):
        return f'<Message {self.id}>'

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participants = db.Column(db.Text, nullable=False) # Storing as a comma-separated list of user IDs
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Conversation {self.id}>'

class Milestone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(Enum('pending', 'completed', name='milestone_statuses'), default='pending')
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    order = db.relationship('Order', backref='milestones')

    def __repr__(self):
        return f'<Milestone {self.title}>'

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order = db.relationship('Order', backref='reviews')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref='given_reviews')
    seller = db.relationship('User', foreign_keys=[seller_id], backref='received_reviews')

    def __repr__(self):
        return f'<Review {self.id}>'

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    provider = db.Column(db.String(50), nullable=False) # stripe, paypal, test
    status = db.Column(db.String(50), nullable=False) # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='payments')
    order = db.relationship('Order', backref='payments')

    def __repr__(self):
        return f'<Payment {self.id}>'

class Dispute(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    raised_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='open') # open, under_review, resolved
    resolution_notes = db.Column(db.Text, nullable=True)

    order = db.relationship('Order', backref='disputes')
    raised_by = db.relationship('User', backref='disputes')

    def __repr__(self):
        return f'<Dispute {self.id}>'

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    session_id = db.Column(db.String(255), nullable=True)
    meta = db.Column(db.JSON, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='events')

    def __repr__(self):
        return f'<Event {self.event_type}>'

class SiteSetting(db.Model):
    __tablename__ = 'site_setting'

    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(128), default='My Marketplace')
    site_description = db.Column(db.String(256), default='A great place to buy and sell.')
    contact_email = db.Column(db.String(128), default='')
    contact_phone = db.Column(db.String(32), default='')
    social_media_facebook = db.Column(db.String(256), default='')
    social_media_twitter = db.Column(db.String(256), default='')
    social_media_instagram = db.Column(db.String(256), default='')
    social_media_linkedin = db.Column(db.String(256), default='')
    google_analytics_id = db.Column(db.String(64), default='')
    maintenance_mode = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<SiteSetting {self.site_name}>'