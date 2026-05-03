import db
from recommendation import RecommendationEngine


def build_requirements_snapshot(student_username):
    completed = set(db.get_student_completed_courses(student_username))
    in_progress = set(db.get_student_in_progress_courses(student_username))
    degree_plan = db.get_student_degree_plan(student_username)
    prereqs = db.get_prerequisites_map()

    in_progress_courses = [c for c in degree_plan if c in in_progress and c not in completed]
    remaining = [c for c in degree_plan if c not in completed and c not in in_progress]

    eligible = []
    blocked = []
    missing_prereqs = {}
    for course_id in remaining:
        course_prereqs = prereqs.get(course_id, [])
        missing = [p for p in course_prereqs if p not in completed]
        if missing:
            blocked.append(course_id)
            missing_prereqs[course_id] = missing
        else:
            eligible.append(course_id)

    engine = RecommendationEngine()
    recommended = engine.generate(
        list(completed),
        degree_plan,
        prereqs,
        exclude=list(completed | in_progress),
        limit=6,
    )

    return {
        "student": student_username,
        "degree_plan": degree_plan,
        "completed_courses": sorted(completed),
        "in_progress_courses": in_progress_courses,
        "remaining_courses": remaining,
        "eligible_courses": eligible,
        "blocked_courses": blocked,
        "missing_prereqs": missing_prereqs,
        "recommended_courses": recommended,
    }
