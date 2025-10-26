####################################################################################################
# Agent Routs: end-points for provide some service about agent particularly roadmap design

import asyncio
from fastapi import APIRouter, Body
from uuid import UUID
from APP.Configration import IDs
from APP.Services.async_search import searching_Serper_Tavily_YouTube_AssemblyAI

router = APIRouter(prefix="/Web_Search", tags=["Web Search End-Points"])

@router.post(f"/Text_Search{id}")
async def text_search(id: UUID, query: str = Body(...)):
    """
    Async endpoint - no blocking!
    FastAPI natively supports async/await.
    """
    # Validation:
    if id not in IDs:
        return {"This ID not exist in the student database"}
    # processing:

    results = await searching_Serper_Tavily_YouTube_AssemblyAI(id, query, "search")
    return {"results": results, "count": len(results)}

@router.post(f"/Video_Search{id}")
async def video_search(id: UUID, query: str = Body(...)):
    """
    Async endpoint - no blocking!
    FastAPI natively supports async/await.
    """
    # Validation:
    if id not in IDs:
        return {"This ID not exist in the student database"}
    # processing:
    results = await searching_Serper_Tavily_YouTube_AssemblyAI(id, query, "videos")
    return {"results": results, "count": len(results)}

####################################################################################################