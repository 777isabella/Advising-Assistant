class User:
    def __init__(self, username, role):
        self.username = username
        self.role = role

#student class
#inherits from user
class Student(User):
    def __init__(self, username, transcript, degree_plan):
        super().__init__(username, "student")
        self.transcript = transcript
        self.degree_plan = degree_plan

#possibly will need to make a class for faculty
# but for testing purposes so far its not needed
