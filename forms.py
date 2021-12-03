from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, Email, Length
from flask_ckeditor import CKEditorField


##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class RegisterForm(FlaskForm):
    email = StringField(label='Email', validators=[DataRequired(), Email()])
    password = PasswordField(label='Password', validators=[ DataRequired(), Length(min=5)])
    name = StringField(label='Name', validators=[DataRequired()])
    submit = SubmitField(label='Sign Me Up')


class LoginForm(FlaskForm):
    email = StringField(label='Email', validators=[DataRequired(), Email()])
    password = PasswordField(label='Password', validators=[ DataRequired(), Length(min=5)])
    submit = SubmitField(label='Let Me In')


class CommentForm(FlaskForm):
    comment = CKEditorField(label='Comment', validators=[DataRequired()])
    submit = SubmitField('Submit Comment')
