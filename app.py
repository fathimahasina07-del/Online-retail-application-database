from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database import get_db, init_db
import os

app = Flask(__name__)
app.secret_key = "shopnest_secret_key_2024"

# ─────────────────────────────────────────────
#  HELPER
# ─────────────────────────────────────────────
def current_user():
    return session.get("user_id")

def row_to_dict(row):
    if row is None:
        return None
    return dict(row)

def rows_to_list(rows):
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────
#  PAGE ROUTES
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/product/<int:product_id>")
def product_page(product_id):
    return render_template("product.html", product_id=product_id)

@app.route("/cart")
def cart_page():
    if not current_user():
        return redirect(url_for("login_page"))
    return render_template("cart.html")

@app.route("/checkout")
def checkout_page():
    if not current_user():
        return redirect(url_for("login_page"))
    return render_template("checkout.html")

@app.route("/orders")
def orders_page():
    if not current_user():
        return redirect(url_for("login_page"))
    return render_template("orders.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/search")
def search_page():
    return render_template("search.html")

@app.route("/category/<int:cat_id>")
def category_page(cat_id):
    return render_template("category.html", cat_id=cat_id)


# ─────────────────────────────────────────────
#  AUTH API
# ─────────────────────────────────────────────
@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.json
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip()
    password = data.get("password", "").strip()
    address  = data.get("address", "").strip()
    phone    = data.get("phone", "").strip()

    if not name or not email or not password:
        return jsonify({"success": False, "message": "Name, email and password are required."})

    db = get_db()
    existing = db.execute("SELECT user_id FROM users WHERE email=?", (email,)).fetchone()
    if existing:
        db.close()
        return jsonify({"success": False, "message": "Email already registered. Please login."})

    db.execute(
        "INSERT INTO users (name, email, password, address, phone) VALUES (?,?,?,?,?)",
        (name, email, password, address, phone)
    )
    db.commit()
    user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    db.close()

    session["user_id"]   = user["user_id"]
    session["user_name"] = user["name"]
    session["user_email"]= user["email"]
    return jsonify({"success": True, "message": f"Welcome, {name}!"})


@app.route("/api/login", methods=["POST"])
def api_login():
    data     = request.json
    email    = data.get("email", "").strip()
    password = data.get("password", "").strip()

    db   = get_db()
    user = db.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password)).fetchone()
    db.close()

    if not user:
        return jsonify({"success": False, "message": "Invalid email or password."})

    session["user_id"]   = user["user_id"]
    session["user_name"] = user["name"]
    session["user_email"]= user["email"]
    return jsonify({"success": True, "message": f"Welcome back, {user['name']}!"})


@app.route("/api/logout")
def api_logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/api/me")
def api_me():
    if current_user():
        return jsonify({
            "logged_in": True,
            "user_id":   session["user_id"],
            "name":      session["user_name"],
            "email":     session["user_email"]
        })
    return jsonify({"logged_in": False})


# ─────────────────────────────────────────────
#  PRODUCTS API
# ─────────────────────────────────────────────
@app.route("/api/products")
def api_products():
    db     = get_db()
    limit  = int(request.args.get("limit", 30))
    offset = int(request.args.get("offset", 0))
    rows   = db.execute(
        "SELECT p.*, c.category_name, c.icon FROM products p "
        "JOIN categories c ON p.category_id=c.category_id "
        "ORDER BY p.product_id LIMIT ? OFFSET ?",
        (limit, offset)
    ).fetchall()
    db.close()
    return jsonify(rows_to_list(rows))


@app.route("/api/product/<int:pid>")
def api_product(pid):
    db  = get_db()
    row = db.execute(
        "SELECT p.*, c.category_name, c.icon FROM products p "
        "JOIN categories c ON p.category_id=c.category_id "
        "WHERE p.product_id=?", (pid,)
    ).fetchone()
    reviews = db.execute(
        "SELECT r.*, u.name as user_name FROM reviews r "
        "JOIN users u ON r.user_id=u.user_id "
        "WHERE r.product_id=? ORDER BY r.created_at DESC LIMIT 5", (pid,)
    ).fetchall()
    db.close()
    if not row:
        return jsonify({"error": "Product not found"}), 404
    result = row_to_dict(row)
    result["user_reviews"] = rows_to_list(reviews)
    return jsonify(result)


@app.route("/api/categories")
def api_categories():
    db   = get_db()
    rows = db.execute("SELECT * FROM categories").fetchall()
    db.close()
    return jsonify(rows_to_list(rows))


