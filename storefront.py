import os
import sqlite3
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

