from flask import (
    render_template, request, jsonify, session,
    redirect, url_for, flash
)
from app import app, db, mail
from models import Product, Order, OrderItem, User, Cart
from forms import LoginForm, RegisterForm, ProductForm
from werkzeug.utils import secure_filename
from flask_mail import Message as MailMessage
from itsdangerous import URLSafeTimedSerializer
import os
from datetime import datetime
from flask import render_template, request
from flask import jsonify
from models import db, Order, OrderItem, Product
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from models import db, Product, AddProductForm
from models import Message


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# ==========================================
# 🔐 إعداد تشفير الروابط (تأكيد البريد)
# ==========================================
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# ==========================================
# 🧩 HELPERS
# ==========================================
def session_get_cart():
    """Get cart stored in session (guest cart). Format: [{'product_id': id, 'quantity': n}, ...]"""
    return session.get("cart", [])


def session_save_cart(cart):
    session["cart"] = cart
    session.modified = True


def get_db_cart_items(user_id):
    """Return list of Cart rows for a user (SQLAlchemy objects)."""
    return Cart.query.filter_by(user_id=user_id).all()


def cart_items_to_json(cart_items):
    """Convert DB Cart rows to list of dicts suitable for frontend."""
    data = []
    for item in cart_items:
        product = Product.query.get(item.product_id)
        if not product:
            continue
        data.append({
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "quantity": item.quantity,
            "image": url_for('static', filename=f'images/{product.image}') if product.image else ''
        })
    return data


def merge_session_cart_into_db(user_id):
    """
    If a guest (session) has cart items and then logs in, merge them into DB cart.
    This function moves session cart items into DB (incrementing quantities if needed).
    """
    sess_cart = session_get_cart()
    if not sess_cart:
        return
    for s_item in sess_cart:
        pid = s_item.get('product_id')
        qty = int(s_item.get('quantity', 1))
        if not pid:
            continue
        existing = Cart.query.filter_by(user_id=user_id, product_id=pid).first()
        if existing:
            existing.quantity += qty
        else:
            db.session.add(Cart(user_id=user_id, product_id=pid, quantity=qty))
    db.session.commit()
    session_save_cart([])  # clear session cart after merging
    
    
    
# ==========================================
# 🧩 product
# =========================================
@app.route('/admin/product', methods=['GET', 'POST'])
@app.route('/admin/product/<int:product_id>', methods=['GET', 'POST'])
def add_or_edit_product(product_id=None):
    edit_mode = product_id is not None
    product = Product.query.get(product_id) if edit_mode else None
    form = AddProductForm(obj=product)

    if form.validate_on_submit():
        # 🧵 البيانات
        name = form.name.data
        price = form.price.data
        description = form.description.data
        publish_location = form.publish_location.data

        # 📸 الصورة
        image_file = form.image.data
        filename = product.image if edit_mode and product.image else None

        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)

        # 🪄 إضافة أو تحديث المنتج
        if edit_mode:
            product.name = name
            product.price = price
            product.description = description
            product.publish_location = publish_location
            product.image = filename
            flash('✅ Product updated successfully!', 'success')
        else:
            new_product = Product(
                name=name,
                price=price,
                description=description,
                image=filename,
                publish_location=publish_location
            )
            db.session.add(new_product)
            flash('🧵 Product added successfully!', 'success')

        db.session.commit()
        return redirect(url_for('admin_home'))

    return render_template(
        'add_product.html',
        form=form,
        edit_mode=edit_mode,
        product=product
    )
