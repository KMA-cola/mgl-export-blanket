from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)
from functools import wraps
import sqlite3

from db_manager import DBManager

# -------------------------------------------------
# Flask app setup
# -------------------------------------------------
app = Flask(__name__)
app.secret_key = "mgl_export_blanket_secret_key"

# SQLite DB manager
db_manager = DBManager("mgl_blanket.db")

# -------------------------------------------------
# Admin config
# -------------------------------------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "mgl12345"  # later you can change


def is_admin() -> bool:
    """Check admin login flag in session."""
    return session.get("is_admin") is True


def admin_required(view_func):
    """Decorator to protect admin routes."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not is_admin():
            flash("Admin Login လုပ်ရမယ်။")
            return redirect(url_for("admin_login"))
        return view_func(*args, **kwargs)

    return wrapper


# =================================================
# Public pages
# =================================================
@app.route("/")
def index():
    # All active products
    products = db_manager.get_all_products()
    featured_products = products[:3]  # first 3 as featured

    return render_template("index.html", featured_products=featured_products)


@app.route("/products")
def products():
    products = db_manager.get_all_products()
    return render_template("products.html", products=products)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = db_manager.get_product(product_id)
    if not product:
        flash("ရွေးချယ်ထားသော စောင်ကို မတွေ့ဘူးပါ။")
        return redirect(url_for("products"))
    return render_template("product_detail.html", product=product)


@app.route("/about")
def about():
    return render_template("about.html")


# ---------------------------
# Order pages
# ---------------------------
@app.route("/order", methods=["GET"])
def order_page():
    product_id = request.args.get("product_id", type=int)
    products = db_manager.get_all_products()
    selected_product = db_manager.get_product(product_id) if product_id else None

    return render_template(
        "order.html",
        products=products,
        selected_product=selected_product,
    )


@app.route("/order", methods=["POST"])
def submit_order():
    # DB ထဲကို order သိမ်း
    db_manager.create_order(request.form)

    flash(
        "မှာယူချက်ကို လက်ခံပြီးပါပြီ။ "
        "Viber / ဖုန်းနဲ့ ပြန်အတည်ပြုပေးမယ် ဖြစ်ပါတယ်။"
    )
    return redirect(url_for("index"))


# =================================================
# Admin authentication
# =================================================
@app.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["is_admin"] = True
            flash("Admin အဖြစ် login ဝင်ပြီးပါပြီ။")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Username / Password မှားနေပါတယ်။")

    return render_template("login.html")


@app.route("/logout")
def admin_logout():
    session.clear()
    flash("Logout ပြီးပါပြီ။")
    return redirect(url_for("index"))


# =================================================
# Admin panel
# =================================================
@app.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin_dashboard.html")


@app.route("/admin/products")
@admin_required
def admin_products():
    products = db_manager.get_all_products()
    return render_template("admin_products.html", products=products)


def fetch_all_orders():
    """orders table ကို simple list နဲ့ဖတ်တဲ့ helper."""
    conn = sqlite3.connect("mgl_blanket.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id,
               product_id,
               customer_name,
               phone,
               city,
               address,
               qty,
               created_at
        FROM orders
        ORDER BY created_at DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


@app.route("/admin/orders")
@admin_required
def admin_orders():
    orders = fetch_all_orders()
    return render_template("admin_orders.html", orders=orders)


# =================================================
# Invoice / Receipt preview
# =================================================
@app.route("/admin/orders/<int:order_id>/invoice", methods=["GET", "POST"])
@admin_required
def admin_order_invoice(order_id):
    order = db_manager.get_order(order_id)
    if not order:
        flash("အဲ့ order ကို မတွေ့နိုင်ပါ။")
        return redirect(url_for("admin_orders"))

    product = db_manager.get_product(order["product_id"])
    qty = order["qty"]
    default_unit_price = product["price"] if product else 0

    if request.method == "POST":
        # unit_price
        try:
            unit_price = float(request.form.get("unit_price") or default_unit_price)
        except ValueError:
            unit_price = default_unit_price

        # amount_paid
        try:
            amount_paid = float(request.form.get("amount_paid") or 0)
        except ValueError:
            amount_paid = 0

        payment_mode = request.form.get("payment_mode") or "order_only"

        total_amount = unit_price * qty
        balance = total_amount - amount_paid

        # Full paid လို့ရွေးရင် / balance မရှိတော့ရင် PAID သတ်မှတ်
        is_paid = payment_mode == "full_paid" or balance <= 0.001

        return render_template(
            "admin_invoice.html",
            order=order,
            product=product,
            qty=qty,
            unit_price=unit_price,
            total_amount=total_amount,
            amount_paid=amount_paid,
            balance=balance,
            payment_mode=payment_mode,
            is_paid=is_paid,
        )

    # GET – default preview
    total_amount = default_unit_price * qty
    return render_template(
        "admin_invoice.html",
        order=order,
        product=product,
        qty=qty,
        unit_price=default_unit_price,
        total_amount=total_amount,
        amount_paid=0,
        balance=total_amount,
        payment_mode="order_only",
        is_paid=False,
    )


# =================================================
# Run server
# =================================================
if __name__ == "__main__":
    print(">>> MGL Blanket Flask app starting...")
    app.run(debug=True)
