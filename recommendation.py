class RecommendationEngine:
    def generate(self, completed, degree_plan, prerequisites):
        recommended = []

        for course in degree_plan:
            if course not in completed:
                prereqs = prerequisites.get(course, [])
                if all(p in completed for p in prereqs):
                    recommended.append(course)

        return recommended