@app.route("/api/products/category/<int:cat_id>")
def api_products_by_category(cat_id):
    db   = get_db()
    rows = db.execute(
        "SELECT p.*, c.category_name, c.icon FROM products p "
        "JOIN categories c ON p.category_id=c.category_id "
        "WHERE p.category_id=?", (cat_id,)
    ).fetchall()
    db.close()
    return jsonify(rows_to_list(rows))


@app.route("/api/search")
def api_search():
    q  = request.args.get("q", "").strip()
    db = get_db()
    if not q:
        return jsonify([])
    rows = db.execute(
        "SELECT p.*, c.category_name, c.icon FROM products p "
        "JOIN categories c ON p.category_id=c.category_id "
        "WHERE p.name LIKE ? OR p.description LIKE ? OR c.category_name LIKE ?",
        (f"%{q}%", f"%{q}%", f"%{q}%")
    ).fetchall()
    db.close()
    return jsonify(rows_to_list(rows))


# ─────────────────────────────────────────────
#  CART API
# ─────────────────────────────────────────────
@app.route("/api/cart")
def api_cart():
    uid = current_user()
    if not uid:
        return jsonify({"error": "not_logged_in"}), 401
    db   = get_db()
    rows = db.execute(
        "SELECT c.cart_id, c.quantity, p.product_id, p.name, p.price, p.image_url, p.stock "
        "FROM cart c JOIN products p ON c.product_id=p.product_id "
        "WHERE c.user_id=?", (uid,)
    ).fetchall()
    db.close()
    return jsonify(rows_to_list(rows))


@app.route("/api/cart/add", methods=["POST"])
def api_cart_add():
    uid = current_user()
    if not uid:
        return jsonify({"success": False, "message": "Please login to add items to cart."})

    data = request.json
    pid  = data.get("product_id")
    qty  = int(data.get("quantity", 1))

    db = get_db()
    # Check stock
    product = db.execute("SELECT stock FROM products WHERE product_id=?", (pid,)).fetchone()
    if not product or product["stock"] < qty:
        db.close()
        return jsonify({"success": False, "message": "Not enough stock available."})

    existing = db.execute(
        "SELECT cart_id, quantity FROM cart WHERE user_id=? AND product_id=?", (uid, pid)
    ).fetchone()

    if existing:
        new_qty = existing["quantity"] + qty
        db.execute("UPDATE cart SET quantity=? WHERE cart_id=?", (new_qty, existing["cart_id"]))
    else:
        db.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?,?,?)", (uid, pid, qty))

    db.commit()
    # Return updated cart count
    count = db.execute("SELECT SUM(quantity) as total FROM cart WHERE user_id=?", (uid,)).fetchone()
    db.close()
    return jsonify({"success": True, "message": "Added to cart!", "cart_count": count["total"] or 0})


@app.route("/api/cart/update", methods=["POST"])
def api_cart_update():
    uid = current_user()
    if not uid:
        return jsonify({"success": False, "message": "Not logged in."})

    data    = request.json
    cart_id = data.get("cart_id")
    qty     = int(data.get("quantity", 1))

    db = get_db()
    if qty <= 0:
        db.execute("DELETE FROM cart WHERE cart_id=? AND user_id=?", (cart_id, uid))
    else:
        db.execute("UPDATE cart SET quantity=? WHERE cart_id=? AND user_id=?", (qty, cart_id, uid))
    db.commit()
    db.close()
    return jsonify({"success": True})


@app.route("/api/cart/remove", methods=["POST"])
def api_cart_remove():
    uid = current_user()
    if not uid:
        return jsonify({"success": False})
    data    = request.json
    cart_id = data.get("cart_id")
    db = get_db()
    db.execute("DELETE FROM cart WHERE cart_id=? AND user_id=?", (cart_id, uid))
    db.commit()
    db.close()
    return jsonify({"success": True})


@app.route("/api/cart/count")
def api_cart_count():
    uid = current_user()
    if not uid:
        return jsonify({"count": 0})
    db    = get_db()
    row   = db.execute("SELECT SUM(quantity) as total FROM cart WHERE user_id=?", (uid,)).fetchone()
    db.close()
    return jsonify({"count": row["total"] or 0})


