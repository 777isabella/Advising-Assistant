users = {
    "student1": {"password": "123", "role": "student"},
    "faculty1": {"password": "123", "role": "faculty"}
}

students = {
    "student1": {
        "transcript": ["CYBI1", "MATH1"],
        "degree_plan": ["CYBI1", "CYBI2", "MATH1", "MATH2"]
    }
}

prerequisites = {
    "CYBI2": ["CYBI1"],
    "MATH2": ["MATH1"]
}

faculty_advisees = {
    "faculty1": ["student1"]
}
