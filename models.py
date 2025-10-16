from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, TextAreaField, FileField
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed

db = SQLAlchemy()

# ================== FORM ==================
class AddProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    description = TextAreaField('Description')
    image = FileField('Product Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Save')

# ================== MODELS ==================
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(200), nullable=True)  # نخزن فقط اسم الصورة

    def __repr__(self):
        return f"<Product {self.name}>"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')  # user أو admin

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100))
    address = db.Column(db.String(255))
    total = db.Column(db.Float)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float)
