from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from dotenv import load_dotenv
import os

# تحميل ملف .env
load_dotenv()

# إنشاء التطبيق
app = Flask(__name__)
app.config.from_object(Config)

# أو نستخدم القيم من .env مباشرة (في حال ما كانت في Config)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecretkey')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///store.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 🟢 استيراد قاعدة البيانات من models
from models import db, Product, Order, OrderItem, User

# 🟢 تهيئة قاعدة البيانات مع التطبيق
db.init_app(app)
migrate = Migrate(app, db)

# 🟢 استيراد المسارات بعد تهيئة قاعدة البيانات
from routes import *

# 🟢 تشغيل التطبيق
if __name__ == "__main__":
    app.run(debug=True)
