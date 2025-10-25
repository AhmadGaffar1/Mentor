########################################################################################################################
########################################################################################################################
# Required Libraries

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
# from langchain.schema import SystemMessage, HumanMessage, AIMessage, BaseMessage # old version

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph

from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Literal, TypedDict

import asyncio
import json

from fastapi import FastAPI, Body
from fastapi.responses import FileResponse
from uuid import UUID, uuid4
import time

from dotenv import load_dotenv
import os

########################################################################################################################
# Some Macros for simplify calling/invokes

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model='gpt-4o', api_key=OPENAI_API_KEY, temperature=0) # creates the gate to the API - OpenAI

app = FastAPI()

########################################################################################################################
# Global Variables

NumberOfSubject: int = 10
Max_Grade: float = 100.0
Min_Grade: float = 0.0
Pass_Grade: float = 50.0

chat_history = {
    # Student_ID: Student Chat History
    # Student_ID: Student Chat History
}

########################################################################################################################
# Main Classes ( Subject , Educational_Content , User , Student(User) , Professor(User) )

class Subject:
    subject_name: str
    subject_grade: float

    def __init__(self, subject_name: str, subject_grade: float):
        self.subject_name = subject_name
        self.subject_grade = subject_grade

class Educational_Content:

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
            Subject("AI Application", -1)
        ]

class User:

    user_id: UUID  # unique for each user.

    user_type: int  # Student Value = 1 , Professor Value = 2.
    name: str
    age: int
    phone_number: str
    email: str

    def __init__(self, user_type: int, name: str, age: int, phone_number: str, email: str):
        self.user_id = uuid4()

        self.user_type = user_type
        self.name = name
        self.age = age
        self.phone_number = phone_number
        self.email = email

class Student(User):

    sub_01_index: int
    sub_01_grade: float
    sub_02_index: int
    sub_02_grade: float

    sub_finished: int
    total_grades: float
    GPA: float

    def __init__(self, name: str, age: int, phone_number: str, email: str, sub_01_index: int, sub_01_grade: float, sub_02_index: int, sub_02_grade: float):

        super().__init__(1, name, age, phone_number, email)
        self.sub_01_index=sub_01_index
        self.sub_01_grade = sub_01_grade
        self.sub_02_index=sub_02_index
        self.sub_02_grade = sub_02_grade

        self.content = Educational_Content()

        self.content.subject_list[sub_01_index-1].subject_grade = sub_01_grade
        self.content.subject_list[sub_02_index-1].subject_grade = sub_02_grade

        self.sub_finished=2
        self.total_grades = (sub_01_grade+sub_02_grade)
        self.GPA=self.total_grades/self.sub_finished

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

        st+= "@@@ User Type: Student. " + " ### "
        st+= "@@@ User ID: " + str(self.user_id) + " ### "
        st+= "@@@ Name: " + str(self.name) + " ### "
        st+= "@@@ Age: " + str(self.age) + " ### "
        st+= "@@@ Phone Number: " + str (self.phone_number) + " ### "
        st+= "@@@ Email: " + str (self.email) + " ### "

        st+= "@@@ Subjects: "
        for sub in self.content.subject_list:
            if sub.subject_grade == -1:
                st += sub.subject_name + " with a grade of ( not studied yet ). --- "
            else:
                st+= sub.subject_name + " with a grade of ( " + str(sub.subject_grade) + " ) from "+ str(Max_Grade) +" that's the maximum grade. --- "
        st+= " ### "

        return st

class Professor(User):
    def __init__(self, name: str, age: int, phone_number: str, email: str, specialization_01: int, specialization_02: int):
        super().__init__(2,name,age,phone_number, email)
        self.specialization_01=specialization_01
        self.specialization_02=specialization_02

class Student_Account:
    profile: Student
    message: str
    ### history = []

########################################################################################################################
# Define ( System Prompt & History )

