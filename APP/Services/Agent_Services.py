####################################################################################################
# only the main agent function ( communicate_with_agent )

import time
from uuid import UUID
from fastapi import Body
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from APP.Services.Student_Services import students
from APP.Prompts import *
from APP.Configration import *
from APP.Chats.Chat_Display_Format import Chat_Display_in_Markdown_file



OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")

architect_Agent = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY, temperature=0)
sage_Agent = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY, temperature=0)
maestro_Agent = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY, temperature=0)

architect_Agent_Requests=0
sage_Agent_Requests=0
maestro_Agent_Requests=0

def generate_roadmap(id: UUID, student_request: str = Body (...)):
    start_time = time.time()

    # Declare only one global counter for next two loops
    I: int = 0

    # if it's the first time to chat with agent, should be set the chat rules before chatting
    # chatting rules:
        # 1- System Prompt.
        # 2- Student Profile
    if id not in chat_history.keys():
        # 1- Adding System Prompt, as a first element in the list representing student history - chat_history [0] = SYSTEM_Prompt
        chat_history[id] = [SystemMessage(content=SYSTEM_PROMPT["Architect"])]
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
            chat_history[id].append(HumanMessage(content = student_request))

            # Then send the whole student history to LLM for ( Reasoning , Thinking, and Processing )
            agent_response = architect_Agent.invoke(chat_history[id])

            # Adding Agent Response to the chat history between ( Student & Agent )
            ### chat_history[id].append(agent_response.content)
            chat_history[id].append(AIMessage(content=agent_response.content))

            # Display the whole chat in a markdown file for curation
            global architect_Agent_Requests
            architect_Agent_Requests+=1
            Chat_Display_in_Markdown_file(id,i,student_request,agent_response.content,1,
                                          architect_Agent_Requests+sage_Agent_Requests+maestro_Agent_Requests)

            return {
                "Latency in Seconds:" : time.time() - start_time,
                "Student ID:" : id,
                "Student Name:" :students[i].name,
                "Chat History Length:": len(chat_history[id]) - 2,
                ### "Student_Request": student_request,
                ### "Agent_Response:" : agent_response.content,
                ### "Chat_History": [msg.content for msg in chat_history[Student_ID]]  # return clean texts
                ### "Chat History:" : chat_history[id]
            }

def explain_with_texts(id: UUID, student_request: str = Body (...)):
    start_time = time.time()

    # Declare only one global counter for next two loops
    I: int = 0

    # if it's the first time to chat with agent, should be set the chat rules before chatting
    # chatting rules:
        # 1- System Prompt.
        # 2- Student Profile
    if id not in chat_history.keys():
        # 1- Adding System Prompt, as a first element in the list representing student history - chat_history [0] = SYSTEM_Prompt
        chat_history[id] = [SystemMessage(content=SYSTEM_PROMPT["Sage"])]
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
            chat_history[id].append(HumanMessage(content = student_request))

            # Then send the whole student history to LLM for ( Reasoning , Thinking, and Processing )
            agent_response = sage_Agent.invoke(chat_history[id])

            # Adding Agent Response to the chat history between ( Student & Agent )
            ### chat_history[id].append(agent_response.content)
            chat_history[id].append(AIMessage(content=agent_response.content))

            # Display the whole chat in a markdown file for curation
            global sage_Agent_Requests
            sage_Agent_Requests+=1
            Chat_Display_in_Markdown_file(id,i,student_request,agent_response.content,2,
                                          architect_Agent_Requests+sage_Agent_Requests+maestro_Agent_Requests)

            return {
                "Latency in Seconds:" : time.time() - start_time,
                "Student ID:" : id,
                "Student Name:" :students[i].name,
                "Chat History Length:": len(chat_history[id]) - 2,
                ### "Student_Request": student_request,
                ### "Agent_Response:" : agent_response.content,
                ### "Chat_History": [msg.content for msg in chat_history[Student_ID]]  # return clean texts
                ### "Chat History:" : chat_history[id]
            }

def explain_with_videos(id: UUID, student_request: str = Body (...)):

    start_time = time.time()

    # Declare only one global counter for next two loops
    I: int = 0

    # if it's the first time to chat with agent, should be set the chat rules before chatting
    # chatting rules:
        # 1- System Prompt.
        # 2- Student Profile
    if id not in chat_history.keys():
        # 1- Adding System Prompt, as a first element in the list representing student history - chat_history [0] = SYSTEM_Prompt
        chat_history[id] = [SystemMessage(content=SYSTEM_PROMPT["Maestro"])]
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
            chat_history[id].append(HumanMessage(content = student_request))

            # Then send the whole student history to LLM for ( Reasoning , Thinking, and Processing )
            agent_response = maestro_Agent.invoke(chat_history[id])

            # Adding Agent Response to the chat history between ( Student & Agent )
            ### chat_history[id].append(agent_response.content)
            chat_history[id].append(AIMessage(content=agent_response.content))

            # Display the whole chat in a markdown file for curation
            global maestro_Agent_Requests
            maestro_Agent_Requests+=1
            Chat_Display_in_Markdown_file(id,i,student_request,agent_response.content,3,
                                          architect_Agent_Requests+sage_Agent_Requests+maestro_Agent_Requests)

            return {
                "Latency in Seconds:" : time.time() - start_time,
                "Student ID:" : id,
                "Student Name:" :students[i].name,
                "Chat History Length:": len(chat_history[id]) - 2,
                ### "Student_Request": student_request,
                ### "Agent_Response:" : agent_response.content,
                ### "Chat_History": [msg.content for msg in chat_history[Student_ID]]  # return clean texts
                ### "Chat History:" : chat_history[id]
            }

########################################################################################################################