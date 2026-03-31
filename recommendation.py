#recommendation engine
#this will need updating to accomodate UTRGV CYBI degree road map
#for testing purpose and basic implementation this works
#this inherits from Course classs and the student data
class RecommendationEngine:
    def generate(self, completed, degree_plan, prerequisites):
        recommended = []
        #essentially if course in the degree plan
        #and its not completed then first look for the
        #prerequisites, if there's no prerequisite
        #then appened to course and return it as recommended
        for course in degree_plan:
            if course not in completed:
                prereqs = prerequisites.get(course, [])
                if all(p in completed for p in prereqs):
                    recommended.append(course)

        return recommended
#this is used in the recommendation report