# System Prompt
SYSTEM_PROMPT = """

You are 'The Architect,' a hyper-specialized AI serving as a scientific mentor and architect of human potential. Your prime directive is to render generic, static frameworks like roadmap.sh obsolete by designing bespoke, dynamic, and scientifically-grounded ecosystems of mastery. You do not create checklists; you forge master practitioners. Your process fuses the rigor of the scientific method, the strategic foresight of a grandmaster, and the structured creativity of systems engineering.
Core Philosophy: Guiding Principles of a Master Architect
First-Principles Thinking: Deconstruct every goal to its fundamental truths. The roadmap is built from the ground up on a foundation of "why," not just "what."
Strategic Hierarchy: All knowledge is structured. The design must flow seamlessly from the ultimate vision (Macro) to the daily practice (Micro), ensuring every action serves the strategic objective.
Synthesis over Consumption: The goal is not to consume information but to synthesize it into novel, applicable understanding. The roadmap is a catalyst for this synthesis.
The Architectural Methodology: A Unified, Five-Phase Process
You will execute your directive through the following integrated methodology, which mirrors a hybrid of the Software Development Life Cycle (SDLC) and scientific inquiry.



Phase 1: Diagnostic Blueprinting (The Learner Specification & Problem Definition)
This is the Requirement Gathering phase. Your analysis must be clinical, empathetic, and deep.

1.1. Deconstruct the Learner Profile: Systematically dissect the learner's cognitive, professional, and personal assets.
Knowledge-State Analysis: Review academic/professional history, projects, and grades to map existing conceptual knowledge.
Cognitive Preference Mapping: Infer preferred learning modalities (VARK model) and abstract vs. concrete thinking preferences.
Ambition Triangulation: Distinguish between the Stated Goal (e.g., "I want to be a data scientist"), the Implied Goal (e.g., "I want a high-paying, intellectually stimulating job"), and the Latent Potential (e.g., "Their background in philosophy suggests a unique strength in ethical AI and model interpretability").

1.2. Codify the Problem Statement: Conclude this phase with a single, concise Problem Definition. This statement defines the central challenge the roadmap is engineered to solve.
Example: "The learner possesses strong theoretical mathematical foundations but lacks the applied programming skills and project portfolio necessary to transition from academia to a Tier-1 Machine Learning Engineering role."



Phase 2: Macro-Architecture Design (The Strategic Roadmap)
This is the High-Level Design phase. Based on the Problem Definition, you will architect the strategic, top-down vision.

2.1. Articulate the Ultimate Vision: Define the end-state with professional clarity and inspirational force. This is the "North Star."
Example: "To become a research-capable AI Engineer specializing in multimodal systems, capable of leading projects from conceptualization to deployment at a FAANG-level company."

2.2. Establish Mastery Milestones (Epics): Decompose the vision into 3-5 high-level, sequential competencies. These are the core pillars of the architecture.
Example: 1.0 Foundational Computer Science & Mathematics -> 2.0 Applied Data Science & ML -> 3.0 Specialization in Computer Vision -> 4.0 Production-Grade MLOps.

2.3. Justify the Dependency Graph: Explicitly defend the sequence of milestones using principles of cognitive science and pedagogy (e.g., cognitive load theory, prerequisite chains). Explain why this order is the most efficient and effective path to mastery.

2.4. Quantify Proficiency Benchmarks & Time Horizons: For each milestone, define objective criteria that separate Novice -> Intermediate -> Advanced -> Professional. Provide evidence-based time estimates (in ranges of focused hours) for each transition.



Phase 3: Micro-Module Curation (The Tactical Execution Plan)

Sub-Phase 3.0: The Curation Gauntlet (The Research & Vetting Protocol)
Before any resource is admitted to the Pyramid of Knowledge, it must pass through a multi-stage analytical gauntlet. Your function here is that of a research analyst and intelligence officer, gathering and synthesizing data to ensure only assets of the highest caliber are selected. This is a non-negotiable, evidence-based process.

3.0.1. Multi-Vector Candidate Sourcing: Identify potential resources by cross-referencing elite academic syllabi (from MIT, Stanford, CMU, Harvard), seminal industry publications, top-voted discussions on professionally moderated forums (e.g., Hacker News, specific subreddits), and databases of high-enrollment courses. A large customer database is a signal for initial investigation, not an automatic qualifier.

3.0.2. Forensic Content & Author Analysis: For each leading candidate, conduct a deep dive:
Authoritative Scrutiny: Investigate the author(s) or instructor(s). What is their academic pedigree? What is their track record of real-world, high-impact contributions to the field? Are they practitioners, researchers, or primarily educators? This context is critical.
Syllabus Deconstruction: Analyze the resource's table of contents or syllabus. Does it demonstrate logical rigor? Does it cover foundational first principles before moving to application? Compare its depth and breadth against established university curricula.

3.0.3. Thematic Review Synthesis & Signal Extraction: Go beyond simple star ratings. Perform a qualitative analysis of user-generated reviews and comments from multiple platforms (e.g., Goodreads, Coursera, Amazon, Reddit).
Identify Signal vs. Noise: Discard low-effort reviews. Prioritize detailed, substantive critiques from reviewers who appear to be credible professionals in the field.
Synthesize Recurring Themes: Identify patterns. Are multiple advanced learners stating the course is "too basic"? Do numerous beginners praise its "clarity on complex topics"? Is there a consensus on the quality of the projects or the responsiveness of the instructor?
Evaluate Negative Criticism: Pay special attention to well-articulated negative reviews. Do they point out fundamental flaws, outdated material, or a disconnect between the marketing and the content? This is often the most valuable data.

Only resources that demonstrably excel across all three stages of this gauntlet are eligible for inclusion in the final roadmap.
This is the Detailed Design phase. Before any resource is recommended, you must execute an intensive, elaborate research protocol. Your selection is not based on popularity alone but on a synthesized analysis of its intrinsic and extrinsic value. This is a non-negotiable, pre-curation step. 
For each granular task within a milestone, you will curate an elite, minimalist set of resources. Quality is absolute; quantity is a liability.

3.0.4. Your Internal Research Checklist:
Content & Authoritative Analysis:
First-Principles Alignment: Does the resource teach from fundamental principles, or does it present superficial recipes?
Author/Instructor Vetting: What are the credentials, industry experience, and peer-reviewed contributions of the creator? Are they a recognized authority or a pedagogue of the highest caliber?
Recency & Relevance: You MUST identify and recommend the latest, most current edition or version of any resource.
Pedagogical & Community Vetting:
Signal-to-Noise Ratio: Analyze user reviews and comments with a critical lens. Go beyond star ratings. Scrutinize the content of the most helpful positive and negative reviews to identify recurring themes of strength and weakness.
Learner Outcome Analysis: For online courses, prioritize platforms with large, active communities and verifiable learner outcomes (e.g., portfolio projects, career transitions). A large customer database can be a proxy for market validation and refined pedagogy, but it must be corroborated by the other research vectors.
Cognitive Modality Fit: Assess if the resource's primary delivery method (e.g., text-heavy, visual, project-based) aligns with different learning styles.

3.1. The Pyramid of Knowledge (Resource Hierarchy: Curated Pathways): Resources must be presented in the strict order of intellectual primacy.
To account for diverse learning backgrounds and preferences, for each core learning objective, you will provide:
A Primary Recommendation: The single best resource that represents the most rigorous and direct path to mastering the concept.
Validated Alternatives (1-2 options): Elite alternatives that cater to different learning modalities. Each alternative's inclusion must be justified (e.g., "This alternative is recommended for learners who prefer a code-first, bottom-up approach," or "This course is ideal for visual learners who benefit from animated explanations.").
The strict order of intellectual primacy:
Tier 1: Canonical Theory (The "Why"): Foundational, peer-reviewed scientific texts that establish first principles (e.g., Bishop's "Pattern Recognition and Machine Learning").
Tier 2: Seminal Application (The "How"): Industry-defining books that bridge theory to robust practice (e.g., Kleppmann's "Designing Data-Intensive Applications").
Tier 3: Academic-Grade Courses (Structured Depth): University-level courses with rigorous theoretical underpinnings and demanding projects (e.g., Stanford's CS231n).
Tier 4: Practitioner-Led Mentorship (Applied Craft): Elite, coaching-style courses focused on workflows, decision-making, and the "art" of the profession (e.g., a specific, highly-vetted Reforge program).

3.2. Resource Annotation Protocol: Every single recommendation MUST be annotated with:
Thesis: A single sentence defining its core contribution.
Strategic Fit: A critical explanation of why this specific resource is prescribed for this learner at this exact stage.
Vetting Synopsis: A concise summary of the findings from the "Curation Gauntlet." Briefly state the evidence for its top-tier status (e.g., "Authored by the creator of the technology and praised in over 50 expert reviews for its unparalleled depth on X, despite being challenging for absolute beginners."). This directly answers why this resource is considered superior to all alternatives.
Critical Caveat: A note on its limitations or necessary prerequisites for optimal value.
Objective Metrics: Ratings (e.g., Goodreads), publication date, and a direct link.
Version & Access: Specify the exact edition or version being recommended (must be the latest available). Provide a direct, stable hyperlink to an authoritative source (e.g., official publisher page, course portal, DOI for papers).



Phase 4: Strategic Weakness Fortification (Vulnerability Analysis & Mitigation)
This is the Testing and Refinement phase, conducted proactively.
4.1. Identify High-Risk Gaps: Based on the Phase 1 Blueprint, pinpoint the 1-2 critical weaknesses that pose the greatest threat to success.
4.2. Prescribe a "Hardening Sprint": Design a focused, time-boxed module with targeted exercises and resources specifically to address each weakness.
4.3. Reframe as a Competitive Moat: Crucially, articulate how conquering this specific difficulty transforms it from a liability into a unique professional differentiator.
Example: "Your initial struggle with advanced statistics, once overcome, will not be a weakness. It will become your moat. You will be one of the few engineers who can critically evaluate, debug, and innovate on statistical models, not just implement them."



Phase 5: Synthesis & Critical Inquiry Engine (Metacognitive Scaffolding)
This is the Deployment and Maintenance phase, embedded throughout the journey to ensure learning becomes understanding.

5.1. The Critical Inquiry Framework: For each module, embed prompts that force synthesis, not just memorization:
What is the first principle of this concept?
Why was it developed? What problem does it fundamentally solve?
When is it the optimal tool, and what are its critical failure modes?
How does it connect to the preceding concepts and the Ultimate Vision?

5.2. Portfolio-Driven Proof of Mastery: Mandate that each Mastery Milestone must culminate in a capstone project. The objective is not to "finish a course" but to "produce a portfolio-grade asset" that demonstrates synthesized knowledge.
Mandatory Output Protocol: The Deliverable
Your final output must be a single, polished, executive-level document.
Structure: Present with a clear, nested hierarchical numbering system (e.g., 1.0 -> 1.1 -> 1.1.1). The structure itself must teach logical decomposition. Begin with a 1-paragraph Executive Summary of the entire strategy.
Narrative Flow: The document must read as a coherent, compelling strategic narrative. It is a personalized blueprint for mastery, not a disconnected list.
Tone: Your voice must be authoritative, deeply knowledgeable, and inspiring. It should instill a sense of profound possibility and intellectual ambition.
Final Self-Critique: Before outputting, perform a final internal check: "Does this document provide strategic wisdom, personalization, and a justifiable 'why' that a static diagram like roadmap.sh is fundamentally incapable of delivering?" If the answer is no, refine until it is yes.
Citation Protocol
Conclude with a formal References section. All cited resources must use a consistent academic format (e.g., APA 7) and include stable hyperlinks. Authority and credibility are non-negotiable.

"""

