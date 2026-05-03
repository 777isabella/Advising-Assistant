SEED_USERS = {
    "student1": {"password": "123", "role": "student"},
    "faculty1": {"password": "123", "role": "faculty"},
}


DEGREE_PLANS = {
    "UTRGV_CYBI_BS_2025_2026": {
        "title": "UTRGV Cyber Security BS (2025-2026)",
        "terms": [
            {
                "term": "Year 1 - Fall",
                "courses": ["ENGL1301", "MATH2412", "CYBI1101", "CSCI1380", "CRIJ1301"],
            },
            {
                "term": "Year 1 - Spring",
                "courses": ["ENGL1302", "CYBI2322", "CYBI2324", "CYBI2326", "STAT2334"],
            },
            {
                "term": "Year 2 - Fall",
                "courses": ["CYBI3318", "COMM1315", "CYBI3345", "CYBI4319", "BLAW3337"],
            },
            {
                "term": "Year 2 - Spring",
                "courses": ["CYBI3335", "CYBI3343", "CRIJ3316", "COMM3313", "LIFE_PHYS_SCI_1"],
            },
            {
                "term": "Year 3 - Fall",
                "courses": ["CYBI3346", "CYBI3101", "CYBI4347", "CYBI4365", "POLS2305", "PHIL2326"],
            },
            {
                "term": "Year 3 - Spring",
                "courses": [
                    "CYBI3331",
                    "LIFE_PHYS_SCI_2",
                    "FREE_ELECTIVE_1",
                    "POLS2306",
                    "PRESCRIBED_ELECTIVE_1",
                ],
            },
            {
                "term": "Year 4 - Fall",
                "courses": [
                    "AMERICAN_HISTORY_1",
                    "CREATIVE_ARTS_1",
                    "INFS3308",
                    "PRESCRIBED_ELECTIVE_2",
                    "FREE_ELECTIVE_2",
                ],
            },
            {
                "term": "Year 4 - Spring",
                "courses": [
                    "CYBI4340",
                    "PRESCRIBED_ELECTIVE_3",
                    "AMERICAN_HISTORY_2",
                    "SOC_BEHAV_SCI_1",
                ],
            },
        ],
    },
}


def flatten_degree_plan(plan_key):
    plan = DEGREE_PLANS.get(plan_key)
    if not plan:
        raise KeyError(f"Unknown degree plan: {plan_key}")
    courses = []
    for term in plan["terms"]:
        courses.extend(term["courses"])
    return courses


SEED_STUDENTS = {
    "student1": {
        "transcript": [
            {"course_id": "ENGL1301", "term": "Fall 2025", "grade": "A"},
            {"course_id": "MATH2412", "term": "Fall 2025", "grade": "B+"},
            {"course_id": "CYBI1101", "term": "Fall 2025", "grade": "A"},
        ],
        "degree_plan_key": "UTRGV_CYBI_BS_2025_2026",
    },
    "student2": {
        "transcript": [],
        "degree_plan_key": "UTRGV_CYBI_BS_2025_2026",
    },
    "isabella": {
        "transcript": [
            {"course_id": "ENGL1301", "term": "Summer 2024", "grade": "A"},
            {"course_id": "MATH2412", "term": "Summer 2024", "grade": "A"},
            {"course_id": "CYBI1101", "term": "Fall 2025", "grade": "A"},
            {"course_id": "CSCI1380", "term": "Summer 2024", "grade": "A"},
            {"course_id": "ENGL1302", "term": "Summer 2024", "grade": "A"},
            {"course_id": "CYBI2322", "term": "Spring 2025", "grade": "A"},
            {"course_id": "CYBI2324", "term": "Spring 2025", "grade": "A"},
            {"course_id": "CYBI3335", "term": "Spring 2026", "grade": None},
            {"course_id": "CYBI3331", "term": "Spring 2026", "grade": None},
            {"course_id": "BLAW3337", "term": "Summer 2025", "grade": "A"},
            {"course_id": "CYBI3343", "term": "Spring 2026", "grade": None},
            {"course_id": "COMM3313", "term": "Summer 2025", "grade": "A"},
            {"course_id": "CRIJ1301", "term": "Summer 2025", "grade": "A"},
            {"course_id": "POLS2305", "term": "Spring 2026", "grade": None},
            {"course_id": "CYBI2326", "term": "Fall 2025", "grade": "A"},
            {"course_id": "INFS3308", "term": "Fall 2024", "grade": "A"},
        ],
        "degree_plan_key": "UTRGV_CYBI_BS_2025_2026",
    },
}


