import os
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

DB_PATH = Path(os.environ.get("INVENTORY_DB", Path(__file__).parent / "inventory.db"))

class InventoryError(Exception):
    """Raised when inventory operations couldn't be completed"""

def connect(path=DB_PATH):
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection

def add_product(connection, sku, name, category, supplier_id, unit_price, in_stock, reorder_level):
    try:
        cursor = connection.execute(
            "INSERT INTO products (sku, name, category, supplier_id, unit_price, in_stock, reorder_level) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (sku, name, category, supplier_id, unit_price, in_stock, reorder_level),
        )
    except sqlite3.IntegrityError as e:
        if "products.sku" in str(e):
            raise InventoryError("Duplicate sku")
        if "products.name" in str(e):
            raise InventoryError("Duplicate name")
        if "FOREIGN" in str(e):
            raise InventoryError("Unknown supplier")
        if "CHECK" in str(e):
            raise InventoryError("Negative number")
        raise InventoryError(f"Product couldn't be added: {e}")

    connection.commit()
    return cursor.lastrowid

def get_product(connection, sku):
    cursor = connection.execute(
        "SELECT p.id, p.sku, p.name, s.name AS supplier, p.category, p.unit_price, p.in_stock, p.reorder_level "
        "FROM products p JOIN suppliers s ON s.id = p.supplier_id "
        "WHERE p.sku = ?",
        (sku,),
    ).fetchone()
    return cursor

def change_price(connection, sku, new_price):
    try:
        cursor = connection.execute(
            "UPDATE products SET unit_price = ? WHERE sku = ? ",
            (new_price, sku),
        )
    except sqlite3.IntegrityError:
        raise InventoryError("Price couldn't be updated. Likely negative")
    connection.commit()
    return cursor.rowcount == 1

def delete_product(connection, sku):
    try:
        cursor = connection.execute(
            "DELETE FROM products WHERE sku = ?", (sku,)
        )
    except sqlite3.IntegrityError:
        raise InventoryError(f"Cant delete product with sku: {sku} as it has already been sold or has a stock_movement")
    connection.commit()
    return cursor.rowcount == 1

def search_products(connection, text="", category=None, max_price_cents=None, in_stock_only=False, low_stock_only=False):
    sql = ("SELECT p.id, p.sku, p.name, s.name AS supplier, p.unit_price, p.in_stock "
           "FROM products p JOIN suppliers s ON s.id = p.supplier_id "
           "WHERE (p.name LIKE ? OR s.name LIKE ? OR p.sku LIKE ?)")
    params = [f"%{text}%", f"%{text}%", f"%{text}%"]
    if category is not None:
        sql += " AND p.category = ?"
        params.append(category)
    if max_price_cents is not None:
        sql += " AND p.unit_price <= ?"
        params.append(max_price_cents)
    if in_stock_only:
        sql += " AND p.in_stock > 0"
    if low_stock_only:
        sql += " AND p.in_stock <= p.reorder_level"
    sql += " ORDER BY p.name"
    return connection.execute(sql, params).fetchall()

#----------Reports----------#
def count_low_stock(connection):
    sql = "SELECT COUNT(*) FROM products WHERE in_stock <= reorder_level"
    return connection.execute(sql).fetchone()[0]

def stock_value_by_supplier(connection):
    sql = ("""
    SELECT s.name AS supplier, SUM(p.unit_price * p.in_stock) AS stock_value
    FROM products p JOIN suppliers s ON s.id = p.supplier_id
    GROUP BY s.id
    ORDER BY stock_value DESC
    """)
    return connection.execute(sql).fetchall()

def low_stock(connection):
    sql = ("""
    SELECT name, sku, in_stock, reorder_level - in_stock AS short_by
    FROM products
    WHERE in_stock <= reorder_level
    ORDER BY short_by DESC
    """)
    return connection.execute(sql).fetchall()

def sales_by_product(connection):
    sql = ("""
    SELECT p.name,
           SUM(si.quantity) AS products_sold,
           SUM(si.quantity * si.price_charged) AS revenue
    FROM products p JOIN sale_items si ON si.product_id = p.id
    GROUP BY p.id
    ORDER BY revenue DESC
    """)
    return connection.execute(sql).fetchall()

def never_sold(connection):
    sql = ("""
    SELECT p.name
    FROM products p
    WHERE NOT EXISTS (
        SELECT 1 FROM sale_items si WHERE si.product_id = p.id
    )
    ORDER BY p.name
    """)
    return connection.execute(sql).fetchall()

#----------Stock-Changes-and-Sales----------#

