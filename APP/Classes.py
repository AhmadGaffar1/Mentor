####################################################################################################
# Classes in the intelligent personalized education system

from uuid import UUID, uuid4
from APP.Configration import IDs, Max_Grade

class Subject:
    def __init__(self, subject_name: str, subject_grade: float):
        self.subject_name = subject_name
        self.subject_grade = subject_grade

class EducationalContent:
    def __init__(self):
        self.subject_list = [
            Subject("Programming Principles", -1),
            Subject("Object Oriented Programming", -1),
            Subject("Data Structures and Algorithms", -1),
            Subject("Algorithms Analysis and Design", -1),
            Subject("Databases", -1),
            Subject("System Analysis and Design", -1),
            Subject("Software Engineering", -1),
            Subject("Machine Learning", -1),
            Subject("Research", -1),
            Subject("AI Application", -1),
        ]

class User:
    def __init__(self, user_type: int, name: str, age: int, phone_number: str, email: str):
        self.user_id = uuid4()
        self.user_type = user_type
        self.name = name
        self.age = age
        self.phone_number = phone_number
        self.email = email

        IDs.append(self.user_id)

class Student(User):
    def __init__(self, name: str, age: int, phone_number: str, email: str,
                 sub_01_index: int, sub_01_grade: float, sub_02_index: int, sub_02_grade: float):
        super().__init__(1, name, age, phone_number, email)
        self.sub_01_index=sub_01_index
        self.sub_01_grade=sub_01_grade
        self.sub_02_index=sub_02_index
        self.sub_02_grade=sub_02_grade

        self.content = EducationalContent()
        self.content.subject_list[sub_01_index-1].subject_grade = sub_01_grade
        self.content.subject_list[sub_02_index-1].subject_grade = sub_02_grade

        self.sub_finished = 2
        self.total_grades = sub_01_grade + sub_02_grade
        self.GPA = self.total_grades / self.sub_finished

    def profile(self):
        return {
            "User_Type": "Student",
            "User_Id": str(self.user_id),
            "Name": self.name,
            "Age": self.age,
            "Phone Number": self.phone_number,
            "Email": self.email,
            "Subjects": self.content.subject_list,
        }

    def profile_message(self):
        st: str = ""

        st += "@@@ User Type: Student. " + " ### "
        st += "@@@ User ID: " + str(self.user_id) + " ### "
        st += "@@@ Name: " + str(self.name) + " ### "
        st += "@@@ Age: " + str(self.age) + " ### "
        st += "@@@ Phone Number: " + str(self.phone_number) + " ### "
        st += "@@@ Email: " + str(self.email) + " ### "

        st += "@@@ Subjects: "
        for sub in self.content.subject_list:
            if sub.subject_grade == -1:
                st += f"{sub.subject_name} with a grade of ( not studied yet ). --- "
            else:
                st += f"{sub.subject_name} with a grade of ( {str(sub.subject_grade)} ) from {str(Max_Grade)} that's the maximum grade. --- "
        st += " ### "

        return st

class Student_Account:
    profile: Student
    message: str
    ### history = []

####################################################################################################