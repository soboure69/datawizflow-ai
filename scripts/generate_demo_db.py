from __future__ import annotations

import os
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path


def create_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    cur.execute("PRAGMA foreign_keys = ON;")

    cur.executescript(
        """
        DROP TABLE IF EXISTS sales;
        DROP TABLE IF EXISTS dates;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS regions;

        CREATE TABLE regions (
            region_id INTEGER PRIMARY KEY,
            region_name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            unit_price REAL NOT NULL
        );

        CREATE TABLE dates (
            date TEXT PRIMARY KEY,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            day INTEGER NOT NULL,
            quarter INTEGER NOT NULL
        );

        CREATE TABLE sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_date TEXT NOT NULL,
            region_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            revenue REAL NOT NULL,

            FOREIGN KEY (sale_date) REFERENCES dates(date),
            FOREIGN KEY (region_id) REFERENCES regions(region_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );

        CREATE INDEX idx_sales_date ON sales(sale_date);
        CREATE INDEX idx_sales_region ON sales(region_id);
        CREATE INDEX idx_sales_product ON sales(product_id);
        """
    )
    conn.commit()


def seed_dimensions(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    regions = ["North", "South", "East", "West"]
    cur.executemany(
        "INSERT INTO regions(region_id, region_name) VALUES (?, ?)",
        [(i + 1, name) for i, name in enumerate(regions)],
    )

    products = [
        (1, "Laptop Pro 14", "Tech", 1299.0),
        (2, "Laptop Air 13", "Tech", 999.0),
        (3, "Mouse Wireless", "Tech", 29.0),
        (4, "Keyboard Mechanical", "Tech", 89.0),
        (5, "Desk Basic", "Office", 199.0),
        (6, "Chair Comfort", "Office", 149.0),
        (7, "Notebook A5", "Office", 4.5),
        (8, "Pen Black", "Office", 1.2),
        (9, "Coffee Beans", "Food", 8.9),
        (10, "Tea Green", "Food", 3.5),
    ]
    cur.executemany(
        "INSERT INTO products(product_id, product_name, category, unit_price) VALUES (?, ?, ?, ?)",
        products,
    )

    start = date(2024, 1, 1)
    end = date(2024, 12, 31)
    d = start
    rows = []
    while d <= end:
        q = (d.month - 1) // 3 + 1
        rows.append((d.isoformat(), d.year, d.month, d.day, q))
        d += timedelta(days=1)

    cur.executemany(
        "INSERT INTO dates(date, year, month, day, quarter) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()


def seed_sales(conn: sqlite3.Connection, n_rows: int = 500, seed: int = 42) -> None:
    random.seed(seed)
    cur = conn.cursor()

    # Load dimensions for random choices
    region_ids = [r[0] for r in cur.execute("SELECT region_id FROM regions").fetchall()]
    product_rows = cur.execute("SELECT product_id, unit_price FROM products").fetchall()
    products = [(pid, float(price)) for pid, price in product_rows]
    date_rows = cur.execute("SELECT date FROM dates").fetchall()
    dates = [d[0] for d in date_rows]

    sales = []
    for _ in range(n_rows):
        sale_date = random.choice(dates)
        region_id = random.choice(region_ids)

        product_id, unit_price = random.choice(products)

        # Quantity biased: small items sell more than expensive items
        if unit_price > 500:
            quantity = random.randint(1, 3)
        elif unit_price > 100:
            quantity = random.randint(1, 6)
        else:
            quantity = random.randint(1, 25)

        # Small random "discount noise" included directly in revenue
        discount = random.choice([0.0, 0.0, 0.05, 0.10, 0.15])
        revenue = quantity * unit_price * (1 - discount)

        sales.append((sale_date, region_id, product_id, quantity, revenue))

    cur.executemany(
        """
        INSERT INTO sales(sale_date, region_id, product_id, quantity, revenue)
        VALUES (?, ?, ?, ?, ?)
        """,
        sales,
    )
    conn.commit()


def main() -> None:
    db_url = os.environ.get("DATABASE_URL", "sqlite:///db/demo.db")
    if not db_url.startswith("sqlite:///"):
        raise ValueError("For Phase 1 demo, DATABASE_URL must be sqlite:///...")

    db_path = db_url.replace("sqlite:///", "", 1)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        create_schema(conn)
        seed_dimensions(conn)
        seed_sales(conn, n_rows=500, seed=42)
        print(f"Demo DB created at: {db_path}")
        print("Rows:")
        cur = conn.cursor()
        for table in ["regions", "products", "dates", "sales"]:
            n = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"- {table}: {n}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()