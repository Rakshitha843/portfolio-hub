"""Password hashing, JWT cookies and the access-control decorators."""
import datetime as dt
from functools import wraps

import jwt
from flask import abort, g, jsonify, redirect, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import config
import db

# Used to keep login timing similar whether or not the email exists.
_DUMMY_HASH = generate_password_hash("not-a-real-password")


def hash_password(password):
    return generate_password_hash(password)


def verify_password(stored_hash, password):
    if not stored_hash:
        check_password_hash(_DUMMY_HASH, password)
        return False
    return check_password_hash(stored_hash, password)


def create_token(user):
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": user["id"],
        "iat": now,
        "exp": now + dt.timedelta(hours=config.JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm="HS256")


def set_auth_cookie(response, token):
    response.set_cookie(
        config.COOKIE_NAME, token,
        max_age=config.JWT_EXPIRE_HOURS * 3600,
        httponly=True, samesite="Lax", secure=config.COOKIE_SECURE,
    )


def clear_auth_cookie(response):
    response.delete_cookie(config.COOKIE_NAME)


def current_user():
    """The logged-in user (loaded fresh from Redis, so deleted users lose access at once)."""
    if "_user" in g:
        return g._user
    user = None
    token = request.cookies.get(config.COOKIE_NAME)
    if token:
        try:
            claims = jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
            user = db.get_user(claims.get("sub"))
        except jwt.PyJWTError:
            user = None
    g._user = user
    return user


def public_user(user):
    """The safe subset of a user record (never includes the password hash)."""
    if not user:
        return None
    return {"id": user["id"], "email": user["email"], "role": user["role"]}


def require_user(role=None, api=True):
    """Protect a view. api=True answers with JSON errors; api=False redirects/aborts."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                if api:
                    return jsonify(error="Please log in to continue"), 401
                return redirect(url_for("pages.login", next=request.path))
            if role and user["role"] != role:
                if api:
                    return jsonify(error="You do not have permission to do that"), 403
                abort(403)
            return view(*args, **kwargs)
        return wrapper
    return decorator
