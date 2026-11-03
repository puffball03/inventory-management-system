# Inventory-management-system
A terminal inventory system using sqlite3. It manages products and suppliers, searches with filters, records restocks, adjustments, and sales,
runs four reports, and supports backups.

## How to run

Requires python 3.12 and SQLite 3.37 or newer
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed_db.py
python main.py
```

`seed_db.py` should print:

```
suppliers: 4
products: 12
sales: 5
sale_items: 12
stock_movements: 0
```

## How to run the tests

```
pytest -q
ruff check .
```

## Expected report results

**Stock value by supplier**

| Supplier | Stock value |
|---|---|
| Computer Company | $1,960.00 |
| Drink Company | $287.28 |
| Tool Company | $158.00 |
| Food Company | $104.00 |

**Low stock**

| Product | SKU | In stock | Units short |
|---|---|---|---|
| Hammer | TOO-TOO-002 | 1 | 1 |
| Desktop | COM-COM-002 | 2 | 0 |

**Sales by product**

| Product | Units sold | Revenue |
|---|---|---|
| Desktop | 3 | $1,200.00 |
| Monitor | 1 | $150.00 |
| Hammer | 9 | $72.00 |
| Mouse | 1 | $40.00 |
| Mallet | 5 | $25.00 |
| Wrench | 2 | $20.00 |
| Coke | 3 | $11.97 |
| Chips | 2 | $8.00 |
| Candy | 3 | $6.00 |
| Tic-Tacs | 3 | $4.50 |

**Never sold:** Diet Coke, Sprite

## What happens when a sale fails halfway

The call below sells 2 Wrenches and then 5 Hammers when only 1 is in stock:

`record_a_sale(connection, [("TOO-TOO-001", 2), ("TOO-TOO-002", 5)])`

```
BEFORE {'suppliers': 4, 'products': 12, 'sales': 5, 'sale_items': 12, 'stock_movements': 0} [('TOO-TOO-001', 10), ('TOO-TOO-002', 1)]
ERROR: Not enough stock for this order
AFTER {'suppliers': 4, 'products': 12, 'sales': 5, 'sale_items': 12, 'stock_movements': 0} [('TOO-TOO-001', 10), ('TOO-TOO-002', 1)]
```

The Wrench line had already been written when the Hammer line failed. All the steps run inside one `with connection:` block, so the error rolled everything back: no sale row, no lines, no movements and no stock change.

## Backup and restore

**To back up:** choose `7. Backup` in the menu. It uses SQLite's backup function to write `inventory-backup.db` next to the database, and each backup replaces the last one.

```
Backed up to /data/inventory-backup.db
integrity_check: ok
live: {'suppliers': 4, 'products': 12, 'sales': 5, 'sale_items': 12, 'stock_movements': 1}
backup: {'suppliers': 4, 'products': 12, 'sales': 5, 'sale_items': 12, 'stock_movements': 1}
```

The copy passes `PRAGMA integrity_check` and has the same row counts as the original.

**To restore:** stop any running containers, copy the backup over the database, then start the program and check the row counts.

```
docker run --rm -v inventory-data:/data inventory:1.0.0 cp /data/inventory-backup.db /data/inventory.db
```

## Configuration
| Variable | Purpose | Default |
|---|---|---|
| INVENTORY_DB | Path to the database file | inventory.db |

## Deploy with Docker
```
docker build -t inventory:1.0.0 .
docker volume create inventory-data
docker run --rm -v inventory-data:/data inventory:1.0.0 python seed_db.py
docker run -it --rm -v inventory-data:/data inventory:1.0.0
```

## Image build output
Below is the real output of building the image using docker build -t inventory:1.0.0 .
```
docker build --no-cache -t inventory:1.0.0 .
[+] Building 7.5s (10/10) FINISHED                                                                                                           docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                                         0.0s
 => => transferring dockerfile: 296B                                                                                                                         0.0s
 => [internal] load metadata for docker.io/library/python:3.12.7-slim                                                                                        0.2s
 => [internal] load .dockerignore                                                                                                                            0.0s
 => => transferring context: 122B                                                                                                                            0.0s
 => [1/5] FROM docker.io/library/python:3.12.7-slim@sha256:60d9996b6a8a3689d36db740b49f4327be3be09a21122bd02fb8895abb38b50d                                  0.0s
 => => resolve docker.io/library/python:3.12.7-slim@sha256:60d9996b6a8a3689d36db740b49f4327be3be09a21122bd02fb8895abb38b50d                                  0.0s
 => [internal] load build context                                                                                                                            0.0s
 => => transferring context: 340B                                                                                                                            0.0s
 => CACHED [2/5] WORKDIR /app                                                                                                                                0.0s
 => [3/5] COPY requirements.txt .                                                                                                                            0.0s
 => [4/5] RUN pip install --no-cache-dir -r requirements.txt                                                                                                 6.5s
 => [5/5] COPY . .                                                                                                                                           0.0s
 => exporting to image                                                                                                                                       0.7s
 => => exporting layers                                                                                                                                      0.5s
 => => exporting manifest sha256:4566568d4a2cdb7070281186758dc98354d78808cf32269c04632744e1bdd5a8                                                            0.0s
 => => exporting config sha256:c4b524559ac011445d7b6087ea073f7057ee7d219c25e72b2d47a4752f19d43e                                                              0.0s
 => => exporting attestation manifest sha256:7b7ddbd9e70df07fae5f447a3329060e92ba0069e3c290ee4071cc8aded748ba                                                0.0s
 => => exporting manifest list sha256:dec9d1fd3bed38e64d623b1fab65e0137019d69f9f39f9c133f2737c38d13176                                                       0.0s
 => => naming to docker.io/library/inventory:1.0.0                                                                                                           0.0s
 => => unpacking to docker.io/library/inventory:1.0.0     
