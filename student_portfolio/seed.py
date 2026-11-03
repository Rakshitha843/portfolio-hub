"""Admin bootstrap + demo students.  Run `python seed.py` to (re)load missing demo data."""
import config
import db
from auth import hash_password

NO_LINKS = {"github": "", "linkedin": "", "website": ""}


def _links(handle, github=True, linkedin=True):
    # example.com is a reserved placeholder domain, so no real person's profile is linked.
    return {
        "github": "https://example.com/%s-github" % handle if github else "",
        "linkedin": "https://example.com/%s-linkedin" % handle if linkedin else "",
        "website": "",
    }


def _project(title, description, tech):
    return {"title": title, "description": description, "tech": tech, "link": ""}


def _cert(name, issuer, year):
    return {"name": name, "issuer": issuer, "year": year, "link": ""}


DEMO_STUDENTS = [
    {
        "name": "Aarav Sharma", "email": "aarav.sharma@demo.edu", "usn": "1BI21CS014",
        "department": "CSE", "year": 4, "is_public": 1,
        "about": "Final-year CSE student who likes turning messy data into useful products. "
                 "Currently building recommendation systems and full-stack apps.",
        "skills": ["Python", "JavaScript", "React", "Flask", "SQL", "Machine Learning", "Git", "Docker"],
        "projects": [
            _project("Campus Placement Predictor",
                     "Predicts a student's placement likelihood from academics and skills, "
                     "with an explainable score for each factor.",
                     ["Python", "scikit-learn", "Flask"]),
            _project("Smart Attendance Tracker",
                     "Face-recognition attendance for classrooms with a faculty dashboard "
                     "and monthly reports.",
                     ["OpenCV", "Python", "SQLite"]),
        ],
        "certifications": [_cert("Machine Learning Specialization", "Coursera", 2024),
                           _cert("Cloud Practitioner", "AWS", 2024)],
        "achievements": ["Winner, inter-college hackathon 2024", "Class representative for two semesters"],
        "links": _links("aarav"),
    },
    {
        "name": "Diya Nair", "email": "diya.nair@demo.edu", "usn": "1BI21IS027",
        "department": "ISE", "year": 4, "is_public": 1,
        "about": "Backend-leaning developer who enjoys clean APIs and reliable deployments. "
                 "Looking for a software engineering fresher role.",
        "skills": ["Java", "Spring Boot", "React", "MySQL", "AWS", "Git", "REST APIs"],
        "projects": [
            _project("Hostel Mess Feedback Portal",
                     "Residents rate meals daily and wardens see weekly trends and complaints.",
                     ["Java", "Spring Boot", "MySQL"]),
            _project("Event Registration System",
                     "Club event sign-ups with QR check-in used by three college fests.",
                     ["React", "Node.js", "MongoDB"]),
        ],
        "certifications": [_cert("Java SE Associate", "Oracle", 2023)],
        "achievements": ["Technical lead, ISE department fest 2024"],
        "links": _links("diya"),
    },
    {
        "name": "Rohan Gowda", "email": "rohan.gowda@demo.edu", "usn": "1BI22AI009",
        "department": "AIML", "year": 3, "is_public": 1,
        "about": "Third-year AIML student fascinated by computer vision. "
                 "I like experiments that run on a laptop, not just a GPU cluster.",
        "skills": ["Python", "PyTorch", "OpenCV", "Machine Learning", "Deep Learning", "NumPy", "Pandas"],
        "projects": [
            _project("Crop Disease Detector",
                     "A CNN that identifies leaf diseases from phone photos, "
                     "trained on a public plant dataset.",
                     ["PyTorch", "Python", "Streamlit"]),
            _project("Traffic Sign Recognition",
                     "Classifies 43 traffic sign types with a lightweight model.",
                     ["TensorFlow", "OpenCV"]),
        ],
        "certifications": [_cert("Deep Learning Specialization", "Coursera", 2025)],
        "achievements": ["Runner-up, college AI paper presentation"],
        "links": _links("rohan"),
    },
    {
        "name": "Ananya Rao", "email": "ananya.rao@demo.edu", "usn": "1BI22DS015",
        "department": "Data Science", "year": 3, "is_public": 1,
        "about": "I turn spreadsheets into stories. Comfortable with SQL, dashboards "
                 "and explaining numbers to non-technical people.",
        "skills": ["Python", "SQL", "Power BI", "Tableau", "Pandas", "Statistics", "Excel"],
        "projects": [
            _project("Retail Sales Forecasting Dashboard",
                     "Monthly demand forecasts with seasonality for a small retailer.",
                     ["Python", "Pandas", "Power BI"]),
            _project("Student Performance Analysis",
                     "Finds which study habits correlate with higher internal marks.",
                     ["Python", "Seaborn"]),
        ],
        "certifications": [_cert("Data Analytics Certificate", "Google", 2024)],
        "achievements": ["Top 10, college data-visualisation contest"],
        "links": _links("ananya", github=False),
    },
    {
        "name": "Kabir Mehta", "email": "kabir.mehta@demo.edu", "usn": "1BI21EC033",
        "department": "ECE", "year": 4, "is_public": 1,
        "about": "Embedded systems tinkerer. Happiest with a soldering iron, a logic "
                 "analyser and a problem that involves sensors.",
        "skills": ["C", "Embedded C", "Arduino", "Raspberry Pi", "IoT", "MATLAB", "PCB Design"],
        "projects": [
            _project("Smart Irrigation Controller",
                     "Soil-moisture based watering with a phone app and low-power sleep modes.",
                     ["Arduino", "IoT", "C"]),
            _project("Gesture Controlled Robot Car",
                     "Drives a robot car from hand tilt using an accelerometer glove.",
                     ["Embedded C", "Arduino"]),
        ],
        "certifications": [_cert("Embedded Systems Essentials", "NPTEL", 2023)],
        "achievements": ["Best project, ECE project exhibition 2024"],
        "links": _links("kabir", github=False),
    },
    {
        "name": "Meera Iyer", "email": "meera.iyer@demo.edu", "usn": "1BI23CS042",
        "department": "CSE", "year": 2, "is_public": 1,
        "about": "Second-year student building a strong base in data structures and web development.",
        "skills": ["Python", "C", "HTML", "CSS", "JavaScript", "Data Structures", "Git"],
        "projects": [
            _project("Personal Budget Tracker",
                     "Track monthly spending by category with simple charts.",
                     ["HTML", "CSS", "JavaScript"]),
        ],
        "certifications": [],
        "achievements": ["Solved 150+ problems on coding platforms", "Volunteer, coding club"],
        "links": _links("meera", linkedin=False),
    },
    {
        "name": "Sahil Khan", "email": "sahil.khan@demo.edu", "usn": "1BI21ME019",
        "department": "Mechanical", "year": 4, "is_public": 1,
        "about": "Mechanical engineering student focused on design for manufacturing and low-cost assistive devices.",
        "skills": ["SolidWorks", "AutoCAD", "ANSYS", "3D Printing", "MATLAB", "Python"],
        "projects": [
            _project("Low-cost Prosthetic Hand",
                     "A 3D-printed tendon-driven hand costing under a tenth of commercial options.",
                     ["SolidWorks", "3D Printing"]),
        ],
        "certifications": [_cert("Certified SolidWorks Associate", "Dassault Systemes", 2024)],
        "achievements": ["Finalist, national mechanical design challenge"],
        "links": _links("sahil", github=False),
    },
    {
        "name": "Priya Verma", "email": "priya.verma@demo.edu", "usn": "1BI22CS051",
        "department": "CSE", "year": 3, "is_public": 0,
        "about": "Draft portfolio - still adding projects. (Private: only Priya and admins can see it.)",
        "skills": ["Java", "Python", "SQL", "React"],
        "projects": [
            _project("Library Management System",
                     "Issue, return and fine tracking for a small college library.",
                     ["Java", "MySQL"]),
        ],
        "certifications": [],
        "achievements": [],
        "links": dict(NO_LINKS),
    },
]


def ensure_admin():
    """Create the admin account from ADMIN_EMAIL / ADMIN_PASSWORD if it does not exist yet."""
    created = db.create_admin(config.ADMIN_EMAIL, hash_password(config.ADMIN_PASSWORD))
    return created is not None


def seed_demo():
    """Insert demo students that are not already present. Returns how many were added."""
    password_hash = hash_password(config.DEMO_STUDENT_PASSWORD)
    added = 0
    for profile in DEMO_STUDENTS:
        data = dict(profile)
        email = data.pop("email")
        try:
            db.create_student_account(email, password_hash, data)
            added += 1
        except db.DuplicateError:
            continue
    return added


if __name__ == "__main__":
    db.ensure_index()
    made_admin = ensure_admin()
    count = seed_demo()
    db.mark_seeded()
    print("Admin:    %s %s" % (config.ADMIN_EMAIL, "(created)" if made_admin else "(already existed)"))
    print("Students: %d added (password for all demo students: %s)" % (count, config.DEMO_STUDENT_PASSWORD))