@app.route('/api/order/<int:order_id>')
def get_order_details(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    items = (
        db.session.query(OrderItem, Product)
        .join(Product, OrderItem.product_id == Product.id)
        .filter(OrderItem.order_id == order.id)
        .all()
    )

    item_list = []
    for order_item, product in items:
        item_list.append({
            "name": product.name,
            "price": order_item.price,
            "quantity": order_item.quantity,
            "image": product.image if product.image else ""
        })

    return jsonify({
        "id": order.id,
        "customer_name": order.customer_name,
        "address": order.address,
        "total": order.total,
        "items": item_list
    })


# ==========================================
# 🏠 GENERAL ROUTES
# ==========================================
@app.route('/')
def index():
    # show products that should appear on home: 'both' or 'home_only'
    products = Product.query.filter(Product.publish_location.in_(['both', 'home_only'])).all()
    return render_template('index.html', products=products)


@app.route("/products")
def products_page():
    # show products for products page: 'both' or 'products_only'
    products = Product.query.filter(Product.publish_location.in_(['both', 'products_only'])).all()
    return render_template("products.html", products=products)


@app.route("/cart")
def cart_page():
    return render_template("cart.html")


# ==========================================
# 👤 AUTHENTICATION
# ==========================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('⚠️ Email already registered!', 'warning')
            return redirect(url_for('register'))

        new_user = User(username=form.username.data, email=form.email.data)
        new_user.set_password(form.password.data)

        # ✅ لو هو الأدمن نفعّله تلقائيًا
        if form.email.data == "admin@store.com":
            new_user.role = 'admin'
            new_user.confirmed = True

        db.session.add(new_user)
        db.session.commit()

        # ✅ المستخدمين الجدد فقط لازم يأكدون البريد
        if not new_user.confirmed:
            token = s.dumps(new_user.email, salt='email-confirm')
            confirm_url = url_for('confirm_email', token=token, _external=True)

            msg = Message(
                subject="📧 Confirm your Crochet Rory Store account",
                recipients=[form.email.data],
                body=f"Hi {form.username.data},\n\nPlease confirm your email by clicking the link below:\n\n{confirm_url}\n\n– The Crochet Rory Team 💕"
            )
            mail.send(msg)
            flash('✅ Registration successful! Please check your email to confirm your account.', 'info')
            return redirect(url_for('login'))

        flash('✅ Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except:
        flash('❌ Invalid or expired confirmation link.', 'danger')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first_or_404()
    if getattr(user, "confirmed", False):
        flash('✅ Account already confirmed. Please log in.', 'success')
    else:
        user.confirmed = True
        db.session.commit()
        flash('🎉 Your account has been confirmed! You can now log in.', 'success')

    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if not user or not user.check_password(form.password.data):
            flash('❌ Invalid email or password!', 'danger')
            return render_template('login.html', form=form)

        if user.role != 'admin' and not getattr(user, "confirmed", True):
            flash('⚠️ Please confirm your email before logging in.', 'warning')
            return redirect(url_for('login'))

        # تسجيل الدخول: نحفظ اسم المستخدم وحقل id للمستخدم
        session['user'] = user.username
        session['user_id'] = user.id
        session['is_admin'] = (user.role == 'admin')

        # لو كان في سلة بالجلسة (guest) نندمجها مع سلة الـ DB للمستخدم
        merge_session_cart_into_db(user.id)

        flash(f"Welcome back, {user.username} 💕", "success")
        return redirect(url_for('admin_home') if session['is_admin'] else url_for('home_logged'))

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    # تنظيف الـ session لكن مع إمكانية ترك ملفات أخرى لو حبّيت
    session.clear()
    flash('👋 You have been logged out.', 'info')
    return redirect(url_for('login'))


# ==========================================
# 🛒 CART (single set of endpoints supporting session or DB)
# ==========================================
@app.route('/api/cart/add', methods=['POST'])
def api_cart_add():
    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1) or 1)

    if not product_id:
        return jsonify({'success': False, 'error': 'No product_id provided'}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'error': 'Product not found'}), 404

    user_id = session.get('user_id')
    if user_id:
        # logged in -> store in DB cart
        existing = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
        if existing:
            existing.quantity += quantity
        else:
            db.session.add(Cart(user_id=user_id, product_id=product_id, quantity=quantity))
        db.session.commit()
        return jsonify({'success': True, 'message': 'Product added to cart (DB)!'})
    else:
        # guest -> use session cart
        cart = session_get_cart()
        found = False
        for item in cart:
            if item.get('product_id') == product_id:
                item['quantity'] = item.get('quantity', 1) + quantity
                found = True
                break
        if not found:
            cart.append({'product_id': product_id, 'quantity': quantity})
        session_save_cart(cart)
        return jsonify({'success': True, 'message': 'Product added to cart (session)!'})