SEED_COURSES = {
    "ENGL1301": {"description": "Rhetoric and Composition I", "credits": 3},
    "MATH2412": {"description": "Precalculus", "credits": 4},
    "CYBI1101": {"description": "Introduction to Cyberspace & Informatics", "credits": 1},
    "CSCI1380": {"description": "Introduction to Programming in Python", "credits": 3},
    "CRIJ1301": {"description": "Introduction to Criminal Justice", "credits": 3},
    "ENGL1302": {"description": "Rhetoric and Composition II", "credits": 3},
    "CYBI2322": {"description": "Foundations of Systems I", "credits": 3},
    "CYBI2324": {"description": "Foundations of Systems II", "credits": 3},
    "CYBI2326": {"description": "Programming of Cyber Systems & Reverse Engineering", "credits": 3},
    "STAT2334": {"description": "Applied Statistics for Health", "credits": 3},
    "CYBI3318": {"description": "Cryptography", "credits": 3},
    "COMM1315": {"description": "Public Speaking", "credits": 3},
    "CYBI3345": {"description": "Operating Systems and Security", "credits": 3},
    "CYBI4319": {"description": "Digital Forensics", "credits": 3},
    "BLAW3337": {"description": "Business Law I", "credits": 3},
    "CYBI3335": {"description": "Data Communications and Networking", "credits": 3},
    "CYBI3343": {
        "description": "Intrusion Detection, Incident Response and Information Assurance",
        "credits": 3,
    },
    "CRIJ3316": {"description": "Criminal Evidence & Proof", "credits": 3},
    "COMM3313": {"description": "Business and Technical Communication", "credits": 3},
    "LIFE_PHYS_SCI_1": {"description": "Life and Physical Sciences (Choose 1)", "credits": 4},
    "CYBI3346": {"description": "Distributed and Cloud Computing Security", "credits": 3},
    "CYBI3101": {"description": "Certification", "credits": 1},
    "CYBI4347": {"description": "Wireless and Mobile Security", "credits": 3},
    "CYBI4365": {"description": "Network Security", "credits": 3},
    "POLS2305": {"description": "U.S. Federal Govt & Politics", "credits": 3},
    "PHIL2326": {"description": "Ethics, Technology & Society", "credits": 3},
    "CYBI3331": {"description": "Software Engineering and Project Management", "credits": 3},
    "LIFE_PHYS_SCI_2": {"description": "Life and Physical Sciences (Choose 1)", "credits": 4},
    "FREE_ELECTIVE_1": {"description": "Free Elective - Any Level", "credits": 3},
    "POLS2306": {"description": "Texas Government & Politics", "credits": 3},
    "PRESCRIBED_ELECTIVE_1": {"description": "Prescribed Elective (Advanced Level)", "credits": 3},
    "AMERICAN_HISTORY_1": {"description": "American History (Choose 1)", "credits": 3},
    "CREATIVE_ARTS_1": {"description": "Creative Arts (Choose 1)", "credits": 3},
    "INFS3308": {"description": "Business Information Infrastructure", "credits": 3},
    "PRESCRIBED_ELECTIVE_2": {"description": "Prescribed Elective (Advanced Level)", "credits": 3},
    "FREE_ELECTIVE_2": {"description": "Free Elective - Any Level", "credits": 3},
    "CYBI4340": {"description": "Capstone Project", "credits": 3},
    "PRESCRIBED_ELECTIVE_3": {"description": "Prescribed Elective (Advanced Level)", "credits": 3},
    "AMERICAN_HISTORY_2": {"description": "American History (Choose 1)", "credits": 3},
    "SOC_BEHAV_SCI_1": {"description": "Social and Behavioral Sciences (Choose 1)", "credits": 3},
}


SEED_PREREQUISITES = {
    "ENGL1302": ["ENGL1301"],
    "CYBI2322": ["MATH2412", "CSCI1380"],
    "CYBI2324": ["MATH2412", "CSCI1380"],
    "CYBI2326": ["MATH2412", "CSCI1380"],
    "CYBI3318": ["CYBI2322", "CYBI2324", "CYBI2326"],
    "CYBI3345": ["CYBI2322", "CYBI2324", "CYBI2326"],
    "CYBI4319": ["CYBI2322", "CYBI2324", "CYBI2326"],
    "CYBI3335": ["CYBI2322", "CYBI2324", "CYBI2326"],
    "CYBI3343": ["CYBI3335"],
    "CYBI3346": ["CYBI3335"],
    "CYBI4347": ["CYBI3335"],
    "CYBI4365": ["CYBI3335"],
    "CYBI3331": ["CYBI2322", "CYBI2324", "CYBI2326"],
    "CYBI4340": ["CYBI3335"],
}


SEED_FACULTY_ADVISEES = {
    "faculty1": ["student1"],
    "faculty1": ["isabella"],
}
