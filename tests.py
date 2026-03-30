def generate_recommendations(completed, degree_plan, prerequisites):
    recommended = []

    for course in degree_plan:
        if course not in completed:
            prereqs = prerequisites.get(course, [])
            if all(p in completed for p in prereqs):
                continue
            recommended.append(course)
    return recommended


# TEST 1
completed = ["CS1", "MATH1"]
degree_plan = ["CS1", "CS2", "MATH1", "MATH2"]
prereqs = {"CS2": ["CS1"], "MATH2": ["MATH1"]}

print(generate_recommendations(completed, degree_plan, prereqs))
#["CS2", "MATH2"]

# TEST 2
completed = []
degree_plan = ["CS1", "CS2"]
prereqs = {"CS2": ["CS1"]}

print(generate_recommendations(completed, degree_plan, prereqs))
#== ["CS1"]

# TEST 3
completed = ["CS1", "CS2"]
degree_plan = ["CS1", "CS2"]
prereqs = {"CS2": ["CS1"]}

print(generate_recommendations(completed, degree_plan, prereqs)) # == []