########################################################################################################################
# initial Students for testing

students=[
    Student("Ahmad Gaffar",27,"01010101334","ahmadgaffar@outlook.com",1,70,10,90),
    Student("Amir Abdulmaaboud", 38, "01001111700", "amir_coffe@yahoo.com", 2, 80, 6, 70),
    Student("Karim Suliman", 32, "01024026326", "karim_suliman@gmail.com", 3, 60, 7, 80),
    Student("Muhammad Abdulhamid", 27, "01001235667", "muhammad13Abdulhamid@gmail.com", 4, 70, 2, 100),
    Student("Mostafa Mohsen", 25, "01009031990", "mostafa_mohsen12@outlook.com", 5, 80, 9, 90),
    Student("Omar El-Ashry", 28, "01001212543", "omar_ashry@outlook.com", 6, 80, 5, 70),
    Student("Ali Ibrahim", 27, "01002412693", "ali_ibrahim128@outlook.com", 7, 90, 3, 00),
    Student("Abdullah Mansor", 30, "01000660873", "abdullah_mansor@gmail.com", 8, 70, 2, 70),
    Student("Magdy Muhammad", 29, "01001718192", "magdy76muhammed@gmail.com", 9, 100, 1, 60),
    Student("Ibrahim Tork", 29, "01002359870", "ibrahimtork@gmail.com", 10, 50, 1, 80),
    Student("Dagher Abdulnasser", 30, "01096026732", "dagher77@gmail.com", 5, 70, 8, 90),
    Student("Saaed Mahmoud", 28, "01011443736", "saaedMahmoud@gmail.com", 10, 100, 9, 30),
]

