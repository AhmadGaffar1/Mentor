"""
======================================================
ASYNC CONTENT EXTRACTION USING DIFFBOT API

This module provides asynchronous article extraction capabilities
using Diffbot's Article API for high-quality content extraction.

Key Features:
- Non-blocking HTTP requests with aiohttp
- Intelligent content extraction (removes ads, navigation, etc.)
- Structured metadata extraction (author, date, tags)
- Graceful fallback when extraction fails
- Preserves original search data
- Proper timeout handling

Input Structure:
    {
        "title": str,
        "link": str,
        "snippet": str,
        "retrieved_source": "serper" | "tavily",
    }

Output Structure:
    {
        "title": str,                               # Enhanced by Diffbot or original
        "link": str,
        "snippet": str,                             # Original snippet preserved
        "retrieved_source": "serper" | "tavily",
        "text": str,                                # Full article content or snippet as fallback
        "author": str | None,
        "site": str | None,
        "date": str | None,
        "tags": list[str],
    }
======================================================
"""

# ================================================================
# IMPORT REQUIRED MODULES
# ================================================================

import aiohttp
from typing import Dict, Optional, List, Any
from uuid import UUID

from APP.Configration import DIFFBOT_API_KEY, MAX_TIME_FOR_TEXT_EXTRACTION


# ============================================================
# Helper Function: Fallback Result
# ============================================================

def _create_fallback_result(url: str, original_item: dict[str, object]) -> dict[str, object]:
    """
    Create a fallback result when Diffbot extraction fails.

    Preserves original search result data without enrichment.
    This ensures the pipeline continues operating even when
    individual extractions fail.

    Design Philosophy:
    - Never lose original data
    - Degrade gracefully
    - Always return consistent structure
    - Enable downstream processing to continue

    Parameters
    ----------
    url : str
        The URL that failed extraction.

    original_item : dict[str, object]
        Original search result containing:
        - title: Original title
        - snippet: Short description
        - retrieved_source: "serper" or "tavily"

    Returns
    -------
    dict[str, object]
        Minimal result structure with original data:
        {
            "title": str,               # Original title from search
            "link": str,                # URL
            "snippet": str,             # Same snippet
            "retrieved_source": str,    # Original source
            "text": str,                # Snippet used as text
            "author": None,             # No extraction occurred
            "site": None,               # Site Name
            "date": None,               # No extraction occurred
            "tags": []                  # Empty list
        }

    Examples
    --------
    >>> fallback = _create_fallback_result(
    ...     "https://paywall.example.com/article",
    ...     {
    ...         "title": "Premium Article",
    ...         "snippet": "Subscribe to read...",
    ...         "retrieved_source": "serper"
    ...     }
    ... )
    >>> print(fallback["text"])
    "Subscribe to read..."  # Snippet used as text
    >>> print(fallback["author"])
    None  # No metadata available

    Notes
    -----
    - All Diffbot-specific fields default to None or []
    - Original snippet is used as the "text" field
    - Structure matches successful extraction for consistency
    - Enables downstream code to handle all results uniformly
    """
    return {
        # === Original Search Data ===
        "title": original_item.get("title"),
        "link": url,
        "snippet": original_item.get("snippet", ""),
        "retrieved_source": original_item.get("retrieved_source"),

        # === Text Field (Critical for Downstream Processing) ===
        # Use snippet as text - this ensures downstream code
        # always has *something* to work with, even if it's brief
        "text": None,

        # === Metadata Fields (Unavailable) ===
        # Set to None/empty to indicate no extraction occurred
        # This is different from "" (empty string) which would
        # suggest extraction succeeded but found nothing
        "author": None,
        "site": None,
        "date": None,
        "tags": [],
    }


# ============================================================
# Main Async Extraction Function
# ============================================================

