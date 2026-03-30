class User:
    def __init__(self, username, role):
        self.username = username
        self.role = role


class Student(User):
    def __init__(self, username, transcript, degree_plan):
        super().__init__(username, "student")
        self.transcript = transcript
        self.degree_plan = degree_plan