"""
======================================================
EDUCATIONAL RETRIEVAL PIPELINE (Simple & Clean)
======================================================
This script:
    1- Uses ( Serper API ) and ( Tavily API ) to discover text & video sources.
    2- Uses Diffbot for extract all data from any text-based url
    3- Uses YouTube Data API to get video metadata and captions.
    4- Uses AssemblyAI API for transcribing videos, if no captions available from YouTube metadata.

Performance improvements:
    - Serper + Tavily run simultaneously (2x faster discovery)
    - Multiple URLs processed concurrently (n-way parallelism)
    - Proper async rate limiting (no wasteful time.sleep)
    - Non-blocking I/O throughout the pipeline
======================================================
if texts:
    old shape:
        {
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "retrieved_source": "serper",   or  "tavily",
        }

    desired shape:
        {
            # "title": item.get("title", ""),     # overwrite by diffbot iff diffbot retrieved
            # "link": item.get("link", ""),       # overwrite by diffbot iff diffbot retrieved
            "snippet": ".........."
            "retrieved_source": "serper",   or  "tavily",

            "title": (str) Clean article title,
            "link": (str) The original source link
            "text": (str) Full cleaned article body text,
            "author": (str) Author name if available,
            "date": (str) Published date if detected,
            "tags": (list[str]) Any auto-detected tags or keywords,
        }

if videos:
    old shape:
        {
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "retrieved_source": "serper",   or  "tavily",
        }

    desired shape:
        {
            # "title": item.get("title", ""),     # overwrite by diffbot iff diffbot retrieved
            # "link": item.get("link", ""),       # overwrite by diffbot iff diffbot retrieved
            "snippet": ".........."
            "retrieved_source": "serper",   or  "tavily",

            "title": (str) Clean article title,
            "link": (str) The original source link
            "video_id": "7IgVGSaQPaw",

            "description": (str) Full cleaned article body text,

            "channel": "TechWorld with Nana",
            "duration": "PT46M22S",
            "has_captions": true,

            "text": null,

            "transcript_source": "YouTube Captions",
            "summary": null,
            "chapters": [],
            "error": null
        }
======================================================
"""

# ================================================================
# IMPORT REQUIRED MODULES
# ================================================================

import asyncio
from uuid import UUID

from APP.Services.async_search_serper import discover_with_serper
from APP.Services.async_search_tavily import discover_with_tavily
from APP.Services.async_extract_diffbot import extract_with_diffbot
from APP.Services.async_videos_metadata import process_videos


# ============================================================
# Helper Function
# ============================================================

def combine_results(
        tavily_results: list[dict[str, object]],
        serper_results: list[dict[str, object]]
) -> list[dict[str, object]]:
    """
    Combine Tavily and Serper discovery results into a single, deduplicated list.

    Parameters
    ----------
    tavily_results : List[Dict[str, object]]
        List of Tavily search results. Each dict must contain keys:
        { "title": str, "link": str, "snippet": str }

    serper_results : List[Dict[str, object]]
        List of Serper search results with the same structure.

    Returns
    -------
    combined_results : List[Dict[str, object]]
        Unified, deduplicated list (Tavily first, Serper next).
    """
    seen_links = set()
    combined_results: List[Dict[str, object]] = []

    # --- Add Tavily results first (typically higher quality) ---
    for item in tavily_results:
        link = item.get("link", "").strip().lower()
        if link and link not in seen_links:
            combined_results.append(item)
            seen_links.add(link)

    # --- Add Serper results that aren't duplicates ---
    for item in serper_results:
        link = item.get("link", "").strip().lower()
        if link and link not in seen_links:
            combined_results.append(item)
            seen_links.add(link)

    return combined_results


# ============================================================
# Main Async Function
# ============================================================

async def searching_Serper_Tavily_YouTube_AssemblyAI(
        id: UUID,
        query: str,
        search_type: str = "search"
) -> list[dict[str, object]]:
    """
    Asynchronous pipeline for discovering and enriching educational content.

    Parameters
    ----------
    id : UUID
        Unique identifier of the user request for personalization.
    query : str
        User's search query.
    search_type : str
        Either "search" (text content) or "videos" (YouTube videos).

    Returns
    -------
    list[dict[str, object]]
        Enriched results with full metadata and extracted content.
    """

    # ================================================================
    # Step[01]: CONCURRENT discovery from Serper and Tavily
    # ================================================================
    # Run both API calls simultaneously using asyncio.gather
    # This cuts discovery time in half compared to sequential execution

    tavily_task = discover_with_tavily(id, query, search_type)
    serper_task = discover_with_serper(id, query, search_type)

    # Wait for both to complete (whichever finishes first doesn't block the other)
    tavily_results, serper_results = await asyncio.gather(
        tavily_task,
        serper_task,
        return_exceptions=True  # Don't let one failure kill the other
    )

    # Handle exceptions gracefully
    if isinstance(tavily_results, Exception):
        print(f"[Warning] Tavily API failed: {tavily_results}")
        tavily_results = []
    if isinstance(serper_results, Exception):
        print(f"[Warning] Serper API failed: {serper_results}")
        serper_results = []

    # Merge and deduplicate results
    final_results = combine_results(tavily_results, serper_results)

    if not final_results:
        print(f"[Warning] No results found for query: {query}")
        return []

    # ================================================================
    # Step[02]: PARALLEL metadata extraction based on search type
    # ================================================================

    if search_type == "search":
        # --- Text-based URLs: Extract with Diffbot in parallel ---
        tasks = [
            extract_with_diffbot(id, item["link"], item)
            for item in final_results
        ]

    elif search_type == "videos":
        # --- Video URLs: Process with YouTube + AssemblyAI in parallel ---
        tasks = [
            process_videos(id, item["link"], item)
            for item in final_results
        ]
    else:
        raise ValueError(f"Invalid search_type: {search_type}. Must be 'search' or 'videos'")

    # Execute all extraction tasks concurrently
    # This is the biggest performance gain: processing n URLs simultaneously
    final_results_with_metadata = await asyncio.gather(
        *tasks,
        return_exceptions=True  # Continue even if some items fail
    )

    # ================================================================
    # Step[03]: Filter out failed items and return successful results
    # ================================================================

    # Remove any results that raised exceptions
    successful_results = [
        result for result in final_results_with_metadata
        if not isinstance(result, Exception)
    ]

    # Log failed items
    failed_count = len(final_results_with_metadata) - len(successful_results)
    if failed_count > 0:
        print(f"[Warning] {failed_count} items failed during metadata extraction")

    print(f"[Success] Retrieved {len(successful_results)} enriched results")
    return successful_results
