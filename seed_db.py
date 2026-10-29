import sqlite3

connection = sqlite3.connect("inventory.db")
connection.execute("PRAGMA foreign_keys = ON")
connection.executescript((folder / "schema.sql").read_text(encoding="utf-8"))

suppliers = [('Nestle',), ('Blackwater Friendship Fund',), ('Theranos',), ('FTX',) ]
connection.executemany("INSERT INTO suppliers (name) VALUES (?)", suppliers)