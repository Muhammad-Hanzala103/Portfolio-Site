from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, BooleanField, PasswordField, IntegerField, DateField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, URL
from flask_ckeditor import CKEditorField

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    remember_me = BooleanField('Remember Me')

class ProjectForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    long_description = CKEditorField('Long Description')
    technologies = StringField('Technologies (comma separated)', validators=[DataRequired()])
    github_url = StringField('GitHub URL', validators=[Optional(), URL()])
    live_url = StringField('Live URL', validators=[Optional(), URL()])
    image = FileField('Project Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!')])
    category = SelectField('Category', choices=[
        ('web', 'Web Development'),
        ('mobile', 'Mobile Development'),
        ('desktop', 'Desktop Application'),
        ('api', 'API Development'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    featured = BooleanField('Featured Project')
    order_index = IntegerField('Order Index', validators=[Optional(), NumberRange(min=0)])

class SkillForm(FlaskForm):
    name = StringField('Skill Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    proficiency = IntegerField('Proficiency (%)', validators=[DataRequired(), NumberRange(min=0, max=100)])
    years_experience = IntegerField('Years of Experience', validators=[Optional(), NumberRange(min=0, max=50)])
    category = SelectField('Category', choices=[], validators=[Optional()])
    icon = StringField('Icon Class (Font Awesome)', validators=[Optional()])
    order_index = IntegerField('Order Index', validators=[Optional(), NumberRange(min=0)])

class ServiceForm(FlaskForm):
    title = StringField('Service Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    icon = StringField('Icon Class (Font Awesome)', validators=[Optional()])
    price_range = StringField('Price Range', validators=[Optional()])
    features = TextAreaField('Features (one per line)', validators=[Optional()])
    order_index = IntegerField('Order Index', validators=[Optional(), NumberRange(min=0)])

class TestimonialForm(FlaskForm):
    client_name = StringField('Client Name', validators=[DataRequired(), Length(max=100)])
    client_position = StringField('Client Position', validators=[Optional(), Length(max=100)])
    client_company = StringField('Client Company', validators=[Optional(), Length(max=100)])
    testimonial = TextAreaField('Testimonial', validators=[DataRequired()])
    rating = IntegerField('Rating (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    client_image = FileField('Client Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    featured = BooleanField('Featured Testimonial')
    order_index = IntegerField('Order Index', validators=[Optional(), NumberRange(min=0)])

class BlogPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = CKEditorField('Content', validators=[DataRequired()])
    excerpt = TextAreaField('Excerpt', validators=[Optional(), Length(max=500)])
    featured_image = FileField('Featured Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    category = SelectField('Category', choices=[
        ('technology', 'Technology'),
        ('web-development', 'Web Development'),
        ('programming', 'Programming'),
        ('tutorial', 'Tutorial'),
        ('personal', 'Personal'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    tags = StringField('Tags (comma separated)', validators=[Optional()])
    published = BooleanField('Published')
    featured = BooleanField('Featured Post')
    meta_description = StringField('Meta Description', validators=[Optional(), Length(max=160)])
    meta_keywords = StringField('Meta Keywords', validators=[Optional()])

class GalleryForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    image = FileField('Image', validators=[DataRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    category = SelectField('Category', choices=[
        ('projects', 'Projects'),
        ('personal', 'Personal'),
        ('events', 'Events'),
        ('certificates', 'Certificates'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    order_index = IntegerField('Order Index', validators=[Optional(), NumberRange(min=0)])

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=10)])

class CommentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    content = TextAreaField('Comment', validators=[DataRequired(), Length(min=5)])
    website = StringField('Website', validators=[Optional(), URL()])

class SettingsForm(FlaskForm):
    site_name = StringField('Site Name', validators=[DataRequired(), Length(max=100)])
    site_description = TextAreaField('Site Description', validators=[DataRequired()])
    site_keywords = StringField('Site Keywords', validators=[Optional()])
    contact_email = StringField('Contact Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[Optional()])
    address = TextAreaField('Address', validators=[Optional()])
    social_facebook = StringField('Facebook URL', validators=[Optional(), URL()])
    social_twitter = StringField('Twitter URL', validators=[Optional(), URL()])
    social_linkedin = StringField('LinkedIn URL', validators=[Optional(), URL()])
    social_github = StringField('GitHub URL', validators=[Optional(), URL()])
    social_instagram = StringField('Instagram URL', validators=[Optional(), URL()])
    google_analytics_id = StringField('Google Analytics ID', validators=[Optional()])
    maintenance_mode = BooleanField('Maintenance Mode')