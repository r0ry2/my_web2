from flask import render_template, request, jsonify, session, redirect, url_for, flash
from app import app, db, mail
from models import Product, Order, OrderItem, User
from forms import LoginForm, RegisterForm, AddProductForm
from werkzeug.utils import secure_filename
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
import os
from itsdangerous import URLSafeTimedSerializer  # ضيفي هذا الاستيراد فوق في بداية الملف




# 🔐 تشفير الروابط (لتأكيد البريد)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])


# ================== HELPERS ==================
def get_cart():
    return session.get("cart", [])

def save_cart(cart):
    session["cart"] = cart
    session.modified = True


# ================== ROUTES ==================
@app.route('/')
def index():
    return render_template('index.html')


@app.route("/products")
def products_page():
    products = Product.query.all()
    return render_template("products.html", products=products)


@app.route("/cart")
def cart_page():
    return render_template("cart.html")


# ========== LOGIN & REGISTER ==========

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('⚠️ Email already registered!', 'warning')
            return redirect(url_for('register'))

        new_user = User(
            username=form.username.data,
            email=form.email.data
        )
        new_user.set_password(form.password.data)

        # ✅ لو هو الأدمن نفعّله تلقائيًا
        if form.email.data == "admin@store.com":
            new_user.role = 'admin'
            new_user.confirmed = True  

        db.session.add(new_user)
        db.session.commit()

        # ✅ المستخدمين الجدد فقط لازم يأكدون البريد
        if not new_user.confirmed:
            s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
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


# ✅ تأكيد البريد الإلكتروني
@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)  # صالح لمدة ساعة
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
        print("🔍 Trying to log in:", form.email.data)
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            print("✅ User found:", user.email)
            print("🔑 Password correct?", user.check_password(form.password.data))
        else:
            print("❌ No user found.")
            flash('❌ Invalid email or password!', 'danger')
            return render_template('login.html', form=form)

        # ✅ لو المستخدم موجود
        if user.check_password(form.password.data):
            # لو المستخدم عادي وغير مفعل
            if user.role != 'admin' and not getattr(user, "confirmed", True):
                flash('⚠️ Please confirm your email before logging in.', 'warning')
                return redirect(url_for('login'))

            # تسجيل الدخول
            session['user'] = user.username
            session['is_admin'] = (user.role == 'admin')

            print("➡️ Redirecting to:", 'admin_home' if session['is_admin'] else 'index')
            flash(f"Welcome back, {user.username} 💕", "success")

            return redirect(url_for('admin_home') if session['is_admin'] else url_for('index'))


        else:
            flash('❌ Invalid password!', 'danger')

    return render_template('login.html', form=form)




@app.route('/logout')
def logout():
    session.clear()
    flash('👋 You have been logged out.', 'info')
    return redirect(url_for('login'))


# ========== CART ==========
@app.route("/api/cart", methods=["GET"])
def get_cart_items():
    cart = get_cart()
    detailed = []
    total = 0
    for item in cart:
        product = Product.query.get(item["product_id"])
        if product:
            subtotal = product.price * item["quantity"]
            total += subtotal
            detailed.append({
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "quantity": item["quantity"],
                "subtotal": subtotal,
                "image": product.image
            })
    return jsonify({"cart": detailed, "total": total})


@app.route("/api/cart/add", methods=["POST"])
def add_to_cart():
    data = request.get_json()
    pid = data.get("product_id")
    qty = int(data.get("quantity", 1))
    product = Product.query.get(pid)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    cart = get_cart()
    for item in cart:
        if item["product_id"] == pid:
            item["quantity"] += qty
            save_cart(cart)
            return jsonify({"message": "Quantity updated", "cart": cart})
    cart.append({"product_id": pid, "quantity": qty})
    save_cart(cart)
    return jsonify({"message": "Added", "cart": cart})


@app.route("/api/cart/remove", methods=["POST"])
def remove_from_cart():
    data = request.get_json()
    pid = data.get("product_id")
    cart = get_cart()
    new_cart = [item for item in cart if item["product_id"] != pid]
    save_cart(new_cart)
    return jsonify({"message": "Removed", "cart": new_cart})


