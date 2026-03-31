#this is a sample for now, we'd like to implement a database
#purely for testing
#sample user accs for each role
users = {
    "student1": {"password": "123", "role": "student"},
    "faculty1": {"password": "123", "role": "faculty"}
}

#epurely for testing
students = {
    "student1": {
        "transcript": ["CYBI1", "MATH1"],
        "degree_plan": ["CYBI1", "CYBI2", "MATH1", "MATH2"]
    }
}

#sample courses, but we will be implementing the attached UTRGV cybersecurity 2024-2025 degree map
courses = {
    "CYBI1": {"description": "Intro to Cyberseccurity", "credits": 3},
    "CYBI2": {"description": "Intro to Programming in Python", "credits": 3},
    "MATH1": {"description": "College Algebra", "credits": 3},
    "MATH2": {"description": "Precalculus", "credits": 4}
}

#more sample data for testing
prerequisites = {
    "CYBI2": ["CYBI1"],
    "MATH2": ["MATH1"]
}
#faculty, advisees relation, this will allow faculty to see their advisees information
faculty_advisees = {
    "faculty1": ["student1"]
}