```

## Persistence
The code block below shows a created volume being edited, relaunching the image, then ensuring the value remains 11. Each container is deleted when it exits `--rm` and only the `inventory_data` volume is kept.
```

$ docker volume create inventory-data
inventory-data
(.venv) $ docker run --rm -v inventory-data:/data inventory:1.0.0 python seed_db.py
suppliers: 4
products: 12
sales: 5
sale_items: 12
stock_movements: 0
(.venv) $ % docker run -it --rm -v inventory-data:/data inventory:1.0.0
Inventory v1.0.0

1. Search
2. Product lookup
3. Add product
4. Restock
5. Record a sale
6. Reports
7. Backup
8. Quit
Choose an option
> 4
SKU
> TOO-TOO-002
Amount to add
> 10
Stock is now 11.

1. Search
2. Product lookup
3. Add product
4. Restock
5. Record a sale
6. Reports
7. Backup
8. Quit
Choose an option
> 8
(.venv) $ docker run --rm -v inventory-data:/data inventory:1.0.0 python -c "import inventory_db as db; print(db.get_product(db.connect(), 'TOO-TOO-002')['in_stock'])"
11
```

## Rolling back

Back up first, stop the 1.1.0 container, then start 1.0.0 on the same volume.

```
docker run -it --rm -v inventory-data:/data inventory:1.0.0
```

```
$ docker build -t inventory:1.1.0 .
[+] Building 0.5s (11/11) FINISHED                                                                                                           docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                                         0.0s
 => => transferring dockerfile: 296B                                                                                                                         0.0s
 => [internal] load metadata for docker.io/library/python:3.12.7-slim                                                                                        0.4s
 => [auth] library/python:pull token for registry-1.docker.io                                                                                                0.0s
 => [internal] load .dockerignore                                                                                                                            0.0s
 => => transferring context: 122B                                                                                                                            0.0s
 => [1/5] FROM docker.io/library/python:3.12.7-slim@sha256:60d9996b6a8a3689d36db740b49f4327be3be09a21122bd02fb8895abb38b50d                                  0.0s
 => => resolve docker.io/library/python:3.12.7-slim@sha256:60d9996b6a8a3689d36db740b49f4327be3be09a21122bd02fb8895abb38b50d                                  0.0s
 => [internal] load build context                                                                                                                            0.0s
 => => transferring context: 22.03kB                                                                                                                         0.0s
 => CACHED [2/5] WORKDIR /app                                                                                                                                0.0s
 => CACHED [3/5] COPY requirements.txt .                                                                                                                     0.0s
 => CACHED [4/5] RUN pip install --no-cache-dir -r requirements.txt                                                                                          0.0s
 => [5/5] COPY . .                                                                                                                                           0.0s
 => exporting to image                                                                                                                                       0.0s
 => => exporting layers                                                                                                                                      0.0s
 => => exporting manifest sha256:d2223bc9e4c0e2de16777b286f02c4121c1328d984faf975d2d1adeea076fc01                                                            0.0s
 => => exporting config sha256:89f3e0d3a52487fa6ca87f000a3125f94e135bcee75b99251ae0eabbf657fd98                                                              0.0s
 => => exporting attestation manifest sha256:ce3b2aa328e23c2231bd22235f71d400c217368691020766a3287e3f527956f2                                                0.0s
 => => exporting manifest list sha256:bcf09619a0e4d89f57cdf57aab00de2bc28bdcf769dd30bd3bddc373e1bea6e8                                                       0.0s
 => => naming to docker.io/library/inventory:1.1.0                                                                                                           0.0s
 => => unpacking to docker.io/library/inventory:1.1.0                                                                                                        0.0s

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/c6tgn6hp3yy0p1gvvc6kuj5hq
$ docker run -it --rm -v inventory-data:/data inventory:1.1.0
Inventory v1.1.0
Low stock: 1 product(s) at or below their reorder level

1. Search
2. Product lookup
3. Add product
4. Restock
5. Record a sale
6. Reports
7. Backup
8. Quit
Choose an option
> 7
Backed up to /data/inventory-backup.db
integrity_check: ok
live: {'suppliers': 4, 'products': 12, 'sales': 5, 'sale_items': 12, 'stock_movements': 1}
backup: {'suppliers': 4, 'products': 12, 'sales': 5, 'sale_items': 12, 'stock_movements': 1}

1. Search
2. Product lookup
3. Add product
4. Restock
5. Record a sale
6. Reports
7. Backup
8. Quit
Choose an option
> 8
$ docker run --rm -v inventory-data:/data inventory:1.1.0 python seed_db.py
suppliers: 4
products: 12
sales: 5
sale_items: 12
stock_movements: 1
$ docker run -it --rm -v inventory-data:/data inventory:1.0.0
Inventory v1.0.0

1. Search
2. Product lookup
3. Add product
4. Restock
5. Record a sale
6. Reports
7. Backup
8. Quit
Choose an option
> 8
$ docker run --rm -v inventory-data:/data inventory:1.0.0 python seed_db.py
suppliers: 4
products: 12
sales: 5
sale_items: 12
stock_movements: 1
```