@app.route('/api/cart')
def api_cart_get():
    user_id = session.get('user_id')
    if user_id:
        # return DB cart
        cart_items = get_db_cart_items(user_id)
        return jsonify({'cart': cart_items_to_json(cart_items)})
    else:
        # return session cart details (with product info)
        sess = session_get_cart()
        out = []
        for item in sess:
            pid = item.get('product_id')
            qty = item.get('quantity', 1)
            product = Product.query.get(pid)
            if not product:
                continue
            out.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': qty,
                'image': url_for('static', filename=f'images/{product.image}') if product.image else ''
            })
        return jsonify({'cart': out})


@app.route('/api/cart/remove', methods=['POST'])
def api_cart_remove():
    data = request.get_json() or {}
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({'success': False, 'error': 'No product_id provided'}), 400

    user_id = session.get('user_id')
    if user_id:
        item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
        if item:
            db.session.delete(item)
            db.session.commit()
        return jsonify({'success': True})
    else:
        cart = session_get_cart()
        new_cart = [it for it in cart if it.get('product_id') != product_id]
        session_save_cart(new_cart)
        return jsonify({'success': True})


# ==========================================
# 💳 CHECKOUT
# ==========================================
@app.route("/checkout")
def checkout_page():
    return render_template("checkout.html")

@app.route("/api/checkout", methods=["POST"])
def api_checkout():
    data = request.get_json() or {}
    name = data.get('name') or 'Guest'
    address = data.get('address') or ''
    user_id = session.get('user_id')

    # collect cart items depending on guest or logged-in
    cart_entries = []
    total = 0.0

    if user_id:
        db_cart = get_db_cart_items(user_id)
        if not db_cart:
            return jsonify({'error': 'Cart is empty'}), 400
        for item in db_cart:
            product = Product.query.get(item.product_id)
            if not product:
                continue
            subtotal = (product.price or 0) * item.quantity
            total += subtotal
            cart_entries.append({'product': product, 'quantity': item.quantity})
    else:
        sess = session_get_cart()
        if not sess:
            return jsonify({'error': 'Cart is empty'}), 400
        for it in sess:
            product = Product.query.get(it.get('product_id'))
            if not product:
                continue
            qty = int(it.get('quantity', 1))
            subtotal = (product.price or 0) * qty
            total += subtotal
            cart_entries.append({'product': product, 'quantity': qty})

    # Create order
    order = Order(user_id=user_id, customer_name=name, address=address, total=0)
    db.session.add(order)
    db.session.flush()  # get order.id

    # Create order items and remove cart entries
    for entry in cart_entries:
        prod = entry['product']
        qty = entry['quantity']
        oi = OrderItem(order_id=order.id, product_id=prod.id, quantity=qty, price=prod.price)
        db.session.add(oi)
        # remove from DB cart if user logged in
        if user_id:
            db_item = Cart.query.filter_by(user_id=user_id, product_id=prod.id).first()
            if db_item:
                db.session.delete(db_item)

    order.total = total
    db.session.commit()

    # clear session cart if guest
    if not user_id:
        session_save_cart([])

    return jsonify({'message': 'Checkout successful!', 'order_id': order.id, 'total': order.total})


# ==========================================
# USER HOME (after login)
# ==========================================
@app.route('/home_logged')
def home_logged():
    # show products suitable for home (both + home_only)
    products = Product.query.filter(Product.publish_location.in_(['both', 'home_only'])).all()
    return render_template("home_logged.html", products=products)


# ==========================================
# 👑 ADMIN ROUTES
# ==========================================
@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Access denied. Admins only!', 'danger')
        return redirect(url_for('login'))

    products = Product.query.all()
    orders = Order.query.all()
    return render_template('admin/admin_dashboard.html', products=products, orders=orders)

@app.route('/admin/home')
def admin_home():
    if 'user' not in session or not session.get('is_admin'):
        flash("⚠️ Access denied! Admins only.", "danger")
        return redirect(url_for('login'))

    new_messages = Message.query.filter_by(is_read=False).count()
    product_count = Product.query.count()
    order_count = Order.query.count()
    user_count = User.query.count()
    orders = Order.query.order_by(Order.id.desc()).limit(5).all()

    return render_template(
        'admin/admin_home.html',
        product_count=product_count,
        order_count=order_count,
        user_count=user_count,
        orders=orders,
        new_messages=new_messages
    )


