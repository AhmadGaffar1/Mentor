####################################################################################################
# Some Services related to students

import os
from uuid import UUID

from langchain_core.messages import HumanMessage

from APP.Classes import Student
from APP.Fake_Database import students
from APP.Configration import *

def get_all_students():
    return [ st.profile() for st in students ]

def get_all_ids():
    return IDs

def find_student_by_id(student_id: UUID):
    for st in students:
        if st.user_id == student_id:
            return st.profile()
    return None # already validating at the end-point, before calling the function

def filtering_students_by_GPA(Min_GPA: float, Max_GPA: float):
    list = []
    for i in range(len(students)):
        if students[i].GPA >= Min_GPA and students[i].GPA <= Max_GPA:
            list.append(students[i])
    if len(list) == 0:
        return {"There are no students within this grade range"}
    else:
        return [ st.profile() for st in list ]

def inserting_new_student(name: str, age: int, phone_number: str, email: str, sub_01_index: int, sub_01_grade: float, sub_02_index: int, sub_02_grade: float):
    # instantiate new student  --then-->>  adding into "students" (database: list of class Student)
    new_student = Student(name, age, phone_number, email, sub_01_index, sub_01_grade, sub_02_index, sub_02_grade)
    students.append(new_student)
    IDs.append(new_student.user_id)
    return {"Received Student" : new_student.profile()}

def remove_student_from_database(id: UUID):
    for i in range(len(students)):
        if students[i].user_id == id:

            # Deleting chat history for deleted student
            if id in chat_history.keys():
                # Deleting chat history from dictionary data structure:
                chat_history.pop(students[i].user_id)
                # Deleting chat history file:
                # Project Directory
                # Project_Directory = os.path.dirname(os.path.abspath(__file__))
                # target file
                file_path = os.path.join(os.getcwd(), "APP", "Chat_Histories", f"{students[i].name}_Chat_{students[i].user_id}.md")
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Deleted Chat History for {students[i].name} with ID: {students[i].user_id}")
                else:
                    print(f"The Deleted student not own any chat history for deletion: {file_path}")

            # Deleting student profile from student database && Deleting student ID from IDs Database
            IDs.pop(i)
            return {"Deleted Student": students.pop(i).profile()}

def updating_student_profile(id: UUID, sub_01_index: int, sub_01_grade: float, sub_02_index: int, sub_02_grade: float):
    # Retrieving the student’s profile to update it by recording the grades from recently completed courses
    for i in range(len(students)):
        if students[i].user_id == id:

            students[i].age = students[i].age + 1

            students[i].sub_01_index=sub_01_index
            students[i].sub_02_index=sub_02_index

            students[i].content.subject_list[sub_01_index-1].subject_grade = sub_01_grade
            students[i].content.subject_list[sub_02_index-1].subject_grade = sub_02_grade

            students[i].sub_finished += 2
            students[i].total_grades += (sub_01_grade+sub_02_grade)
            students[i].GPA=students[i].total_grades/students[i].sub_finished

            # Update Student Profile in chat history
            if id in chat_history.keys():
                chat_history[id][1]=(HumanMessage(content=students[i].profile_message()))

            return { "Upgraded Student": students[i].profile() }

####################################################################################################