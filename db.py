import os
import sqlite3


DB_PATH = os.environ.get("ADVISING_DB_PATH") or os.path.join(
    os.path.dirname(__file__), "advising.db"
)


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(seed_fn=None):
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              username TEXT PRIMARY KEY,
              password TEXT NOT NULL,
              role TEXT NOT NULL CHECK(role IN ('student','faculty'))
            );

            CREATE TABLE IF NOT EXISTS students (
              username TEXT PRIMARY KEY,
              FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS faculty (
              username TEXT PRIMARY KEY,
              FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS faculty_advisees (
              faculty_username TEXT NOT NULL,
              student_username TEXT NOT NULL,
              PRIMARY KEY (faculty_username, student_username),
              FOREIGN KEY(faculty_username) REFERENCES faculty(username) ON DELETE CASCADE,
              FOREIGN KEY(student_username) REFERENCES students(username) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS courses (
              course_id TEXT PRIMARY KEY,
              description TEXT NOT NULL,
              credits INTEGER NOT NULL CHECK(credits > 0)
            );

            CREATE TABLE IF NOT EXISTS prerequisites (
              course_id TEXT NOT NULL,
              prereq_course_id TEXT NOT NULL,
              PRIMARY KEY (course_id, prereq_course_id),
              FOREIGN KEY(course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
              FOREIGN KEY(prereq_course_id) REFERENCES courses(course_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS degree_plan (
              student_username TEXT NOT NULL,
              course_id TEXT NOT NULL,
              sort_order INTEGER NOT NULL,
              PRIMARY KEY (student_username, course_id),
              FOREIGN KEY(student_username) REFERENCES students(username) ON DELETE CASCADE,
              FOREIGN KEY(course_id) REFERENCES courses(course_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS enrollments (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              student_username TEXT NOT NULL,
              course_id TEXT NOT NULL,
              term TEXT,
              grade TEXT,
              FOREIGN KEY(student_username) REFERENCES students(username) ON DELETE CASCADE,
              FOREIGN KEY(course_id) REFERENCES courses(course_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS audit_log (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ts DATETIME DEFAULT CURRENT_TIMESTAMP,
              actor_username TEXT,
              action TEXT NOT NULL,
              target_username TEXT,
              metadata TEXT
            );
            """
        )

        if seed_fn is None:
            return

        user_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        course_count = conn.execute("SELECT COUNT(*) AS c FROM courses").fetchone()["c"]
        has_new_plan_course = (
            conn.execute(
                "SELECT 1 FROM courses WHERE course_id = ?",
                ("ENGL1301",),
            ).fetchone()
            is not None
        )

        has_plaintext_passwords = (
            conn.execute(
                """
                SELECT 1
                FROM users
                WHERE password NOT LIKE 'pbkdf2:%' AND password NOT LIKE 'scrypt:%'
                LIMIT 1
                """
            ).fetchone()
            is not None
        )

        if (
            user_count == 0
            or course_count == 0
            or not has_new_plan_course
            or has_plaintext_passwords
        ):
            seed_fn(conn)


def get_user(username):
    with connect() as conn:
        return conn.execute(
            "SELECT username, password, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()


def create_user(username, password, role):
    with connect() as conn:
        conn.execute(
            "INSERT INTO users(username, password, role) VALUES(?,?,?)",
            (username, password, role),
        )
        if role == "student":
            conn.execute("INSERT INTO students(username) VALUES(?)", (username,))
        else:
            conn.execute("INSERT INTO faculty(username) VALUES(?)", (username,))


def list_advisees(faculty_username):
    with connect() as conn:
        rows = conn.execute(
            "SELECT student_username FROM faculty_advisees WHERE faculty_username = ? ORDER BY student_username",
            (faculty_username,),
        ).fetchall()
        return [r["student_username"] for r in rows]


def get_student_degree_plan(student_username):
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT course_id
            FROM degree_plan
            WHERE student_username = ?
            ORDER BY sort_order ASC
            """,
            (student_username,),
        ).fetchall()
        return [r["course_id"] for r in rows]


def get_student_completed_courses(student_username):
    with connect() as conn:
        rows = conn.execute(
            "SELECT course_id FROM enrollments WHERE student_username = ? AND grade IS NOT NULL",
            (student_username,),
        ).fetchall()
        return [r["course_id"] for r in rows]


def get_student_in_progress_courses(student_username):
    with connect() as conn:
        rows = conn.execute(
            "SELECT course_id FROM enrollments WHERE student_username = ? AND grade IS NULL",
            (student_username,),
        ).fetchall()
        return [r["course_id"] for r in rows]


def get_transcript_rows(student_username):
    with connect() as conn:
        return conn.execute(
            """
            SELECT e.course_id, c.description, c.credits, e.term, e.grade
            FROM enrollments e
            JOIN courses c ON c.course_id = e.course_id
            WHERE e.student_username = ?
            ORDER BY e.id ASC
            """,
            (student_username,),
        ).fetchall()


def get_course(course_id):
    with connect() as conn:
        return conn.execute(
            "SELECT course_id, description, credits FROM courses WHERE course_id = ?",
            (course_id,),
        ).fetchone()


def get_prerequisites_map():
    with connect() as conn:
        rows = conn.execute(
            "SELECT course_id, prereq_course_id FROM prerequisites ORDER BY course_id, prereq_course_id"
        ).fetchall()
    result = {}
    for r in rows:
        result.setdefault(r["course_id"], []).append(r["prereq_course_id"])
    return result


def grade_points(letter):
    if letter is None:
        return None
    letter = letter.strip().upper()
    mapping = {
        "A": 4.0,
        "A-": 3.7,
        "B+": 3.3,
        "B": 3.0,
        "B-": 2.7,
        "C+": 2.3,
        "C": 2.0,
        "C-": 1.7,
        "D+": 1.3,
        "D": 1.0,
        "D-": 0.7,
        "F": 0.0,
    }
    return mapping.get(letter)


def calculate_gpa(transcript_rows):
    quality_points = 0.0
    credits_attempted = 0.0
    for r in transcript_rows:
        points = grade_points(r["grade"])
        if points is None:
            continue
        credits = float(r["credits"])
        quality_points += points * credits
        credits_attempted += credits

    if credits_attempted == 0:
        return None
    return round(quality_points / credits_attempted, 2)


def log_audit(action, actor_username=None, target_username=None, metadata=None):
    with connect() as conn:
        conn.execute(
            "INSERT INTO audit_log(actor_username, action, target_username, metadata) VALUES(?,?,?,?)",
            (actor_username, action, target_username, metadata),
        )
