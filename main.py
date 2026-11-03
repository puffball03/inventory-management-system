import sqlite3
from contextlib import closing

import inventory_db as db
from seed_db import create_tables

VERSION = "1.1.0"
MONEY_COLUMNS = {"unit_price", "stock_value", "revenue"}

def to_cents(text):
    return round(float(text.lstrip("$")) * 100)

#Prompting stuff
def prompt_user(msg, expected=str, required=True):
    while True:
        text = input(f"{msg}\n> ").strip()
        if not text:
            if not required:
                return None
            print("This field is required")
            continue
        try:
            return expected(text)
        except (ValueError, OverflowError):
            print("Invalid Input. Try again.")

def prompt_yes_no(msg):
    answer = prompt_user(f"{msg} (y/n)", required=False) or ""
    return answer.lower().startswith("y")

def format_value(column, value):
    return db.format_cents(value) if column in MONEY_COLUMNS else str(value)

def print_rows(rows):
    if not rows:
        print("Nothing Found")
        return
    columns = rows[0].keys()
    print(" | ".join(columns))
    for row in rows:
        print(" | ".join(format_value(column, row[column]) for column in columns))

#Interacting with the database

def search(connection):
    print_rows(db.search_products(
        connection,
        prompt_user("Search text (blank for all columns)", required=False) or "",
        category=prompt_user("Category (blank for any)", required=False),
        max_price_cents=prompt_user("Max price (blank for all)", to_cents, required=False),
        in_stock_only=prompt_yes_no("In stock only?"),
        low_stock_only=prompt_yes_no("Low stock only?"),
    ))

def lookup(connection):
    product = db.get_product(connection, prompt_user("SKU"))
    print_rows([product] if product else [])

def add_product(connection):
    product_id = db.add_product(
        connection,
        prompt_user("SKU"),
        prompt_user("Name"),
        prompt_user("Category"),
        prompt_user("Supplier id", int),
        prompt_user("Unit price (ex: 12.50)", to_cents),
        prompt_user("Quantity in stock", int),
        prompt_user("Reorder level", int)
    )
    print(f"Added product #{product_id}.")

def restock(connection):
    new_stock = db.restock(
        connection,
        prompt_user("SKU"),
        prompt_user("Amount to add", int),
    )
    print(f"Stock is now {new_stock}.")

def record_a_sale(connection):
    items = []
    while True:
        sku = prompt_user("SKU (blank to finish)", required=False)
        if not sku:
            break
        items.append((sku, prompt_user("Quantity", int)))
    print(f"Recorded sale #{db.record_a_sale(connection, items)}.")


#Reports
REPORTS = {
    "1": ("Stock value by supplier", db.stock_value_by_supplier),
    "2": ("Low stock", db.low_stock),
    "3": ("Sales by product", db.sales_by_product),
    "4": ("Never sold", db.never_sold),
}

def reports(connection):
    for key, (label, _) in REPORTS.items():
        print(f"{key}. {label}")
    choice = prompt_user("Choose a report", required=False)
    if choice in REPORTS:
        print_rows(REPORTS[choice][1](connection))
    else:
        print("Invalid option. Please try again.")

def backup(connection):
    target = db.DB_PATH.parent / "inventory-backup.db"
    db.backup(connection, target)
    integrity, live_counts, backup_counts = db.verify_backup(connection, target)
    print(f"Backed up to {target}")
    print(f"integrity_check: {integrity}")
    print(f"live: {live_counts}")
    print(f"backup: {backup_counts}")

#Menu Logic

MENU = {
    "1": ("Search", search),
    "2": ("Product lookup", lookup),
    "3": ("Add product", add_product),
    "4": ("Restock", restock),
    "5": ("Record a sale", record_a_sale),
    "6": ("Reports", reports),
    "7": ("Backup", backup)
}
QUIT = "8"

def run_action(action, connection):
    try:
        action(connection)
    except db.InventoryError as error:
        print(f"Sorry man: {error}")
    except OverflowError:
        print("NUMBER WAY TOO BIG")
    except sqlite3.Error as error:
        print(f"Database issue: {error}")
    except OSError as error:
        print(f"Could not write the file: {error}")

def show_low_stock_banner(connection):
    count = db.count_low_stock(connection)
    print(f"Low stock: {count} product(s) at or below their reorder level")

def run_menu(connection):
    print(f"Inventory v{VERSION}")
    show_low_stock_banner(connection)
    while True:
        print()
        for key, (label, _) in MENU.items():
            print(f"{key}. {label}")
        print(f"{QUIT}. Quit")
        choice = prompt_user("Choose an option", required=False)
        if choice == QUIT:
            return
        if choice in MENU:
            run_action(MENU[choice][1], connection)
        else:
            print("Invalid option. Please try again.")

def main():
    try:
        with closing(db.connect()) as connection:
            create_tables(connection)
            run_menu(connection)
    except sqlite3.Error as error:
        print(f"Couldnt open the db: {error}")
    except (EOFError, KeyboardInterrupt):
        print("\nCya.")

if __name__ == "__main__":
    main()