# Plan: Inventory Management System

## 1. Tables

### suppliers
| Column | Type | Constraints | Why |
|---|---|---|---|
| id | INTEGER | PRIMARY KEY | No Duplicate IDs |
| name | TEXT | UNIQUE NOT NULL | No unnamed suppliers, must be unique. |


### products
| Column | Type | Constraints | Why |
|---|---|---|---|
| id | INTEGER | PRIMARY KEY | No duplicate IDs |
| SKU | TEXT | UNIQUE NOT NULL | each product should have a unique sku, and it shouldnt be null |
| name | TEXT | UNIQUE NOT NULL | no null products and they must be unique |
| category | TEXT | NOT NULL | dupes ok.
| supplier_id | INTEGER | NOT NULL, REFERENCES suppliers(id) | Every product comes from a supplier
| unit_price | INTEGER | NOT NULL CHECK (unit_price >= 0) | everything has a price cash moneyyyy, and that price cash moneyyyy cannot be 0 or < 0
| in_stock | INT | NOT NULL DEFAULT 0 CHECK (in_stock >= 0) | cant be null, starts at 0, must be positive
| reorder_level | INT | NOT NULL DEFAULT 0 CHECK (reorder_level >= 0) | Cant be null, must be at or above 0, defaults at reordering when the product is out of stock |



### sales
| Column | Type | Constraints | Why |
|---|---|---|---|
| id | INTEGER | PRIMARY KEY | No duplicate IDs for sales |
| order_date | TEXT | NOT NULL | Must have an order date | 


### sale_items
| Column | Type | Constraints | Why |
|---|---|---|---|
| id | INTEGER | PRIMARY KEY | No duplicate IDs for sale_items |
| product_id | INTEGER | NOT NULL, REFERENCES products(id) | each sale contains a product. Must not be null
| quantity | INTEGER | NOT NULL, CHECK (quantity > 0) | cant sell 0 items, cant sell negative items, cant sell null items
| price_charged | INTEGER | NOT NULL, CHECK (price_charged >= 0) | cant sell items at a null, 0 or negative price.
| sale_id | INT | NOT NULL, REFERENCES sales(ID) | reference to the actual sale

### stock_movements
| Column | Type | Constraints | Why |
|---|---|---|---|
| id | INTEGER | PRIMARY KEY | No duplicate IDs
| product_id | INTEGER | NOT NULL, REFERENCES products(id) | each movement references a product |
| signed_change | INTEGER | NOT NULL, CHECK (signed_change != 0)| can be pos or neg but not 0, amount product should be updated by |
| reason | TEXT | NOT NULL, CHECK (reason IN ('restock', 'adjustment', 'sale')) | Must have some reason |
| sold_at | TEXT | NOT NULL | Each stock movement must have happened on a particular date |

## 2. Relationships
- One-to-many relationships between tables, and which column is the foreign key

One supplier has many products; each product stores supplier_id
One sales has many sale_items; each sale_items stores sale_id
One product has many sale_items; each sale_items stores product_id
One product has many stock_movements; each stock_movements stores product_id

- What happens when someone tries to delete a referenced row

## 3. Indexes
- Which index(es), and which query each one supports

Index on supplier_id supports product lookup, search by supplier name, stock value report
product_id: sales-by-product report, never-sold report, delete check

## 4. Public functions

### Setup
| Function | Inputs | Returns | Errors raised |
|---|---|---|---|
| connect | db_path | sqlite3.Connection w foreign keys on, rows readable by column name | none |

### Products
| Function | Inputs | Returns | Errors raised |
|---|---|---|---|
| add_product | conn, sku, name, category, supplier_id, price_cents, quantity, reorder_level| new product id (int) | InventoryError if SKU or name are already used, supplier doesnt exist, or price, quantity, or reorder_level are negative |
| get_product | conn, sku | one row with the product's fields, plus the supplier name, or None if none found | none |
| change_price | conn, sku, new_price_cents | True/False | InventoryError for negative price
| delete_product | conn, sku | bool(true/false depending on if sku is found) | InventoryError if the product has been sold |

