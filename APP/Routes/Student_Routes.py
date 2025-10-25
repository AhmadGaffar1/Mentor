####################################################################################################
# Student Routs: end-points for provide some service about student

from fastapi import APIRouter, Body
from uuid import UUID
from APP.Services.Student_Services import *
from APP.Fake_Database import students
from APP.Classes import Student
from APP.Configration import *

router = APIRouter(prefix="/Students", tags=["Students End-Points"])



@router.get("/Profiles")
def display_all_students():
    # Validation:
    if len(students) == 0:
        return {"The Student Database is Empty !!!"}
    # Processing:
    return get_all_students()

@router.get("/IDs")
def display_all_ids():
    # Validation:
    if len(students) == 0:
        return {"The Student Database is Empty !!!"}
    # Processing:
    return get_all_ids()

@router.get(f"/Search{id}")
def display_student_by_id(id: UUID):
    # Validation:
    if id not in IDs:
        return {"This ID not exist in the student database"}
    # processing:
    return find_student_by_id(id)

@router.get("/GPA_Filtration")
def display_all_students_in_specific_GPA_range(Min_GPA: float, Max_GPA: float):
    # Validation:
    if len(students) == 0:
        return {"The Student Database is Empty !!!"}
    # processing:
    return filtering_students_by_GPA(Min_GPA,Max_GPA)

@router.post("/Enrollment")
def student_enrollment(name: str = Body(...), age: int = Body(...), phone_number: str = Body(...), email: str = Body (...) , sub_01_index: int = Body (...), sub_01_grade: float = Body (...), sub_02_index: int = Body (...), sub_02_grade: float = Body (...)):
    # Validation:
    if (sub_01_index < 1 or sub_02_index < 1 or sub_01_index > NumberOfSubject or sub_02_index > NumberOfSubject or sub_01_index == sub_02_index or sub_01_grade < Min_Grade or sub_02_grade < Min_Grade or sub_01_grade > Max_Grade or sub_02_grade > Max_Grade):
        return {"Error Message": f"Please choose two different Subjects Indices in range [1 : {NumberOfSubject}], and choose Subject Grade an float number in [{Min_Grade} : {Max_Grade}]"}
    # processing:
    return inserting_new_student(name, age, phone_number, email, sub_01_index, sub_01_grade, sub_02_index, sub_02_grade)

@router.delete(f"/Deletion/{id}")
def deleting_student_by_id(id: UUID):
    # Validation:
    if id not in IDs:
        return {"This ID not exist in the student database"}
    # processing:
    return remove_student_from_database(id)

@router.put(f"/Upgrade/{id}")
def upgrading_student_profile(id: UUID, sub_01_index: int = Body (...), sub_01_grade: float = Body (...), sub_02_index: int = Body (...), sub_02_grade: float = Body (...)):
    # Validation:
    if (sub_01_index < 1 or sub_02_index < 1 or sub_01_index > NumberOfSubject or sub_02_index > NumberOfSubject or sub_01_index == sub_02_index or sub_01_grade < Min_Grade or sub_02_grade < Min_Grade or sub_01_grade > Max_Grade or sub_02_grade > Max_Grade):
        return {"Error Message": f"Please choose two different Subjects Indices in range [1 : {NumberOfSubject}], and choose Subject Grade an float number in [{Min_Grade} : {Max_Grade}]"}
    # processing:
    return updating_student_profile(id, sub_01_index, sub_01_grade, sub_02_index, sub_02_grade)

####################################################################################################
