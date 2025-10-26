"""
======================================================
ASYNC DISCOVERY USING SERPER API

This module provides asynchronous web search capabilities using
Serper API (Google Search wrapper).

Key Features:
- Non-blocking HTTP requests with aiohttp
- Concurrent execution support
- Domain filtering for text vs video content
- Proper timeout handling
- Clean error messages

Return Structure:
    [
        {
            "title": str,
            "link": str,
            "snippet": str,
            "retrieved_source": "serper",
        },
        ...
    ]
======================================================
"""

# ================================================================
# IMPORT REQUIRED MODULES
# ================================================================

import aiohttp
import requests
from urllib.parse import urlparse
from typing import List, Dict
from uuid import UUID

from APP.Configration import SERPER_API_KEY, MAX_LINKS

# ============================================================
# Domain Filters
# ============================================================

# --- List of known video hosting or embedding domains ---
# These domains are excluded from text searches and required for video searches
VIDEO_DOMAINS = [
    # Major video platforms
    "youtube.com", "youtu.be", "vimeo.com", "dailymotion.com", "metacafe.com",
    "twitch.tv", "bilibili.com", "veoh.com", "vevo.com",

    # Social media video platforms
    "facebook.com", "fb.watch", "instagram.com", "tiktok.com", "x.com", "twitter.com",
    "linkedin.com/video",

    # Educational & course-based video hosting
    "coursera.org/lecture", "udemy.com/course", "edx.org/course", "khanacademy.org/video",

    # Streaming services & media CDNs
    "netflix.com", "hulu.com", "primevideo.com", "disneyplus.com",
    "player.vimeo.com", "video.google.com", "cdn.jwplayer.com", "videos.cdn", "dai.ly",
]

# --- Video Whitelist (for video-only searches) ---
# Only these platforms are included in video search results
VIDEO_WHITELIST = [
    # Major platforms with reliable APIs
    "youtube.com", "youtu.be", "vimeo.com", "dailymotion.com",
    "twitch.tv", "bilibili.com",

    # Social video (limited support)
    "linkedin.com/video",

    # Educational platforms (well-structured content)
    "coursera.org/lecture", "udemy.com/course", "edx.org/course", "khanacademy.org/video",

    # Other supported platforms
    "video.google.com",
]


# ============================================================
# Helper Functions
# ============================================================

def clean_url(link: str) -> str:
    """
    Ensure the URL is valid and normalized.

    Handles edge cases like:
    - Missing scheme (http/https)
    - Extra whitespace
    - Relative URLs

    Arguments:
        link (str): A raw URL string returned by Serper API.

    Returns:
        (str): Normalized URL with proper scheme (https://example.com/path).

    Examples:
        >>> clean_url("example.com")
        "https://example.com"
        >>> clean_url("https://example.com")
        "https://example.com"
    """
    link = link.strip()
    parsed = urlparse(link)

    # If missing scheme (like 'example.com'), prepend 'https://'
    if not parsed.scheme:
        return "https://" + link

    return link


def is_video_link(link: str) -> bool:
    """
    Check whether a given URL belongs to a known video domain.

    Used to filter out video content from text-based searches.

    Arguments:
        link (str): URL to check.

    Returns:
        (bool): True if the URL is from a video hosting platform.

    Examples:
        >>> is_video_link("https://youtube.com/watch?v=xyz")
        True
        >>> is_video_link("https://wikipedia.org/wiki/Python")
        False
    """
    # Extract domain from URL (e.g., "www.youtube.com" → "youtube.com")
    domain = urlparse(link).netloc.lower()

    # Check if any video domain is present in the URL
    return any(vd in domain or vd in link.lower() for vd in VIDEO_DOMAINS)


def is_allowed_video_link(link: str) -> bool:
    """
    Check if the link is in the whitelist for video retrieval.

    More restrictive than is_video_link() - only allows platforms
    we have proper support for (YouTube, Vimeo, etc.).

    Arguments:
        link (str): URL to check.

    Returns:
        (bool): True if the URL is from an allowed video platform.

    Examples:
        >>> is_allowed_video_link("https://youtube.com/watch?v=xyz")
        True
        >>> is_allowed_video_link("https://netflix.com/watch/12345")
        False  # Not in whitelist
    """

    # < .netloc >   Extracts the domain name (like www.youtube.com, youtube.com, wikipedia.org, etc.) from a full URL.
    # < .lower() >  Converts to lowercase for case-insensitive comparison, because domains aren’t case-sensitive.
    domain = urlparse(link).netloc.lower()
    return any(vd in domain or vd in link.lower() for vd in VIDEO_WHITELIST)