# ========== CHECKOUT ==========
@app.route("/checkout")
def order_confirmation():
    order_id = request.args.get("id")
    return render_template("checkout.html", order_id=order_id)


@app.route("/api/checkout", methods=["POST"])
def checkout():
    data = request.get_json()
    name = data.get("name", "Guest")
    address = data.get("address", "")
    cart = get_cart()
    if not cart:
        return jsonify({"error": "Cart is empty"}), 400

    total = 0
    order = Order(customer_name=name, address=address, total=0)
    db.session.add(order)
    db.session.flush()

    for item in cart:
        product = Product.query.get(item["product_id"])
        if product:
            subtotal = product.price * item["quantity"]
            total += subtotal
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item["quantity"],
                price=product.price
            )
            db.session.add(order_item)

    order.total = total
    db.session.commit()
    save_cart([])

    return jsonify({"message": "Order created", "order_id": order.id, "total": total})


# ========== ADMIN ==========
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

    # استيراد الموديلات
    from models import Product, Order, User

    # نجلب الإحصائيات
    product_count = Product.query.count()
    order_count = Order.query.count()
    user_count = User.query.count()

    # آخر 5 طلبات مثلاً
    orders = Order.query.order_by(Order.id.desc()).limit(5).all()

    # ✅ نرسلها للقالب الصحيح
    return render_template('admin/admin_home.html',
                           product_count=product_count,
                           order_count=order_count,
                           user_count=user_count,
                           orders=orders)


@app.route('/admin/add_product', methods=['GET', 'POST'])
def add_product():
    if not session.get('is_admin'):
        flash('Access denied. Admins only!', 'danger')
        return redirect(url_for('login'))

    form = AddProductForm()
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
            image=filename
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




# 🧑‍💼 عرض المستخدمين (لصفحة Manage Users)
@app.route('/admin/users')
def admin_users():
    if 'user' not in session or not session.get('is_admin'):
        flash("⚠️ Access denied! Admins only.", "danger")
        return redirect(url_for('login'))

    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')

    users = User.query
    if search:
        users = users.filter(
            (User.username.contains(search)) | (User.email.contains(search))
        )
    if role_filter:
        users = users.filter_by(role=role_filter)

    users = users.all()
    return render_template(
        'admin/admin_users.html',
        users=users,
        search=search,
        role_filter=role_filter
    )


# 🔼 ترقية مستخدم إلى Admin
@app.route('/admin/make_admin/<int:id>', methods=['POST'])
def make_admin(id):
    user = User.query.get_or_404(id)
    user.role = 'admin'
    db.session.commit()
    flash(f"✅ {user.username} is now an Admin!", "success")
    return redirect(url_for('admin_users'))


# 🔽 إرجاع الأدمن إلى User
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


# 🗑️ حذف مستخدم
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



# ✏️ تعديل منتج موجود
@app.route('/admin/edit_product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if 'user' not in session or not session.get('is_admin'):
        flash("⚠️ Access denied! Admins only.", "danger")
        return redirect(url_for('login'))

    from forms import AddProductForm as ProductForm
    from models import Product
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    edit_mode = True

    if form.validate_on_submit():
        product.name = form.name.data
        product.price = form.price.data
        product.description = form.description.data

        # إذا تم رفع صورة جديدة
        if form.image.data:
            image = form.image.data
            image_filename = image.filename
            image_path = os.path.join('static/images', image_filename)
            image.save(image_path)
            product.image = image_filename

        db.session.commit()
        flash("✅ Product updated successfully!", "success")
        return redirect(url_for('admin_products'))


    return render_template(
        'admin/admin_product.html',
        form=form,
        product=product,
        edit_mode=edit_mode
    )
    
    # 🗑️ حذف منتج
@app.route('/admin/delete_product/<int:id>', methods=['POST'])
def delete_product(id):
    if 'user' not in session or not session.get('is_admin'):
        flash("⚠️ Access denied! Admins only.", "danger")
        return redirect(url_for('login'))

    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash(f"🗑️ Product '{product.name}' deleted successfully.", "success")
    return redirect(url_for('admin_dashboard'))