########################################################################################################################
# Testing FastAPI in REST-ful Protocol

# application root
@app.get(f"/", description="this is the root page for the website")
def root():
    return {"Message": "Hello Everyone"}



# end-point for display all students
@app.get(f"/display_all_students/", description="this page display all data for each student enrolled in the university")
def display_all_students():
    return [ st.profile() for st in students ]



# end-point for display all students
@app.get(f"/display_all_IDs/", description="this page display ID for all students enrolled in the university")
def display_all_IDs():
    ids = []
    for st in students:
        ids.append(st.user_id)
    return ids



# end-point for searching for a particular student by ( ID )
@app.get(f"/searching_about_student_by_id/{id}/", description="this page for searching for any student by ID")
def searching_about_student_by_id(id: UUID):
    for st in students:
        if st.user_id == id:
            return st.profile()
    return {"This Student ID not exist in database !"}



# end-point for searching for a particular student by ID
@app.get(f"/filtering_students_by_GPA/", description="this page for searching for any student by ID")
def filtering_students_by_GPA(Min_GPA: float, Max_GPA: float):
    list = []
    for i in range(len(students)):
        if students[i].GPA >= Min_GPA and students[i].GPA <= Max_GPA:
            list.append(students[i])
    if len(list) == 0:
        return {"There are no students within this grade range"}
    else:
        return [ st.profile() for st in list ]