def filter_text_results(results: List[Dict]) -> List[Dict]:
    """
    Remove any video-related links from text-based search results.

    Ensures clean separation between text articles and video content.

    Arguments:
        results (List[Dict]): Raw search results from Serper API.

    Returns:
        (List[Dict]): Filtered results containing only text-based URLs.
    """
    return [item for item in results if not is_video_link(item.get("link", ""))]


def filter_video_results(results: List[Dict]) -> List[Dict]:
    """
    Keep only allowed video platform links for video-based search.

    Filters out unsupported platforms and ensures we only return
    videos we can properly process.

    Arguments:
        results (List[Dict]): Raw search results from Serper API.

    Returns:
        (List[Dict]): Filtered results containing only whitelisted video URLs.
    """
    return [item for item in results if is_allowed_video_link(item.get("link", ""))]


# ============================================================
# Main Async Function
# ============================================================

async def discover_with_serper(
        id: UUID,
        query: str,
        search_type: str = "search"
) -> list[dict[str, object]]:
    """
    Asynchronously discover relevant results using Serper's API (Google Search wrapper).

    This function performs non-blocking HTTP requests to Serper API, which provides
    structured access to Google Search results. It supports both text-based searches
    and video-specific searches with appropriate filtering.

    Architecture:
    ------------
    1. Build API request with proper headers and payload
    2. Execute async HTTP POST request (non-blocking)
    3. Parse and validate JSON response
    4. Extract relevant fields (title, link, snippet)
    5. Apply domain filters based on search_type
    6. Return top N results (limited by MAX_LINKS)

    Arguments:
    ----------
    id : UUID
        Unique identifier of the user request for personalization.
        Used for tracking/logging purposes (not sent to Serper API).

    query : str
        The user's search query string.
        Examples: "machine learning basics", "python tutorial"

    search_type : str, optional (default="search")
        Type of search to perform:
        - 'search' : Text-based web pages (articles, documentation, etc.)
        - 'videos' : Video content (YouTube, Vimeo, etc.)

    NOTE:
    Inside Serper:
    Serper provides different REST endpoints for different verticals (search, news, images, videos).
    It wraps Google Search API results into clean JSON.



    Returns:
    -------
    list[dict[str, object]]
        List of search results, each containing:
        [
            {
                "title": str,                   # Page/video title
                "link": str,                    # Full URL
                "snippet": str,                 # Short description/excerpt
                "retrieved_source": "serper"    # Source identifier
            },
            ...
        ]

        Returns empty list [] if:
        - No results found
        - API error occurs
        - Network timeout

    Raises
    ------
    Exception
        - If Serper API returns non-200 status code
        - If network connection fails (wrapped in Exception)
        - If JSON parsing fails

    Examples
    --------
    >>> results = await discover_with_serper(
    ...     uuid4(),
    ...     "async python tutorial",
    ...     "search"
    ... )
    >>> print(f"Found {len(results)} results")
    >>> print(results[0]['title'])

    Notes
    -----
    - Uses aiohttp for async HTTP (non-blocking I/O)
    - Respects 30-second timeout per request
    - Automatically filters video content from text searches
    - Limits results to MAX_LINKS (configured in APP.Configration)
    - Serper API requires valid API key in SERPER_API_KEY

    Performance
    -----------
    - Typical latency: 1-3 seconds per request
    - Non-blocking: allows concurrent requests
    - Memory efficient: streams JSON response

    API Documentation
    -----------------
    Serper API endpoint format:
        POST https://google.serper.dev/{search_type}

    Required headers:
        - X-API-KEY: Your Serper API key
        - Content-Type: application/json

    Payload structure:
        Optional Arguments:
        Makes code flexible — you can later add other fields (like "gl": "us" or "hl": "en") easily:
        payload = {"q": query, "gl": "us", "hl": "en"}

        | ------ | -------------------------------------------- | --------------------------------------------------------------------------------------  | --------------------------- |
        | Field  | Meaning                                      | Expected Type                                                                           | Typical Example             |
        | ------ | -------------------------------------------- | --------------------------------------------------------------------------------------  | --------------------------- |
        | `"q"`  | The search query string                      | `str`                                                                                   | `"machine learning basics"` |
        | `"gl"` | The country code (stands for Geo Location)   | `str` (2-letter [ISO-3166] (https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2))          | `"us"`, `"fr"`, `"jp"`      |
        | `"hl"` | The host language (stands for Host Language) | `str` (2-letter [IETF language code] (https://en.wikipedia.org/wiki/IETF_language_tag)) | `"en"`, `"es"`, `"ar"`      |
        | ------ | -------------------------------------------- | --------------------------------------------------------------------------------------  | --------------------------- |
    """

    # ============================================================
    # Step[01]: Build the API Request
    # ============================================================

    # === Serper API Endpoint ===
    # The endpoint changes based on search_type:
    # - "search" → https://google.serper.dev/search
    # - "videos" → https://google.serper.dev/videos
    serper_API_endpoint = f"https://google.serper.dev/{search_type}"

    # === Request Headers ===
    # CRITICAL: "X-API-KEY" is the exact header name required by Serper.
    # Changing this name to something else (like "API_KEY" or "SERPER_API_KEY"),
    # will result in 401 Unauthorized errors.
    # "Content-Type" tells the server we're sending JSON data.
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    # === Request Payload ===
    # JSON payload that Serper expects:
    #
    # Field Descriptions:
    # - "q" (required): The search query string
    # - "hl" (optional): Host language code (ISO 639-1 format)
    #     Examples: "en" (English), "es" (Spanish), "fr" (French)
    #
    # Optional fields you can add:
    # - "gl": Geographic location (country code, e.g., "us", "uk")
    # - "num": Number of results to return (default: 10)
    # - "page": Page number for pagination
    payload = {
        "q": query,
        "hl": "en",  # Request results in English
    }

    # ============================================================
    # Step[02]: Perform Async HTTP Request
    # ============================================================

    # === Configure Timeout ===
    # Prevent hanging on slow API responses or network issues.
    # Total timeout includes connection + request + response time.
    timeout = aiohttp.ClientTimeout(total=30)

    # === Async HTTP Client Session ===
    # aiohttp.ClientSession() manages connection pooling and keeps
    # connections alive for better performance across multiple requests.
    #
    # Using 'async with' ensures proper cleanup even if errors occur.
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            # === Execute POST Request (Non-Blocking) ===
            # 'await' keyword yields control to event loop while waiting,
            # allowing other async tasks to run concurrently.
            async with session.post(
                    serper_API_endpoint,
                    headers=headers,
                    json=payload  # Automatically serializes dict to JSON
            ) as response:

                # === Verify Response Status ===
                # HTTP 200 = Success
                # Common error codes:
                # - 401: Invalid API key
                # - 429: Rate limit exceeded
                # - 500: Serper server error
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Serper API error {response.status}: {error_text}")

                # === Parse JSON Response (Non-Blocking) ===
                # Converts JSON string → Python dictionary
                # 'await' because reading response body is I/O operation
                data = await response.json()

        except aiohttp.ClientError as e:
            # Network-level errors (connection refused, DNS failure, etc.)
            raise Exception(f"Serper API network error: {e}")

    # ============================================================
    # Step[03]: Extract and Normalize Fields
    # ============================================================

    # === Initialize Results List ===
    raw_results: list[dict[str, object]] = []

    # === Extract Based on Search Type ===
    if search_type == "search":
        # Text-based search: Extract from "organic" results
        # "organic" include all types (Text, News, Images, Videos)
        # So we need more filtration process
        # "organic" contains natural search results (not ads)
        # Structure: {"organic": [{...}, {...}, ...]}
        for item in data.get("organic", []):
            raw_results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "retrieved_source": "serper",
            })

    elif search_type == "videos":
        # Video search: Extract from "videos" results
        # Structure: {"videos": [{...}, {...}, ...]}
        for item in data.get("videos", []):
            raw_results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "retrieved_source": "serper",
            })

    # ============================================================
    # Step[04]: Apply Domain Filters
    # ============================================================

    # === Filter Results Based on Search Type ===
    results: list[dict[str, object]] = []

    if search_type == "search":
        # Text search: Remove all video platform URLs
        # Ensures clean separation between content types
        results = filter_text_results(raw_results)

    elif search_type == "videos":
        # Video search: Keep only whitelisted video platforms
        # Filters out platforms we can't process properly
        results = filter_video_results(raw_results)

    # ============================================================
    # Step[05]: Return Top N Results
    # ============================================================

    # === Limit to MAX_LINKS ===
    # Prevents overwhelming downstream processing with too many URLs
    # MAX_LINKS is configured in APP.Configration (typically 5-10)
    return results[:MAX_LINKS]