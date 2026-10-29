import pytest
import sqlite3
from pathlib import Path

import storefront as db
from seed_db import seed

PROJECT_FOLDER = Path(__file__).parent.parent

@pytest.fixture
def connection():
    con = db.connect(":memory:")
    con.executescript((PROJECT_FOLDER / "schema.sql").read_text(encoding="utf-8"))
    seed(con)
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
