"""
Data layer: every Redis call in the project lives in this file.

Redis Stack = RedisJSON (document storage) + RediSearch (secondary index / full-text search).

Keys
  student:<id>    JSON document  the portfolio itself (indexed by idx:students)
  user:<id>       JSON document  login account (email, password hash, role)
  email:<email>   string         -> user id     (unique-email guard, SET NX)
  usn:<USN>       string         -> student id  (unique-USN guard, SET NX)
  photo:<id>      binary string  400x400 JPEG profile photo
  rl:login:*      counter + TTL  failed-login rate limiting
  meta:seeded     flag           demo data is inserted only once
"""
import json
import re
import time
import uuid
from collections import Counter

import redis
from redis.commands.search.field import NumericField, TagField, TextField
from redis.commands.search.query import Query

try:  # redis-py 6+ renamed this module
    from redis.commands.search.index_definition import IndexDefinition, IndexType
except ImportError:  # redis-py 5.x
    from redis.commands.search.indexDefinition import IndexDefinition, IndexType

import config

r = redis.Redis.from_url(config.REDIS_URL, decode_responses=True)
rb = redis.Redis.from_url(config.REDIS_URL, decode_responses=False)  # raw bytes (photos)

INDEX = config.STUDENT_INDEX
STUDENT_PREFIX = "student:"
_ID_RE = re.compile(r"^[0-9a-f]{10}$")
_TAG_SPECIALS = re.compile(r"([^\w])", re.UNICODE)


class DuplicateError(Exception):
    """Raised when an email or USN is already registered."""

    def __init__(self, field):
        super().__init__(field)
        self.field = field


# ------------------------------------------------------------------ helpers / setup
def new_id():
    return uuid.uuid4().hex[:10]


def valid_id(value):
    return isinstance(value, str) and bool(_ID_RE.match(value))


def _index_missing(message):
    """Different Redis versions word 'no such index' differently."""
    msg = str(message).lower()
    return "unknown" in msg or "no such index" in msg or "not found" in msg


def ping():
    return bool(r.ping())


def ensure_index():
    """Create the RediSearch index over student:* JSON documents (safe to call repeatedly)."""
    ft = r.ft(INDEX)
    try:
        ft.info()
        return False
    except redis.ResponseError as exc:
        msg = str(exc).lower()
        if "unknown command" in msg:
            raise RuntimeError(
                "This Redis server has no RediSearch/RedisJSON modules. "
                "Use Redis Stack (docker compose up -d) or Redis Cloud."
            ) from exc
        if not _index_missing(msg):
            raise

    schema = (
        TextField("$.name", as_name="name", weight=5.0, sortable=True),
        TagField("$.usn", as_name="usn"),
        TagField("$.email", as_name="email"),
        TagField("$.department", as_name="department"),
        NumericField("$.year", as_name="year", sortable=True),
        TagField("$.skills[*]", as_name="skills"),
        TextField("$.about", as_name="about"),
        TextField("$.projects[*].title", as_name="project_title"),
        NumericField("$.is_public", as_name="is_public"),
        NumericField("$.created_at", as_name="created_at", sortable=True),
    )
    definition = IndexDefinition(prefix=[STUDENT_PREFIX], index_type=IndexType.JSON)
    try:
        ft.create_index(schema, definition=definition)
    except redis.ResponseError as exc:
        if "already exists" not in str(exc).lower():
            raise
        return False
    return True


# ------------------------------------------------------------------ users
def get_user(user_id):
    if not valid_id(user_id):
        return None
    return r.json().get(f"user:{user_id}")


def get_user_by_email(email):
    uid = r.get(f"email:{email}")
    return get_user(uid) if uid else None


def create_admin(email, password_hash):
    """Create the admin account. Returns None if the email is already taken."""
    uid = new_id()
    if not r.set(f"email:{email}", uid, nx=True):
        return None
    user = {
        "id": uid,
        "email": email,
        "password_hash": password_hash,
        "role": "admin",
        "created_at": int(time.time()),
    }
    r.json().set(f"user:{uid}", "$", user)
    return user


def create_student_account(email, password_hash, profile):
    """Create the login account and the portfolio document together."""
    uid = new_id()
    now = int(time.time())
    if not r.set(f"email:{email}", uid, nx=True):
        raise DuplicateError("email")
    if not r.set(f"usn:{profile['usn']}", uid, nx=True):
        r.delete(f"email:{email}")
        raise DuplicateError("usn")

    user = {
        "id": uid,
        "email": email,
        "password_hash": password_hash,
        "role": "student",
        "created_at": now,
    }
    student = {
        "id": uid,
        "name": profile["name"],
        "email": email,
        "usn": profile["usn"],
        "department": profile["department"],
        "year": profile["year"],
        "about": profile.get("about", ""),
        "skills": profile.get("skills", []),
        "projects": profile.get("projects", []),
        "certifications": profile.get("certifications", []),
        "achievements": profile.get("achievements", []),
        "links": profile.get("links", {"github": "", "linkedin": "", "website": ""}),
        "is_public": int(profile.get("is_public", 0)),
        "has_photo": 0,
        "created_at": now,
        "updated_at": now,
    }
    try:
        r.json().set(f"user:{uid}", "$", user)
        r.json().set(f"student:{uid}", "$", student)
    except Exception:
        r.delete(f"email:{email}", f"usn:{profile['usn']}", f"user:{uid}", f"student:{uid}")
        raise
    return student


