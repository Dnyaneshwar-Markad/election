# import streamlit as st
# import pandas as pd
# from api_client import APIClient
# import time 
# import os


# def get_api_client():
#     base = os.getenv("API_URL", "http://127.0.0.1:8000")
#     token = st.session_state.get("access_token") or st.session_state.get("token")
#     return APIClient(base_url=base, token=token)


# def load_voter_data(section_no=None, force_reload=False):
#     """
#     Load voter data with intelligent caching
#     - Caches for 5 minutes
#     - Per-user cache
#     - Pagination support
#     """
#     cache_key = f"voter_data_{section_no}"
#     cache_time_key = f"{cache_key}_time"
    
#     # Check if cached data exists and is fresh (5 minutes)
#     current_time = time.time()
#     cached_time = st.session_state.get(cache_time_key, 0)
    
#     if (not force_reload and 
#         cache_key in st.session_state and 
#         current_time - cached_time < 300):  # 5 minutes
#         return st.session_state[cache_key]
    
#     # Load fresh data
#     try:
#         api = get_api_client()
#         all_rows = []
#         limit = 5000  # Reduced from 3000
#         offset = 0
        
#         # ✅ PAGINATION WITH TIMEOUT
#         while True:
#             try:
#                 res = api.get_voters(limit=limit, offset=offset)
#                 rows = res.get("rows", [])
                
#                 if not rows:
#                     break
                
#                 all_rows.extend(rows)
                
#                 # ✅ BREAK IF LESS THAN LIMIT (no more data)
#                 if len(rows) < limit:
#                     break
                
#                 offset += limit
                
#             except Exception as e:
#                 print(f"Error loading voters at offset {offset}: {e}")
#                 break
        
#         df = pd.DataFrame(all_rows)
        
#         # Cache the result
#         st.session_state[cache_key] = df
#         st.session_state[cache_time_key] = current_time
        
#         return df
    
#     except Exception as e:
#         print(f"Error loading voter data: {e}")
#         # Return empty DataFrame on error
#         return pd.DataFrame()

# # ==================== OPTIMIZED: Load Survey Data ====================
# def load_survey_data(user_id=None, force_reload=False):
#     """
#     Load survey data with intelligent caching
#     - Caches for 2 minutes
#     - Per-user cache
#     """
#     cache_key = f"survey_data_{user_id}"
#     cache_time_key = f"{cache_key}_time"
    
#     # Check cache (2 minutes for surveys as they update more frequently)
#     current_time = time.time()
#     cached_time = st.session_state.get(cache_time_key, 0)
    
#     if (not force_reload and 
#         cache_key in st.session_state and 
#         current_time - cached_time < 120):  # 2 minutes
#         return st.session_state[cache_key]
    
#     # Load fresh data
#     try:
#         api = get_api_client()
#         all_rows = []
#         limit = 500  # Reduced from 1000
#         offset = 0
        
#         while True:
#             try:
#                 res = api.get_surveys(limit=limit, offset=offset)
#                 rows = res.get("rows", [])
                
#                 if not rows:
#                     break
                
#                 all_rows.extend(rows)
                
#                 if len(rows) < limit:
#                     break
                
#                 offset += limit
                
#             except Exception as e:
#                 print(f"Error loading surveys at offset {offset}: {e}")
#                 break
        
#         df = pd.DataFrame(all_rows)
        
#         # Cache the result
#         st.session_state[cache_key] = df
#         st.session_state[cache_time_key] = current_time
        
#         return df
    
#     except Exception as e:
#         print(f"Error loading survey data: {e}")
#         return pd.DataFrame()

# # ==================== OPTIMIZED: Load Filters ====================
# def load_filters(section_no=None, force_reload=False):
#     """
#     Load filters with caching (10 minutes - filters rarely change)
#     """
#     cache_key = f"filters_data_{section_no}"
#     cache_time_key = f"{cache_key}_time"
    
#     current_time = time.time()
#     cached_time = st.session_state.get(cache_time_key, 0)
    
#     if (not force_reload and 
#         cache_key in st.session_state and 
#         current_time - cached_time < 600):  # 10 minutes
#         return st.session_state[cache_key]
    
#     try:
#         api = get_api_client()
#         filters = api.get_voter_filters()
        
#         # Cache the result
#         st.session_state[cache_key] = filters
#         st.session_state[cache_time_key] = current_time
        