# ==========================================
# 🧶 ADD / EDIT / DELETE PRODUCTS
# ==========================================
@app.route('/admin/add_product', methods=['GET', 'POST'])
def add_product():
    if not session.get('is_admin'):
        flash('Access denied. Admins only!', 'danger')
        return redirect(url_for('login'))

    form = ProductForm()

    if form.validate_on_submit():
        filename = None
        if form.image.data:
            image_file = form.image.data
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.root_path, 'static/images', filename)
            image_file.save(image_path)

        new_product = Product(
            name=form.name.data,
            price=form.price.data,
            description=form.description.data,
            image=filename,
            publish_location=form.publish_location.data
        )

        db.session.add(new_product)
        db.session.commit()

        flash('✅ Product added successfully!', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/add_product.html', form=form)


@app.route('/admin/products')
def admin_products():
    if not session.get('is_admin'):
        flash('Access denied. Admins only!', 'danger')
        return redirect(url_for('login'))
    products = Product.query.all()
    return render_template('admin/admin_products.html', products=products)


@app.route('/admin/edit_product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if 'user' not in session or not session.get('is_admin'):
        flash("⚠️ Access denied! Admins only.", "danger")
        return redirect(url_for('login'))

    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    edit_mode = True

    if form.validate_on_submit():
        product.name = form.name.data
        product.price = form.price.data
        product.description = form.description.data
        product.publish_location = form.publish_location.data

        if form.image.data:
            image = form.image.data
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.root_path, 'static/images', filename)
            image.save(image_path)
            product.image = filename

        db.session.commit()
        flash("✅ Product updated successfully!", "success")
        return redirect(url_for('admin_products'))

    return render_template('admin/admin_product.html', form=form, product=product, edit_mode=edit_mode)


@app.route('/admin/delete_product/<int:id>', methods=['POST'])
def delete_product(id):
    if 'user' not in session or not session.get('is_admin'):
        flash("⚠️ Access denied! Admins only.", "danger")
        return redirect(url_for('login'))

    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash(f"🗑️ Product '{product.name}' deleted successfully.", "success")
    return redirect(url_for('admin_products'))


# ==========================================
# 👥 USER MANAGEMENT (admin)
# ==========================================
@app.route('/admin/users')
def admin_users():
    if 'user' not in session or not session.get('is_admin'):
        flash("⚠️ Access denied! Admins only.", "danger")
        return redirect(url_for('login'))

    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')

    users = User.query
    if search:
        users = users.filter((User.username.contains(search)) | (User.email.contains(search)))
    if role_filter:
        users = users.filter_by(role=role_filter)

    users = users.all()
    return render_template('admin/admin_users.html', users=users, search=search, role_filter=role_filter)


@app.route('/admin/make_admin/<int:id>', methods=['POST'])
def make_admin(id):
    user = User.query.get_or_404(id)
    user.role = 'admin'
    db.session.commit()
    flash(f"✅ {user.username} is now an Admin!", "success")
    return redirect(url_for('admin_users'))


@app.route('/admin/demote_user/<int:id>', methods=['POST'])
def demote_user(id):
    user = User.query.get_or_404(id)
    if user.email == 'admin@store.com':
        flash("❌ You cannot demote the main admin.", "danger")
    else:
        user.role = 'user'
        db.session.commit()
        flash(f"⬇ {user.username} has been demoted to User.", "info")
    return redirect(url_for('admin_users'))


@app.route('/admin/delete_user/<int:id>', methods=['POST'])
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.email == 'admin@store.com':
        flash("⚠️ You cannot delete the main admin.", "warning")
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f"🗑️ User {user.username} deleted successfully.", "success")
    return redirect(url_for('admin_users'))


@app.route('/contact', methods=['GET', 'POST'])
def contact_page():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message_text = request.form.get('message')

        new_message = Message(name=name, email=email, message=message_text)
        db.session.add(new_message)
        db.session.commit()

        flash("💖 Your message has been sent successfully!")
        return redirect(url_for('contact_page'))

    return render_template('contact.html')

# 📩 عرض جميع الرسائل في صفحة الإدمن
@app.route('/admin/messages')
def admin_messages():
    if 'user' not in session or not session.get('is_admin'):
        flash("⚠️ Access denied! Admins only.", "danger")
        return redirect(url_for('login'))

    messages = Message.query.order_by(Message.id.desc()).all()
    return render_template('admin/admin_messages.html', messages=messages)




