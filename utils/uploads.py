"""
Media Upload Utilities
Handles image and video processing for the portfolio site.

Features:
- Image resizing with thumbnails (420x420) and medium (1600px max)
- WebP conversion for better performance
- Video handling with size limits
- Secure filename generation
- Storage abstraction (local + S3 ready)
"""

import os
import uuid
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'webm', 'avi'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'zip', 'doc', 'docx'}

# Size limits (in bytes)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 200 * 1024 * 1024  # 200MB

# Image dimensions
THUMB_SIZE = (420, 420)
MEDIUM_MAX_WIDTH = 1600


def get_upload_folder():
    """Get the upload folder path from config or default."""
    return current_app.config.get('UPLOAD_FOLDER', 'static/uploads')


def allowed_file(filename, kind='image'):
    """Check if file extension is allowed."""
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if kind == 'image':
        return ext in ALLOWED_IMAGE_EXTENSIONS
    elif kind == 'video':
        return ext in ALLOWED_VIDEO_EXTENSIONS
    elif kind == 'document':
        return ext in ALLOWED_DOCUMENT_EXTENSIONS
    elif kind == 'any':
        return ext in ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS | ALLOWED_DOCUMENT_EXTENSIONS
    
    return False


def generate_unique_filename(original_filename):
    """Generate a unique filename with UUID prefix."""
    safe_name = secure_filename(original_filename)
    unique_id = uuid.uuid4().hex[:8]
    name, ext = os.path.splitext(safe_name)
    return f"{unique_id}_{name}{ext}"


def save_image(fileobj, dest_folder='', max_width=1600, create_thumb=True, thumb_size=(420, 420)):
    """
    Legacy function - saves an uploaded image securely with thumbnail.
    Returns the filename of the saved image.
    """
    if not fileobj:
        return None

    filename = secure_filename(fileobj.filename)
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext not in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg']:
        raise ValueError("Invalid file format. Allowed: jpg, jpeg, png, webp, gif, svg")

    # Generate unique filename
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    
    # Ensure destination exists
    full_dest_path = os.path.join(current_app.config['UPLOAD_FOLDER'], dest_folder) if dest_folder else current_app.config['UPLOAD_FOLDER']
    os.makedirs(full_dest_path, exist_ok=True)
    
    save_path = os.path.join(full_dest_path, unique_filename)

    # SVG files - just save as-is
    if file_ext == '.svg':
        fileobj.save(save_path)
        return os.path.join(dest_folder, unique_filename).replace('\\', '/') if dest_folder else unique_filename

    # Process image with Pillow
    img = Image.open(fileobj)
    
    # Convert to RGB if necessary
    if img.mode in ('RGBA', 'P') and file_ext in ['.jpg', '.jpeg']:
        img = img.convert('RGB')

    # Resize if too large
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

    # Save optimized original
    img.save(save_path, optimize=True, quality=85)

    # Create thumbnail if requested
    if create_thumb:
        thumb_filename = f"thumb_{unique_filename}"
        thumb_path = os.path.join(full_dest_path, thumb_filename)
        
        thumb_img = img.copy()
        thumb_img.thumbnail(thumb_size, Image.Resampling.LANCZOS)
        thumb_img.save(thumb_path, optimize=True, quality=85)

    return os.path.join(dest_folder, unique_filename).replace('\\', '/') if dest_folder else unique_filename


def save_media(fileobj, dest_folder=None, kind='image'):
    """
    Save uploaded media file with processing.
    
    Args:
        fileobj: FileStorage object from request.files
        dest_folder: Destination subfolder (default: uploads root)
        kind: 'image', 'video', or 'document'
    
    Returns:
        dict with paths: {
            'original': 'uploads/filename.jpg',
            'thumb': 'uploads/thumb_filename.jpg',
            'medium': 'uploads/medium_filename.jpg',
            'webp': 'uploads/filename.webp'
        }
    """
    if not fileobj or not fileobj.filename:
        return None
    
    if not allowed_file(fileobj.filename, kind):
        return None
    
    unique_filename = generate_unique_filename(fileobj.filename)
    
    upload_folder = get_upload_folder()
    if dest_folder:
        upload_folder = os.path.join(upload_folder, dest_folder)
    
    os.makedirs(upload_folder, exist_ok=True)
    
    original_path = os.path.join(upload_folder, unique_filename)
    result = {}
    
    if kind == 'image':
        result = _process_image(fileobj, original_path, unique_filename, upload_folder)
    elif kind == 'video':
        result = _process_video(fileobj, original_path, unique_filename)
    else:
        fileobj.save(original_path)
        result = {'original': _to_relative_path(original_path)}
    
    return result


