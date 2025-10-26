"""
======================================================
EDUCATIONAL RETRIEVAL PIPELINE (Simple & Clean)
======================================================
This script:
    1- Uses ( Serper API ) and ( Tavily API ) to discover text & video sources.
    2- Uses Diffbot for extract all data from any text-based url
    3- Uses YouTube Data API to get video metadata and captions.
    4- Uses AssemblyAI API for transcribing videos, if no captions available from YouTube metadata.
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

import time
from uuid import UUID

from APP.Services.Search_Serper import discover_with_serper
from APP.Services.Search_Tavily import discover_with_tavily
from APP.Services.Extract_Diffbot import extract_with_diffbot
from APP.Services.VideosMetadata_YouTubeAPI_AssemblyAIAPI import process_videos

# ============================================================
# Helper Function
# ============================================================

def combine_results(tavily_results: list[dict[str,object]], serper_results: list[dict[str,object]]) -> list[dict[str,object]]:
    """
    Combine Tavily and Serper discovery results into a single, deduplicated list.

    Parameters
    ----------
    tavily_results : list[dict[str,object]]
        List of Tavily search results. Each dict must contain keys:
        { "title": str, "link": str, "text": str }

    serper_results : list[dict[str,object]]
        List of Serper search results with the same structure.

    Returns
    -------
    combined_results : list[dict[str,object]]
        Unified, deduplicated list (Tavily first, Serper next).
    """

    seen_links = set()
    combined_results: list[dict[str,object]] = []

    # --- Add Tavily results first ---
    for item in tavily_results:
        link = item.get("link", "").strip().lower()
        if link and link not in seen_links:
            combined_results.append(item)
            seen_links.add(link)

    # --- Add Serper results that aren’t duplicates ---
    for item in serper_results:
        link = item.get("link", "").strip().lower()
        if link and link not in seen_links:
            combined_results.append(item)
            seen_links.add(link)

    return combined_results

# ============================================================
# Main Function
# ============================================================

def searching_Serper_Tavily_YouTube_AssemblyAI(id: UUID, query: str, search_type: str = "search") -> list:
    # ================================================================
    # Step[01]: Merging results from (serper) and (tavily), without any duplication
    # ================================================================
    tavily_results = discover_with_tavily(id,query,search_type)
    serper_results = discover_with_serper(id,query,search_type)
    final_results = combine_results(tavily_results,serper_results)

    final_results_with_metadata: list[dict[str, object]] = []

    # ================================================================
    # Step[02]: Extracting metadata by (Diffbot API) only when url is text-based
    # ================================================================
    if search_type == "search":
        for item in final_results:

            title = item["title"]
            link = item["link"]
            snippet = item["snippet"]
            retrieved_source = item["retrieved_source"]

            augmented_result = extract_with_diffbot(id, link)

            augmented_result ["title"] = title
            augmented_result ["link"] = link
            augmented_result["snippet"] = snippet
            augmented_result["retrieved_source"] = retrieved_source

            final_results_with_metadata.append(augmented_result)

            time.sleep(5)

    # ================================================================
    # Step[03]: Extracting metadata by (YouTube API) & (AssemblyAI API) only when url is youtube Video-based
    # ================================================================
    if search_type == "videos":
        for item in final_results:

            title = item["title"]
            link = item["link"]
            snippet = item["snippet"]
            retrieved_source = item["retrieved_source"]

            augmented_result = process_videos(id, link)

            augmented_result ["title"] = title
            augmented_result ["link"] = link
            augmented_result["snippet"] = snippet
            augmented_result["retrieved_source"] = retrieved_source

            final_results_with_metadata.append(augmented_result)

            time.sleep(5)

    # ================================================================
    # Step[04]: Return Results: list[...]
    # ================================================================
    return final_results_with_metadata