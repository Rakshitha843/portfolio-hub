from flask import Blueprint, jsonify, request

import db
from auth import (clear_auth_cookie, create_token, current_user, hash_password,
                  public_user, set_auth_cookie, verify_password)
from validators import ValidationError, validate_registration

bp = Blueprint("auth_api", __name__, url_prefix="/api/auth")


@bp.post("/register")
def register():
    try:
        data = validate_registration(request.get_json(silent=True))
    except ValidationError as exc:
        return jsonify(error="Please fix the highlighted fields", fields=exc.errors), 422

    profile = {k: data[k] for k in ("name", "usn", "department", "year")}
    profile["is_public"] = 0  # private until the student chooses to publish
    try:
        student = db.create_student_account(data["email"], hash_password(data["password"]), profile)
    except db.DuplicateError as exc:
        message = {
            "email": "An account with this email already exists",
            "usn": "This USN is already registered",
        }[exc.field]
        return jsonify(error=message, fields={exc.field: message}), 409

    user = db.get_user(student["id"])
    resp = jsonify(user=public_user(user), redirect="/dashboard")
    resp.status_code = 201
    set_auth_cookie(resp, create_token(user))
    return resp


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()[:120]
    password = str(data.get("password", ""))[:128]

    limiter_key = "rl:login:%s:%s" % (request.remote_addr, email)
    if db.login_blocked(limiter_key):
        return jsonify(error="Too many failed attempts. Try again in 15 minutes."), 429

    user = db.get_user_by_email(email) if email else None
    if not verify_password(user["password_hash"] if user else None, password) or not user:
        db.login_failed(limiter_key)
        return jsonify(error="Incorrect email or password"), 401

    db.login_ok(limiter_key)
    target = "/admin" if user["role"] == "admin" else "/dashboard"
    resp = jsonify(user=public_user(user), redirect=target)
    set_auth_cookie(resp, create_token(user))
    return resp


@bp.post("/logout")
def logout():
    resp = jsonify(ok=True)
    clear_auth_cookie(resp)
    return resp


@bp.get("/me")
def me():
    return jsonify(user=public_user(current_user()))
