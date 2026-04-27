from flask import Flask, render_template, request, redirect, session

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
app.secret_key = "secret"

engine = RecommendationEngine()


def seed_database(conn):
    merged_users = dict(SEED_USERS)
    for student_username in SEED_STUDENTS.keys():
        if student_username not in merged_users:
            merged_users[student_username] = {"password": "123", "role": "student"}

    for username, payload in merged_users.items():
        conn.execute(
            "INSERT OR IGNORE INTO users(username, password, role) VALUES(?,?,?)",
            (username, payload["password"], payload["role"]),
        )
        if payload["role"] == "student":
            conn.execute("INSERT OR IGNORE INTO students(username) VALUES(?)", (username,))
        else:
            conn.execute("INSERT OR IGNORE INTO faculty(username) VALUES(?)", (username,))

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
            conn.execute(
                "INSERT OR REPLACE INTO degree_plan(student_username, course_id, sort_order) VALUES(?,?,?)",
                (student_username, course_id, idx),
            )

        transcript = payload.get("transcript", [])
        conn.execute("DELETE FROM enrollments WHERE student_username = ?", (student_username,))
        for row in transcript:
            conn.execute(
                "INSERT INTO enrollments(student_username, course_id, term, grade) VALUES(?,?,?,?)",
                (student_username, row["course_id"], row.get("term"), row.get("grade")),
            )


db.init_db(seed_fn=seed_database)

#-----------Register--------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        #user and passwd fields
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        if db.get_user(username) is not None:
            return "Username already exists!"

        db.create_user(username, password, role)

        if role == "student":
            default_plan = flatten_degree_plan("UTRGV_CYBI_BS_2025_2026")
            with db.connect() as conn:
                for idx, course_id in enumerate(default_plan):
                    conn.execute(
                        "INSERT INTO degree_plan(student_username, course_id, sort_order) VALUES(?,?,?)",
                        (username, course_id, idx),
                    )

        return redirect("/")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        #user and passwd fields
        username = request.form["username"]
        password = request.form["password"]

        user = db.get_user(username)
        if user is not None and user["password"] == password:
            session["user"] = username
            session["role"] = user["role"]
            return redirect("/dashboard")

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
    if "user" not in session:
        return redirect("/")

    #security check
    if session["role"] == "student" and student != session["user"]:
        return "Access Denied"

    transcript_rows = db.get_transcript_rows(student)
    gpa = db.calculate_gpa(transcript_rows)
    return render_template(
        "transcript.html", student=student, transcript_rows=transcript_rows, gpa=gpa
    )

# ---------------- RECOMMENDATIONS ----------------
@app.route("/recommend/<student>")
def recommend(student):
    if "user" not in session:
        return redirect("/")

    if session["role"] == "student" and student != session["user"]:
        return "Access Denied"
    completed = db.get_student_completed_courses(student)
    degree_plan = db.get_student_degree_plan(student)
    prereqs = db.get_prerequisites_map()
    recs = engine.generate(completed, degree_plan, prereqs)

    return render_template("recommendations.html", recs=recs)


@app.route("/requirements/<student>")
def requirements(student):
    if "user" not in session:
        return redirect("/")

    if session["role"] == "student" and student != session["user"]:
        return "Access Denied"

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
    if "user" not in session:
        return redirect("/")

    #security check
    if session["role"] == "student" and student != session["user"]:
        return "Access Denied"
    completed = db.get_student_completed_courses(student)
    degree_plan = db.get_student_degree_plan(student)
    prereqs = db.get_prerequisites_map()
    recs = engine.generate(completed, degree_plan, prereqs)

    snapshot = build_requirements_snapshot(student)

    #outputs
    report_text = f"""
    Advising Report for {student}

    Completed Courses:
    {', '.join(completed)}

    Remaining Courses:
    {', '.join([c for c in degree_plan if c not in completed])}

    Recommended Next Courses:
    {', '.join(recs)}

    Eligible Courses (Prereqs Met):
    {', '.join(snapshot['eligible_courses'])}

    Blocked Courses (Missing Prereqs):
    {', '.join(snapshot['blocked_courses'])}
    """

    return f"<pre>{report_text}</pre>"

#--------------logout----------------
@app.route("/logout")
def logout():
    session.clear()  # removes all session data
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