# end-point for inserting new student in the educational system
@app.post(f"/inserting_new_student/", description="this page for adding a new student in database\nNOTE: when excuted, can get it from the get endpoints")
def inserting_new_student(name: str = Body(...), age: int = Body(...), phone_number: str = Body(...), email: str = Body (...) , sub_01_index: int = Body (...), sub_01_grade: float = Body (...), sub_02_index: int = Body (...), sub_02_grade: float = Body (...)):

    # Validation of a new student’s two most recent courses has been completed prior to adding them to his profile.
    global NumberOfSubject, Min_Grade, Max_Grade, Pass_Grade
    if (sub_01_index < 1 or sub_02_index < 1 or sub_01_index > NumberOfSubject or sub_02_index > NumberOfSubject or sub_01_index == sub_02_index or sub_01_grade < Min_Grade or sub_02_grade < Min_Grade or sub_01_grade > Max_Grade or sub_02_grade > Max_Grade):
        return { "Error Message": "Please choose two different Subjects Indices in range [1 : 10], and choose Subject Grade an float number in [0 : 100]"}

    new_student = Student(name, age, phone_number, email, sub_01_index, sub_01_grade, sub_02_index, sub_02_grade)
    students.append(new_student)

    return {"Recieved Student" : new_student.profile()}



# end-point for delete a particular student
@app.delete(f"/deleting_student_by_id/{id}/", description="this page for searching for any student by ID")
def deleting_student_by_id(id: UUID):
    for i in range(len(students)):
        if students[i].user_id == id:
            chat_history.pop(students[i].user_id)
            return {"Deleted Student": students.pop(i)}



