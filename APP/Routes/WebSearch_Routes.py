####################################################################################################
# Agent Routs: end-points for provide some service about agent particularly roadmap design

from fastapi import APIRouter, Body
from uuid import UUID
from APP.Configration import IDs
from APP.Services.Search import searching_Serper_Tavily_YouTube_AssemblyAI

router = APIRouter(prefix="/Web_Search", tags=["Web Search End-Points"])

@router.post(f"/Text_Search{id}")
def text_search(id: UUID, query: str = Body(...)):
    # Validation:
    if id not in IDs:
        return {"This ID not exist in the student database"}
    # processing:
    return searching_Serper_Tavily_YouTube_AssemblyAI(id, query, "search")

@router.post(f"/Video_Search{id}")
def video_search(id: UUID, query: str = Body(...)):
    # Validation:
    if id not in IDs:
        return {"This ID not exist in the student database"}
    # processing:
    return searching_Serper_Tavily_YouTube_AssemblyAI(id, query, "videos")

####################################################################################################