# PDF Report Generator

## What this is

A small FastAPI backend that queries a seeded SQLite orders database, aggregates it with SQL, renders the numbers into an HTML report, and converts that HTML to a PDF with Playwright's headless Chromium. The finished PDF is stored on disk and served back to the client by link through the API. `POST /reports` is idempotent: as long as a report already exists for today it returns that one (HTTP 200) instead of generating a duplicate, unless you explicitly pass `{"force": true}`.

## Dataset

A SQLite database (`report.db`) with a single `orders` table:

| column | type | meaning |
|--------|------|---------|
| id | INTEGER | auto-incrementing primary key |
| customer | TEXT | fake customer name |
| product | TEXT | one of 6 fake product names |
| amount | REAL | order value between 5 and 200 |
| created_at | TEXT | ISO date within the last 30 days |

It is populated with ~200 random rows by running `python seed.py`. The script deletes existing rows before inserting, so it never duplicates data.

## How to run it

1. Clone the repo:
   ```
   git clone https://github.com/siedaa/-PDF-report-generator.git
   cd -PDF-report-generator
   ```
2. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Install the Playwright Chromium browser:
   ```
   playwright install chromium
   ```
5. Seed the database:
   ```
   python seed.py
   ```
6. Start the server:
   ```
   uvicorn main:app --reload --port 8000
   ```

## Aggregation SQL

The queries below are extracted from `report_data.py`.

```sql
-- Total number of orders
SELECT COUNT(*) FROM orders

-- Sum of all order amounts (total revenue)
SELECT SUM(amount) FROM orders

-- Top 5 products by revenue, descending
SELECT product, SUM(amount) AS revenue
FROM orders
GROUP BY product
ORDER BY revenue DESC
LIMIT 5

-- Orders per day for the last 7 calendar days (0-count days are filled in Python)
SELECT created_at, COUNT(*)
FROM orders
WHERE created_at >= ?
GROUP BY created_at
```

The results are assembled into a dict with `total_orders`, `total_revenue`, `top_products`, and `orders_per_day`.

## API endpoints

| Method | Path | What it does |
|--------|------|--------------|
| POST | `/reports` | Builds today's report. Idempotent: returns the existing report (200) if one was already created today, unless `{"force": true}` is sent. Generates a new PDF (201) otherwise. |
| GET | `/reports/{id}` | Returns report metadata (`id`, `path`, `created_at`). 404 if the id doesn't exist. |
| GET | `/reports/{id}/file` | Serves the actual PDF from disk as `application/pdf`. 404 if the id or file doesn't exist. |

## Proof: generate and download

```powershell
curl.exe -s -w " [HTTP %{http_code}]" -X POST http://127.0.0.1:8000/reports
curl.exe -s -o report.pdf -w "downloaded %{size_download} bytes [HTTP %{http_code}]" http://127.0.0.1:8000/reports/1/file
```

Example output:

```
{"id":1,"file":"/reports/1/file"} [HTTP 201]
downloaded 69764 bytes [HTTP 200]
```

Calling `POST /reports` again with no body returns the same id with HTTP 200 and creates no new PDF.

## Design notes

**Background jobs.** Right now rendering happens synchronously inside the request handler — the client waits a few seconds for Playwright to launch Chromium, render the HTML, and write the PDF. You'd move that into a background job (e.g. a queue like Celery/RQ, or FastAPI's `BackgroundTasks`) as soon as report generation gets slow enough to risk HTTP timeouts — for example a much larger dataset, a long multi-page document, or many concurrent requests. The API would return `202 Accepted` with a job id immediately, and the client would poll until the report is ready. That decouples the fast request/response contract from the slow PDF work.

**Idempotency.** The check in `POST /reports` (whether a report already exists for today) protects against duplicate rows and wasted render work when the same request is sent more than once — most commonly because a client retries after a timeout, or the frontend double-submits a button click. A concrete example where a missing check costs money or trust: a financial reporting portal that charges per generated statement. If a customer's browser fires two requests because of a slow network retry, they get billed twice and see two invoice PDFs — an instant support ticket, a refund, and lost trust in your billing.

## Screenshot
![Report page 1](image.png)
