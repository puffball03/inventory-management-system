from pathlib import Path

import pytest

import inventory_db as db
import main as menu
from seed_db import seed

PROJECT_FOLDER = Path(__file__).parent.parent

@pytest.fixture
def connection():
    con = db.connect(":memory:")
    con.executescript((PROJECT_FOLDER / "schema.sql").read_text(encoding="utf-8"))
    with con: seed(con)
    yield con
    con.close()

def test_change_price_updates_price(connection):
    sku = 'TOO-TOO-001'
    assert db.change_price(connection, sku, 1200) is True
    assert db.get_product(connection, sku)["unit_price"] == 1200

def test_change_price_on_wrong_sku_fails(connection):
    sku = 'TOO-TOO-000'
    assert db.change_price(connection, sku, 1200) is False

def test_search_text_is_never_run_as_sql(connection):
    assert db.search_products(connection, "'; DROP TABLE products; --") == []
    assert len(db.search_products(connection, "Mallet")) == 1

def test_delete_wrong_sku_fails(connection):
    assert db.delete_product(connection, "LOL") is False

def snapshot(connection):
    counts = (
        connection.execute("SELECT COUNT(*) FROM sales").fetchone()[0],
        connection.execute("SELECT COUNT(*) FROM sale_items").fetchone()[0],
        connection.execute("SELECT COUNT(*) FROM stock_movements").fetchone()[0],
    )
    stock = connection.execute("SELECT sku, in_stock FROM products ORDER BY sku").fetchall()
    return counts, [tuple(row) for row in stock]

def test_low_stock(connection):
    rows = db.low_stock(connection)
    assert [tuple(row) for row in rows] == [
        ("Hammer", "TOO-TOO-002", 1, 1),
        ("Desktop", "COM-COM-002", 2, 0),
    ]
def test_stock_value_by_supplier(connection):
    rows = db.stock_value_by_supplier(connection)
    assert [tuple(row) for row in rows] == [
        ("Computer Company", 196000),
        ("Drink Company", 28728),
        ("Tool Company", 15800),
        ("Food Company", 10400),
    ]
def test_sales_by_product(connection):
    rows = db.sales_by_product(connection)
    assert [tuple(row) for row in rows] == [
        ("Desktop", 3, 120000),
        ("Monitor", 1, 15000),
        ("Hammer", 9, 7200),
        ("Mouse", 1, 4000),
        ("Mallet", 5, 2500),
        ("Wrench", 2, 2000),
        ("Coke", 3, 1197),
        ("Chips", 2, 800),
        ("Candy", 3, 600),
        ("Tic-Tacs", 3, 450)
        ]
def test_never_sold(connection):
    rows = db.never_sold(connection)
    assert [tuple(row) for row in rows] == [
        ("Diet Coke",),
        ("Sprite",)
    ]
    
def test_record_a_sale(connection):
    sale_id = db.record_a_sale(connection, [("TOO-TOO-001", 2)])

    lines = connection.execute(
        "SELECT p.sku, si.quantity, si.price_charged "
        "FROM sale_items si JOIN products p ON p.id = si.product_id "
        "WHERE si.sale_id = ?",
        (sale_id,),
    ).fetchall()

    assert [tuple(line) for line in lines] == [("TOO-TOO-001", 2, 1000)]
    assert db.get_product(connection, "TOO-TOO-001")["in_stock"] == 8

def test_adjust_of_zero_is_refused(connection):
    with pytest.raises(db.InventoryError):
        db.adjust(connection, "TOO-TOO-001", 0)

def test_restock_unknown_product_is_refused(connection):
    before = snapshot(connection)
    with pytest.raises(db.InventoryError):
        db.restock(connection, "NOPE-000", 5)
    assert snapshot(connection) == before

def test_empty_sale_is_refused(connection):
    with pytest.raises(db.InventoryError) as e:
        db.record_a_sale(connection, [])
    assert str(e.value) == "A sale needs at least one item"

def test_duplicate_sku_refused(connection):
    with pytest.raises(db.InventoryError) as e:
        db.add_product(connection, 'TOO-TOO-001', "bruh", 'Tools', 800, 2, 10, 2)
    assert str(e.value) == "Duplicate sku"

def test_restock_0_items_is_refused(connection):
    before = snapshot(connection)
    with pytest.raises(db.InventoryError):
        db.restock(connection, "Wrench", 0)
    assert snapshot(connection) == before

def test_format_cents():
    assert db.format_cents(180000) == "$1,800.00"
    assert db.format_cents(505) == "$5.05"
        

def test_add_product_returns_new_id(connection):
    assert db.add_product(connection, "TOO-TOO-004", "Saw", "Tools", 1, 1500, 5, 1) == 13

def test_add_product_with_unknown_supplier_refuses(connection):
    with pytest.raises(db.InventoryError):
        db.add_product(connection, "TOO-TOO-004", "Saw", "Tools", 99, 1500, 5, 1)

def test_sold_product_cant_be_deleted(connection):
    assert db.delete_product(connection, "DRI-DRI-002") is True
    assert db.get_product(connection, "DRI-DRI-002") is None

def names(rows):
    return [row["name"] for row in rows]

def test_search_category_filter(connection):
    assert names(db.search_products(connection, category="Tools")) == ["Hammer", "Mallet", "Wrench"]

def test_search_max_price_filter(connection):
    assert names(db.search_products(connection, max_price_cents=200)) == ["Candy", "Tic-Tacs"]

def test_search_in_stock_only_filter(connection):
    db.add_product(connection, "TOO-TOO-004", "Saw", "Tools", 1, 1500, 0, 1)
    assert "Saw" not in names(db.search_products(connection, in_stock_only=True))

def test_search_low_stock_only_filter(connection):
    assert names(db.search_products(connection, low_stock_only=True)) == ["Desktop", "Hammer"]

def test_search_filters_combined(connection):
    assert names(db.search_products(connection, category="Tools", low_stock_only=True)) == ["Hammer"]

def test_restock_negative_amount_is_refused(connection):
    with pytest.raises(db.InventoryError):
        db.restock(connection, "TOO-TOO-002", -5)

@pytest.mark.parametrize("price, quantity", [(-1, 5), (1500, -1)])
def test_add_product_negative_price_or_quantity_gets_refused(connection, price, quantity):
    with pytest.raises(db.InventoryError):
        db.add_product(connection, "TOO-TOO-004", "Saw", "Tools", 1, price, quantity, 1)

def test_never_sold_can_be_deleted(connection):
    assert db.delete_product(connection, "DRI-DRI-002") is True
    assert db.get_product(connection, "DRI-DRI-002") is None

def test_sale_that_fails_halfway_changes_nothing(connection):
    before = snapshot(connection)
    with pytest.raises(db.InventoryError):
        db.record_a_sale(connection, [("TOO-TOO-001", 2), ("TOO-TOO-002", 50)])
    assert snapshot(connection) == before

def test_sale_of_unknown_product_changes_nothing(connection):
    before = snapshot(connection)
    with pytest.raises(db.InventoryError):
        db.record_a_sale(connection, [("TOO-TOO-001", 2), ("LOLLMAOEVEN", 1)])
    assert snapshot(connection) == before

def test_count_low_stock(connection):
    assert db.count_low_stock(connection) == 2
def test_banner_shows_low_stock_count(connection, capsys):
    menu.show_low_stock_banner(connection)
    assert "Low stock: 2 product(s)" in capsys.readouterr().out