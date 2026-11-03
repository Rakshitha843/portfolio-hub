from flask import Blueprint, jsonify

import config
import db
from routes.helpers import card_view, search_args

bp = Blueprint("public_api", __name__, url_prefix="/api")


@bp.get("/meta")
def meta():
    return jsonify(departments=config.DEPARTMENTS, years=config.YEARS)


@bp.get("/public/students")
def public_students():
    args = search_args()
    docs, total = db.search_students(public=True, **args)
    return jsonify(
        items=[card_view(d) for d in docs],
        total=total, page=args["page"], per_page=args["per_page"],
    )