#         return filters
    
#     except Exception as e:
#         print(f"Error loading filters: {e}")
#         return {}


# # ==================== âœ… CRITICAL FIX: LAZY LOADING ====================
# def load_voter_summary(section_no=None, force_reload=False):
#     """
#     âœ… Load ONLY summary stats, not full data
#     This should be INSTANT (< 100ms)
#     """
#     cache_key = f"summary_{section_no}"
#     cache_time_key = f"{cache_key}_time"
    
#     current_time = time.time()
#     cached_time = st.session_state.get(cache_time_key, 0)
    
#     # Cache for 5 minutes
#     if (not force_reload and 
#         cache_key in st.session_state and 
#         current_time - cached_time < 300):
#         return st.session_state[cache_key]
    
#     try:
#         api = get_api_client()
#         summary = api.get("/voters/summary")  # New optimized endpoint
        
#         st.session_state[cache_key] = summary
#         st.session_state[cache_time_key] = current_time
        
#         return summary
#     except Exception as e:
#         print(f"Error loading summary: {e}")
#         return {
#             "total": 0,
#             "visited": 0,
#             "not_visited": 0,
#             "male": 0,
#             "female": 0
#         }
        
# # ==================== âœ… PAGINATED LOADING ====================
# def load_voters_page(page=0, page_size=100, search="", section_no=None):
#     """
#     âœ… Load ONE PAGE at a time
#     Never load all data
#     """
#     cache_key = f"voters_page_{page}_{page_size}_{search}_{section_no}"
#     cache_time_key = f"{cache_key}_time"
    
#     current_time = time.time()
#     cached_time = st.session_state.get(cache_time_key, 0)
    
#     # Cache pages for 2 minutes
#     if (cache_key in st.session_state and 
#         current_time - cached_time < 120):
#         return st.session_state[cache_key]
    
#     try:
#         api = get_api_client()
#         offset = page * page_size
        
#         result = api.get("/voters", params={
#             "limit": page_size,
#             "offset": offset,
#             "search": search
#         })
        
#         df = pd.DataFrame(result.get("rows", []))
#         total = result.get("total", 0)
        
#         response = {
#             "data": df,
#             "total": total,
#             "page": page,
#             "page_size": page_size
#         }
        
#         st.session_state[cache_key] = response
#         st.session_state[cache_time_key] = current_time
        
#         return response
        
#     except Exception as e:
#         print(f"Error loading page: {e}")
#         return {
#             "data": pd.DataFrame(),
#             "total": 0,
#             "page": page,
#             "page_size": page_size
#         }

# # ==================== âœ… OPTIMIZED DASHBOARD DATA ====================
# def load_dashboard_data(section_no=None):
#     """
#     âœ… Load ONLY what dashboard needs
#     - Summary stats (aggregated)
#     - Top 10 addresses (aggregated)
#     - NO individual voter records
#     """
#     cache_key = f"dashboard_{section_no}"
#     cache_time_key = f"{cache_key}_time"
    
#     current_time = time.time()
#     cached_time = st.session_state.get(cache_time_key, 0)
    
#     if (cache_key in st.session_state and 
#         current_time - cached_time < 300):
#         return st.session_state[cache_key]
    
#     try:
#         api = get_api_client()
        
#         # Get aggregated summary
#         summary = api.get("/voters/summary")
        
#         # Get top addresses (aggregated on backend)
#         top_addresses = api.get("/voters/top-addresses", params={"limit": 10})
        
#         data = {
#             "summary": summary,
#             "top_addresses": top_addresses
#         }
        
#         st.session_state[cache_key] = data
#         st.session_state[cache_time_key] = current_time
        
#         return data
        
#     except Exception as e:
#         print(f"Error loading dashboard: {e}")
#         return {
#             "summary": {
#                 "total": 0,
#                 "visited": 0,
#                 "not_visited": 0,
#                 "male": 0,
#                 "female": 0
#             },
#             "top_addresses": []
#         }

# # ==================== âœ… SURVEYS WITH LIMIT ====================
# def load_surveys_page(page=0, page_size=50, user_id=None):
    
#     """
#     âœ… Paginated survey loading
#     """
#     cache_key = f"surveys_page_{page}_{page_size}_{user_id}"
#     cache_time_key = f"{cache_key}_time"
    
#     current_time = time.time()
#     cached_time = st.session_state.get(cache_time_key, 0)
    
