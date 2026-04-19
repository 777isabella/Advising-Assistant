from flask import Flask, render_template, request, redirect, session
from data import users, students, prerequisites, faculty_advisees, courses
from recommendation import RecommendationEngine

app = Flask(__name__)
app.secret_key = "secret"

engine = RecommendationEngine()
#-----------Register--------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        #user and passwd fields
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        if username in users:
            return "Username already exists!"

        users[username] = {"password": password, "role": role}

        # If student, initialize empty data
        #this is for testing purposes
        #will remove later
        if role == "student":
            students[username] = {
                "transcript": [],
                "degree_plan": ["CYBI1", "CYBI2", "MATH1", "MATH2"]
            }

        return redirect("/")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        #user and passwd fields
        username = request.form["username"]
        password = request.form["password"]

        #authentication of credentials
        if username in users and users[username]["password"] == password:
            session["user"] = username
            session["role"] = users[username]["role"]
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
        advisees = faculty_advisees.get(session["user"], [])
        return render_template("dashboard.html", role=role, advisees=advisees)


# ---------------- TRANSCRIPT ----------------
@app.route("/transcript/<student>")
def transcript(student):
    if "user" not in session:
        return redirect("/")

    #security check
    if session["role"] == "student" and student != session["user"]:
        return "Access Denied"

    data = students.get(student)

    return render_template("transcript.html", student=student, data=data)

# ---------------- RECOMMENDATIONS ----------------
@app.route("/recommend/<student>")
def recommend(student):
    if "user" not in session:
        return redirect("/")

    if session["role"] == "student" and student != session["user"]:
        return "Access Denied"
    data = students.get(student)

    completed = data["transcript"]
    degree_plan = data["degree_plan"]
    #calls recommendationEngine which inherits from course and student classes
    recs = engine.generate(completed, degree_plan, prerequisites)

    return render_template("recommendations.html", recs=recs)


# --------------course details page-----------------
#this used for the course infromation, if you click on a course,
#you will be redirected to a page with the course information
#possibly might convert this into a pop-up instead like UTRGV Assist
@app.route("/course/<course_id>")
def course_detail(course_id):
    course = courses.get(course_id)

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
    data = students.get(student)

    if not data:
        return "Student not found"

    completed = data["transcript"]
    degree_plan = data["degree_plan"]

    recs = engine.generate(completed, degree_plan, prerequisites)

    #outputs
    report_text = f"""
    Advising Report for {student}

    Completed Courses:
    {', '.join(completed)}

    Remaining Courses:
    {', '.join([c for c in degree_plan if c not in completed])}

    Recommended Next Courses:
    {', '.join(recs)}
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