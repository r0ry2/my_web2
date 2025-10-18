from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField  # <-- أضفناه هنا
from wtforms.validators import DataRequired, Email, Length, EqualTo       # <-- واحذف SelectField من هنا
from wtforms import StringField, FloatField, TextAreaField, SubmitField
from flask_wtf.file import FileField, FileAllowed
from flask_wtf.file import FileField, FileAllowed
from wtforms import SelectField

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    image = FileField('Product Image')

    # 🆕 خيار النشر
    publish_location = SelectField(
        'Publish Product',
        choices=[
            ('both', 'Show in Home + Products pages'),
            ('products_only', 'Show only in Products page')
        ],
        default='products_only'
    )

    submit = SubmitField('Save')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')







