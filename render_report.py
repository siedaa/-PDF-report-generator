import sqlite3
from datetime import date

from playwright.sync_api import sync_playwright

DB_PATH = "report.db"


def build_html(report_data, all_orders):
    today = date.today().isoformat()

    totals_html = f"""
    <div class="totals">
      <div class="total-card">
        <span class="total-label">Total Orders</span>
        <span class="total-value">{report_data["total_orders"]}</span>
      </div>
      <div class="total-card">
        <span class="total-label">Total Revenue</span>
        <span class="total-value">${report_data["total_revenue"]:,.2f}</span>
      </div>
    </div>
    """

    top_products_rows = "".join(
        f"<tr><td>{p['product']}</td><td class='num'>${p['revenue']:,.2f}</td></tr>"
        for p in report_data["top_products"]
    )

    all_orders_rows = "".join(
        (
            f"<tr>"
            f"<td>{o[0]}</td>"
            f"<td>{o[1]}</td>"
            f"<td>{o[2]}</td>"
            f"<td class='num'>${o[3]:,.2f}</td>"
            f"<td>{o[4]}</td>"
            f"</tr>"
        )
        for o in all_orders
    )

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Sales Report {today}</title>
<style>
  body {{ font-family: Arial, Helvetica, sans-serif; font-size: 12px; color: #222; }}
  h1 {{ font-size: 22px; margin-bottom: 4px; }}
  .subtitle {{ color: #666; margin-bottom: 20px; }}
  .totals {{ display: flex; gap: 16px; margin-bottom: 24px; }}
  .total-card {{ border: 1px solid #ccc; border-radius: 6px; padding: 12px 20px; background: #f8f8f8; }}
  .total-label {{ display: block; font-size: 12px; color: #666; }}
  .total-value {{ display: block; font-size: 26px; font-weight: bold; }}
  h2 {{ font-size: 16px; margin: 20px 0 8px; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; }}
  th, td {{ border: 1px solid #ccc; padding: 6px 8px; text-align: left; }}
  th {{ background: #eaeaea; }}
  td.num {{ text-align: right; }}
  tr {{ break-inside: avoid; }}
</style>
</head>
<body>
  <h1>Sales Report</h1>
  <div class="subtitle">{today}</div>
  {totals_html}
  <h2>Top Products</h2>
  <table>
    <thead>
      <tr><th>Product</th><th>Revenue</th></tr>
    </thead>
    <tbody>
      {top_products_rows}
    </tbody>
  </table>
  <h2>All Orders</h2>
  <table>
    <thead>
      <tr><th>ID</th><th>Customer</th><th>Product</th><th>Amount</th><th>Created At</th></tr>
    </thead>
    <tbody>
      {all_orders_rows}
    </tbody>
  </table>
</body>
</html>"""


def render_pdf(html, output_path):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html)
        page.pdf(path=output_path, format="A4", print_background=True)
        browser.close()


def get_all_orders():
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, customer, product, amount, created_at FROM orders")
        return cur.fetchall()
    finally:
        conn.close()