#     if (cache_key in st.session_state and 
#         current_time - cached_time < 120):
#         return st.session_state[cache_key]
    
#     try:
#         api = get_api_client()
#         offset = page * page_size
        
#         result = api.get("/surveys", params={
#             "limit": page_size,
#             "offset": offset
#         })
        
#         response = {
#             "data": pd.DataFrame(result.get("rows", [])),
#             "total": result.get("total", 0)
#         }
        
#         st.session_state[cache_key] = response
#         st.session_state[cache_time_key] = current_time
        
#         return response
        
#     except Exception as e:
#         print(f"Error loading surveys: {e}")
#         return {
#             "data": pd.DataFrame(),
#             "total": 0
#         }

# # ==================== CLEAR CACHE ====================
# def clear_all_cache():
#     """Clear all cached data"""
#     keys_to_clear = [
#         k for k in st.session_state.keys() 
#         if any(k.startswith(prefix) for prefix in 
#             ["voters_page_", "summary_", "dashboard_", "surveys_page_"])
#     ]
    
#     for key in keys_to_clear:
#         del st.session_state[key]
# # ==================== CLEAR FUNCTIONS ====================
# def clear_voter_data():
#     """Clear only voter data cache"""
#     keys_to_clear = [k for k in st.session_state.keys() if k.startswith("voter_data_")]
#     for key in keys_to_clear:
#         del st.session_state[key]
#         time_key = f"{key}_time"
#         if time_key in st.session_state:
#             del st.session_state[time_key]

# def clear_survey_data():
#     """Clear only survey data cache"""
#     keys_to_clear = [k for k in st.session_state.keys() if k.startswith("survey_data_")]
#     for key in keys_to_clear:
#         del st.session_state[key]
#         time_key = f"{key}_time"
#         if time_key in st.session_state:
#             del st.session_state[time_key]

# def clear_all_data():
#     """Clear all cached data"""
#     keys_to_clear = [
#         k for k in st.session_state.keys() 
#         if any(k.startswith(prefix) for prefix in 
#             ["voter_data_", "survey_data_", "filters_data_", "summary_data_"])
#     ]
    
#     for key in keys_to_clear:
#         del st.session_state[key]

# # ==================== FORCE RELOAD FUNCTIONS ====================
# def force_reload_voters():
#     """Force reload voter data on next call"""
#     clear_voter_data()

# def force_reload_surveys():
#     """Force reload survey data on next call"""
#     clear_survey_data()

# def force_reload_all():
    # """Force reload all data on next call"""
    # clear_all_data()


# def force_reload_all():
    # """Force reload all data on next call"""
    # clear_all_data()
    
    
# optimized_data_loader.py
"""
✅ OPTIMIZED DATA LOADER
- Intelligent caching (per section, per user)
- Pagination support
- Minimal API calls
- Fast cache invalidation
"""

import streamlit as st
import pandas as pd
from api_client import APIClient
import time
import os
from typing import Optional, Dict, Tuple, Any

# ==================== API CLIENT ====================
def get_api_client() -> APIClient:
    """Get API client with current session token"""
    base = os.getenv("API_URL", "http://127.0.0.1:8000")
    token = st.session_state.get("access_token") or st.session_state.get("token")
    return APIClient(base_url=base, token=token)

# ==================== CACHE KEY GENERATORS ====================
def _get_cache_key(prefix: str, **kwargs) -> str:
    """Generate consistent cache key"""
    parts = [prefix]
    for key, value in sorted(kwargs.items()):
        if value is not None:
            parts.append(f"{key}_{value}")
    return "_".join(parts)

def _is_cache_valid(cache_key: str, ttl: int) -> bool:
    """Check if cache is still valid"""
    cache_time_key = f"{cache_key}_time"
    cached_time = st.session_state.get(cache_time_key, 0)
    return (time.time() - cached_time) < ttl

def _set_cache(cache_key: str, data: Any):
    """Store data in cache with timestamp"""
    cache_time_key = f"{cache_key}_time"
    st.session_state[cache_key] = data
    st.session_state[cache_time_key] = time.time()

def _get_cache(cache_key: str) -> Optional[Any]:
    """Retrieve data from cache"""
    return st.session_state.get(cache_key)

# ==================== OPTIMIZED DATA LOADERS ====================

