# PortfolioHub: Student Portfolio System

A web app where students build and publish their own portfolio (skills, projects, certifications, achievements, links, photo) and admins manage everyone. Data is stored in **Redis Stack**, a NoSQL document database, as JSON documents.

| Layer | Technology |
|---|---|
| Database (NoSQL) | Redis Stack: **RedisJSON** (documents) + **RediSearch** (indexing, full-text search) |
| Backend | Python, Flask REST API, JWT login (HttpOnly cookie) |
| Frontend | HTML, CSS, JavaScript, Bootstrap 5, Chart.js, html2pdf.js |

## Features

- **Two roles.** Students edit only their own portfolio. Admins see and manage all of them.
- **Student dashboard.** Photo, bio, skill tags, projects, certifications, achievements, links, and a profile-strength meter.
- **Public gallery** with live search (name, skill, project, USN), department and year filters, pagination.
- **Shareable link** per student (`/p/<id>`) and **Download as PDF**.
- **Privacy switch.** New portfolios start private. Email and USN are never shown publicly.
- **Admin page.** Stats, charts (students per department, top skills, per year), filters, show/hide a portfolio, edit, delete, export CSV.
- **Security basics.** Hashed passwords, JWT cookie, login rate limiting, server-side validation on every field, XSS-safe rendering, upload checks, CSRF header guard.

## Quick start

You need Python 3.9+ and Docker (for Redis Stack).

```bash
# 1. Start Redis Stack (database + RedisInsight GUI at http://localhost:8001)
docker compose up -d

# 2. Create a virtual environment and install packages
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure
cp .env.example .env              # Windows: copy .env.example .env

# 4. Run
python app.py
```

Open **http://127.0.0.1:5000**. On first start the app creates the search index, the admin account and 8 demo students (7 public, 1 private).

| Account | Email | Password |
|---|---|---|
| Admin | `admin@college.edu` | `Admin@123` |
| Demo student | `aarav.sharma@demo.edu` | `Student@123` |

