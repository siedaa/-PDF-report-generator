import sqlite3
from datetime import date, timedelta

DB_PATH = "report.db"


def get_report_data():
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM orders")
        total_orders = cur.fetchone()[0]

        cur.execute("SELECT SUM(amount) FROM orders")
        total_revenue = round(cur.fetchone()[0] or 0.0, 2)

        cur.execute(
            """
            SELECT product, SUM(amount) AS revenue
            FROM orders
            GROUP BY product
            ORDER BY revenue DESC
            LIMIT 5
            """
        )
        top_products = [
            {"product": product, "revenue": round(revenue, 2)}
            for product, revenue in cur.fetchall()
        ]

        today = date.today()
        start_date = today - timedelta(days=6)
        cur.execute(
            """
            SELECT created_at, COUNT(*)
            FROM orders
            WHERE created_at >= ?
            GROUP BY created_at
            """,
            (start_date.isoformat(),),
        )
        counts = dict(cur.fetchall())
        orders_per_day = [
            {
                "date": (start_date + timedelta(days=i)).isoformat(),
                "count": counts.get((start_date + timedelta(days=i)).isoformat(), 0),
            }
            for i in range(7)
        ]

        return {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "top_products": top_products,
            "orders_per_day": orders_per_day,
        }
    finally:
        conn.close()