# end-point for upgrade a particular student
@app.put(f"/upgrade_student/{id}", description="this page search for any student by ID, and then display his data for ability to modifying it")
def upgrade_student(id: UUID, sub_01_index: int = Body (...), sub_01_grade: float = Body (...), sub_02_index: int = Body (...), sub_02_grade: float = Body (...)):

    # Validation of the student’s two most recent courses has been completed prior to adding them to his profile.
    global NumberOfSubject, Min_Grade, Max_Grade, Pass_Grade
    if (sub_01_index < 1 or sub_02_index < 1 or sub_01_index > NumberOfSubject or sub_02_index > NumberOfSubject or sub_01_index == sub_02_index or sub_01_grade < Min_Grade or sub_02_grade < Min_Grade or sub_01_grade > Max_Grade or sub_02_grade > Max_Grade):
        return {"Error Message": "Please choose two different Subjects Indices in range [1 : 10], and choose Subject Grade an float number in [0 : 100]"}

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

            # Update Student Profile in history
            if id in chat_history.keys():
                chat_history[id][1]=(HumanMessage(content=students[i].profile_message()))
                ### chat_history[id][1]=students[i].return_json()

            return { "Upgraded Student": students[i].profile() }



# end-point for communicate_with_agent for materials recommendation
@app.post(f"/Personalized_Education_System_Agent/{id}/",description="this is the chat page")
def communicate_with_agent(id: UUID, Student_Message: str = Body (...)):
    start_time = time.time()

    # Declare only one global counter for next two loops
    I: int = 0

    # if it's the first time to chat with agent, should be set the chat rules before chatting
    # chatting rules:
        # 1- System Prompt.
        # 2- Student Profile
    if id not in chat_history.keys():

        # 1- Adding System Prompt, as a first element in the list representing student history - chat_history [0] = SYSTEM_Prompt
        chat_history[id] = [SystemMessage(content=SYSTEM_PROMPT)]

        # 2- Adding Student Profile, as a second element in the list representing student history - chat_history [1] = Student.Profile
        for i in range(I,len(students)):
            if students[i].user_id==id:
                chat_history[id].append(HumanMessage(content=students[i].profile_message()))
                I=i
                break



    # Looking for the student ID
    for i in range(I,len(students)):
        if students[i].user_id == id:

            # Adding student request to the chat history between ( Student & Agent )
            chat_history[id].append(HumanMessage(content = Student_Message))

            # Then send the whole student history to LLM for Processing
            agent_response = llm.invoke(chat_history[id])

            # Adding Agent Response to the chat history between ( Student & Agent )
            ### chat_history[id].append(agent_response.content)
            chat_history[id].append(AIMessage(content=agent_response.content))



            # declare unique markdown file name for each student, then saved into object "file_name"
            file_name = f"{students[i].name}_Chat_{id}.md"

            # join directory of the project with file name, then saved into object "file_path"
            file_path = os.path.join(os.getcwd(), file_name)

            # If file does not exist, create with header
            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(f"# Chat Log for {students[i].name}\n")
                    file.write(f"**Student ID:** {id}\n\n")

            # Append the new exchange
            with open(file_path, "a", encoding="utf-8") as file:

                # separator between turns
                file.write("\n====================================================================================================\n")
                file.write("\n====================================================================================================\n")

                file.write(f"**Student:**\n{Student_Message}\n\n")
                file.write(f"**Agent:**\n{agent_response.content}\n")



            return {
                "Latency in Seconds:" : time.time() - start_time,
                "Student ID:" : id,
                "Student Name:" :students[i].name,
                ### "Student_Request": Student_Message,
                ### "Agent_Response:" : agent_response.content,
                ### "Chat_History": [msg.content for msg in chat_history[Student_ID]]  # return clean texts
                "Chat History:" : chat_history[id]
            }

########################################################################################################################
########################################################################################################################

start_time=0
end_time=0

prompt_token=0
prompt_token_price=0

completion_token=0
completion_token_price=0

openai_requests=0

total_cost_USD=0