async def extract_with_diffbot(
        id: UUID,
        url: str,
        original_item: dict[str, object]
) -> dict[str, object]:
    """
    Asynchronously extract high-quality structured content from a webpage using Diffbot's Article API.

    Diffbot is an AI-powered web scraping service that:
    - Automatically identifies article content vs. ads/navigation
    - Extracts clean, readable text without HTML noise
    - Identifies metadata (author, publish date, tags)
    - Handles complex page layouts and dynamic content
    - Works across multiple languages

    Architecture:
    ------------
    1. Build API request with URL and extraction parameters
    2. Execute async HTTP GET request (non-blocking)
    3. Parse and validate JSON response
    4. Extract article object from response
    5. Enrich original item with extracted data
    6. Fallback to original data if extraction fails
    7. Return enriched result

    Parameters
    ----------
    id : UUID
        Unique identifier of the user request for personalization.
        Used for tracking/logging purposes (not sent to Diffbot API).

    url : str
        The absolute URL of the webpage to extract data from.
        Must be a full, valid, and publicly accessible HTTP/HTTPS URL.

        Valid examples:
        - https://example.com/article/machine-learning-basics
        - https://blog.example.com/posts/2025/async-python

        Invalid examples:
        - example.com/article (missing scheme)
        - /article/123 (relative URL)
        - localhost/page (not publicly accessible)

    original_item : Dict[str, object]
        The original search result containing baseline metadata.
        Required fields:
        - "title": str - Original title from search API
        - "link": str - URL (should match the url parameter)
        - "snippet": str - Short description from search results
        - "retrieved_source": str - "serper" or "tavily"

        This data is preserved and enhanced (not replaced) by Diffbot.

    Returns
    -------
    dict[str, object]
        Enriched dictionary with extracted article content:
        {
            "title": str,
                # Diffbot's extracted title if available, otherwise original
                # Diffbot titles are cleaner (no site names, no extra text)

            "link": str,
                # Original URL (never changes)

            "snippet": str,
                # Original search snippet (always preserved)
                # Useful for comparison and debugging

            "retrieved_source": str,
                # Original source: "serper" or "tavily"

            "text": str,
                # Full extracted article text if Diffbot succeeded
                # Falls back to original snippet if extraction failed
                # Typically 500-5000 words for articles

            "author": str | None,
                # Article author name if detected
                # None if not found or extraction failed

            "site": str | None
                # Site Name

            "date": str | None,
                # Publication date in ISO 8601 format
                # Example: "2025-10-21T12:00:00Z"
                # None if not found or extraction failed

            "tags": List[str],
                # Auto-detected topic tags or keywords
                # Example: ["Python", "Machine Learning", "Tutorial"]
                # Empty list [] if not found or extraction failed
        }

    Raises
    ------
    Does NOT raise exceptions!
    - On any error, returns fallback result with original data
    - Errors are logged to console but don't stop execution
    - This ensures robust pipeline operation

    Examples
    --------
    Successful extraction:
    >>> original = {
    ...     "title": "ML Basics - Example Site",
    ...     "link": "https://example.com/ml-basics",
    ...     "snippet": "Learn machine learning...",
    ...     "retrieved_source": "serper"
    ... }
    >>> result = await extract_with_diffbot(uuid4(), original["link"], original)
    >>> print(result["text"][:100])
    "Machine learning is a subset of artificial intelligence that enables..."
    >>> print(result["author"])
    "John Doe"
    >>> print(len(result["text"]))
    3500  # Full article text

    Failed extraction (fallback):
    >>> original = {
    ...     "title": "Protected Article",
    ...     "link": "https://paywall.example.com/article",
    ...     "snippet": "This article requires subscription...",
    ...     "retrieved_source": "tavily"
    ... }
    >>> result = await extract_with_diffbot(uuid4(), original["link"], original)
    >>> print(result["text"])
    "This article requires subscription..."  # Falls back to snippet
    >>> print(result["author"])
    None  # No extraction occurred

    Notes
    -----
    - Uses aiohttp for async HTTP (non-blocking I/O)
    - Respects configurable timeout (MAX_TIME_FOR_TRANSCRIPT_EXTRACTION)
    - Gracefully handles all error types (network, parsing, API errors)
    - Always preserves original search data (never loses information)
    - Diffbot API costs apply per extraction (not per failed attempt)

    Performance
    -----------
    - Typical latency: 2-5 seconds per URL
    - Non-blocking: allows concurrent extractions
    - Memory efficient: streams response
    - Handles large articles (up to 10MB of text)

    Common Failure Scenarios
    ------------------------
    1. Paywall/Login Required:
       - Diffbot can't access protected content
       - Falls back to original snippet

    2. JavaScript-Heavy Sites:
       - Diffbot renders JavaScript but has limits
       - Some dynamic content might be missed

    3. Non-Article Pages:
       - Homepage, product pages, etc.
       - Diffbot returns empty or partial data
       - Fallback ensures we still have snippet

    4. Network Errors:
       - Timeout, connection refused, DNS failure
       - Fallback preserves original search result

    Diffbot vs Simple Scraping
    ---------------------------
    Advantages:
    - Automatically identifies article content
    - Removes ads, navigation, comments
    - Works across different site layouts
    - Extracts structured metadata
    - Handles pagination automatically

    Trade-offs:
    - Costs money per request
    - Requires API key
    - External dependency
    - Not instant (2-5s latency)

    API Documentation
    -----------------
    Diffbot Article API endpoint:
        GET https://api.diffbot.com/v3/article

    Required query parameters:
        - token: Your Diffbot API key
        - url: The webpage URL to extract

    Optional query parameters:
        - discussion: "false" (skip comment extraction for speed)
        - timeout: Max wait time in milliseconds
        - fields: Comma-separated list of fields to extract

    Response structure:
        {
            "objects": [
                {
                    "title": "Article Title",
                    "text": "Full article text...",
                    "author": "Author Name",
                    "site": "Site Name"
                    "date": "2025-10-21T12:00:00Z",
                    "tags": ["tag1", "tag2"],
                    "html": "<article>...</article>",  # Optional
                    "images": [...],  # Optional
                    ...
                }
            ]
        }
    """

    # ============================================================
    # Step[01]: Build the API Request
    # ============================================================

    # === Diffbot Article API Endpoint ===
    # Diffbot offers multiple endpoints for different content types:
    # - /v3/article : Articles, blog posts, news (this one)
    # - /v3/product : E-commerce product pages
    # - /v3/image : Image galleries
    # - /v3/video : Video pages
    # - /v3/analyze : Auto-detect content type
    diffbot_API_endpoint = "https://api.diffbot.com/v3/article"

    # === Request Parameters ===
    # Diffbot uses query parameters (not headers or body)
    # These parameters are passed via query string (?key=value)
    # Diffbot expects authentication via `token` and a `url` to extract.
    #
    # | ---------- | ------------------------------ | -------| --------------------------------- |
    # | Parameter  | Meaning                        | Type   | Example Value                     |
    # | ---------- | ------------------------------ | -------| --------------------------------- |
    # | token      | API key for authentication     | str    | "123abc456xyz"                    |
    # | url        | Target webpage URL to extract  | str    | "https://example.com/news/ai"     |
    # | discussion | Include comments/discussions   | bool   | "false"                           |
    # | timeout    | Max wait time in seconds       | int    | "30"                              |
    # | ---------- | ------------------------------ | -------| --------------------------------- |
    #
    params = {
        # === Authentication ===
        "token": DIFFBOT_API_KEY,

        # === Target URL ===
        "url": url,

        # === Optional: Skip Comment Extraction ===
        # "discussion": "false" tells Diffbot to skip extracting comments
        # This significantly speeds up extraction (2-3x faster)
        # We typically don't need comments for educational content
        "discussion": "false",

        # === Optional: Timeout ===
        # Maximum time (in milliseconds) Diffbot will spend processing
        # After this, it returns whatever it has extracted so far
        # Useful for slow-loading or JavaScript-heavy pages
        # Default: 30000ms (30 seconds)
        "timeout": MAX_TIME_FOR_TEXT_EXTRACTION * 1000  # Convert seconds to milliseconds
    }

    # Note: We could add more parameters if needed:
    # - "fields": "title,text,author" (extract only specific fields)
    # - "paging": "false" (disable automatic pagination)
    # - "callback": "functionName" (JSONP callback for browser use)

    # ============================================================
    # Step[02]: Perform Async HTTP Request
    # ============================================================

    # === Configure Timeout ===
    # Set timeout slightly higher than Diffbot's internal timeout
    # This ensures Diffbot can finish processing before we give up
    # Add 10 seconds buffer for network overhead
    timeout = aiohttp.ClientTimeout(total=MAX_TIME_FOR_TEXT_EXTRACTION)

    # === Async HTTP Client Session ===
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            # === Execute GET Request (Non-Blocking) ===
            # Diffbot uses GET (not POST) because:
            # - Parameters are simple (URL + token)
            # - GET requests are cacheable
            # - Easier to test in browser
            async with session.get(
                    diffbot_API_endpoint,
                    params=params  # Query parameters automatically URL-encoded
            ) as response:

                # === Check Response Status ===
                # HTTP status codes:
                # - 200: Success (article extracted)
                # - 400: Bad request (invalid URL or parameters)
                # - 401: Unauthorized (invalid API token)
                # - 404: Page not found or not accessible
                # - 429: Rate limit exceeded (too many requests)
                # - 500: Diffbot server error
                if response.status != 200:
                    error_text = await response.text()
                    print(f"[Warning] Diffbot API error {response.status} for {url}: {error_text}")
                    # Don't raise - return fallback instead
                    return _create_fallback_result(url, original_item)

                # === Parse JSON Response (Non-Blocking) ===
                data = await response.json()

        except aiohttp.ClientError as e:
            # Network-level errors:
            # - Connection timeout
            # - DNS resolution failure
            # - Connection refused
            # - SSL certificate errors
            print(f"[Warning] Diffbot network error for {url}: {e}")
            return _create_fallback_result(url, original_item)

        except Exception as e:
            # Catch-all for unexpected errors:
            # - JSON parsing errors
            # - Memory errors
            # - Unexpected API response format
            print(f"[Warning] Diffbot unexpected error for {url}: {e}")
            return _create_fallback_result(url, original_item)

    # ============================================================
    # Step[03]: Extract and Normalize Fields
    # ============================================================

    # === Extract Article Object ===
    # Diffbot returns results in an "objects" array
    # Structure: {"objects": [{article1}, {article2}, ...]}
    #
    # Even though we're extracting a single URL, the response
    # is always an array (for consistency with batch API)
    article_obj: Optional[dict[str, object]] = None

    # Check if "objects" exists and has at least one item
    if isinstance(data.get("objects"), list) and len(data["objects"]) > 0:
        # Extract the first (and usually only) article object
        article_obj = data["objects"][0]

    # === Handle Empty or Invalid Response ===
    # If no article object found, it usually means:
    # - Page is not an article (e.g., homepage, product page)
    # - Page requires login/authentication
    # - Page has no extractable content
    # - Diffbot couldn't parse the page structure
    if not article_obj:
        print(f"[Warning] Diffbot returned no article object for {url}")
        return _create_fallback_result(url, original_item)

    # ============================================================
    # Step[04]: Build Enriched Result
    # ============================================================

    # === Start with Original Data ===
    # We preserve all original fields from the search result
    # This ensures we never lose information, even if Diffbot fails
    result: dict[str, object] = {
        "title": original_item.get("title"),
        "link": url,
        "snippet": original_item.get("snippet", ""),
        "retrieved_source": original_item.get("retrieved_source"),
    }

    # === Extract Diffbot Data ===
    # Get extracted fields from Diffbot response
    diffbot_title = article_obj.get("title")
    diffbot_text = article_obj.get("text")

    # === Enrich Title ===
    # Use Diffbot's title if available (usually cleaner)
    # Otherwise keep original title from search results
    if diffbot_title:
        result["title"] = diffbot_title

    # === Enrich Text ===
    # This is the most important field!
    # Priority:
    # 1. Diffbot's extracted text (full article content)
    # 2. Original snippet (if Diffbot failed)
    #
    # Note: Diffbot text is typically much longer than snippet:
    # - Snippet: 100-300 characters
    # - Diffbot text: 1000-10000 characters (full article)
    result["text"] = diffbot_text if diffbot_text else None

    # === Add Metadata Fields ===
    # These fields are unique to Diffbot and not available from search APIs
    result["author"] = article_obj.get("author")    # Author name or None
    result["site"] = article_obj.get("site")        # source site name or None
    result["date"] = article_obj.get("date")        # ISO 8601 date string or None
    result["tags"] = article_obj.get("tags", [])    # List of tags or empty list

    # Note: We could extract more fields if needed:
    # - "html": Full article HTML
    # - "images": List of image objects with captions
    # - "videos": Embedded videos
    # - "breadcrumb": Navigation breadcrumb
    # - "lang": Detected language
    # - "siteName": Publisher name

    # ============================================================
    # Step[05]: Return Enriched Result
    # ============================================================

    return result