"""HTML pages (server-rendered shells; the interactive parts call the JSON API)."""
from flask import Blueprint, Response, abort, jsonify, redirect, render_template, request, url_for

import config
import db
from auth import current_user, require_user

bp = Blueprint("pages", __name__)


def _safe_next(url):
    if url and url.startswith("/") and not url.startswith("//") and "\\" not in url:
        return url
    return ""


def _can_view(student, user):
    if student.get("is_public"):
        return True
    return bool(user and (user["role"] == "admin" or user["id"] == student["id"]))


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/login")
def login():
    user = current_user()
    if user:
        return redirect(url_for("pages.admin" if user["role"] == "admin" else "pages.dashboard"))
    return render_template("login.html", next_url=_safe_next(request.args.get("next")))


@bp.get("/register")
def register():
    if current_user():
        return redirect(url_for("pages.dashboard"))
    return render_template("register.html")


@bp.get("/dashboard")
@require_user(api=False)
def dashboard():
    user = current_user()
    target = user["id"]
    editing_other = False
    if user["role"] == "admin":
        target = request.args.get("id", "")
        if not target:
            return redirect(url_for("pages.admin"))
        if not db.get_student(target):
            abort(404)
        editing_other = True
    return render_template("dashboard.html", target_id=target, editing_other=editing_other)


@bp.get("/p/<sid>")
def portfolio(sid):
    student = db.get_student(sid)
    user = current_user()
    if not student or not _can_view(student, user):
        abort(404)
    can_edit = bool(user and (user["role"] == "admin" or user["id"] == sid))
    edit_url = url_for("pages.dashboard", id=sid) if user and user["role"] == "admin" \
        else url_for("pages.dashboard")
    return render_template("portfolio.html", s=student, can_edit=can_edit, edit_url=edit_url)


@bp.get("/photo/<sid>")
def photo(sid):
    student = db.get_student(sid)
    if not student or not student.get("has_photo") or not _can_view(student, current_user()):
        abort(404)
    data = db.get_photo(sid)
    if not data:
        abort(404)
    resp = Response(data, mimetype="image/jpeg")
    resp.headers["Cache-Control"] = (
        "public, max-age=300" if student.get("is_public") else "private, no-cache"
    )
    return resp


@bp.get("/admin")
@require_user("admin", api=False)
def admin():
    return render_template("admin.html")


@bp.get("/health")
def health():
    try:
        db.ping()
        return jsonify(status="ok", redis=True)
    except Exception:
        return jsonify(status="degraded", redis=False), 503