def load_voter_summary(section_no: Optional[int] = None, force_reload: bool = False) -> Dict:
    """
    ✅ CRITICAL: Load ONLY summary statistics (aggregated)
    This should complete in < 200ms
    
    Returns:
        {
            "total": int,
            "visited": int,
            "not_visited": int,
            "sex_breakdown": {"M": int, "F": int},
            "address_chart": [{"Address": str, "Total": int, ...}]
        }
    """
    cache_key = _get_cache_key("summary", section_no=section_no)
    
    # Check cache (5 minutes TTL)
    if not force_reload and _is_cache_valid(cache_key, ttl=300):
        cached_data = _get_cache(cache_key)
        if cached_data is not None:
            return cached_data
    
    try:
        api = get_api_client()
        summary = api.get_voter_summary()
        
        # Ensure all expected keys exist
        result = {
            "total": summary.get("total", 0),
            "visited": summary.get("visited", 0),
            "not_visited": summary.get("not_visited", 0),
            "sex_breakdown": summary.get("sex_breakdown", {}),
            "address_chart": summary.get("address_chart", [])
        }
        
        _set_cache(cache_key, result)
        return result
        
    except Exception as e:
        print(f"❌ Error loading summary: {e}")
        # Return empty structure on error
        return {
            "total": 0,
            "visited": 0,
            "not_visited": 0,
            "sex_breakdown": {},
            "address_chart": []
        }

def load_voters_page(
    page: int = 0,
    page_size: int = 50,
    search: str = "",
    section_no: Optional[int] = None,
    force_reload: bool = False
) -> Tuple[pd.DataFrame, int]:
    """
    ✅ Load ONE PAGE of voters (paginated)
    Never load all data at once
    
    Args:
        page: Page number (0-indexed)
        page_size: Number of records per page
        search: Search query
        section_no: Section filter
        force_reload: Force cache refresh
    
    Returns:
        (DataFrame, total_count)
    """
    cache_key = _get_cache_key(
        "voters_page",
        page=page,
        size=page_size,
        search=search,
        section=section_no
    )
    
    # Check cache (2 minutes TTL for pages)
    if not force_reload and _is_cache_valid(cache_key, ttl=120):
        cached_data = _get_cache(cache_key)
        if cached_data is not None:
            return cached_data
    
    try:
        api = get_api_client()
        offset = page * page_size
        
        result = api.get_voters(
            limit=page_size,
            offset=offset,
            search=search
        )
        
        df = pd.DataFrame(result.get("rows", []))
        total = result.get("total", 0)
        
        # Cache the result
        cache_data = (df, total)
        _set_cache(cache_key, cache_data)
        
        return df, total
        
    except Exception as e:
        print(f"❌ Error loading voters page: {e}")
        return pd.DataFrame(), 0

def load_survey_summary(
    section_no: Optional[int] = None,
    force_reload: bool = False
) -> Dict:
    """
    ✅ Load survey summary (counts only, no full data)
    
    Returns:
        {
            "total_surveys": int,
            "estimated_voters": int
        }
    """
    cache_key = _get_cache_key("survey_summary", section_no=section_no)
    
    # Check cache (3 minutes TTL)
    if not force_reload and _is_cache_valid(cache_key, ttl=180):
        cached_data = _get_cache(cache_key)
        if cached_data is not None:
            return cached_data
    
    try:
        api = get_api_client()
        
        # Get total count first (fast)
        result = api.get_surveys(limit=1, offset=0)
        total_surveys = result.get("total", 0)
        
        # Get first batch for voter count calculation
        # Only load what's needed for summary
        result = api.get_surveys(limit=500, offset=0)
        df_surveys = pd.DataFrame(result.get("rows", []))
        
        estimated_voters = 0
        if not df_surveys.empty and "VotersCount" in df_surveys.columns:
            estimated_voters = int(df_surveys["VotersCount"].sum())
        
        result = {
            "total_surveys": total_surveys,
            "estimated_voters": estimated_voters
        }
        
        _set_cache(cache_key, result)
        return result
        
    except Exception as e:
        print(f"❌ Error loading survey summary: {e}")
        return {
            "total_surveys": 0,
            "estimated_voters": 0
        }

