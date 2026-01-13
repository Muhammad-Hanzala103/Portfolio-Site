from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, Optional

class SettingsForm(FlaskForm):
    site_name = StringField('Site Name', validators=[DataRequired(), Length(max=128)])
    site_description = TextAreaField('Site Description', validators=[Optional(), Length(max=256)])
    contact_email = StringField('Contact Email', validators=[Optional(), Email(), Length(max=128)])
    contact_phone = StringField('Contact Phone', validators=[Optional(), Length(max=32)])
    social_media_facebook = StringField('Facebook URL', validators=[Optional(), Length(max=256)])
    social_media_twitter = StringField('Twitter URL', validators=[Optional(), Length(max=256)])
    social_media_instagram = StringField('Instagram URL', validators=[Optional(), Length(max=256)])
    social_media_linkedin = StringField('LinkedIn URL', validators=[Optional(), Length(max=256)])
    google_analytics_id = StringField('Google Analytics ID', validators=[Optional(), Length(max=64)])
    maintenance_mode = BooleanField('Maintenance Mode')
    submit = SubmitField('Save Settings')