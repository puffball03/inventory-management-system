from contextlib import closing
from pathlib import Path

from inventory_db import DB_PATH, connect, row_counts

SCHEMA_FILE = Path(__file__).parent / "schema.sql"

def create_tables(connection):
    connection.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))


def seed(connection):
    connection.executemany("INSERT INTO suppliers (name) VALUES (?)", 
    [
        ('Tool Company',), 
        ('Computer Company',), 
        ('Food Company',), 
        ('Drink Company',) ])

    connection.executemany("INSERT INTO products (sku, name, category, unit_price, supplier_id, in_stock, reorder_level) VALUES (?, ?, ?, ?, ?, ?, ?)",[
        ('TOO-TOO-001', 'Wrench', 'Tools', 1000, 1, 10, 2 ), 
        ('TOO-TOO-002', 'Hammer', 'Tools', 800, 1, 1, 2 ), #low stock
        ('TOO-TOO-003', 'Mallet', 'Tools', 500, 1, 10, 2 ),
        ('COM-COM-001', 'Monitor', 'Computers', 15000, 2, 4, 2 ),
        ('COM-COM-002', 'Desktop', 'Computers', 40000, 2, 2, 2 ), #low stock
        ('COM-COM-003', 'Mouse', 'Computers', 4000, 2, 14, 3 ),
        ('FOO-FOO-001', 'Chips', 'Food', 400, 3, 12, 4 ),
        ('FOO-FOO-002', 'Candy', 'Food', 200, 3, 25, 5 ),
        ('FOO-FOO-003', 'Tic-Tacs', 'Food', 150, 3, 4, 2 ),
        ('DRI-DRI-001', 'Coke', 'Drink', 399, 4, 24, 6 ),
        ('DRI-DRI-002', 'Sprite', 'Drink', 399, 4, 24, 6 ),
        ('DRI-DRI-003', 'Diet Coke', 'Drink', 399, 4, 24, 6 )
        ])
    connection.executemany("INSERT INTO sales (order_date) VALUES (?)",[
        ('2026-10-20T14:30:00',),
        ('2026-10-19T12:00:00',),
        ('2026-10-14T09:30:00',),
        ('2026-09-23T14:30:00',),
        ('2026-10-25T15:25:00',)
    ])
    connection.executemany("INSERT INTO sale_items (product_id, quantity, price_charged, sale_id) VALUES (?, ?, ?, ?)",[
        (1, 2, 1000, 1),
        (2, 3, 800, 1),
        (2, 6, 800, 2),
        (4, 1, 15000, 2),
        (5, 3, 40000, 2),
        (6, 1, 4000, 2),
        (7, 2, 400, 3),
        (8, 3, 200, 3),
        (9, 3, 150, 4),
        (10, 1, 399, 4),
        (3, 5, 500, 5),
        (10, 2, 399, 5)
    ])

def main():
    with closing(connect(DB_PATH)) as connection:
        create_tables(connection)
        if row_counts(connection)["suppliers"] == 0:
            with connection:
                seed(connection)
        for table, count in row_counts(connection).items():
            print(f"{table}: {count}")

if __name__ == "__main__":
    main()

