from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer as Serializer
from slugify import slugify

# Create db instance here to avoid circular imports
db = SQLAlchemy()

# Association table for BlogPost tags (many-to-many)
blog_post_tags = db.Table('blog_post_tags',
    db.Column('blog_post_id', db.Integer, db.ForeignKey('blog_post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

# Association table for Project technologies (many-to-many)
project_technologies = db.Table('project_technologies',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('technology_id', db.Integer, db.ForeignKey('technology.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(255), nullable=True) # Nullable for Google-only users initially
    is_admin = db.Column(db.Boolean, default=False)
    google_id = db.Column(db.String(100), unique=True, index=True, nullable=True)
    email_verified = db.Column(db.Boolean, default=False)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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

class VerificationToken(db.Model):
    """Model for 6-digit OTP codes (Email Verification & 2FA)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    token_type = db.Column(db.String(20), nullable=False) # 'verify_email', '2fa'
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('tokens', lazy=True, cascade="all, delete-orphan"))
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f'<User {self.username}>'

class ProjectCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    projects = db.relationship('Project', backref='category_rel', lazy=True)
    
    def __repr__(self):
        return f'<ProjectCategory {self.name}>'

class SkillCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    skills = db.relationship('Skill', backref='category_rel', lazy=True)
    
    def __repr__(self):
        return f'<SkillCategory {self.name}>'

class GalleryCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    gallery_items = db.relationship('Gallery', backref='category_rel', lazy=True)
    
    def __repr__(self):
        return f'<GalleryCategory {self.name}>'

class BlogCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    blog_posts = db.relationship('BlogPost', backref='category_rel', lazy=True)
    
    def __init__(self, **kwargs):
        super(BlogCategory, self).__init__(**kwargs)
        if not self.slug and self.name:
            self.slug = slugify(self.name)
    
    def __repr__(self):
        return f'<BlogCategory {self.name}>'

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Tag {self.name}>'

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, index=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.String(300), nullable=True)
    long_description = db.Column(db.Text, nullable=True)  # Rich text content
    challenge = db.Column(db.Text, nullable=True)  # Case study: The Challenge
    solution = db.Column(db.Text, nullable=True)  # Case study: The Solution
    client = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(100), nullable=True)
    image = db.Column(db.String(255), nullable=True)  # Main featured image
    technologies = db.Column(db.String(255), nullable=True)  # Legacy string field, keep for backup
    github_link = db.Column(db.String(255), nullable=True)
    live_link = db.Column(db.String(255), nullable=True)
    featured = db.Column(db.Boolean, default=False)
    order_index = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('project_category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    images = db.relationship('ProjectImage', backref='project', lazy=True, cascade="all, delete-orphan")
    tech_stack = db.relationship('Technology', secondary=project_technologies, backref=db.backref('projects', lazy='dynamic'))
    
    def __init__(self, **kwargs):
        super(Project, self).__init__(**kwargs)
        if not self.slug and self.title:
            self.slug = slugify(self.title)
    
    @property
    def category(self):
        return self.category_rel.name if self.category_rel else 'Uncategorized'
    
    def __repr__(self):
        return f'<Project {self.title}>'

class ProjectImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(200), nullable=True)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ProjectImage {self.id} for Project {self.project_id}>'

class Technology(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    icon = db.Column(db.String(50), nullable=True)  # FontAwesome class
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Technology {self.name}>'

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    proficiency = db.Column(db.Integer, nullable=False)  # 0-100 percentage
    years_experience = db.Column(db.Integer, default=0)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(255), nullable=True)  # Font Awesome class or image path
    order_index = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('skill_category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship is defined in SkillCategory model
    
    @property
    def category(self):
        return self.category_rel.name if self.category_rel else 'Other'
    
    def __repr__(self):
        return f'<Skill {self.name}>'

class Gallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True) # Cover image
    video_url = db.Column(db.String(500), nullable=True) # YouTube/Vimeo link
    is_video = db.Column(db.Boolean, default=False)
    featured = db.Column(db.Boolean, default=False)
    order_index = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('gallery_category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship is defined in GalleryCategory model
    
    @property
    def category(self):
        return self.category_rel.name if self.category_rel else 'Other'
    
    def __repr__(self):
        return f'<Gallery {self.title}>'

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    client_position = db.Column(db.String(100), nullable=True)
    client_title = db.Column(db.String(100), nullable=True)  # Alias for client_position
    client_company = db.Column(db.String(100), nullable=True)
    testimonial_text = db.Column(db.Text, nullable=False)
    client_image = db.Column(db.String(255), nullable=True)
    platform = db.Column(db.String(50), nullable=True)  # e.g., LinkedIn, Upwork, Fiverr
    rating = db.Column(db.Integer, default=5)  # 1-5 stars
    featured = db.Column(db.Boolean, default=False)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Testimonial {self.client_name}>'

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.String(300), nullable=True)
    icon = db.Column(db.String(255), nullable=True)  # Font Awesome class or image path
    features = db.Column(db.Text, nullable=True)  # JSON string of features list
    price = db.Column(db.String(50), nullable=True)  # e.g., "Starting at $500"
    featured = db.Column(db.Boolean, default=False)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Service {self.title}>'

class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    service = db.relationship('Service', backref=db.backref('faqs', lazy=True))

    def __repr__(self):
        return f'<FAQ {self.question}>'

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.String(300), nullable=True)
    featured_image = db.Column(db.String(255), nullable=True)
    published = db.Column(db.Boolean, default=False, index=True)
    featured = db.Column(db.Boolean, default=False, index=True)
    views = db.Column(db.Integer, default=0)
    reading_time = db.Column(db.Integer, default=0)  # in minutes
    category_id = db.Column(db.Integer, db.ForeignKey('blog_category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships are defined in respective category models
    tags = db.relationship('Tag', secondary=blog_post_tags, backref=db.backref('blog_posts', lazy='dynamic'))
    
    def __init__(self, **kwargs):
        super(BlogPost, self).__init__(**kwargs)
        if not self.slug and self.title:
            self.slug = slugify(self.title)
    
    @property
    def category(self):
        return self.category_rel.name if self.category_rel else 'Uncategorized'
    
    @property
    def comments(self):
        return BlogComment.query.filter_by(post_id=self.id, approved=True).all()
    
    def __repr__(self):
        return f'<BlogPost {self.title}>'

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    replied = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Contact {self.name} - {self.email}>'

class BlogComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)
    author_name = db.Column(db.String(100), nullable=False)
    author_email = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    post = db.relationship('BlogPost', backref=db.backref('all_comments', lazy=True))
    
    def __repr__(self):
        return f'<BlogComment {self.author_name} on {self.post.title}>'

class CommentSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    enable_comments = db.Column(db.Boolean, default=True)
    moderate_comments = db.Column(db.Boolean, default=True)
    auto_close_after = db.Column(db.Integer, nullable=True)


class SiteVisit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(500), nullable=True)
    page_visited = db.Column(db.String(255), nullable=False)
    referrer = db.Column(db.String(255), nullable=True)
    visit_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SiteVisit {self.ip_address} - {self.page_visited}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stripe_session_id = db.Column(db.String(255), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='usd')
    status = db.Column(db.String(20), default='pending')  # pending, paid, failed
    customer_email = db.Column(db.String(120), nullable=True)
    project_details = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.String(50), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=True)
    tier_name = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ServiceTier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)  # Basic, Standard, Premium
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    features = db.Column(db.Text, nullable=True)  # Comma separated
    stripe_price_id = db.Column(db.String(100), nullable=True) # For Stripe integration

    def __repr__(self):
        return f'<ServiceTier {self.name} - {self.service.title}>'

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stripe_session_id = db.Column(db.String(255), unique=True, nullable=False)
    amount_cents = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(10), default='usd')
    status = db.Column(db.String(20), default='pending')  # pending, paid, failed
    customer_email = db.Column(db.String(120), nullable=True)
    metadata_json = db.Column(db.Text, nullable=True) # JSON string of metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Payment {self.stripe_session_id} - {self.status}>'

class ExternalPlatform(db.Model):
    """Model for Fiverr, Upwork, LinkedIn projects/gigs integration."""
    id = db.Column(db.Integer, primary_key=True)
    platform_name = db.Column(db.String(50), nullable=False) # Fiverr, Upwork, LinkedIn
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    thumbnail = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    service_type = db.Column(db.String(100), nullable=True) # e.g. "Web Development"
    rating = db.Column(db.Float, default=5.0)
    reviews_count = db.Column(db.Integer, default=0)
    order_index = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ExternalPlatform {self.platform_name}: {self.title}>'

class Resume(db.Model):
    """Model for managing professional resumes/CVs."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    version = db.Column(db.String(20), nullable=True) # e.g. "v1.2", "Jan 2025"
    language = db.Column(db.String(20), default='English')
    is_active = db.Column(db.Boolean, default=False)
    download_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Resume {self.title} ({self.version})>'

class Newsletter(db.Model):
    """Model for newsletter subscribers."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Newsletter {self.email}>'

class SiteSettings(db.Model):
    """Ultimate Admin configuration persistence."""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, index=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), default="General") # General, SEO, Social, Contact
    description = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f"<SiteSetting {self.key}: {self.value}>"