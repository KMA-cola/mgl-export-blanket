import sqlite3


class DBManager:
    def __init__(self, db_file: str):
        self.db_file = db_file

    # -------------------------
    # Base connection
    # -------------------------
    def connect(self):
        """
        Connect to SQLite and return connection with Row factory
        (row["col"] or row.col style).
        """
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    # -------------------------
    # Products
    # -------------------------
    def get_all_products(self):
        """Active products only."""
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, name_mm, name_en, price, image, short_desc_mm, desc_mm
            FROM products
            WHERE is_active = 1
            ORDER BY id
            """
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_product(self, product_id: int):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, name_mm, name_en, price, image, short_desc_mm, desc_mm
            FROM products
            WHERE id = ?
            """,
            (product_id,),
        )
        row = cur.fetchone()
        conn.close()
        return row

    # -------------------------
    # Orders
    # -------------------------
    def create_order(self, form):
        """Create orders table (if missing) and insert one order."""
        conn = self.connect()
        cur = conn.cursor()

        # create table if not exists
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                customer_name TEXT,
                phone TEXT,
                city TEXT,
                address TEXT,
                qty INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cur.execute(
            """
            INSERT INTO orders (product_id, customer_name, phone, city, address, qty)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                form.get("product_id"),
                form.get("customer_name"),
                form.get("phone"),
                form.get("city"),
                form.get("address"),
                form.get("qty", 1),
            ),
        )

        conn.commit()
        conn.close()

    def get_order(self, order_id: int):
        """Get single order for invoice/receipt."""
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, product_id, customer_name, phone, city, address, qty, created_at
            FROM orders
            WHERE id = ?
            """,
            (order_id,),
        )
        row = cur.fetchone()
        conn.close()
        return row
