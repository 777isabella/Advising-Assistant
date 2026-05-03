import os
import secrets
import time

from flask import Flask, render_template, request, redirect, session
from werkzeug.security import check_password_hash, generate_password_hash

import db
from data import (
    DEGREE_PLANS,
    SEED_COURSES,
    SEED_FACULTY_ADVISEES,
    SEED_PREREQUISITES,
    SEED_STUDENTS,
    SEED_USERS,
    flatten_degree_plan,
)
from recommendation import RecommendationEngine
from requirements import build_requirements_snapshot

app = Flask(__name__)
app.secret_key = os.environ.get("ADVISING_SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

LOGIN_RATE_LIMIT = {}

engine = RecommendationEngine()


def seed_database(conn):
    def ensure_course_exists(course_id):
        if (
            conn.execute(
                "SELECT 1 FROM courses WHERE course_id = ?",
                (course_id,),
            ).fetchone()
            is None
        ):
            conn.execute(
                "INSERT INTO courses(course_id, description, credits) VALUES(?,?,?)",
                (course_id, course_id, 3),
            )

    merged_users = dict(SEED_USERS)
    for student_username in SEED_STUDENTS.keys():
        if student_username not in merged_users:
            merged_users[student_username] = {"password": "123", "role": "student"}

    for username, payload in merged_users.items():
        existing = conn.execute(
            "SELECT password FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        desired_password = payload["password"]
        is_hash = (
            isinstance(desired_password, str)
            and (desired_password.startswith("pbkdf2:") or desired_password.startswith("scrypt:"))
        )
        if not is_hash:
            desired_password = generate_password_hash(desired_password)

        if existing is None:
            conn.execute(
                "INSERT INTO users(username, password, role) VALUES(?,?,?)",
                (username, desired_password, payload["role"]),
            )
        else:
            existing_password = existing["password"]
            is_existing_hash = (
                isinstance(existing_password, str)
                and (existing_password.startswith("pbkdf2:") or existing_password.startswith("scrypt:"))
            )
            if not is_existing_hash:
                conn.execute(
                    "UPDATE users SET password = ?, role = ? WHERE username = ?",
                    (desired_password, payload["role"], username),
                )
        existing_role = conn.execute(
            "SELECT role FROM users WHERE username = ?",
            (username,),
        ).fetchone()["role"]
        if existing_role != payload["role"]:
            conn.execute(
                "UPDATE users SET role = ? WHERE username = ?",
                (payload["role"], username),
            )

        if payload["role"] == "student":
            conn.execute("INSERT OR IGNORE INTO students(username) VALUES(?)", (username,))
            conn.execute("DELETE FROM faculty WHERE username = ?", (username,))
        else:
            conn.execute("INSERT OR IGNORE INTO faculty(username) VALUES(?)", (username,))
            conn.execute("DELETE FROM students WHERE username = ?", (username,))

    for course_id, payload in SEED_COURSES.items():
        conn.execute(
            "INSERT OR REPLACE INTO courses(course_id, description, credits) VALUES(?,?,?)",
            (course_id, payload["description"], payload["credits"]),
        )

    conn.execute("DELETE FROM prerequisites")
    for course_id, prereqs in SEED_PREREQUISITES.items():
        for prereq_course_id in prereqs:
            conn.execute(
                "INSERT OR IGNORE INTO prerequisites(course_id, prereq_course_id) VALUES(?,?)",
                (course_id, prereq_course_id),
            )

    for faculty_username, advisees in SEED_FACULTY_ADVISEES.items():
        for student_username in advisees:
            conn.execute(
                "INSERT OR IGNORE INTO faculty_advisees(faculty_username, student_username) VALUES(?,?)",
                (faculty_username, student_username),
            )

    for student_username, payload in SEED_STUDENTS.items():
        conn.execute("DELETE FROM degree_plan WHERE student_username = ?", (student_username,))
        degree_plan_key = payload.get("degree_plan_key")
        degree_plan = payload.get("degree_plan")
        if degree_plan is None and degree_plan_key is not None:
            degree_plan = flatten_degree_plan(degree_plan_key)
        if degree_plan is None:
            degree_plan = []
        for idx, course_id in enumerate(degree_plan):
            ensure_course_exists(course_id)
            conn.execute(
                "INSERT OR REPLACE INTO degree_plan(student_username, course_id, sort_order) VALUES(?,?,?)",
                (student_username, course_id, idx),
            )

        transcript = payload.get("transcript", [])
        conn.execute("DELETE FROM enrollments WHERE student_username = ?", (student_username,))
        for row in transcript:
            ensure_course_exists(row["course_id"])
            conn.execute(
                "INSERT INTO enrollments(student_username, course_id, term, grade) VALUES(?,?,?,?)",
                (student_username, row["course_id"], row.get("term"), row.get("grade")),
            )


db.init_db(seed_fn=seed_database)


def issue_csrf_token():
    token = secrets.token_urlsafe(32)
    session["csrf_token"] = token
    return token


def validate_csrf():
    token = session.get("csrf_token")
    submitted = request.form.get("csrf_token")
    return bool(token) and bool(submitted) and secrets.compare_digest(token, submitted)


def require_login():
    if "user" not in session:
        return False
    return True


def can_access_student(student_username):
    if not require_login():
        return False
    if session.get("role") == "student":
        return student_username == session.get("user")
    if session.get("role") == "faculty":
        return student_username in set(db.list_advisees(session.get("user")))
    return False


def login_rate_limited(username):
    now = time.time()
    window_seconds = 60
    max_attempts = 10
    attempts = [t for t in LOGIN_RATE_LIMIT.get(username, []) if now - t < window_seconds]
    LOGIN_RATE_LIMIT[username] = attempts
    return len(attempts) >= max_attempts


def record_failed_login(username):
    now = time.time()
    LOGIN_RATE_LIMIT.setdefault(username, []).append(now)


@app.after_request
def add_security_headers(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "same-origin")
    resp.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;",
    )
    return resp

#-----------Register--------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not validate_csrf():
            return "Invalid CSRF token", 400
        #user and passwd fields
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        if db.get_user(username) is not None:
            return "Username already exists!"

        db.create_user(username, generate_password_hash(password), role)

        if role == "student":
            default_plan = flatten_degree_plan("UTRGV_CYBI_BS_2025_2026")
            with db.connect() as conn:
                for idx, course_id in enumerate(default_plan):
                    conn.execute(
                        "INSERT INTO degree_plan(student_username, course_id, sort_order) VALUES(?,?,?)",
                        (username, course_id, idx),
                    )

        return redirect("/")

    issue_csrf_token()
    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if not validate_csrf():
            return "Invalid CSRF token", 400
        #user and passwd fields
        username = request.form["username"]
        password = request.form["password"]

        if login_rate_limited(username):
            db.log_audit("login_rate_limited", actor_username=username)
            return "Too many login attempts. Try again later.", 429

        user = db.get_user(username)
        if user is not None and check_password_hash(user["password"], password):
            session["user"] = username
            session["role"] = user["role"]
            db.log_audit("login_success", actor_username=username)
            return redirect("/dashboard")

        record_failed_login(username)
        db.log_audit("login_failed", actor_username=username)

    issue_csrf_token()

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    #privacy reason, so s to not be able to bypass by going to /dashboard
    if "user" not in session:
        return redirect("/")

    role = session["role"]

    if role == "student":
        return render_template("dashboard.html", role=role)

    if role == "faculty":
        advisees = db.list_advisees(session["user"])
        return render_template("dashboard.html", role=role, advisees=advisees)


# ---------------- TRANSCRIPT ----------------
@app.route("/transcript/<student>")
def transcript(student):
    if not can_access_student(student):
        return "Access Denied", 403

    db.log_audit("view_transcript", actor_username=session.get("user"), target_username=student)

    transcript_rows = db.get_transcript_rows(student)
    gpa = db.calculate_gpa(transcript_rows)
    return render_template(
        "transcript.html", student=student, transcript_rows=transcript_rows, gpa=gpa
    )

# ---------------- RECOMMENDATIONS ----------------
@app.route("/recommend/<student>")
def recommend(student):
    if not can_access_student(student):
        return "Access Denied", 403

    db.log_audit("view_recommendations", actor_username=session.get("user"), target_username=student)
    completed = db.get_student_completed_courses(student)
    in_progress = db.get_student_in_progress_courses(student)
    degree_plan = db.get_student_degree_plan(student)
    prereqs = db.get_prerequisites_map()
    recs = engine.generate(
        completed,
        degree_plan,
        prereqs,
        exclude=list(set(completed) | set(in_progress)),
        limit=6,
    )

    return render_template("recommendations.html", recs=recs)


@app.route("/requirements/<student>")
def requirements(student):
    if not can_access_student(student):
        return "Access Denied", 403

    db.log_audit("view_requirements", actor_username=session.get("user"), target_username=student)

    snapshot = build_requirements_snapshot(student)
    return render_template("requirements.html", **snapshot)


# --------------course details page-----------------
#this used for the course infromation, if you click on a course,
#you will be redirected to a page with the course information
#possibly might convert this into a pop-up instead like UTRGV Assist
@app.route("/course/<course_id>")
def course_detail(course_id):
    course = db.get_course(course_id)

    if not course:
        return "Course not found"

    return render_template("course.html", course_id=course_id, course=course)


# ------------------ STUDENT'S REPORT -------------------------
#This acts like a UTRGV's student degreeWorks
#much more readable
@app.route("/report/<student>")
def report(student):
    if not can_access_student(student):
        return "Access Denied", 403

    db.log_audit("view_report", actor_username=session.get("user"), target_username=student)
    completed = db.get_student_completed_courses(student)
    in_progress = db.get_student_in_progress_courses(student)
    degree_plan = db.get_student_degree_plan(student)
    prereqs = db.get_prerequisites_map()
    recs = engine.generate(
        completed,
        degree_plan,
        prereqs,
        exclude=list(set(completed) | set(in_progress)),
        limit=6,
    )

    snapshot = build_requirements_snapshot(student)

    return render_template(
        "report.html",
        student=student,
        completed_courses=sorted(set(completed)),
        in_progress_courses=sorted(set(in_progress)),
        remaining_courses=[c for c in degree_plan if c not in set(completed) and c not in set(in_progress)],
        recommended_courses=recs,
        eligible_courses=snapshot["eligible_courses"],
        blocked_courses=snapshot["blocked_courses"],
        missing_prereqs=snapshot["missing_prereqs"],
    )

#--------------logout----------------
@app.route("/logout")
def logout():
    session.clear()  # removes all session data
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
