import os

from render_report import build_html, get_all_orders, render_pdf
from report_data import get_report_data

os.makedirs("reports", exist_ok=True)

report_data = get_report_data()
all_orders = get_all_orders()
html = build_html(report_data, all_orders)
render_pdf(html, "reports/test.pdf")

print(f"Rendered reports/test.pdf with {len(all_orders)} orders")