def _process_image(fileobj, original_path, unique_filename, upload_folder):
    """Process and save image with thumbnails and WebP conversion."""
    result = {}
    ext = unique_filename.rsplit('.', 1)[1].lower()
    
    # SVG - save as-is
    if ext == 'svg':
        fileobj.save(original_path)
        result['original'] = _to_relative_path(original_path)
        return result
    
    try:
        img = Image.open(fileobj)
        
        if img.mode in ('RGBA', 'P') and ext in ('jpg', 'jpeg'):
            img = img.convert('RGB')
        
        # Save original
        img.save(original_path, quality=90, optimize=True)
        result['original'] = _to_relative_path(original_path)
        
        # Create thumbnail (420x420)
        thumb_filename = f"thumb_{unique_filename}"
        thumb_path = os.path.join(upload_folder, thumb_filename)
        thumb_img = img.copy()
        thumb_img.thumbnail(THUMB_SIZE, Image.Resampling.LANCZOS)
        thumb_img.save(thumb_path, quality=85, optimize=True)
        result['thumb'] = _to_relative_path(thumb_path)
        
        # Create medium version (max 1600px width)
        if img.width > MEDIUM_MAX_WIDTH:
            medium_filename = f"medium_{unique_filename}"
            medium_path = os.path.join(upload_folder, medium_filename)
            ratio = MEDIUM_MAX_WIDTH / img.width
            new_height = int(img.height * ratio)
            medium_img = img.resize((MEDIUM_MAX_WIDTH, new_height), Image.Resampling.LANCZOS)
            medium_img.save(medium_path, quality=85, optimize=True)
            result['medium'] = _to_relative_path(medium_path)
        
        # Create WebP version
        if ext not in ('webp', 'gif'):
            webp_filename = unique_filename.rsplit('.', 1)[0] + '.webp'
            webp_path = os.path.join(upload_folder, webp_filename)
            webp_img = img if img.width <= MEDIUM_MAX_WIDTH else medium_img
            if webp_img.mode == 'RGBA':
                webp_img.save(webp_path, 'WEBP', quality=85, optimize=True)
            else:
                webp_img.convert('RGB').save(webp_path, 'WEBP', quality=85, optimize=True)
            result['webp'] = _to_relative_path(webp_path)
        
    except Exception as e:
        current_app.logger.error(f"Error processing image: {e}")
        fileobj.seek(0)
        fileobj.save(original_path)
        result['original'] = _to_relative_path(original_path)
    
    return result


def _process_video(fileobj, original_path, unique_filename):
    """Save video with size validation."""
    result = {}
    
    # Check file size
    fileobj.seek(0, 2)
    size = fileobj.tell()
    fileobj.seek(0)
    
    if size > MAX_VIDEO_SIZE:
        current_app.logger.warning(f"Video too large: {size} bytes")
        return None
    
    fileobj.save(original_path)
    result['original'] = _to_relative_path(original_path)
    
    ext = unique_filename.rsplit('.', 1)[1].lower()
    result['mime'] = f'video/{ext}'
    result['size'] = size
    
    return result


def _to_relative_path(absolute_path):
    """Convert absolute path to relative path for URLs."""
    path = absolute_path.replace('\\', '/')
    if 'static/' in path:
        return path.split('static/')[-1]
    return path


def delete_media(paths):
    """Delete media files."""
    if isinstance(paths, str):
        paths = [paths]
    
    upload_folder = get_upload_folder()
    
    for path in paths:
        if path:
            full_path = os.path.join(upload_folder, path.split('uploads/')[-1]) if 'uploads/' in path else os.path.join(upload_folder, path)
            try:
                if os.path.exists(full_path):
                    os.remove(full_path)
            except Exception as e:
                current_app.logger.error(f"Error deleting {full_path}: {e}")


# Storage abstraction for S3 support
class StorageBackend:
    @staticmethod
    def get_backend():
        backend_type = current_app.config.get('STORAGE_BACKEND', 'local')
        if backend_type == 's3':
            return S3Storage()
        return LocalStorage()


class LocalStorage:
    def save(self, fileobj, path):
        fileobj.save(path)
        return path
    
    def delete(self, path):
        if os.path.exists(path):
            os.remove(path)
    
    def get_url(self, path):
        return f"/static/{path}"


class S3Storage:
    def __init__(self):
        self.bucket = current_app.config.get('S3_BUCKET')
        self.region = current_app.config.get('S3_REGION', 'us-east-1')
    
    def save(self, fileobj, path):
        raise NotImplementedError("S3 storage not yet implemented")
    
    def delete(self, path):
        pass
    
    def get_url(self, path):
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{path}"
