"""Input cleaning and validation. Nothing reaches Redis without passing through here."""
import re
import time
from urllib.parse import urlparse

import config


class ValidationError(Exception):
    """`errors` maps a field path (e.g. 'projects.0.title') to a message."""

    def __init__(self, errors):
        super().__init__("Validation failed")
        self.errors = errors


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
_USN_RE = re.compile(r"^[A-Z0-9]{5,20}$")


# ------------------------------------------------------------------ primitives
def _text(value, field, errors, max_len, required=False, min_len=0, multiline=False):
    if value is None:
        value = ""
    if not isinstance(value, str):
        errors[field] = "Must be text"
        return ""
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = "".join(ch for ch in value if ch == "\n" or ch >= " ")  # drop control chars
    if multiline:
        value = re.sub(r"\n{3,}", "\n\n", value.strip())
    else:
        value = re.sub(r"\s+", " ", value).strip()
    if required and not value:
        errors[field] = "This field is required"
    elif value and len(value) < min_len:
        errors[field] = "Must be at least %d characters" % min_len
    elif len(value) > max_len:
        errors[field] = "Must be at most %d characters" % max_len
    return value


def _int(value, field, errors, lo, hi, required=True):
    if value is None or value == "":
        if required:
            errors[field] = "This field is required"
        return None
    if isinstance(value, bool):
        errors[field] = "Must be a number"
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        errors[field] = "Must be a number"
        return None
    if not lo <= number <= hi:
        errors[field] = "Must be between %d and %d" % (lo, hi)
        return None
    return number


def _url(value, field, errors, host=None):
    """Accept only http(s) links. Optionally require a specific site (e.g. github.com)."""
    if value is None:
        return ""
    if not isinstance(value, str):
        errors[field] = "Must be a link"
        return ""
    v = value.strip()
    if not v:
        return ""
    if len(v) > 300:
        errors[field] = "Link is too long"
        return ""
    if "://" not in v:
        v = "https://" + v
    try:
        parsed = urlparse(v)
        hostname = (parsed.hostname or "").lower()
        _ = parsed.port  # raises ValueError for a bad port
    except ValueError:
        errors[field] = "Enter a valid link"
        return ""
    if parsed.scheme not in ("http", "https") or " " in v or "." not in hostname:
        errors[field] = "Enter a valid http(s) link"
        return ""
    if host and not (hostname == host or hostname.endswith("." + host)):
        errors[field] = "Must be a %s link" % host
        return ""
    return v


# ------------------------------------------------------------------ field helpers
def _usn(value, errors):
    v = _text(value, "usn", errors, 20, required=True).upper().replace(" ", "")
    if v and "usn" not in errors and not _USN_RE.match(v):
        errors["usn"] = "Use 5-20 letters/numbers, e.g. 1BI21CS014"
    return v


def _department(value, errors):
    v = _text(value, "department", errors, 40, required=True)
    if v and "department" not in errors and v not in config.DEPARTMENTS:
        errors["department"] = "Choose a department from the list"
    return v


def _skills(value, errors):
    if value is None:
        return []
    if not isinstance(value, list):
        errors["skills"] = "Skills must be a list"
        return []
    out, seen = [], set()
    for item in value:
        if not isinstance(item, str):
            errors["skills"] = "Each skill must be text"
            return []
        s = re.sub(r"\s+", " ", item.replace(",", " ")).strip()
        s = "".join(ch for ch in s if ch >= " ")
        if not s:
            continue
        if len(s) > 40:
            errors["skills"] = "'%s...' is too long (max 40 characters)" % s[:20]
            continue
        key = s.lower()
        if key not in seen:
            seen.add(key)
            out.append(s)
    if len(out) > 30:
        errors["skills"] = "Add at most 30 skills"
    return out


def _tech(value, field, errors):
    if value is None or value == "":
        return []
    if isinstance(value, str):
        value = value.split(",")
    if not isinstance(value, list):
        errors[field] = "Must be a list"
        return []
    out = []
    for item in value:
        if not isinstance(item, str):
            errors[field] = "Must be text"
            return []
        t = re.sub(r"\s+", " ", item).strip()
        if not t:
            continue
        if len(t) > 30:
            errors[field] = "Each technology must be at most 30 characters"
            continue
        if t.lower() not in [x.lower() for x in out]:
            out.append(t)
    if len(out) > 10:
        errors[field] = "Add at most 10 technologies"
    return out


