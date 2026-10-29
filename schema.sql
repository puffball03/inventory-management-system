CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    sku TEXT UNIQUE NOT NULL,
    name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    unit_price INTEGER NOT NULL CHECK (unit_price >= 0),
    in_stock INTEGER NOT NULL DEFAULT 0 CHECK (in_stock >= 0),
    reorder_level INTEGER NOT NULL DEFAULT 0 CHECK (reorder_level >= 0)
) STRICT;

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY,
    order_date TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS sale_items (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price_charged INTEGER NOT NULL CHECK (price_charged >= 0),
    sale_id INTEGER NOT NULL REFERENCES sales(id)
) STRICT;

CREATE TABLE IF NOT EXISTS stock_movements (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    signed_change INTEGER NOT NULL CHECK (signed_change <> 0),
    reason TEXT NOT NULL CHECK (reason IN('restock', 'adjustment', 'sale')),
    sold_at TEXT NOT NULL 
) STRICT;

CREATE INDEX IF NOT EXISTS idx_products_supplier_id
ON products(supplier_id);

CREATE INDEX IF NOT EXISTS idx_sale_items_product_id
ON sale_items(product_id);