from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from slugify import slugify

# Create db instance here to avoid circular imports
db = SQLAlchemy()

# Association table for BlogPost tags (many-to-many)
blog_post_tags = db.Table('blog_post_tags',
    db.Column('blog_post_id', db.Integer, db.ForeignKey('blog_post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    slug = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.String(300), nullable=True)
    image = db.Column(db.String(255), nullable=True)
    technologies = db.Column(db.String(255), nullable=True)
    github_link = db.Column(db.String(255), nullable=True)
    live_link = db.Column(db.String(255), nullable=True)
    featured = db.Column(db.Boolean, default=False)
    order_index = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('project_category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship is defined in ProjectCategory model
    
    def __init__(self, **kwargs):
        super(Project, self).__init__(**kwargs)
        if not self.slug and self.title:
            self.slug = slugify(self.title)
    
    @property
    def category(self):
        return self.category_rel.name if self.category_rel else 'Uncategorized'
    
    def __repr__(self):
        return f'<Project {self.title}>'

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
    image = db.Column(db.String(255), nullable=False)
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

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.String(300), nullable=True)
    featured_image = db.Column(db.String(255), nullable=True)
    published = db.Column(db.Boolean, default=False)
    featured = db.Column(db.Boolean, default=False)
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

class SiteVisit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(500), nullable=True)
    page_visited = db.Column(db.String(255), nullable=False)
    referrer = db.Column(db.String(255), nullable=True)
    visit_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SiteVisit {self.ip_address} - {self.page_visited}>'