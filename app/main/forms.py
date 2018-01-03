# app/main/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField ,SelectField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo, URL

class YoutubeForm(FlaskForm):
    video_url = StringField('youtube-video-url', validators=[Required(), URL(), Length(1, 64)], )
    downloadFileType = SelectField('file type', choices=[
        ('csv', 'CSV')] ,validators=[Required()])
    outputFileNmae = StringField('output file name',validators=[Required()])
    submit = SubmitField('Download')
    
