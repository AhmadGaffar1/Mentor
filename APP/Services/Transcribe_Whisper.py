"""
======================================================
TRANSCRIBING USING OPENAI WHISPER
======================================================
"""

# ================================================================
# IMPORT REQUIRED MODULES
# ================================================================

import imageio_ffmpeg       # module: Automatically ensures yt_dlp and Whisper can run without manual FFmpeg installation
import yt_dlp               # module: yt_dlp (fork of youtube-dl) for downloading media
import tempfile             # module: provides temporary file creation utilities
from openai import OpenAI   # OpenAI official Python client (client wrapper)
from APP.Configration import OPENAI_API_KEY

# ================================================================
# SETUP YOUR CREDENTIALS
# ================================================================

client = OpenAI(api_key=OPENAI_API_KEY)  # api_key: str (keep secret; environment var recommended)

# ============================================================
# Main Function
# ============================================================

def youtube_to_whisper_transcript(youtube_url: str) -> dict[str, object]:
    """
    Download audio from a YouTube URL to a temporary file and transcribe it using OpenAI Whisper (whisper-1).
    Input:
        - youtube_url: str (public YouTube URL or short link)
    Output:
        - Python dictionary with keys:
            - "title": str              (video title)
            - "transcript": str         (full transcribed text)
            - "segments": list[dict]    (timestamped segments if verbose_json returned segments)
    """

    # ============================================================
    # Step 1: Resolve FFmpeg binary path (from imageio-ffmpeg)
    # ============================================================
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    # ============================================================
    # Step 2: Create a temporary filename for audio.
    # ============================================================
    # NamedTemporaryFile returns a file-like object with attributes:
    # - name: str -> absolute path of the temp file on disk
    # - file handle object (closed automatically when context ends if delete=True)
    # Using tempfile ensures the file is cleaned up after use.
    # ".mp3" more simple but need more space but faster
    # ".m4a" also simple but need less space but slower
    with tempfile.NamedTemporaryFile(suffix=".m4a") as tmp:
        # tmp: _TemporaryFileWrapper (has attribute tmp.name -> path: str)
        # purpose: temporary storage for downloaded/extracted audio (filesystem path)
        # ============================================================
        # Step 3: Configure yt_dlp options to download audio-only.
        # ============================================================
        # ydl_opts: dict controls behaviour of yt_dlp.extract_info and postprocessing.
        # Key entries:
        #  - format: "bestaudio/best" -> select the best audio-only stream available
        #  - outtmpl: tmp.name -> write output directly to tmp file path
        #  - quiet: True -> suppress verbose download logs (useful in production)
        #  - postprocessors: list -> instruct yt_dlp to run FFmpeg extractor to convert to mp3
        ydl_opts = {
            "format": "bestaudio/best",             # str -> stream selection expression
            "outtmpl": tmp.name,                    # str -> output path filename
            "quiet": True,                          # bool -> minimize console output
            "ffmpeg_location": ffmpeg_path,         # Tell yt_dlp to use bundled ffmpeg
            "ignoreerrors": True,
            "noplaylist": True,
            "postprocessors": [],  # Whisper can read directly

            # "postprocessors": [{
            #     "key": "FFmpegExtractAudio",       # FFmpeg postprocessor: extracts audio stream
            #     "preferredcodec": "m4a",           # convert extracted audio to mp3
            #     "preferredquality": "192",         # kbps target bitrate (as str or int)
            # }],
        }
        # ============================================================
        # Step 4: Download the audio (yt_dlp) -> get metadata
        # ============================================================
        # yt_dlp.YoutubeDL returns a context object with method extract_info(url, download=True).
        # - Returns: info: dict (metadata extracted from page and chosen stream)
        # - If download=True, the selected format is written to outtmpl path (tmp.name)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # info: dict -> contains keys like "title": str, "id": str, "formats": list, etc.
            info = ydl.extract_info(youtube_url, download=True)
            # Example: info.get("title") -> "My Lecture on Graph Theory"
            title: str = info.get("title", "")  # title: str, default empty if missing

        # ============================================================
        # Step 5: Open the temp audio file and call OpenAI Whisper transcription API
        # ============================================================
        # Open the mp3/m4a file in binary mode and stream it to the API.
        # - file object type: _io.BufferedReader
        # - client.audio.transcriptions.create expects:
        #    - model: str -> "whisper-1"
        #    - file: a file-like binary stream or path (here: file object)
        #    - language (optional): "en" to force English detection
        #    - response_format (optional): "verbose_json" to receive segments & timestamps
        with open(tmp.name, "rb") as audio_file:
            # audio_file: Binary I/O stream (file pointer at start)
            # Call the OpenAI client's audio transcription endpoint
            transcript_response = client.audio.transcriptions.create(
                model="whisper-1",              # str -> use OpenAI's Whisper model (large-v3 quality)
                file=audio_file,                # Binary IO -> audio content
                language="en",                  # str -> force transcription language to English
                response_format="verbose_json", # str -> get structured output including timestamps
                temperature=0,                  # float -> deterministic transcript behavior
            )

            # The response object (transcript_response) is a structured object.
            # Most SDKs provide:
            # - transcript_response.text -> str (full transcribed text)
            # - transcript_response.segments -> list[dict] (each with start/end/text)
            # If the SDK returns nested JSON, it may be accessible via .to_dict() or dict() as well.
            # We standardize below to safe-access patterns.
            transcript_text: str = getattr(transcript_response, "text", "")  # str
            segments: list = getattr(transcript_response, "segments", [])    # list[dict]

    # ============================================================
    # Step[05]: Return Results: dict {...}
    # ============================================================
    # At this point the temporary file is closed and removed (NamedTemporaryFile context exited).
    # Return a clean Python dict with typed fields for downstream processing.
    return {
        "title": title, # str
        "transcript": transcript_text, # str
        "segments": segments, # list[dict], where each dict often includes "start": float, "end": float, "text": str
    }