def load_surveys_page(
    page: int = 0,
    page_size: int = 50,
    user_id: Optional[int] = None,
    force_reload: bool = False
) -> Tuple[pd.DataFrame, int]:
    """
    ✅ Load ONE PAGE of surveys (paginated)
    
    Returns:
        (DataFrame, total_count)
    """
    cache_key = _get_cache_key(
        "surveys_page",
        page=page,
        size=page_size,
        user=user_id
    )
    
    # Check cache (2 minutes TTL)
    if not force_reload and _is_cache_valid(cache_key, ttl=120):
        cached_data = _get_cache(cache_key)
        if cached_data is not None:
            return cached_data
    
    try:
        api = get_api_client()
        offset = page * page_size
        
        result = api.get_surveys(
            limit=page_size,
            offset=offset
        )
        
        df = pd.DataFrame(result.get("rows", []))
        total = result.get("total", 0)
        
        cache_data = (df, total)
        _set_cache(cache_key, cache_data)
        
        return df, total
        
    except Exception as e:
        print(f"❌ Error loading surveys page: {e}")
        return pd.DataFrame(), 0

def load_filters(
    section_no: Optional[int] = None,
    force_reload: bool = False
) -> Dict:
    """
    ✅ Load filter options (addresses, parts, age range)
    These rarely change, so cache for 10 minutes
    
    Returns:
        {
            "address_list": [str],
            "part_list": [str],
            "min_age": int,
            "max_age": int
        }
    """
    cache_key = _get_cache_key("filters", section_no=section_no)
    
    # Check cache (10 minutes TTL)
    if not force_reload and _is_cache_valid(cache_key, ttl=600):
        cached_data = _get_cache(cache_key)
        if cached_data is not None:
            return cached_data
    
    try:
        api = get_api_client()
        filters = api.get_voter_filters()
        
        result = {
            "address_list": filters.get("address_list", []),
            "part_list": filters.get("part_list", []),
            "min_age": filters.get("min_age", 0),
            "max_age": filters.get("max_age", 100)
        }
        
        _set_cache(cache_key, result)
        return result
        
    except Exception as e:
        print(f"❌ Error loading filters: {e}")
        return {
            "address_list": [],
            "part_list": [],
            "min_age": 0,
            "max_age": 100
        }

# ==================== CACHE MANAGEMENT ====================

def clear_voter_cache():
    """Clear only voter-related caches"""
    keys_to_clear = [
        k for k in st.session_state.keys()
        if k.startswith("voters_page_") or k.startswith("summary_")
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    print(f"✅ Cleared {len(keys_to_clear)} voter cache entries")

def clear_survey_cache():
    """Clear only survey-related caches"""
    keys_to_clear = [
        k for k in st.session_state.keys()
        if k.startswith("surveys_page_") or k.startswith("survey_summary_")
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    print(f"✅ Cleared {len(keys_to_clear)} survey cache entries")

def clear_all_cache():
    """Clear all data caches"""
    keys_to_clear = [
        k for k in st.session_state.keys()
        if any(k.startswith(prefix) for prefix in [
            "voters_page_", "surveys_page_", "summary_", 
            "survey_summary_", "filters_"
        ])
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    print(f"✅ Cleared {len(keys_to_clear)} cache entries")

def force_reload_all():
    """Force reload all data on next access"""
    clear_all_cache()

# ==================== STATISTICS ====================

def get_cache_stats() -> Dict:
    """Get cache statistics for debugging"""
    cache_keys = [
        k for k in st.session_state.keys()
        if any(k.startswith(prefix) for prefix in [
            "voters_page_", "surveys_page_", "summary_", 
            "survey_summary_", "filters_"
        ])
    ]
    
    cache_sizes = {}
    for key in cache_keys:
        data = st.session_state.get(key)
        if isinstance(data, pd.DataFrame):
            cache_sizes[key] = len(data)
        elif isinstance(data, tuple) and len(data) > 0 and isinstance(data[0], pd.DataFrame):
            cache_sizes[key] = len(data[0])
        else:
            cache_sizes[key] = 1
    
    return {
        "total_entries": len(cache_keys),
        "cache_keys": cache_keys,
        "sizes": cache_sizes
    }

# ==================== EXPORT FUNCTIONS ====================

def export_to_cache_info():
    """Print cache info for debugging"""
    stats = get_cache_stats()
    print("\n📊 CACHE STATISTICS:")
    print(f"Total cached entries: {stats['total_entries']}")
    print("\nCached keys:")
    for key in stats['cache_keys']:
        size = stats['sizes'].get(key, 0)
        print(f"  - {key}: {size} records")