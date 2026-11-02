import inventory_db as db

VERSION = "1.0.0"
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
    columns = row[0].keys()
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
        prompt_user("Supplier id", int)
        prompt_user("Unit price (ex: 12.50)", to_cents),
        prompt_user("Quantity in stock", int),
        prompt_user("Reorder level", int)
    )
    print(f"Added product #{product_id}.")

def main():
    with closing(db.connect()) as connection:
        while True:
            print("\n1. Search 2. Product_Lookup 3. Add_Product, 4. Restock 5. Record_Sale 6. Reports 7. Backup 8. Quit")
            choice = input("> ").strip().lower()
            if choice == "1":
                pass
            if choice == "2":
                pass
            else:
                print("Invalid option. Please try again.")
