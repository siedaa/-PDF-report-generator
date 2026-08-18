import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from render_report import build_html, get_all_orders, render_pdf
from report_data import get_report_data

DB_PATH = "report.db"
REPORTS_DIR = "reports"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT,
                created_at TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


class ReportRequest(BaseModel):
    force: bool = False


@app.post("/reports", status_code=201)
def create_report(body: ReportRequest | None = None):
    force = body.force if body else False
    os.makedirs(REPORTS_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        if not force:
            today = datetime.now(timezone.utc).date().isoformat()
            row = conn.execute(
                "SELECT id FROM reports WHERE date(created_at) = ? ORDER BY id DESC LIMIT 1",
                (today,),
            ).fetchone()
            if row is not None:
                return JSONResponse(
                    status_code=200,
                    content={"id": row[0], "file": f"/reports/{row[0]}/file"},
                )

        created_at = datetime.now(timezone.utc).isoformat()
        cur = conn.execute(
            "INSERT INTO reports (path, created_at) VALUES (?, ?)",
            ("", created_at),
        )
        conn.commit()
        report_id = cur.lastrowid

        html = build_html(get_report_data(), get_all_orders())
        pdf_path = os.path.join(REPORTS_DIR, f"{report_id}.pdf")
        render_pdf(html, pdf_path)

        cur.execute("UPDATE reports SET path = ? WHERE id = ?", (pdf_path, report_id))
        conn.commit()
    finally:
        conn.close()

    return {"id": report_id, "file": f"/reports/{report_id}/file"}


@app.get("/reports/{report_id}")
def get_report(report_id: int):
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            "SELECT id, path, created_at FROM reports WHERE id = ?",
            (report_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Report not found")

    return {"id": row[0], "path": row[1], "created_at": row[2]}


@app.get("/reports/{report_id}/file")
def get_report_file(report_id: int):
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute("SELECT path FROM reports WHERE id = ?", (report_id,)).fetchone()
    finally:
        conn.close()

    if row is None or not row[0] or not os.path.exists(row[0]):
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(row[0], media_type="application/pdf")
