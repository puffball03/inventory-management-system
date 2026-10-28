# Plan: Inventory Management System

## 1. Tables

### suppliers
| Column | Type | Constraints | Why |
|---|---|---|---|
| ID | INTEGER | PRIMARY KEY | No Duplicate IDs |
| name | TEXT | UNIQUE NOT NULL | No unnamed suppliers, must be unique. |


### products
| Column | Type | Constraints | Why |
|---|---|---|---|
| ID | INTEGER | PRIMARY KEY | No duplicate IDs |
| SKU | TEXT | UNIQUE NOT NULL | each product should have a unique sku, and it shouldnt be null |
| name | TEXT | UNIQUE NOT NULL | no null products and they must be unique |
| category | TEXT | None | dupes ok, null ok.
| supplier | INTEGER | NOT NULL, REFERENCES suppliers(id) | Every product comes from a supplier
| unit price | REAL | NOT NULL CHECK (price >= 0) | everything has a price cash moneyyyy, and that price cash moneyyyy cannot be 0 or < 0
| in_stock | INT | NOT NULL DEFAULT 0 CHECK (in_stock >= 0) | cant be null, starts at 0, must be positive
| reorder level | INT | NOT NULL DEFAULT 0 CHECK (reorder level >= 0) | Cant be null, must be above 0, defaults at reordering when the product is out of stock |



### sales
| Column | Type | Constraints | Why |
|---|---|---|---|
| ID | INTEGER PRIMARY KEY | No duplicate IDs for sales |
| order_date | TEXT NOT NULL | Must have an order date | 


### sale_items
| Column | Type | Constraints | Why |
|---|---|---|---|
| product | INTEGER | NOT NULL, REFERENCES products(id) | each sale contains a product. Must not be null
| quantity | INTEGER | NOT NULL, CHECK (quantity > 0) | cant sell 0 items, cant sell negative items, cant sell null items
| price_charged | REAL | NOT NULL CHECK (price > 0) | cant sell items at a null, 0 or negative price. 

### stock_movements
| Column | Type | Constraints | Why |
|---|---|---|---|
| product |
| signed_change |
| reason |

## 2. Relationships
- One-to-many relationships between tables, and which column is the foreign key
- What happens when someone tries to delete a referenced row

## 3. Indexes
- Which index(es), and which query each one supports

## 4. Public functions

### Products
| Function | Inputs | Returns | Errors raised |
|---|---|---|---|
| add_product | ... | ... | ... |

### Search
### Reports
### Stock changes and sales
### Backup

## 5. Transactions

### Restock
1. Step...
2. Step...
If a step fails: what gets undone

### Adjust
### Record a sale

## 6. Release plan
- v1.0.0: what's included, how it's tagged and built
- v1.1.0: the low stock banner, built on feature/low-stock-banner
- Branch and PR order (the six branches)
- Rollback approach
- Backup and restore approach