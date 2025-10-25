####################################################################################################
# Agent Routs: end-points for provide some service about agent particularly roadmap design

from fastapi import APIRouter, Body
from uuid import UUID
from APP.Configration import IDs
from APP.Services.Agent_Services import generate_roadmap, explain_with_texts, explain_with_videos

router = APIRouter(prefix="/Agent", tags=["Agent End-Points"])

@router.post(f"/Roadmap_Generation{id}")
def architect(id: UUID, student_request: str = Body(...)):
    # Validation:
    if id not in IDs:
        return {"This ID not exist in the student database"}
    # processing:
    return generate_roadmap(id, student_request)

@router.post(f"/Text_based_Explanations{id}")
def sage(id: UUID, student_request: str = Body(...)):
    # Validation:
    if id not in IDs:
        return {"This ID not exist in the student database"}
    # processing:
    return explain_with_texts(id, student_request)

@router.post(f"/Video_based_Explanations{id}")
def maestro(id: UUID, student_request: str = Body(...)):
    # Validation:
    if id not in IDs:
        return {"This ID not exist in the student database"}
    # processing:
    return explain_with_videos(id, student_request)

####################################################################################################