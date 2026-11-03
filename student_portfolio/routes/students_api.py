import time

from flask import Blueprint, jsonify, request

import db
from auth import current_user, require_user
from media import PhotoError, process_photo
from routes.helpers import serialize_student
from validators import ValidationError, validate_portfolio

bp = Blueprint("students_api", __name__, url_prefix="/api/students")


def _owner_or_admin(user, sid):
    return user["role"] == "admin" or user["id"] == sid


@bp.get("/<sid>")
def get_student(sid):
    user = current_user()
    if sid == "me":
        if not user:
            return jsonify(error="Please log in to continue"), 401
        sid = user["id"]
    student = db.get_student(sid)
    if not student:
        return jsonify(error="Portfolio not found"), 404
    privileged = bool(user and _owner_or_admin(user, sid))
    if not student.get("is_public") and not privileged:
        return jsonify(error="Portfolio not found"), 404
    return jsonify(serialize_student(student, private=privileged))


@bp.put("/<sid>")
@require_user()
def update_student(sid):
    user = current_user()
    if sid == "me":
        sid = user["id"]
    if not _owner_or_admin(user, sid):
        return jsonify(error="You can only edit your own portfolio"), 403
    existing = db.get_student(sid)
    if not existing:
        return jsonify(error="Portfolio not found"), 404

    try:
        clean = validate_portfolio(request.get_json(silent=True))
    except ValidationError as exc:
        return jsonify(error="Please fix the highlighted fields", fields=exc.errors), 422

    if not db.change_usn(sid, existing["usn"], clean["usn"]):
        message = "This USN is already registered"
        return jsonify(error=message, fields={"usn": message}), 409

    existing.update(clean)
    existing["updated_at"] = int(time.time())
    if not db.save_student(sid, existing):
        return jsonify(error="Portfolio not found"), 404
    return jsonify(serialize_student(existing, private=True))


@bp.post("/<sid>/photo")
@require_user()
def upload_photo(sid):
    user = current_user()
    if sid == "me":
        sid = user["id"]
    if not _owner_or_admin(user, sid):
        return jsonify(error="You can only edit your own portfolio"), 403
    student = db.get_student(sid)
    if not student:
        return jsonify(error="Portfolio not found"), 404
    upload = request.files.get("photo")
    if not upload:
        return jsonify(error="Choose a photo to upload"), 400
    try:
        data = process_photo(upload)
    except PhotoError as exc:
        return jsonify(error=str(exc)), 400

    db.save_photo(sid, data)
    student["has_photo"] = 1
    student["updated_at"] = int(time.time())
    db.save_student(sid, student)
    return jsonify(ok=True, updated_at=student["updated_at"])


@bp.delete("/<sid>/photo")
@require_user()
def remove_photo(sid):
    user = current_user()
    if sid == "me":
        sid = user["id"]
    if not _owner_or_admin(user, sid):
        return jsonify(error="You can only edit your own portfolio"), 403
    student = db.get_student(sid)
    if not student:
        return jsonify(error="Portfolio not found"), 404
    db.delete_photo(sid)
    student["has_photo"] = 0
    student["updated_at"] = int(time.time())
    db.save_student(sid, student)
    return jsonify(ok=True, updated_at=student["updated_at"])
