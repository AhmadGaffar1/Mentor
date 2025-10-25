"""
======================================================
CONTENT EXTRACTION USING DIFFBOT

Argument:
    {
        "title": item.get("title", ""),
        "link": item.get("link", ""),
        "text": item.get("snippet", ""),
        "retrieved_source": "serper",   or  "tavily",
    }

Return:
    {
        # "title": item.get("title", ""),     # overwrite by diffbot iff diffbot retrieved
        # "link": item.get("link", ""),       # overwrite by diffbot iff diffbot retrieved
        # "text": item.get("snippet", ""),    # overwrite by diffbot iff diffbot retrieved
        "retrieved_source": "serper",   or  "tavily",

        "title": (str) Clean article title,
        "link": (str) The original source link
        "text": (str) Full cleaned article body text,
        "author": (str) Author name if available,
        "date": (str) Published date if detected,
        "tags": (list[str]) Any auto-detected tags or keywords,
    }
======================================================
"""

# ================================================================
# IMport Required Modules
# ================================================================

import requests
from uuid import UUID
from APP.Configration import DIFFBOT_API_KEY, MAX_TIME_FOR_TRANSCRIPT_EXTRACTION

# ============================================================
# Main Extraction Function
# ============================================================

def extract_with_diffbot(id: UUID, url: str) -> dict[str, object]:
    """
    Extract high-quality structured content from a webpage using Diffbot's Article API.

    Arguments:
    ----------
    - id: (UUID)
        Unique identifier of the extraction session or user request.
        Used here mainly for tracking/logging context.
    - url: (str)
        The absolute URL of the webpage you want to extract data from.
        Must be a full, valid, and reachable HTTP/HTTPS URL.

    Returns:
    --------
    dict [ str , any ]:
        A structured dictionary containing key extracted fields:
        {
            "title": (str) Clean article title,
            "text": (str) Full cleaned article body text,
            "author": (str) Author name if available,
            "date": (str) Published date if detected,
            "tags": (list[str]) Any auto-detected tags or keywords,
            "link": (str) The original source link
        }
    """

    # ============================================================
    # Step[01]: Build the API Request
    # ============================================================

    # === Diffbot Article API Endpoint ===
    # The "analyze" endpoint auto-detects the content type (article, image, video, etc.),
    # but here we specifically use "article" for text-focused extraction quality.
    diffbot_API_endpoint: str = "https://api.diffbot.com/v3/article"

    # === Request Parameters ===
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
        "token": DIFFBOT_API_KEY,                       # (str) Auth token stored in configuration
        "url": url,                                     # (str) Target webpage to extract
        "discussion": "false",                          # (str) Disable comment extraction (optional)
        "timeout": MAX_TIME_FOR_TRANSCRIPT_EXTRACTION   # (int) Wait up to 60s for slow pages
    }

    # === Headers ===
    # Diffbot doesn’t require custom headers for this endpoint,
    # but we explicitly set Content-Type for clarity and forward-compatibility.
    headers = {"Content-Type": "application/json"}

    # ============================================================
    # Step[02]: Perform the HTTP Request
    # ============================================================

    # Use requests.get() because Diffbot expects GET, not POST.
    # The query parameters (token, url, etc.) are appended automatically to the URL.
    response = requests.get(diffbot_API_endpoint, headers=headers, params=params)

    # === Validate Response ===
    # If HTTP status code != 200, Diffbot failed (invalid token, bad URL, etc.)
    if response.status_code != 200:
        raise Exception(f"Diffbot API error {response.status_code}: {response.text}")

    # ============================================================
    # Step[03]: Parse and Process Response
    # ============================================================

    # Convert JSON string → Python dictionary
    # Example raw response shape:
    # {
    #   "objects": [
    #       {
    #           "title": "AI Revolution in 2025",
    #           "text": "Artificial intelligence is transforming...",
    #           "author": "John Doe",
    #           "date": "2025-10-21T12:00:00Z",
    #           "tags": ["AI", "Technology", "Future"]
    #       },
    #
    #       {
    #           "title": "AI Revolution in 2025",
    #           "text": "Artificial intelligence is transforming...",
    #           "author": "John Doe",
    #           "date": "2025-10-21T12:00:00Z",
    #           "tags": ["AI", "Technology", "Future"]
    #       },
    #
    #       ...,
    #   ]
    # }
    #
    data: dict = response.json()

    # ============================================================
    # Step[04]: Extract and Normalize Fields
    # ============================================================

    # === Extract Results ===
    # Extract the first (and usually only) object in the "objects" list.
    # Diffbot returns an array even for single-page results.
    # ( article_obj: dict[str, object] | None ): ( article_obj ) static declared as: ( dict[str, object] ) or ( None )
    # ( = None ): ( article_obj ) initial type as ( None )
    article_obj: dict[str, object] | None = None
    # isinstance(x, list): checks if ( x ) is a ( list )
    # isinstance(x, (list, tuple)): checks if ( x ) is a ( list ) or ( tuple )
    if isinstance(data.get("objects"), list) and len(data["objects"]) > 0:
        article_obj = data["objects"][0]

    # === If no valid article object found, return fallback minimal structure ===
    if not article_obj:
        article_obj = {
            "title": None,
            "link": url,
            "text": None,
            "author": None,
            "date": None,
            "tags": [],
        }

    # === Normalized Results ===
    # Python dictionary (type: dict[str, Any])
    # Stores all extracted data in a normalized schema for uniform downstream processing.

    # check if there are a text retrieved from Diffbot will use it, regardless ( serper | tavily ) retrieved or not.
    # iff Diffbot not retrieved text, use the source retrieved from ( serper | tavily ).

    result: dict[str, object] = {
        # Extracts article title string (if not found, defaults to None)
        "title": article_obj.get("title"),

        # Always preserve original link for traceability
        "link": url,

        # Full textual content of the article (cleaned of HTML and noise)
        "text": article_obj.get("text"),

        # Primary author name if Diffbot detected one
        "author": article_obj.get("author"),

        # Published date (ISO 8601 format if available)
        "date": article_obj.get("date"),

        # Auto-classified topic tags or keywords
        "tags": article_obj.get("tags", []),
    }

    # ============================================================
    # Step[05]: Return Results: dict {...}
    # ============================================================

    return result