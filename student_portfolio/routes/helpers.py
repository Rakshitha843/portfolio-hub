"""Shared request parsing and JSON shaping for the API routes."""
from flask import request

import config


def search_args():
    """Read and sanitise the filter/pagination query string."""
    q = (request.args.get("q") or "").strip()[:80]
    department = request.args.get("department") or ""
    if department not in config.DEPARTMENTS:
        department = ""
    year = request.args.get("year", type=int)
    if year not in config.YEARS:
        year = None
    skill = (request.args.get("skill") or "").strip()[:40]
    sort = request.args.get("sort", "newest")
    if sort not in ("newest", "name"):
        sort = "newest"
    page = max(1, request.args.get("page", 1, type=int) or 1)
    per_page = min(50, max(1, request.args.get("per_page", 12, type=int) or 12))
    return {
        "q": q, "department": department, "year": year, "skill": skill,
        "sort": sort, "page": page, "per_page": per_page,
    }


def serialize_student(doc, private=False):
    """Full portfolio as JSON. Email and USN are only included for the owner/admin."""
    out = dict(doc)
    out["is_public"] = bool(out.get("is_public"))
    out["has_photo"] = bool(out.get("has_photo"))
    if not private:
        out.pop("email", None)
        out.pop("usn", None)
    return out


def card_view(doc):
    """Light summary used by the public gallery."""
    return {
        "id": doc["id"],
        "name": doc["name"],
        "department": doc["department"],
        "year": doc["year"],
        "skills": doc.get("skills", [])[:6],
        "project_count": len(doc.get("projects", [])),
        "has_photo": bool(doc.get("has_photo")),
        "updated_at": doc.get("updated_at", 0),
    }


def admin_row(doc):
    row = card_view(doc)
    row.update({
        "email": doc.get("email", ""),
        "usn": doc.get("usn", ""),
        "is_public": bool(doc.get("is_public")),
        "skill_count": len(doc.get("skills", [])),
    })
    return row
