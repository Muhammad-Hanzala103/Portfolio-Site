import os
import secrets
import re
from PIL import Image
from flask import current_app, url_for
from datetime import datetime
import unicodedata

def allowed_file(filename, allowed_extensions=None):
    """Check if file has allowed extension."""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_picture(form_picture, folder, size=(800, 600)):
    """Save uploaded picture with random filename."""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    
    # Create folder if it doesn't exist
    upload_path = os.path.join(current_app.root_path, 'static', 'uploads', folder)
    os.makedirs(upload_path, exist_ok=True)
    
    picture_path = os.path.join(upload_path, picture_fn)
    
    # Resize image if it's an image file
    if f_ext.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
        try:
            img = Image.open(form_picture)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(picture_path, optimize=True, quality=85)
        except Exception as e:
            # If image processing fails, save original
            form_picture.save(picture_path)
    else:
        form_picture.save(picture_path)
    
    return picture_fn

def delete_picture(filename, folder):
    """Delete picture from uploads folder."""
    if filename:
        picture_path = os.path.join(current_app.root_path, 'static', 'uploads', folder, filename)
        if os.path.exists(picture_path):
            try:
                os.remove(picture_path)
                return True
            except Exception as e:
                current_app.logger.error(f"Error deleting file {picture_path}: {e}")
    return False

def create_slug(text):
    """Create URL-friendly slug from text."""
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    # Convert to lowercase and replace spaces with hyphens
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s]+', '-', text)
    return text

def truncate_text(text, length=150, suffix='...'):
    """Truncate text to specified length."""
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + suffix

def format_datetime(dt, format='%B %d, %Y'):
    """Format datetime object."""
    if dt:
        return dt.strftime(format)
    return ''

def time_ago(dt):
    """Return human-readable time ago string."""
    if not dt:
        return ''
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

def get_file_size(filepath):
    """Get file size in human readable format."""
    try:
        size = os.path.getsize(filepath)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    except:
        return "Unknown"

def validate_image(file):
    """Validate uploaded image file."""
    if not file:
        return False, "No file selected"
    
    if not allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif'}):
        return False, "Invalid file type. Only PNG, JPG, JPEG, and GIF are allowed."
    
    # Check file size (5MB limit)
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    
    if size > 5 * 1024 * 1024:  # 5MB
        return False, "File size too large. Maximum 5MB allowed."
    
    return True, "Valid image"

def generate_meta_description(content, length=160):
    """Generate meta description from content."""
    # Remove HTML tags
    clean_content = re.sub(r'<[^>]+>', '', content)
    # Remove extra whitespace
    clean_content = re.sub(r'\s+', ' ', clean_content).strip()
    return truncate_text(clean_content, length, '...')

def extract_tags_from_content(content):
    """Extract potential tags from content."""
    # Simple tag extraction based on common programming terms
    common_tags = [
        'python', 'javascript', 'html', 'css', 'react', 'flask', 'django',
        'nodejs', 'mongodb', 'mysql', 'postgresql', 'git', 'docker',
        'aws', 'api', 'frontend', 'backend', 'fullstack', 'web development'
    ]
    
    content_lower = content.lower()
    found_tags = [tag for tag in common_tags if tag in content_lower]
    return found_tags[:5]  # Return max 5 tags

def create_breadcrumb(endpoint, **kwargs):
    """Create breadcrumb navigation."""
    breadcrumbs = [{'name': 'Home', 'url': url_for('main.index')}]
    
    if endpoint.startswith('admin.'):
        breadcrumbs.append({'name': 'Admin', 'url': url_for('admin.dashboard')})
        
        if endpoint == 'admin.projects':
            breadcrumbs.append({'name': 'Projects', 'url': None})
        elif endpoint == 'admin.skills':
            breadcrumbs.append({'name': 'Skills', 'url': None})
        elif endpoint == 'admin.blog_posts':
            breadcrumbs.append({'name': 'Blog Posts', 'url': None})
        # Add more as needed
    
    elif endpoint.startswith('main.'):
        if endpoint == 'main.blog':
            breadcrumbs.append({'name': 'Blog', 'url': None})
        elif endpoint == 'main.blog_post':
            breadcrumbs.append({'name': 'Blog', 'url': url_for('main.blog')})
            if 'slug' in kwargs:
                breadcrumbs.append({'name': kwargs['slug'].replace('-', ' ').title(), 'url': None})
        elif endpoint == 'main.contact':
            breadcrumbs.append({'name': 'Contact', 'url': None})
    
    return breadcrumbs

def sanitize_filename(filename):
    """Sanitize filename for safe storage."""
    # Remove or replace unsafe characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    filename = re.sub(r'\s+', '_', filename)
    return filename.lower()