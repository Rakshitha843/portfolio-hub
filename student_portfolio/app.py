"""PortfolioHub - student portfolio app (Flask + Redis Stack)."""
import logging
import os
from urllib.parse import urlparse

import redis
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

import config
import db
from auth import current_user, public_user
from routes import register_blueprints

log = logging.getLogger("portfoliohub")

_MESSAGES = {
    403: "You don't have access to this page.",
    404: "We couldn't find that page. It may have moved, or the portfolio may be private.",
    413: "That upload is too large. Photos can be up to 2 MB.",
    429: "Too many requests. Wait a moment and try again.",
}


def init_data():
    """Check Redis, create the search index, make sure the admin exists, load demo data once."""
    import seed

    try:
        db.ping()
    except (redis.ConnectionError, redis.TimeoutError) as exc:
        target = urlparse(config.REDIS_URL)
        raise SystemExit(
            "\nCannot connect to Redis at %s:%s\n"
            "  Start Redis Stack:  docker compose up -d\n"
            "  Or point REDIS_URL in .env at your Redis Cloud database.\n"
            % (target.hostname, target.port or 6379)
        ) from exc

    if db.ensure_index():
        log.info("Created search index %s", config.STUDENT_INDEX)
    seed.ensure_admin()
    if config.AUTO_SEED and db.mark_seeded():
        added = seed.seed_demo()
        log.info("Loaded %d demo students", added)


def create_app(init=True):
    app = Flask(__name__)
    app.config.update(SECRET_KEY=config.SECRET_KEY, MAX_CONTENT_LENGTH=config.MAX_UPLOAD_BYTES)
    app.json.sort_keys = False
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if config.SECRET_KEY_IS_RANDOM:
        log.warning("SECRET_KEY is not set - logins reset on every restart. Set it in .env.")

    register_blueprints(app)

    @app.template_filter("initials")
    def initials(name):
        parts = [p for p in str(name).split() if p]
        return "".join(p[0] for p in parts[:2]).upper() or "?"

    @app.template_filter("hue")
    def hue(name):
        return sum(ord(c) for c in str(name)) % 360

    @app.template_filter("datefmt")
    def datefmt(ts):
        import time
        return time.strftime("%d %b %Y", time.gmtime(ts or 0))

    @app.context_processor
    def inject_user():
        return {"current_user": public_user(current_user()), "config": config}

    @app.before_request
    def csrf_guard():
        # Browsers cannot add a custom header cross-site without a CORS preflight,
        # so requiring one blocks cross-site form posts against the API.
        if (request.path.startswith("/api/")
                and request.method in ("POST", "PUT", "PATCH", "DELETE")
                and request.headers.get("X-Requested-With") != "fetch"):
            return jsonify(error="Missing request header"), 400

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        if request.path.startswith("/api/"):
            resp.headers.setdefault("Cache-Control", "no-store")
        return resp

    @app.errorhandler(HTTPException)
    def http_error(exc):
        message = _MESSAGES.get(exc.code, exc.description or exc.name)
        if request.path.startswith("/api/"):
            return jsonify(error=message), exc.code
        return render_template("error.html", code=exc.code, title=exc.name, message=message), exc.code

    @app.errorhandler(redis.RedisError)
    def redis_error(exc):
        log.exception("Redis error")
        message = "The database is unavailable right now. Please try again shortly."
        if request.path.startswith("/api/"):
            return jsonify(error=message), 503
        return render_template("error.html", code=503, title="Database unavailable",
                               message=message), 503

    if init:
        init_data()
    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=config._flag("FLASK_DEBUG", False),
    )
