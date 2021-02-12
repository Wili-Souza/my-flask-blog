from flask_wtf import FlaskForm
from app.models import User
from wtforms import ValidationError, StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_wtf.file import FileAllowed, FileField
import email_validator
from flask_login import current_user


class LoginForm(FlaskForm):  # A flask form object
    # DataRequired() -> valid if is not empty 
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Login")

class RegistrationForm(FlaskForm):  # A flask form object
    # DataRequired() -> valid if is not empty 
    username = StringField(
        "Username", 
        validators=[DataRequired(), Length(min=2, max=20)]
    )
    email = StringField(
        "Email", 
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        "Password", 
        validators=[DataRequired()]
    )
    confirm_password = PasswordField(
        "Confirm password", 
        validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField("Sign Up")

    def validate_username(self, username):  #validate_nameOfField adds a validator to the deafult ones
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("The username already exists, choose another one!")
    
    def validate_email(self, email):  # adding validation fo the email field
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("Email already registered, try logging in!")


class UpdateAccountForm(FlaskForm):    # A flask form object
    # DataRequired() -> valid if is not empty 
    username = StringField(
        "Username", 
        validators=[DataRequired(), Length(min=2, max=20)]
    )
    about_me = TextAreaField(
        "About me",
        validators=[Length(min=0, max=140)]
    )
    email = StringField(
        "Email", 
        validators=[DataRequired(), Email()]
    )
    picture = FileField("Profile picture", validators=[FileAllowed(["jpg", "png"])])
    submit = SubmitField("Update")

    # Solves the error when changing username for a existing one -> lets validate_username handle it
    def __init__(self, original_username, *args, **kwargs): # When the form initializes
        super(UpdateAccountForm, self).__init__(*args, **kwargs) #invokes the FlaskForm class (super)
        self.original_username = original_username

    def validate_username(self, username):  #validate_nameOfField adds a validator to the deafult ones
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError("The username already exists, choose another one!")
    
    def validate_email(self, email):  # adding validation fo the email field
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError("Email already registered, try logging in!")

class EmptyForm(FlaskForm):
    submit = SubmitField("Submit")

class PostForm(FlaskForm):
    title = StringField("Title", validators=[
        DataRequired(), Length(min=1, max=100)])
    content = TextAreaField("Post content", validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField("Submit")