
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import Email, DataRequired, Length


class Login_Form(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=13)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=80)])
    remember = BooleanField('Remember Me')


class Register_Form(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(message='Invalid Email'), Length(max=40)])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=80)])
