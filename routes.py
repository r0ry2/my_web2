from flask import render_template, request, jsonify, session, redirect, url_for, flash
from app import app, db
from models import Product, Order, OrderItem, User
from forms import LoginForm, RegisterForm, AddProductForm
from werkzeug.utils import secure_filename
import os

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

        if form.email.data == "admin@store.com":
            new_user.role = 'admin'

        db.session.add(new_user)
        db.session.commit()
        flash('✅ Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    # فقط GET → نعرض النموذج
    return render_template('register.html', form=form)



@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        print("🔍 Trying to log in:", form.email.data)  # debug
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            print("✅ User found:", user.email)
        else:
            print("❌ No user found.")

        if user and user.check_password(form.password.data):
            session['user'] = user.username
            session['is_admin'] = (user.role == 'admin')
            print("✅ Login success! Redirecting...")
            flash(f"Welcome back, {user.username} 💕", "success")
            return redirect(url_for('admin_dashboard') if session['is_admin'] else url_for('index'))
        else:
            print("❌ Login failed (wrong password or no user)")
            flash('❌ Invalid email or password!', 'danger')
    return render_template('login.html', form=form)



@app.route('/logout')
def logout():
    session.clear()
    flash('👋 You have been logged out.', 'info')
    return redirect(url_for('login'))


# ========== CART API ==========
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


# ========== ERROR HANDLERS ==========
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template("500.html"), 500


# ========== ADMIN ==========
@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Access denied. Admins only!', 'danger')
        return redirect(url_for('login'))

    products = Product.query.all()
    orders = Order.query.all()

    # ✅ أضف هذا السطر
    form = AddProductForm()

    return render_template('admin/admin_dashboard.html', products=products, orders=orders, form=form)

@app.route('/admin/home')
def admin_home():
    if not session.get('is_admin'):
        flash('Access denied. Admins only!', 'danger')
        return redirect(url_for('login'))

    product_count = Product.query.count()
    order_count = Order.query.count()
    user_count = User.query.count()
    orders = Order.query.order_by(Order.id.desc()).limit(5).all()

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
        return redirect(url_for('products_page'))  # <<< يودينا صفحة المنتجات

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
    if not session.get('is_admin'):
        flash('Access denied. Admins only!', 'danger')
        return redirect(url_for('login'))

    product = Product.query.get_or_404(id)
    form = AddProductForm(obj=product)

    if form.validate_on_submit():
        product.name = form.name.data
        product.price = form.price.data
        product.description = form.description.data

        if form.image.data:
            image_file = form.image.data
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.root_path, 'static/images', filename)
            image_file.save(image_path)
            product.image = filename

        db.session.commit()
        flash('✅ Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/add_product.html', form=form, edit_mode=True)


@app.route('/admin/delete_product/<int:id>', methods=['POST'])
def delete_product(id):
    if not session.get('is_admin'):
        flash('Access denied. Admins only!', 'danger')
        return redirect(url_for('login'))

    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('🗑️ Product deleted successfully!', 'info')
    return redirect(url_for('admin_products'))