Other demo students use the same password: `diya.nair`, `rohan.gowda`, `ananya.rao`, `kabir.mehta`, `meera.iyer`, `sahil.khan`, `priya.verma` (all `@demo.edu`; Priya's portfolio is private).

**No Docker?** Create a free database on Redis Cloud (make sure the **Search** and **JSON** capabilities are on), then put its URL in `.env` as `REDIS_URL=rediss://default:<password>@<host>:<port>`.

## Project structure

```
app.py              app factory, security headers, error pages, start-up (index + seed)
config.py           settings from .env
db.py               ALL Redis code: documents, index, search, stats, photos
validators.py       cleaning + validation of every input
auth.py             password hashing, JWT cookie, role decorators
media.py            photo check + resize (Pillow)
seed.py             admin bootstrap + demo students (python seed.py)
routes/             pages.py, auth_api.py, students_api.py, public_api.py, admin_api.py
templates/          Jinja pages (gallery, login, register, dashboard, portfolio, admin)
static/             css/style.css, js/*.js
docker-compose.yml  Redis Stack
```

## How the data is stored in Redis

| Key | Type | Holds |
|---|---|---|
| `student:<id>` | JSON | the whole portfolio |
| `user:<id>` | JSON | login account (email, password hash, role) |
| `email:<email>` | string | user id (guarantees unique emails) |
| `usn:<USN>` | string | student id (guarantees unique USNs) |
| `photo:<id>` | binary | 400x400 JPEG |
| `rl:login:*` | counter + TTL | failed-login rate limit |

One portfolio document:

```json
{
  "id": "a1b2c3d4e5",
  "name": "Aarav Sharma", "usn": "1BI21CS014", "department": "CSE", "year": 4,
  "about": "Final-year CSE student...",
  "skills": ["Python", "React", "SQL"],
  "projects": [{"title": "...", "description": "...", "tech": ["Flask"], "link": ""}],
  "certifications": [{"name": "...", "issuer": "Coursera", "year": 2024, "link": ""}],
  "achievements": ["Winner, hackathon 2024"],
  "links": {"github": "", "linkedin": "", "website": ""},
  "is_public": 1, "has_photo": 0, "created_at": 1730000000, "updated_at": 1730000000
}
```

The search index `idx:students` covers every `student:*` document (name and about as full-text, department, skills, USN and email as tags, year and visibility as numbers). Try it in RedisInsight or `redis-cli`:

```
FT.SEARCH idx:students "@skills:{python} @department:{CSE}"
FT.SEARCH idx:students "@name:(aar*)"
JSON.GET student:<id> $.skills
```

## API summary

| Method and path | Who | What |
|---|---|---|
| `POST /api/auth/register`, `/login`, `/logout`; `GET /api/auth/me` | anyone | accounts |
| `GET /api/public/students?q=&department=&year=&skill=&page=` | anyone | public gallery search |
| `GET /api/students/<id or me>` | public or owner/admin | read a portfolio |
| `PUT /api/students/<id or me>` | owner or admin | save a portfolio |
| `POST` / `DELETE /api/students/<id>/photo` | owner or admin | photo |
| `GET /api/admin/students`, `/stats`, `/export.csv` | admin | manage and report |
| `PATCH /api/admin/students/<id>/visibility`, `DELETE /api/admin/students/<id>` | admin | moderate |

## Why NoSQL for this project

A portfolio is one nested object: a student with a list of skills, a list of projects, a list of certifications. In SQL this becomes four or five tables and several joins to show one page. In a document database it is one JSON document read in one call, and adding a new section later (say, internships) needs no schema migration.

## Viva questions, short answers

**Why did you use NoSQL?**
A portfolio is nested data, with lists of skills, projects and certificates. A document store keeps it as one JSON document, so one read gives the whole page and I can add new sections without altering tables.

**Why Redis, and not MongoDB?**
Redis Stack gives me JSON documents plus a built-in search engine in one server. It keeps data in memory, so reads are very fast, and it also handles my login rate limiting and unique-email checks.

**Is Redis only a cache?**
No. Redis Stack is a real database. Here it is configured with append-only persistence, so data survives restarts.

**What are RedisJSON and RediSearch?**
RedisJSON lets me store and update JSON documents. RediSearch builds an index over them, so I can do full-text search, filters and sorting without scanning every document.

**How does search work?**
I created an index on `student:*` keys. Name and bio are text fields, department and skills are tag fields, year is numeric. The search box builds one query string from the filters and Redis returns matching documents.

**How do you keep emails and USNs unique when there are no foreign keys?**
I use `SET key value NX`, which only succeeds if the key does not exist. It is atomic, so two people registering at the same time cannot both win.

**How is login secured?**
Passwords are hashed, never stored plainly. After login the server sets a signed JWT in an HttpOnly cookie, so JavaScript cannot read it. Repeated wrong passwords get blocked for 15 minutes.

**How do you separate student and admin access?**
Every protected route checks the role on the server. A student can only edit their own id, and admin routes return 403 for anyone else. The role is read from the database, not from the token.

**Can a student register as admin?**
No. Registration always creates a student. The admin account comes from the server's `.env` file.

**How do you prevent XSS and bad input?**
All input is validated and cleaned on the server. Pages are rendered with escaping, and links must start with http or https.

**Where are photos stored?**
In Redis as a resized 400x400 JPEG under `photo:<id>`. The upload is checked with Pillow to confirm it is really an image.

**What are the limitations, and how would you scale it?**
The admin stats read all documents, which is fine for hundreds or a few thousand students. For more, I would switch to Redis aggregation queries and add a Redis replica for reads.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Cannot connect to Redis` | Run `docker compose up -d`, or check `REDIS_URL` in `.env`. |
| `no RediSearch/RedisJSON modules` | You are on plain Redis. Use the Redis Stack image or Redis Cloud. |
| Logged out after every restart | Set `SECRET_KEY` in `.env`. |
| PDF button opens the print dialog | The PDF library could not load (offline). Choose "Save as PDF" in the dialog. |
| Want fresh demo data | Run `docker compose down -v` to wipe Redis, then start again. |

## Ideas to extend

Email verification, password reset, resume upload, skill endorsements by faculty, dark mode, Dockerfile for the Flask app.
