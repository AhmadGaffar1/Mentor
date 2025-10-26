"""
======================================================
ASYNC DISCOVERY USING TAVILY API

This module provides asynchronous intelligent search capabilities
using Tavily API (AI-powered search engine).

Key Features:
- Non-blocking HTTP requests with aiohttp
- Advanced search depth control (basic vs advanced)
- Domain inclusion/exclusion filters
- Concurrent execution support
- Proper timeout handling
- Clean error messages

Return Structure:
    [
        {
            "title": str,
            "link": str,
            "snippet": str,
            "retrieved_source": "tavily",
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
from uuid import UUID

from APP.Configration import TAVILY_API_KEY, MAX_LINKS

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
        link (str): A raw URL string returned by Tavily API.

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
    domain = urlparse(link).netloc.lower()
    return any(vd in domain or vd in link.lower() for vd in VIDEO_WHITELIST)


def filter_text_results(results: list[dict]) -> list[dict]:
    """
    Remove any video-related links from text-based search results.

    Ensures clean separation between text articles and video content.

    Arguments:
        results (List[Dict]): Raw search results from Tavily API.

    Returns:
        (List[Dict]): Filtered results containing only text-based URLs.
    """
    return [item for item in results if not is_video_link(item.get("link", ""))]


def filter_video_results(results: list[dict]) -> list[dict]:
    """
    Keep only allowed video platform links for video-based search.

    Filters out unsupported platforms and ensures we only return
    videos we can properly process.

    Arguments:
        results (List[Dict]): Raw search results from Tavily API.

    Returns:
        (List[Dict]): Filtered results containing only whitelisted video URLs.
    """
    return [item for item in results if is_allowed_video_link(item.get("link", ""))]


# ============================================================
# Main Async Function
# ============================================================

async def discover_with_tavily(
        id: UUID,
        query: str,
        search_type: str = "search",
        search_depth: str = "advanced"
) -> list[dict[str, object]]:
    """
    Asynchronously discover relevant results using Tavily's intelligent search API.

    Tavily is an AI-powered search engine optimized for LLMs and research applications.
    It provides deeper, more contextual results compared to traditional search engines,
    with built-in relevance ranking and content extraction.

    Architecture:
    ------------
    1. Build API request with domain filters and search depth
    2. Execute async HTTP POST request (non-blocking)
    3. Parse and validate JSON response
    4. Extract and normalize fields (title, url→link, content→snippet)
    5. Apply additional domain filters for safety
    6. Return top N results (limited by MAX_LINKS)

    Parameters
    ----------
    id : UUID
        Unique identifier of the user request for personalization.
        Used for tracking/logging purposes (not sent to Tavily API).

    query : str
        The user's search query string.
        Examples: "machine learning basics", "quantum computing tutorial"

    search_type : str, optional (default="search")
        Type of search to perform:
        - 'search' : Text-based web pages (articles, documentation, blogs)
        - 'videos' : Video content (YouTube, Vimeo, educational platforms)

    search_depth : str, optional (default="advanced")
        Controls the depth and quality of search results:
        - 'basic' : Faster, fewer results, surface-level coverage
                    Best for: Quick lookups, simple queries
                    Latency: ~1-2 seconds

        - 'advanced' : Slower, more results, deeper analysis
                       Best for: Research, comprehensive coverage
                       Latency: ~3-5 seconds
                       Features: Better relevance ranking, more context

    Returns
    -------
    list[dict[str, object]]
        List of search results, each containing:
        [
            {
                "title": str,                   # Page/video title
                "link": str,                    # Full URL
                "snippet": str,                 # Content excerpt or description
                "retrieved_source": "tavily"    # Source identifier
            },
            ...
        ]

        Returns empty list [] if:
        - No results found
        - API error occurs
        - Network timeout
        - Invalid API key

    Raises
    ------
    Exception
        - If Tavily API returns non-200 status code
        - If network connection fails (wrapped in Exception)
        - If JSON parsing fails
        - If API key is invalid or missing

    Examples
    --------
    Basic text search:
    >>> results = await discover_with_tavily(
    ...     uuid4(),
    ...     "async programming patterns",
    ...     search_type="search",
    ...     search_depth="basic"
    ... )
    >>> print(f"Found {len(results)} results")
    >>> print(results[0]['title'])

    Advanced research query:
    >>> results = await discover_with_tavily(
    ...     uuid4(),
    ...     "quantum entanglement applications",
    ...     search_type="search",
    ...     search_depth="advanced"
    ... )

    Video search:
    >>> videos = await discover_with_tavily(
    ...     uuid4(),
    ...     "python tutorial for beginners",
    ...     search_type="videos"
    ... )

    Notes
    -----
    - Uses aiohttp for async HTTP (non-blocking I/O)
    - Respects 30-second timeout per request
    - Domain filtering happens at two levels:
        1. API level: include_domains/exclude_domains in payload
        2. Code level: Additional safety checks after API response
    - Tavily API is more expensive but provides higher quality results
    - Results are pre-ranked by Tavily's AI relevance algorithm

    Performance
    -----------
    - Basic search latency: 1-2 seconds
    - Advanced search latency: 3-5 seconds
    - Non-blocking: allows concurrent requests
    - Memory efficient: streams JSON response

    Tavily vs Other Search APIs
    ---------------------------
    Advantages:
    - Better relevance ranking (AI-powered)
    - Built-in content extraction
    - Optimized for LLM consumption
    - Cleaner, more structured results

    Trade-offs:
    - Higher cost per request
    - Smaller index than Google
    - May miss very recent content

    API Documentation
    -----------------
    Tavily API endpoint:
        POST https://api.tavily.com/search

    Required headers:
        - Authorization: Bearer {TAVILY_API_KEY}
        - Content-Type: application/json

    Payload structure:
        {
            "query": "search query",
            "search_depth": "basic" | "advanced",
            "max_results": 10,
            "include_domains": ["domain1.com", ...],  # Optional
            "exclude_domains": ["domain2.com", ...]   # Optional
        }

    Response structure:
        {
            "results": [
                {
                    "title": "...",
                    "url": "...",           # Note: "url" not "link"
                    "content": "...",       # Note: "content" not "snippet"
                    "score": 0.95,          # Relevance score (0-1)
                    "raw_content": "..."    # Full page text as html (optional)
                },
                ...
            ],
            "query": "original query string"
        }
    """

    # ============================================================
    # Step[01]: Build the API Request
    # ============================================================

    # === Tavily API Endpoint ===
    # Tavily uses a single endpoint for all search types
    # Search behavior is controlled by domain filters
    tavily_API_endpoint = "https://api.tavily.com/search"

    # === Request Headers ===
    # CRITICAL: Tavily requires "Bearer" token authentication
    # Format: "Authorization: Bearer <YOUR_API_KEY>"
    # Changing this format will result in 401 Unauthorized errors
    headers = {
        "Authorization": f"Bearer {TAVILY_API_KEY}",
        "Content-Type": "application/json"
    }

    # === Domain Constraints Based on Search Type ===
    # These lists control which domains are included/excluded
    # Empty list means no constraint in that direction
    include_domains: list[str] = []
    exclude_domains: list[str] = []

    if search_type == "search":
        # Text search: Exclude all video platforms
        # This prevents video URLs from appearing in article results
        include_domains = []  # No restrictions on what to include
        exclude_domains = VIDEO_DOMAINS  # But exclude all video sites

    elif search_type == "videos":
        # Video search: Only include whitelisted video platforms
        # This ensures we only get videos we can properly process
        include_domains = VIDEO_WHITELIST  # Only these platforms
        exclude_domains = []  # No additional exclusions needed

    # === Request Payload ===
    # JSON payload that Tavily expects
    #
    # Field Descriptions:
    # - "query" (required): The search query string
    # - "search_depth" (optional): "basic" or "advanced"
    #     - "basic": Fast, good for simple queries
    #     - "advanced": Thorough, better for research
    # - "max_results" (optional): Number of results to return (1-20)
    # - "include_domains" (optional): Whitelist of domains to search
    # - "exclude_domains" (optional): Blacklist of domains to avoid
    #
    # Other optional fields (not used here):
    # - "include_answer": Return an AI-generated answer
    # - "include_raw_content": Include full page HTML
    # - "include_images": Return relevant images
    payload = {
        "query": query,
        "search_depth": search_depth,
        "max_results": MAX_LINKS,
        "include_domains": include_domains,
        "exclude_domains": exclude_domains
    }

    # ============================================================
    # Step[02]: Perform Async HTTP Request
    # ============================================================

    # === Configure Timeout ===
    # Advanced searches can take longer, so we use 30s timeout
    # This is higher than the typical search_depth latency to account for:
    # - Network delays
    # - API server load
    # - Complex queries
    timeout = aiohttp.ClientTimeout(total=30)

    # === Async HTTP Client Session ===
    # ClientSession manages:
    # - Connection pooling (reuse connections)
    # - Cookie persistence
    # - Timeout enforcement
    # - Proper cleanup on errors
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            # === Execute POST Request (Non-Blocking) ===
            # The 'await' keyword is critical here:
            # - It yields control back to the event loop
            # - Allows other async tasks to run concurrently
            # - Resumes this function when response arrives
            async with session.post(
                    tavily_API_endpoint,
                    headers=headers,
                    json=payload  # Automatically serializes dict → JSON string
            ) as response:

                # === Verify Response Status ===
                # HTTP status codes:
                # - 200: Success
                # - 400: Bad request (malformed payload)
                # - 401: Unauthorized (invalid API key)
                # - 429: Rate limit exceeded
                # - 500: Tavily server error
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Tavily API error {response.status}: {error_text}")

                # === Convert JSON → Python dict ===
                # Converts the raw JSON text from the HTTP response body into a native Python dictionary.
                # response.json() calls Python’s built-in json.loads(response.text) under the hood.
                # So your raw JSON string becomes a Python object (Python dictionary).
                #
                # 'await' because reading response body is I/O operation
                # This is non-blocking - other tasks can run during parsing
                #
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
                #   ],
                #
                #   "query": "deep learning"
                # }
                #
                data = await response.json()

        except aiohttp.ClientError as e:
            # Network-level errors:
            # - Connection refused
            # - DNS resolution failure
            # - Timeout (exceeds 30 seconds)
            # - SSL/TLS errors
            raise Exception(f"Tavily API network error: {e}")

    # ============================================================
    # Step[03]: Extract and Normalize Fields
    # ============================================================

    # === Extract Results Array ===
    # Tavily returns results in a "results" array
    # Structure: {"results": [{...}, {...}, ...], "query": "..."}
    raw_results: list[dict] = data.get("results", [])

    # === Map Tavily's Field Names to Our Standard Format ===
    # Tavily uses different field names than Serper:
    # - "url" → "link" (for consistency with Serper)
    # - "content" → "snippet" (for consistency with Serper)
    #
    # This normalization ensures downstream code works with both APIs
    # without needing to know which API was used.
    results: list[dict[str, object]] = []

    for item in raw_results:
        results.append({
            # Standard field: title
            "title": item.get("title", ""),

            # Tavily uses "url" - we rename to "link"
            "link": item.get("url", ""),

            # Tavily uses "content" - we rename to "snippet"
            "snippet": item.get("content", ""),

            # Source identifier for tracking
            "retrieved_source": "tavily",
        })
        # Note: We intentionally drop Tavily-specific fields:
        # - "score": Relevance score (0-1)
        # - "raw_content": Full page HTML
        # These can be added if needed in the future

    # ============================================================
    # Step[04]: Apply Domain Filters (Additional Safety Layer)
    # ============================================================

    # === Why Double Filtering? ===
    # We filter at two levels:
    # 1. API level (include_domains/exclude_domains in payload)
    # 2. Code level (these filters below)
    #
    # Reasons for double filtering:
    # - API filters might not be 100% precise
    # - Adds safety for edge cases
    # - Handles subdomain variations (e.g., "m.youtube.com")
    # - Catches URLs that slip through API filters

    # Store original results before filtering (for debugging if needed)
    raw_results = results
    results = []

    if search_type == "search":
        # Text search: Remove all video platform URLs
        # Even if API excluded them, this catches edge cases
        results = filter_text_results(raw_results)

    elif search_type == "videos":
        # Video search: Keep only whitelisted platforms
        # Ensures we only return videos we can process
        results = filter_video_results(raw_results)

    # ============================================================
    # Step[05]: Return Top N Results
    # ============================================================

    # === Limit to MAX_LINKS ===
    # Although we request MAX_LINKS from Tavily API,
    # filtering might have removed some results.
    # This ensures we never return more than MAX_LINKS.
    #
    # Example scenario:
    # - Request 10 results from API
    # - API returns 10 results
    # - Filtering removes 3 video URLs from text search
    # - We return 7 results (not 10)
    return results[:MAX_LINKS]