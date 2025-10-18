from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, TextAreaField, FileField, SelectField
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed
from datetime import datetime


db = SQLAlchemy()

# ================== FORM ==================
class AddProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    image = FileField('Product Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    
    # 🆕 خيار النشر (للتحديد أين يظهر المنتج)
    publish_location = SelectField(
        'Publish Product',
        choices=[
            ('both', 'Show in Home + Products pages'),
            ('products_only', 'Show only in Products page'),
            ('home_only', 'Show only in Home page')
        ],
        default='products_only'
    )

    submit = SubmitField('Save')


# ================== MODELS ==================
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200))
    
    # 🆕 خيار النشر: both / products_only / home_only
    publish_location = db.Column(db.String(20), default="products_only")

    def __repr__(self):
        return f"<Product {self.name}>"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')
    confirmed = db.Column(db.Boolean, default=False)  # ✅ تأكيد البريد الإلكتروني

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ================== CART & ORDER SYSTEM ==================

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)

    user = db.relationship('User', backref='cart_items', lazy=True)
    product = db.relationship('Product', lazy=True)

    def __repr__(self):
        return f"<Cart {self.user_id} - {self.product_id}>"


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    customer_name = db.Column(db.String(100))
    address = db.Column(db.String(255))
    total = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='orders', lazy=True)

    def __repr__(self):
        return f"<Order {self.id} - {self.customer_name}>"


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float)

    order = db.relationship('Order', backref='items', lazy=True)
    product = db.relationship('Product', lazy=True)

    def __repr__(self):
        return f"<OrderItem order={self.order_id}, product={self.product_id}>"


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
