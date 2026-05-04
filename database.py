import sqlite3
import os

DB_NAME = "shopnest.db"

def get_db():
    """Connect to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # allows dict-like access
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Create all tables and insert sample data."""
    conn = get_db()
    cursor = conn.cursor()

    # ── USERS TABLE ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            address     TEXT,
            phone       TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── CATEGORIES TABLE ─────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT    NOT NULL UNIQUE,
            icon          TEXT    DEFAULT '📦'
        )
    """)

    # ── PRODUCTS TABLE ───────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT    NOT NULL,
            description  TEXT,
            price        REAL    NOT NULL,
            stock        INTEGER NOT NULL DEFAULT 0,
            category_id  INTEGER,
            image_url    TEXT,
            rating       REAL    DEFAULT 4.0,
            reviews      INTEGER DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
    """)

    # ── CART TABLE ───────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            cart_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity   INTEGER NOT NULL DEFAULT 1,
            added_at   TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id)    REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    # ── ORDERS TABLE ─────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER NOT NULL,
            total_amount   REAL    NOT NULL,
            status         TEXT    DEFAULT 'Pending',
            payment_method TEXT,
            shipping_addr  TEXT,
            ordered_at     TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # ── ORDER ITEMS TABLE ────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            item_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id   INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity   INTEGER NOT NULL,
            price      REAL    NOT NULL,
            FOREIGN KEY (order_id)   REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    # ── REVIEWS TABLE ────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            review_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id    INTEGER NOT NULL,
            rating     INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            comment    TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            FOREIGN KEY (user_id)    REFERENCES users(user_id)
        )
    """)

    conn.commit()

    # ── SEED DATA ────────────────────────────────────────────────
    # Categories
    categories = [
        ("Electronics", "⚡"),
        ("Clothing",    "👕"),
        ("Books",       "📚"),
        ("Home & Kitchen", "🏠"),
        ("Sports",      "⚽"),
        ("Beauty",      "💄"),
        ("Toys",        "🧸"),
        ("Food",        "🍎"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO categories (category_name, icon) VALUES (?, ?)",
        categories
    )

    # Products (30 products across categories)
    products = [
        # Electronics (cat 1)
        ("iPhone 15 Pro", "Latest Apple flagship with titanium design, A17 Pro chip.", 999.99, 50, 1, "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=400", 4.8, 2341),
        ("Samsung 4K TV 55\"", "Crystal clear 4K display with smart features.", 649.99, 30, 1, "https://images.unsplash.com/photo-1593359677879-a4bb92f829e1?w=400", 4.6, 987),
        ("Sony WH-1000XM5", "Industry-leading noise cancelling headphones.", 349.99, 75, 1, "https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?w=400", 4.9, 5621),
        ("MacBook Air M2", "Thin, light, insanely powerful laptop.", 1099.99, 20, 1, "https://images.unsplash.com/photo-1611186871525-9e4bc6e47a24?w=400", 4.7, 1834),
        ("iPad Pro 12.9\"", "The ultimate iPad experience.", 799.99, 40, 1, "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400", 4.5, 762),
        # Clothing (cat 2)
        ("Classic White T-Shirt", "100% cotton premium quality t-shirt.", 29.99, 200, 2, "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400", 4.3, 3421),
        ("Slim Fit Jeans", "Comfortable stretch denim, modern slim fit.", 59.99, 150, 2, "https://images.unsplash.com/photo-1542272604-787c3835535d?w=400", 4.4, 2198),
        ("Running Shoes", "Lightweight performance running shoes.", 89.99, 100, 2, "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400", 4.6, 4532),
        ("Leather Jacket", "Premium genuine leather biker jacket.", 199.99, 45, 2, "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400", 4.7, 891),
        ("Summer Dress", "Floral pattern breathable summer dress.", 49.99, 80, 2, "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=400", 4.2, 1234),
        # Books (cat 3)
        ("Python Programming", "Learn Python from scratch to advanced.", 39.99, 300, 3, "https://images.unsplash.com/photo-1532012197267-da84d127e765?w=400", 4.8, 8921),
        ("The Great Gatsby", "F. Scott Fitzgerald's classic novel.", 12.99, 500, 3, "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400", 4.5, 3421),
        ("Atomic Habits", "Tiny changes, remarkable results.", 16.99, 400, 3, "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=400", 4.9, 12043),
        ("Data Structures", "Complete guide to algorithms and DS.", 49.99, 150, 3, "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400", 4.6, 2341),
        # Home & Kitchen (cat 4)
        ("Air Fryer 5.8L", "Cook healthier meals with 80% less oil.", 89.99, 60, 4, "https://images.unsplash.com/photo-1648476698514-bccc61c9c94e?w=400", 4.7, 6789),
        ("Coffee Maker", "Brew perfect coffee every morning.", 59.99, 80, 4, "https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?w=400", 4.5, 4321),
        ("Non-stick Pan Set", "3-piece professional cookware set.", 79.99, 100, 4, "https://images.unsplash.com/photo-1590794056226-79ef3a8147e1?w=400", 4.4, 2987),
        ("Robot Vacuum", "Smart robotic vacuum with auto-mapping.", 299.99, 35, 4, "https://images.unsplash.com/photo-1589924691995-400dc9ecc119?w=400", 4.6, 1543),
        # Sports (cat 5)
        ("Yoga Mat", "Premium non-slip eco-friendly yoga mat.", 34.99, 120, 5, "https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=400", 4.5, 5678),
        ("Dumbbells Set", "Adjustable weight set 5-50 lbs.", 149.99, 40, 5, "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400", 4.7, 3421),
        ("Bicycle Helmet", "Certified safety helmet with ventilation.", 49.99, 90, 5, "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400", 4.3, 1234),
        # Beauty (cat 6)
        ("Face Moisturizer SPF50", "Daily hydration with sun protection.", 24.99, 200, 6, "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=400", 4.6, 7654),
        ("Vitamin C Serum", "Brightening antioxidant face serum.", 29.99, 150, 6, "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=400", 4.8, 9876),
        ("Hair Dryer Pro", "Professional ionic hair dryer 2000W.", 79.99, 70, 6, "https://images.unsplash.com/photo-1522338242992-e1a54906a8da?w=400", 4.5, 3210),
        # Toys (cat 7)
        ("LEGO City Set", "Build your dream city! 500+ pieces.", 59.99, 80, 7, "https://images.unsplash.com/photo-1587654780291-39c9404d746b?w=400", 4.8, 4532),
        ("RC Car Turbo", "Remote control racing car 40mph.", 49.99, 60, 7, "https://images.unsplash.com/photo-1561037404-61cd46aa615b?w=400", 4.4, 2198),
        # Food (cat 8)
        ("Organic Green Tea", "Premium Darjeeling green tea 100g.", 14.99, 300, 8, "https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=400", 4.6, 8765),
        ("Dark Chocolate Box", "Assorted luxury dark chocolates.", 19.99, 200, 8, "https://images.unsplash.com/photo-1481391319762-47dff72954d9?w=400", 4.7, 5432),
        ("Almond Butter", "Natural creamy almond butter 500g.", 12.99, 150, 8, "https://images.unsplash.com/photo-1608797178974-15b35a64ede9?w=400", 4.5, 3210),
        ("Mixed Nuts Premium", "Roasted salted mixed nuts 1kg.", 24.99, 100, 8, "https://images.unsplash.com/photo-1599599810769-bcde5a160d32?w=400", 4.6, 4321),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO products (name, description, price, stock, category_id, image_url, rating, reviews) VALUES (?,?,?,?,?,?,?,?)",
        products
    )

    # Demo user
    cursor.execute(
        "INSERT OR IGNORE INTO users (name, email, password, address, phone) VALUES (?,?,?,?,?)",
        ("Demo User", "demo@shopnest.com", "demo123", "123 Main Street, Chennai, Tamil Nadu 600001", "+91 98765 43210")
    )

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

if __name__ == "__main__":
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    init_db()
