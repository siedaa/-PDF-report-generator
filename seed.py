import random
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "report.db"

CUSTOMERS = [
    "Alice Johnson",
    "Bob Smith",
    "Carol White",
    "David Brown",
    "Emma Davis",
    "Frank Wilson",
    "Grace Miller",
    "Henry Moore",
]

PRODUCTS = [
    "Widget",
    "Gadget",
    "Gizmo",
    "Doohickey",
    "Thingamajig",
    "Contraption",
]

TOTAL_ORDERS = 200


def main():
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT,
                product TEXT,
                amount REAL,
                created_at TEXT
            )
            """
        )
        cur.execute("DELETE FROM orders")

        today = datetime.now().date()
        rows = []
        for _ in range(TOTAL_ORDERS):
            created_at = today - timedelta(days=random.randint(0, 29))
            rows.append(
                (
                    random.choice(CUSTOMERS),
                    random.choice(PRODUCTS),
                    round(random.uniform(5.0, 200.0), 2),
                    created_at.isoformat(),
                )
            )

        cur.executemany(
            "INSERT INTO orders (customer, product, amount, created_at) VALUES (?, ?, ?, ?)",
            rows,
        )
        conn.commit()
        print(f"Inserted {cur.rowcount} rows")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
