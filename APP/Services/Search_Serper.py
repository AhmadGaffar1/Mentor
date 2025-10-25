"""
======================================================
DISCOVERY USING SERPER

Return:
    [
        {
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "retrieved_source": "serper",
        }
    ]
======================================================
"""

# ================================================================
# IMPORT REQUIRED MODULES
# ================================================================

import requests
from urllib.parse import urlparse

from APP.Configration import SERPER_API_KEY, MAX_LINKS
from uuid import UUID

# ============================================================
# Domain Filters
# ============================================================

# --- List of known video hosting or embedding domains ---
VIDEO_DOMAINS = [
    # Major platforms
    "youtube.com", "youtu.be", "vimeo.com", "dailymotion.com", "metacafe.com",
    "twitch.tv", "bilibili.com", "veoh.com", "vevo.com",

    # Social video platforms
    "facebook.com", "fb.watch", "instagram.com", "tiktok.com", "x.com", "twitter.com",
    "linkedin.com/video",

    # Education & course-based video hosting
    "coursera.org/lecture", "udemy.com/course", "edx.org/course", "khanacademy.org/video",

    # Streaming / media CDNs
    "netflix.com", "hulu.com", "primevideo.com", "disneyplus.com",
    "player.vimeo.com", "video.google.com", "cdn.jwplayer.com", "videos.cdn", "dai.ly",
]

# --- Video Whitelist (for video-only searches) ---
VIDEO_WHITELIST = [
    # Major platforms
    "youtube.com", "youtu.be", "vimeo.com", "dailymotion.com",
    "twitch.tv", "bilibili.com",

    # Social video platforms
    "linkedin.com/video",

    # Education & course-based video hosting
    "coursera.org/lecture", "udemy.com/course", "edx.org/course", "khanacademy.org/video",

    # Streaming / media CDNs
    "video.google.com",
]

# ============================================================
# Helper Functions
# ============================================================

def clean_url(link: str) -> str:
    """
    Ensure the URL is valid and normalized.

    Arguments:
        link (str): A raw URL string returned by Tavily.

    Returns:
        (str): Normalized URL (scheme + netloc + path).
    """
    parsed = urlparse(link)
    if not parsed.scheme:
        # If missing scheme (like 'example.com'), prepend 'https://'
        return "https://" + link
    return link

def is_video_link(link: str) -> bool:
    """Check whether a given URL belongs to a known video domain."""
    # < .netloc >   Extracts the domain name (like www.youtube.com, youtube.com, wikipedia.org, etc.) from a full URL.
    # < .lower() >  Converts to lowercase for case-insensitive comparison, because domains aren’t case-sensitive.
    domain = urlparse(link).netloc.lower()
    return any(vd in domain or vd in link.lower() for vd in VIDEO_DOMAINS)

def is_allowed_video_link(link: str) -> bool:
    """Check if the link is in the whitelist for video retrieval."""
    # < .netloc >   Extracts the domain name (like www.youtube.com, youtube.com, wikipedia.org, etc.) from a full URL.
    # < .lower() >  Converts to lowercase for case-insensitive comparison, because domains aren’t case-sensitive.
    domain = urlparse(link).netloc.lower()
    return any(vd in domain or vd in link.lower() for vd in VIDEO_WHITELIST)

def filter_text_results(results: list[dict]) -> list[dict]:
    """Remove any video-related links from text-based search results."""
    return [item for item in results if not is_video_link(item.get("link", ""))]

def filter_video_results(results: list[dict]) -> list[dict]:
    """Keep only allowed video platform links for video-based search."""
    return [item for item in results if is_allowed_video_link(item.get("link", ""))]

# ============================================================
# Main Function
# ============================================================

