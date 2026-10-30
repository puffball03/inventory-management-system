import pytest
from pathlib import Path

import inventory_db as db
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
        

