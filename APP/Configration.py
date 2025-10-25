####################################################################################################
# Configration

from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Global constants
NumberOfSubject: int = 10
Min_Grade: float = 00.0
Max_Grade: float = 100.0
Pass_Grade: float = 00.0

# Max Retrieved Links
MAX_LINKS: int = 10

# Max time for extracting data
MAX_TIME_FOR_TEXT_EXTRACTION: int = 60
MAX_TIME_FOR_TRANSCRIPT_EXTRACTION: int = 600

GLOBAL_REQUEST_DELAY = 5  # seconds between AssemblyAI requests

# All Student ID in a list
IDs = [
    # Student_ID
    # Student_ID
    # Student_ID
    # Student_ID
]

# Memory for saving each student history by his ID
chat_history = {
    # Student_ID: Student Chat History
    # Student_ID: Student Chat History
    # Student_ID: Student Chat History
    # Student_ID: Student Chat History
}

# Load .env variables
load_dotenv()

# Use LLMs capabilities
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")



# === Secret Keys for Web Search pipline for retrieving ( Resources & Metadata ) ===

# 1- Uses Serper API to discover text & video sources.
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# 2- Uses Tavily API to discover text & video sources.
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# 3- Uses Diffbot API for extract all data from any url.
DIFFBOT_API_KEY = os.getenv("DIFFBOT_API_KEY")

# 4- Uses YouTube Data API to get video metadata.
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# 5- Uses Whisper API (OpenAI) if no transcript available.
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")



# Initialize FastAPI APP
APP = FastAPI(title="Edulga  ( Intelligent Education System )")

####################################################################################################