from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, FloatField, SelectMultipleField
from wtforms.validators import DataRequired, Email
from flask_wtf.file import FileAllowed, FileField
from wtforms import MultipleFileField
from flask import send_from_directory
from wtforms.widgets import ListWidget, CheckboxInput

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[Email(), DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('user', 'User'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[Email(), DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('PC', 'PC Builder'),
        ('Audio', 'Audiophile'),
        ('Keyboard', 'Mechanical Keyboard'),
        ('SmartHome', 'Smart Home')
    ], validators=[DataRequired()])
    recommended_for = SelectMultipleField(
        'Recommended For',
        choices=[
            ('Students', 'Students'),
            ('Professionals', 'Professionals'),
            ('Editors', 'Editors'),
            ('Hobbyists', 'Hobbyists')
        ],
        option_widget=CheckboxInput(),
        widget=ListWidget(prefix_label=False)
    )
    description = TextAreaField('Description')
    price = FloatField('Price')
    image = FileField('Product Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')])
    submit = SubmitField('Add Product')

class ShowcaseForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    category = SelectMultipleField(
        'Category',
        choices=[
            ('PC', 'PC Builder'),
            ('Audio', 'Audiophile'),
            ('Keyboard', 'Mechanical Keyboard'),
            ('SmartHome', 'Smart Home')
        ],
        option_widget=CheckboxInput(),
        widget=ListWidget(prefix_label=False)
    )
    components = TextAreaField('Components Info', validators=[DataRequired()])
    images = MultipleFileField('Upload Images', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!')
    ])
    submit = SubmitField('Create Showcase')