# ------------------------------------------------------------------ students
def get_student(student_id):
    if not valid_id(student_id):
        return None
    return r.json().get(f"student:{student_id}")


def save_student(student_id, doc):
    """Replace an existing portfolio document. Returns False if it no longer exists."""
    return bool(r.json().set(f"student:{student_id}", "$", doc, xx=True))


def change_usn(student_id, old, new):
    """Move the unique-USN claim. Returns False if another student already owns `new`."""
    if old == new:
        return True
    if not r.set(f"usn:{new}", student_id, nx=True):
        return r.get(f"usn:{new}") == student_id
    r.delete(f"usn:{old}")
    return True


def delete_student_account(student_id):
    student = get_student(student_id)
    user = get_user(student_id)
    pipe = r.pipeline()
    pipe.delete(f"student:{student_id}", f"user:{student_id}")
    if student:
        pipe.delete(f"usn:{student['usn']}")
    if user:
        pipe.delete(f"email:{user['email']}")
    pipe.execute()
    rb.delete(f"photo:{student_id}")
    return bool(student or user)


# ------------------------------------------------------------------ photos
def save_photo(student_id, data):
    rb.set(f"photo:{student_id}", data)


def get_photo(student_id):
    return rb.get(f"photo:{student_id}")


def delete_photo(student_id):
    rb.delete(f"photo:{student_id}")


# ------------------------------------------------------------------ search
def escape_tag(value):
    """Escape punctuation/spaces so a value can be used inside a RediSearch TAG filter."""
    return _TAG_SPECIALS.sub(r"\\\1", value.strip())


def _text_clause(q):
    q = q.strip()
    if "@" in q and " " not in q:  # looks like an email address
        return "@email:{%s}" % escape_tag(q.lower())
    clauses = []
    for token in re.findall(r"\w+", q, re.UNICODE)[:5]:
        token = token[:30]
        if len(token) < 2:
            continue
        tag = escape_tag(token)
        clauses.append(
            "(@name|about|project_title:(%s*) | @skills:{%s} | @usn:{%s})" % (token, tag, tag)
        )
    return " ".join(clauses)


def build_query(q="", department="", year=None, skill="", public=None):
    """Turn the filter form into a RediSearch query string (all clauses are ANDed)."""
    parts = []
    if public is True:
        parts.append("@is_public:[1 1]")
    elif public is False:
        parts.append("@is_public:[0 0]")
    if department:
        parts.append("@department:{%s}" % escape_tag(department))
    if year:
        parts.append("@year:[%d %d]" % (int(year), int(year)))
    if skill:
        parts.append("@skills:{%s}" % escape_tag(skill))
    if q:
        clause = _text_clause(q)
        if clause:
            parts.append(clause)
    return " ".join(parts) or "*"


def _doc_to_dict(doc):
    raw = getattr(doc, "json", None)
    if raw:
        return json.loads(raw)
    return r.json().get(doc.id)  # fallback: fetch the document by key


def _search(query):
    try:
        return r.ft(INDEX).search(query)
    except redis.ResponseError as exc:
        if _index_missing(exc):
            ensure_index()
            return r.ft(INDEX).search(query)
        raise


def search_students(q="", department="", year=None, skill="", public=None,
                    sort="newest", page=1, per_page=12):
    """Return (list_of_portfolio_dicts, total_matches) for one page of results."""
    query = Query(build_query(q, department, year, skill, public)).dialect(2)
    if sort == "name":
        query.sort_by("name", asc=True)
    else:
        query.sort_by("created_at", asc=False)
    query.paging((page - 1) * per_page, per_page)
    res = _search(query)
    return [_doc_to_dict(d) for d in res.docs], res.total


def all_students():
    """Every portfolio (used by stats + CSV export). Fetched in batches of 500."""
    docs, offset, batch = [], 0, 500
    while True:
        res = _search(Query("*").dialect(2).paging(offset, batch))
        if not res.docs:
            break
        docs.extend(_doc_to_dict(d) for d in res.docs)
        offset += batch
        if offset >= res.total or offset >= 10000:
            break
    return docs


def stats():
    docs = all_students()
    by_dept = Counter(d["department"] for d in docs)
    by_year = Counter(d["year"] for d in docs)
    skill_counts, display = Counter(), {}
    for d in docs:
        for s in d.get("skills", []):
            key = s.lower()
            skill_counts[key] += 1
            display.setdefault(key, s)
    return {
        "total": len(docs),
        "public": sum(1 for d in docs if d.get("is_public")),
        "projects": sum(len(d.get("projects", [])) for d in docs),
        "by_department": [
            {"label": k, "count": v}
            for k, v in sorted(by_dept.items(), key=lambda kv: (-kv[1], kv[0]))
        ],
        "by_year": [{"label": "Year %d" % y, "count": by_year.get(y, 0)} for y in config.YEARS],
        "top_skills": [
            {"label": display[k], "count": c} for k, c in skill_counts.most_common(10)
        ],
    }


# ------------------------------------------------------------------ misc flags / limits
def mark_seeded():
    """True only for the first caller, so demo data is inserted exactly once."""
    return bool(r.set("meta:seeded", "1", nx=True))


def login_blocked(key, limit=8):
    return int(r.get(key) or 0) >= limit


def login_failed(key, window=900):
    if r.incr(key) == 1:
        r.expire(key, window)


def login_ok(key):
    r.delete(key)