def discover_with_serper(id: UUID, query: str, search_type: str = "search") -> list:
    """
    Discover relevant results using Serper's API (Wrapper for Google Search Engine API).

    Arguments:
    ----------
    - id: (UUID)
        Unique identifier of the search session or user request.
        Used here mainly for tracking/logging, not required by Serper API.
    - query: (str)
        The user search query
    - search_type: '
        - search' for text pages.
        - 'videos' for YouTube results.

    NOTE:
    Inside Serper:
    Serper provides different REST endpoints for different verticals (search, news, images, videos).
    It wraps Google Search API results into clean JSON.

    Returns:
    --------
    list [ dict ]:
        [
            { "title": "<page title>", "link": "<URL>",  "snippet": "...", "retrieved_source": "serper" },
            { "title": "<page title>", "link": "<URL>",  "snippet": "...", "retrieved_source": "serper" },
            ...,
        ]
    """

    # ============================================================
    # Step[01]: Build the API Request
    # ============================================================

    # === Serper API Endpoint for Search ===
    serper_API_endpoint = f"https://google.serper.dev/{search_type}"

    # === Request Headers ===
    # "X-API-KEY"  is the key name required by Serper’s API spec
    # If you renamed "X-API-KEY" to something else (like "API_KEY" or "SERPER_API_KEY"),
    # Serper’s server would not recognize it, and you’d get an HTTP 401 Unauthorized error.
    # Content-Type must be JSON, as Serper expects JSON-formatted POST body.
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}

    # === Request Payload, should be in JSON ===
    # NOTES for "payload" arguments in Serper:
    #
    # JSON "payload" that Serper expects:
    # Mandatory Arguments:
    # You must wrap it as a dictionary like: object = {"q": query}
    # because the Serper API expects JSON with a field named "q", not just a raw string.
    #
    # Optional Arguments:
    # Makes code flexible — you can later add other fields (like "gl": "us" or "hl": "en") easily:
    # payload = {"q": query, "gl": "us", "hl": "en"}
    #
    # | ------ | -------------------------------------------- | --------------------------------------------------------------------------------------  | --------------------------- |
    # | Field  | Meaning                                      | Expected Type                                                                           | Typical Example             |
    # | ------ | -------------------------------------------- | --------------------------------------------------------------------------------------  | --------------------------- |
    # | `"q"`  | The search query string                      | `str`                                                                                   | `"machine learning basics"` |
    # | `"gl"` | The country code (stands for Geo Location)   | `str` (2-letter [ISO-3166] (https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2))          | `"us"`, `"fr"`, `"jp"`      |
    # | `"hl"` | The host language (stands for Host Language) | `str` (2-letter [IETF language code] (https://en.wikipedia.org/wiki/IETF_language_tag)) | `"en"`, `"es"`, `"ar"`      |
    # | ------ | -------------------------------------------- | --------------------------------------------------------------------------------------  | --------------------------- |
    #
    payload = {
        "q": query,
        "hl": "en",
    }

    # ============================================================
    # Step[02]: Perform HTTP Request
    # ============================================================

    # Send POST request with JSON payload.
    # requests.post() returns a Response object.
    response = requests.post(serper_API_endpoint, headers=headers, json=payload)

    # === Verify Response Status ===
    # If not 200, raise explicit exception.
    if response.status_code != 200:
        raise Exception(f"Serper API error {response.status_code}: {response.text}")

    # ============================================================
    # Step[03]: Parse and Process Response
    # ============================================================

    # === Convert JSON → Python dict ===
    # Converts the raw JSON text from the HTTP response body into a native Python dictionary.
    # response.json() calls Python’s built-in json.loads(response.text) under the hood.
    # So your raw JSON string becomes a Python object (Python dictionary).
    #
    # Example for data after stored in Python dictionary:
    # data = response.json()
    # data:
    # {
    #   "organic": [
    #     {"title": "Intro to Machine Learning", "link": "https://example.com/ml-intro", "snippet": "---", ...},
    #     {"title": "Basics of ML", "link": "https://ml-basics.com", "snippet": "---", ...},
    #     ...,
    #   ],
    #   "videos": [
    #     {"title": "Machine Learning Crash Course", "link": "https://youtube.com/watch?v=xyz", , "snippet": "---", ...},
    #     {"title": "---", "link": "---", , "snippet": "---", ...},
    #     ...,
    #   ]
    # }
    #
    data = response.json()

    # ============================================================
    # Step[04]: Extract and Normalize Fields
    # ============================================================

    # === Extract Results ===
    # Storing only data relevant to search_type into variable ( results )
    raw_results: list[dict[str,object]] = []
    if search_type == "search":
        # "organic" include all types (Text, News, Images, Videos)
        # So we need more filtration process
        for item in data.get("organic", []):
            raw_results.append(
                {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "retrieved_source": "serper",
                }
            )

    elif search_type == "videos":
        for item in data.get("videos", []):
            raw_results.append(
                {
                    "title": item.get("title",""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "retrieved_source": "serper",
                }
            )

    # === Normalize Results (Filtration) ===
    results: list[dict[str,object]] = []
    if search_type == "search":
        results = filter_text_results(raw_results)
    elif search_type == "videos":
        results = filter_video_results(raw_results)

    # ================================================================
    # Step[05]: Return Results: list[ dict {...} ]
    # ================================================================

    # === Keep Only Top ( n == MAX_LINK ) Links ===
    results = results[:MAX_LINKS]

    return results