def record_a_sale(connection, items, order_date=None):
    if not items:
        raise InventoryError("A sale needs at least one item")
    if order_date is None:
        order_date = datetime.now().isoformat(timespec="seconds")
    try:
        with connection:
            cursor = connection.execute(
                "INSERT INTO sales (order_date) VALUES (?)",
                (order_date,),
            )
            order_id = cursor.lastrowid

            seen = set()
            for sku, quantity in items:
                if sku in seen:
                    raise InventoryError(f"Product {sku} is listed twice")
                seen.add(sku)
                product = connection.execute(
                    "SELECT id, unit_price FROM products WHERE sku = ?", (sku,)
                ).fetchone()
                if product is None:
                    raise InventoryError(f"No product with sku {sku}")
                connection.execute(
                    "INSERT INTO sale_items (product_id, quantity, price_charged, sale_id) "
                    "VALUES (?, ?, ?, ?)",
                    (product['id'], quantity, product['unit_price'], order_id)
                )
                connection.execute(
                    "UPDATE products SET in_stock = in_stock - ? WHERE id = ?",
                    (quantity, product['id']),
                )
                connection.execute(
                    "INSERT INTO stock_movements (product_id, signed_change, reason, sold_at) "
                    "VALUES (?, ?, ?, ?)",
                    (product['id'], -quantity, 'sale', order_date)
                )
    except sqlite3.IntegrityError:
        raise InventoryError("Not enough stock for this order")
    
    return order_id
def adjust(connection, sku, change, order_date=None):
    if change == 0:
        raise InventoryError("Can't adjust by nothing STUPID")
    if order_date is None:
        order_date = datetime.now().isoformat(timespec="seconds")
    try:
        with connection:
            product = connection.execute(
                "SELECT id FROM products WHERE sku = ?", (sku,)
            ).fetchone()
            if product is None:
                raise InventoryError(f"No product with sku: {sku}")
            connection.execute(
                "UPDATE products SET in_stock = in_stock + ? WHERE id = ?",
                (change, product['id']),
            )
            connection.execute(
                "INSERT INTO stock_movements (product_id, signed_change, reason, sold_at) "
                "VALUES (?, ?, ?, ?)",
                (product['id'], change, 'adjustment', order_date),
            )
            new_quantity = connection.execute(
                "SELECT in_stock FROM products WHERE sku = ?", (sku,)
            ).fetchone()["in_stock"]
    except sqlite3.IntegrityError:
        raise InventoryError("That adjustment would make the stock negative")

    return new_quantity 

def restock(connection, sku, change, order_date=None):
    if change <= 0:
        raise InventoryError("Restock amount must be positive")
    if order_date is None:
        order_date = datetime.now().isoformat(timespec="seconds")
    try:
        with connection:
            product = connection.execute(
                "SELECT id FROM products WHERE sku = ?", (sku,)
            ).fetchone()
            if product is None:
                raise InventoryError(f"No product with sku: {sku}")
            connection.execute(
                "UPDATE products SET in_stock = in_stock + ? WHERE id = ?",
                (change, product['id']),
            )
            connection.execute(
                "INSERT INTO stock_movements (product_id, signed_change, reason, sold_at) "
                "VALUES (?, ?, ?, ?)",
                (product['id'], change, 'restock', order_date),
            )
            new_quantity = connection.execute(
                "SELECT in_stock FROM products WHERE sku = ?", (sku,)
            ).fetchone()["in_stock"]
    except sqlite3.IntegrityError:
        raise InventoryError("You shouldn't even be here")

    return new_quantity 

TABLE_COUNT_QUERIES = {
    "suppliers": "SELECT COUNT(*) FROM suppliers",
    "products": "SELECT COUNT(*) FROM products",
    "sales": "SELECT COUNT(*) FROM sales",
    "sale_items": "SELECT COUNT(*) FROM sale_items",
    "stock_movements": "SELECT COUNT(*) FROM stock_movements",
}

def row_counts(connection):
    return {table: connection.execute(sql).fetchone()[0] for table, sql in TABLE_COUNT_QUERIES.items()}

def format_cents(cents):
    dollars, remainder = divmod(cents, 100)
    return f"${dollars:,}.{remainder:02d}"

def backup(connection, destination):
    with closing(connect(destination)) as target:
        connection.backup(target)
    return destination
def verify_backup(connection, backup_path):
    with closing(connect(backup_path)) as copy:
        integrity = copy.execute("PRAGMA integrity_check").fetchone()[0]
        return integrity, row_counts(connection), row_counts(copy)

