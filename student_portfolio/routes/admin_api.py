import csv
import io
import time

from flask import Blueprint, Response, jsonify, request

import db
from auth import require_user
from routes.helpers import admin_row, search_args

bp = Blueprint("admin_api", __name__, url_prefix="/api/admin")


def _csv_safe(value):
    """Stop spreadsheet formula injection (cells starting with = + - @)."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


@bp.get("/students")
@require_user("admin")
def list_students():
    args = search_args()
    visibility = request.args.get("visibility")
    public = True if visibility == "public" else False if visibility == "private" else None
    docs, total = db.search_students(public=public, **args)
    return jsonify(
        items=[admin_row(d) for d in docs],
        total=total, page=args["page"], per_page=args["per_page"],
    )


@bp.get("/stats")
@require_user("admin")
def stats():
    return jsonify(db.stats())


@bp.patch("/students/<sid>/visibility")
@require_user("admin")
def set_visibility(sid):
    student = db.get_student(sid)
    if not student:
        return jsonify(error="Portfolio not found"), 404
    data = request.get_json(silent=True) or {}
    student["is_public"] = 1 if data.get("is_public") is True else 0
    student["updated_at"] = int(time.time())
    db.save_student(sid, student)
    return jsonify(ok=True, is_public=bool(student["is_public"]))


@bp.delete("/students/<sid>")
@require_user("admin")
def delete_student(sid):
    if not db.valid_id(sid) or not db.delete_student_account(sid):
        return jsonify(error="Portfolio not found"), 404
    return jsonify(ok=True)


@bp.get("/export.csv")
@require_user("admin")
def export_csv():
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["Name", "USN", "Email", "Department", "Year", "Skills",
                     "Projects", "Certifications", "Public"])
    for d in db.all_students():
        writer.writerow([_csv_safe(v) for v in (
            d["name"], d["usn"], d["email"], d["department"], d["year"],
            "; ".join(d.get("skills", [])), len(d.get("projects", [])),
            len(d.get("certifications", [])), "yes" if d.get("is_public") else "no",
        )])
    return Response(out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=students.csv"})