# ─────────────────────────────────────────────
#  CHECKOUT / ORDERS API
# ─────────────────────────────────────────────
@app.route("/api/checkout", methods=["POST"])
def api_checkout():
    uid = current_user()
    if not uid:
        return jsonify({"success": False, "message": "Please login to place an order."})

    data           = request.json
    payment_method = data.get("payment_method", "COD")
    shipping_addr  = data.get("address", "").strip()

    if not shipping_addr:
        return jsonify({"success": False, "message": "Please provide a shipping address."})

    db = get_db()
    # Get cart items
    cart_items = db.execute(
        "SELECT c.cart_id, c.quantity, p.product_id, p.name, p.price, p.stock "
        "FROM cart c JOIN products p ON c.product_id=p.product_id "
        "WHERE c.user_id=?", (uid,)
    ).fetchall()

    if not cart_items:
        db.close()
        return jsonify({"success": False, "message": "Your cart is empty."})

    # Validate stock for every item first
    for item in cart_items:
        if item["stock"] < item["quantity"]:
            db.close()
            return jsonify({"success": False, "message": f"'{item['name']}' is out of stock."})

    # Calculate total
    total = sum(item["price"] * item["quantity"] for item in cart_items)

    # Create order
    cursor = db.execute(
        "INSERT INTO orders (user_id, total_amount, status, payment_method, shipping_addr) "
        "VALUES (?,?,?,?,?)",
        (uid, round(total, 2), "Confirmed", payment_method, shipping_addr)
    )
    order_id = cursor.lastrowid

    # Insert order items and reduce stock
    for item in cart_items:
        db.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?,?,?,?)",
            (order_id, item["product_id"], item["quantity"], item["price"])
        )
        db.execute(
            "UPDATE products SET stock = stock - ? WHERE product_id=?",
            (item["quantity"], item["product_id"])
        )

    # Clear cart
    db.execute("DELETE FROM cart WHERE user_id=?", (uid,))
    db.commit()
    db.close()

    return jsonify({
        "success":  True,
        "message":  "Order placed successfully! 🎉",
        "order_id": order_id,
        "total":    round(total, 2)
    })


@app.route("/api/orders")
def api_orders():
    uid = current_user()
    if not uid:
        return jsonify({"error": "not_logged_in"}), 401
    db = get_db()
    orders = db.execute(
        "SELECT * FROM orders WHERE user_id=? ORDER BY ordered_at DESC", (uid,)
    ).fetchall()
    result = []
    for o in orders:
        od = row_to_dict(o)
        items = db.execute(
            "SELECT oi.*, p.name, p.image_url FROM order_items oi "
            "JOIN products p ON oi.product_id=p.product_id "
            "WHERE oi.order_id=?", (o["order_id"],)
        ).fetchall()
        od["items"] = rows_to_list(items)
        result.append(od)
    db.close()
    return jsonify(result)


@app.route("/api/order/<int:order_id>")
def api_order_detail(order_id):
    uid = current_user()
    if not uid:
        return jsonify({"error": "not_logged_in"}), 401
    db    = get_db()
    order = db.execute("SELECT * FROM orders WHERE order_id=? AND user_id=?", (order_id, uid)).fetchone()
    if not order:
        db.close()
        return jsonify({"error": "Order not found"}), 404
    items = db.execute(
        "SELECT oi.*, p.name, p.image_url FROM order_items oi "
        "JOIN products p ON oi.product_id=p.product_id "
        "WHERE oi.order_id=?", (order_id,)
    ).fetchall()
    db.close()
    od = row_to_dict(order)
    od["items"] = rows_to_list(items)
    return jsonify(od)


# ─────────────────────────────────────────────
#  REVIEWS API
# ─────────────────────────────────────────────
@app.route("/api/review/add", methods=["POST"])
def api_add_review():
    uid = current_user()
    if not uid:
        return jsonify({"success": False, "message": "Please login to leave a review."})
    data    = request.json
    pid     = data.get("product_id")
    rating  = int(data.get("rating", 5))
    comment = data.get("comment", "").strip()

    db = get_db()
    db.execute(
        "INSERT INTO reviews (product_id, user_id, rating, comment) VALUES (?,?,?,?)",
        (pid, uid, rating, comment)
    )
    # Update product average rating
    avg = db.execute(
        "SELECT AVG(rating) as avg_r, COUNT(*) as cnt FROM reviews WHERE product_id=?", (pid,)
    ).fetchone()
    db.execute(
        "UPDATE products SET rating=?, reviews=? WHERE product_id=?",
        (round(avg["avg_r"], 1), avg["cnt"], pid)
    )
    db.commit()
    db.close()
    return jsonify({"success": True, "message": "Review submitted!"})


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    if not os.path.exists("shopnest.db"):
        init_db()
    app.run(debug=False, port=5000)