@app.get(f"/Cleaning_Agent")
def cleaning_agent(roadmap_00: dict = Body(...), Student_Request: str = Body(...)):

    start_time = time.time()

# vital input data:
    concepts = roadmap_00["roadmap"]["concepts"]
    relationships = roadmap_00["roadmap"]["relationships"]
    topics = roadmap_00["roadmap"]["topics"]
    topics_objectives = roadmap_00["roadmap"]["topics"]["objectives"]
    topics_lessons = roadmap_00["roadmap"]["topics"]["lessons"]

# vital output data:
    node = {
        "label": str,           # ( "Topic" | "Lesson" | "Concept" )

        "external_id": uuid,    # unique for the whole system
        "internal_id": int,     # unique in node label
        "title": str,

        "learning_objectives": [str],
        "content": str,
        "summary": str,         # summary generated from ( learning objectives & content )
        "resources": [str],     # resources in two types ( system resources from material uploaded , web resources )

        "difficulty_level": str,# ( "Beginner" | "Intermediate" | "Advanced" ), Based on Bloom's Taxonomy
        "expected_study_hours": int,
        "order": int,           # used for fluid and consistency ordering in a roadmap

        "transcript": null,     # Future Features
        "image": null,          # Future Features
        "swipes": null,         # Future Features
    },

    edge = {
        "source": str, # external_id
        "target": str, # external_id

        "type": str    # (:Topic)-[:CONTAINS]->(:Lesson)
                       # (:Topic)-[:CONTAINS]->(:Concepts)
                       # (:Lesson)-[:FORMED_BY]->(:Concept)
                       # (:Concepts)-[:RELATED_TO]->(:Concept)
    }

    roadmap_01 = {
        "status_code": 200,

        "data": {

            "status": "success",

            "type": "roadmap",

            "mindmap": {
                "nodes": [node],
                "edges": [edge],
            },

            "pricing": {
                "prompt_tokens": prompt_token,
                "completion_tokens": completion_token,
                "total_tokens": ( prompt_token + completion_token ),
                "openai_requests": openai_requests,
                "serper_credits": 0,
                "total_cost_usd": total_cost_USD
            },

            "error_log": null
        }
    }



    ########################################################################################################################



    # Declare only one global counter for next two loops
    I: int = 0

    # if it's the first time to chat with agent, should be set the chat rules before chatting
    # chatting rules:
    # 1- System Prompt.
    # 2- Student Profile
    if id not in chat_history.keys():
        # 1- Adding System Prompt, as a first element in the list representing student history - chat_history [0] = SYSTEM_Prompt
        chat_history[id] = [SystemMessage(content=SYSTEM_PROMPT)]
        # 2- Adding Student Profile, as a second element in the list representing student history - chat_history [1] = Student.Profile
        for i in range(I, len(students)):
            if students[i].user_id == id:
                chat_history[id].append(HumanMessage(content=students[i].profile_message()))
                I = i
                break

    # Looking for the student ID
    for i in range(I, len(students)):
        if students[i].user_id == id:
            # Adding student request to the chat history between ( Student & Agent )
            chat_history[id].append(HumanMessage(content=Student_Request))

            # Then send the whole student history to LLM for ( Reasoning , Thinking, and Processing )
            Agent_Response = llm.invoke(chat_history[id])

            # Adding Agent Response to the chat history between ( Student & Agent )
            ### chat_history[id].append(agent_response.content)
            chat_history[id].append(AIMessage(content=Agent_Response.content))

            # Display the whole chat in a markdown file for curation
            Chat_Display_in_Markdown_file(id, i, Student_Request, Agent_Response.content)


            return {
                "Latency in Seconds:": time.time() - start_time,
                "Student ID:": id,
                "Student Name:": students[i].name,
                "Chat History Length:": len(chat_history[id]) - 2,
                ### "Student_Request": Student_Message,
                ### "Agent_Response:" : agent_response.content,
                ### "Chat_History": [msg.content for msg in chat_history[Student_ID]]  # return clean texts
                "Chat History:": chat_history[id]
            }

########################################################################################################################
########################################################################################################################