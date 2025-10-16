from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField  # <-- أضفناه هنا
from wtforms.validators import DataRequired, Email, Length, EqualTo       # <-- واحذف SelectField من هنا
from wtforms import StringField, FloatField, TextAreaField, SubmitField
from flask_wtf.file import FileField, FileAllowed
from flask_wtf.file import FileField, FileAllowed


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



class AddProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(min=2, max=100)])
    price = StringField('Price', validators=[DataRequired()])
    description = StringField('Description')
    image = FileField('Product Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Save')




