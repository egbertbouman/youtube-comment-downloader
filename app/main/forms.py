# app/main/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField ,SelectField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo, URL


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')

class YoutubeForm(FlaskForm):
    video_url = StringField('youtube-video-url', validators=[Required(), URL(), Length(1, 64)], )
    downloadFileType = SelectField('file type', choices=[
        ('csv', 'CSV'),
        ('xlsx', 'Excel')] ,validators=[Required()])
    outputFileNmae = StringField('output file name',validators=[Required()])
    # submit = SubmitField('Start scraping')
    submit = SubmitField('Preview')
    