def _projects(value, errors):
    if value is None:
        return []
    if not isinstance(value, list):
        errors["projects"] = "Projects must be a list"
        return []
    if len(value) > 15:
        errors["projects"] = "Add at most 15 projects"
        return []
    out = []
    for i, p in enumerate(value):
        base = "projects.%d" % i
        if not isinstance(p, dict):
            errors[base] = "Invalid project"
            continue
        out.append({
            "title": _text(p.get("title"), base + ".title", errors, 100, required=True),
            "description": _text(p.get("description"), base + ".description", errors, 500,
                                 multiline=True),
            "tech": _tech(p.get("tech"), base + ".tech", errors),
            "link": _url(p.get("link"), base + ".link", errors),
        })
    return out


def _certifications(value, errors):
    if value is None:
        return []
    if not isinstance(value, list):
        errors["certifications"] = "Certifications must be a list"
        return []
    if len(value) > 20:
        errors["certifications"] = "Add at most 20 certifications"
        return []
    max_year = time.gmtime().tm_year + 1
    out = []
    for i, c in enumerate(value):
        base = "certifications.%d" % i
        if not isinstance(c, dict):
            errors[base] = "Invalid certification"
            continue
        out.append({
            "name": _text(c.get("name"), base + ".name", errors, 100, required=True),
            "issuer": _text(c.get("issuer"), base + ".issuer", errors, 100),
            "year": _int(c.get("year"), base + ".year", errors, 1990, max_year, required=False),
            "link": _url(c.get("link"), base + ".link", errors),
        })
    return out


def _achievements(value, errors):
    if value is None:
        return []
    if not isinstance(value, list):
        errors["achievements"] = "Achievements must be a list"
        return []
    out = []
    for i, item in enumerate(value):
        text = _text(item, "achievements.%d" % i, errors, 200)
        if text:
            out.append(text)
    if len(out) > 20:
        errors["achievements"] = "Add at most 20 achievements"
    return out


# ------------------------------------------------------------------ public validators
def validate_registration(data):
    if not isinstance(data, dict):
        raise ValidationError({"_": "Invalid request"})
    errors = {}
    name = _text(data.get("name"), "name", errors, 80, required=True, min_len=2)
    email = _text(data.get("email"), "email", errors, 120, required=True).lower()
    if email and "email" not in errors and not _EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email address"

    password = data.get("password")
    if not isinstance(password, str) or len(password) < 8:
        errors["password"] = "Use at least 8 characters"
    elif len(password) > 128:
        errors["password"] = "Use at most 128 characters"
    elif not (re.search(r"[A-Za-z]", password) and re.search(r"\d", password)):
        errors["password"] = "Include at least one letter and one number"

    usn = _usn(data.get("usn"), errors)
    department = _department(data.get("department"), errors)
    year = _int(data.get("year"), "year", errors, 1, 4)
    if errors:
        raise ValidationError(errors)
    return {
        "name": name, "email": email, "password": password,
        "usn": usn, "department": department, "year": year,
    }


def validate_portfolio(data):
    """Validate the whole editable portfolio. Returns a clean dict ready to store."""
    if not isinstance(data, dict):
        raise ValidationError({"_": "Invalid request body"})
    errors = {}
    name = _text(data.get("name"), "name", errors, 80, required=True, min_len=2)
    usn = _usn(data.get("usn"), errors)
    department = _department(data.get("department"), errors)
    year = _int(data.get("year"), "year", errors, 1, 4)
    about = _text(data.get("about"), "about", errors, 600, multiline=True)
    skills = _skills(data.get("skills"), errors)
    projects = _projects(data.get("projects"), errors)
    certifications = _certifications(data.get("certifications"), errors)
    achievements = _achievements(data.get("achievements"), errors)

    raw_links = data.get("links") or {}
    if not isinstance(raw_links, dict):
        errors["links"] = "Links must be an object"
        raw_links = {}
    links = {
        "github": _url(raw_links.get("github"), "links.github", errors, host="github.com"),
        "linkedin": _url(raw_links.get("linkedin"), "links.linkedin", errors, host="linkedin.com"),
        "website": _url(raw_links.get("website"), "links.website", errors),
    }
    is_public = 1 if data.get("is_public") in (True, 1, "1", "true", "True") else 0

    if errors:
        raise ValidationError(errors)
    return {
        "name": name, "usn": usn, "department": department, "year": year, "about": about,
        "skills": skills, "projects": projects, "certifications": certifications,
        "achievements": achievements, "links": links, "is_public": is_public,
    }
