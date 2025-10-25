"""
======================================================
DISCOVERY USING TAVILY

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

from APP.Configration import TAVILY_API_KEY, MAX_LINKS
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

def discover_with_tavily(id: UUID, query: str, search_type: str = "search", search_depth: str = "advanced") -> list:
    """
    Discover relevant results using Tavily's intelligent search API.

    Arguments:
    ----------
    - id: (UUID)
        Unique identifier of the search session or user request.
        Used here mainly for tracking/logging, not required by Tavily API.
    - query: (str)
        The user search query
    - search_depth: (str)
        Can be 'basic' or 'advanced'.
        - 'basic'  → faster, fewer results, less web traversal.
        - 'advanced' → slower, deeper search coverage and relevance ranking.

    Returns:
    --------
    list [ dict ]:
        [
            { "title": "<page title>", "link": "<URL>",  "snippet": "...", "retrieved_source": "tavily" },
            { "title": "<page title>", "link": "<URL>",  "snippet": "...", "retrieved_source": "tavily" },
            ...,
        ]
    """

    # ============================================================
    # Step[01]: Build the API Request
    # ============================================================

    # === Tavily API Endpoint for Search ===
    tavily_API_endpoint = "https://api.tavily.com/search"

    # === Request Headers ===
    # The Authorization header must contain "Bearer <YOUR_API_KEY>".
    # If you renamed "Authorization" to something else (like "API_KEY" or "Tavily_API_KEY"),
    # Tavily’s server would not recognize it, and you’d get an HTTP 401 Unauthorized error.
    # Content-Type must be JSON, as Tavily expects JSON-formatted POST body.
    headers = {"Authorization": f"Bearer {TAVILY_API_KEY}", "Content-Type": "application/json"}

    # Domain constraints to simulate Serper's search_type
    include_domains = []
    exclude_domains = []
    if search_type == "search":
        include_domains = []
        exclude_domains = VIDEO_DOMAINS
    elif search_type == "videos":
        include_domains = VIDEO_WHITELIST
        exclude_domains = []

    # === Request Payload, should be in JSON ===
    # NOTES for "payload" arguments in Tavily:
    #
    # JSON "payload" that Tavily expects:
    # {
    #   "query": "<query string>",
    #   "search_depth": "basic" | "advanced",
    #   "max_results": <int>
    # }
    #
    # Each field:
    # - "query": str  — the user search query.
    # - "search_depth": str  — determines how broad Tavily’s search expansion is.
    # - "max_results": int  — how many results you want (usually ≤20).
    # - "include_domains": list [str] — domains should be to include it
    # - "exclude_domains": list [str] — domains should be to exclude it
    #
    payload = {
        "query": query,
        "search_depth": search_depth,
        "max_results": MAX_LINKS,
        "include_domains": include_domains,
        "exclude_domains": exclude_domains
    }

    # ============================================================
    # Step[02]: Perform HTTP Request
    # ============================================================

    # Send POST request with JSON payload.
    # requests.post() returns a Response object.
    response = requests.post(tavily_API_endpoint, headers=headers, json=payload)

    # === Verify Response Status ===
    # If not 200, raise explicit exception.
    if response.status_code != 200:
        raise Exception(f"Tavily API error {response.status_code}: {response.text}")

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
    #   "results": [
    #       {
    #           "title": "Deep Learning Basics",
    #           "url": "https://example.com/deep-learning",
    #           "content": "Summary snippet ...",
    #           "score": 0.92,
    #           "raw_content": null,
    #       },
    #
    #       {
    #           "title": "---",
    #           "url": "---",
    #           "content": "---",
    #           "score": x.xx
    #           "raw_content": "---",
    #       },
    #
    #       ...,
    #   ],
    #
    #   "query": "deep learning"
    # }
    #
    data: dict = response.json()

    # ============================================================
    # Step[04]: Extract and Normalize Fields
    # ============================================================

    # === Extract Results ===
    raw_results: list[dict] = data.get("results", [])

    # === Cleaning Resulting, through erase (content) and (score) from raw_results ===
    # We only keep fields "title" and "link" to match Serper’s output format.
    # If title missing, fallback to empty string.
    results: list[dict[str,object]] = []
    for item in raw_results:
        results.append(
            {
                "title": item.get("title", ""),
                "link": item.get("url", ""),
                "snippet": item.get("content", ""),
                "retrieved_source": "tavily",
            }
        )

    # === Normalize Results (Filtration) ===
    # already filtered through "payload", this only for more guaranteed
    raw_results = results
    results = []
    if search_type == "search":
        results = filter_text_results(raw_results)
    elif search_type == "videos":
        results = filter_video_results(raw_results)

    # ============================================================
    # Step[05]: Return Results: list [ dict {...} ]
    # ============================================================

    results = results[:MAX_LINKS]
    return results