### Search
| Function | Inputs | Returns | Errors raised |
|---|---|---|---|
| search_product | conn, text, category=None, max_price=None, in_stock_only=False, low_stock_only=False | list of rows sorted by product name | none |

### Reports
| Function | Inputs | Returns | Errors raised |
|---|---|---|---|
| stock_value_by_supplier | conn | rows of(supplier name, total stock value in cents), descending order | none |
| low_stock | conn | rows of(product name, num below reorder level), most units short first | none |
| sales_by_product | conn | rows of(product name, revenue in cents, units sold), highest revenue first | none |
| never_sold | conn | rows of(product name), sorted by name (A to Z) | none |

### Stock changes and sales
| Function | Inputs | Returns | Errors raised |
|---|---|---|---|
| restock | conn, sku, quantity, now=None | product quantity | InventoryError if sku cant be found, quantity is <= 0
| adjust | conn, sku, signed quantity, now=None | product quantity | InventoryError if sku cant be found, product would be negative
| record_a_sale | conn, items (list of (sku, quantity) pairs), now=None | new sale id (int) | InventoryError “nothing is saved” if not enough stock, any unknown sku, same sku twice |


### Backup
| Function | Inputs | Returns | Errors raised |
|---|---|---|---|
| backup | conn, path | path | InventoryError if backup cant be written |

## 5. Transactions

### Restock
all steps run inside one with conn: block
1. Lookup the item by sku. If it doesn't exist, raise InventoryError
2. Increment the product quantity by the specified amount. Raise InventoryError if the amount is 0 or negative
3. insert a stock_movements row with reason restock, positive change, and the time

If step 3 fails, the quantity increased from step 2 is rolled back.

### Adjust
all steps run inside one with conn: block
1. Lookup the item by sku. If it doesn't exist, raise an InventoryError
2. Increment the product quantity by the signed amount. Raise InventoryError if the amount is 0 or if the stock goes negative
3. Insert a stock_movements row with reason adjustment, pos or negative change, and the time.

If step 3 fails, the quantity adjustment from step 2 is rolled back.

### Record a sale
all steps run inside one with conn: block

1. Create a new sales row containing the date

for each item
2. Lookup sku. Raise InventoryError if none exists for any or if the same appears twice.
3. Reduce the product quantity by the sold amount. InventoryError if there isn't enough stock for the sale
4. Create a new sale_items row for each containing the product, quantity sold, and unit price  InventoryError if quantity sold is 0 or negative.
5. Insert a new stock_movements row with reason sale, the negative change, and the time.
If any line fails, everything is rolled back.

## 6. Release plan
- v1.0.0: what's included, how it's tagged and built
1.0.0 Includes a complete sqlite3 database with all tables and their corresponding functions. It contains a seed_db script that will seed the database. A dockerfile will containerize everything. Tagged 1.0.0 after 5th git PR.
- v1.1.0: the low stock banner, built on feature/low-stock-banner with a changelog entry

v1.0.0: Git tag v1.0.0 and Docker image tag 1.0.0
v1.1.0: Git tag v1.1.0 and Docker image tag 1.1.0

- Branch and PR order (the six branches)
feature/database-and-seed
feature/products-and-search
feature/reports
feature/stock-and-sales
feature/menu-and-container
feature/low-stock-banner
- Rollback approach
Backup the database first
stop the container running 1.1.0
start a new container attached to the same db running 1.0.0
check the row counts to make sure it aligns with the backup
- Backup approach
Choose the menu's backup option
The function uses the builtin .backup() function to copy the live db into a file
Run PRAGMA integrity_check and confirm the row counts match the original

- Restore approach
Stop the container if it is running
Copy the backup file into the docker volume over the database file. 
Start the program and verify rowcount

