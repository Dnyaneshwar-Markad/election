import streamlit as st
import pandas as pd
from api_client import APIClient
import time 
import os


def get_api_client():
    base = os.getenv("API_URL", "https://election-are-near-backend.onrender.com")
    token = st.session_state.get("access_token") or st.session_state.get("token")
    return APIClient(base_url=base, token=token)


def load_voter_data(section_no=None, force_reload=False):
    """
    Load voter data with intelligent caching
    - Caches for 5 minutes
    - Per-user cache
    - Pagination support
    """
    cache_key = f"voter_data_{section_no}"
    cache_time_key = f"{cache_key}_time"
    
    # Check if cached data exists and is fresh (5 minutes)
    current_time = time.time()
    cached_time = st.session_state.get(cache_time_key, 0)
    
    if (not force_reload and 
        cache_key in st.session_state and 
        current_time - cached_time < 300):  # 5 minutes
        return st.session_state[cache_key]
    
    # Load fresh data
    try:
        api = get_api_client()
        all_rows = []
        limit = 5000  # Reduced from 3000
        offset = 0
        
        # ✅ PAGINATION WITH TIMEOUT
        while True:
            try:
                res = api.get_voters(limit=limit, offset=offset)
                rows = res.get("rows", [])
                
                if not rows:
                    break
                
                all_rows.extend(rows)
                
                # ✅ BREAK IF LESS THAN LIMIT (no more data)
                if len(rows) < limit:
                    break
                
                offset += limit
                
            except Exception as e:
                print(f"Error loading voters at offset {offset}: {e}")
                break
        
        df = pd.DataFrame(all_rows)
        
        # Cache the result
        st.session_state[cache_key] = df
        st.session_state[cache_time_key] = current_time
        
        return df
    
    except Exception as e:
        print(f"Error loading voter data: {e}")
        # Return empty DataFrame on error
        return pd.DataFrame()

# ==================== OPTIMIZED: Load Survey Data ====================
def load_survey_data(user_id=None, force_reload=False):
    """
    Load survey data with intelligent caching
    - Caches for 2 minutes
    - Per-user cache
    """
    cache_key = f"survey_data_{user_id}"
    cache_time_key = f"{cache_key}_time"
    
    # Check cache (2 minutes for surveys as they update more frequently)
    current_time = time.time()
    cached_time = st.session_state.get(cache_time_key, 0)
    
    if (not force_reload and 
        cache_key in st.session_state and 
        current_time - cached_time < 120):  # 2 minutes
        return st.session_state[cache_key]
    
    # Load fresh data
    try:
        api = get_api_client()
        all_rows = []
        limit = 500  # Reduced from 1000
        offset = 0
        
        while True:
            try:
                res = api.get_surveys(limit=limit, offset=offset)
                rows = res.get("rows", [])
                
                if not rows:
                    break
                
                all_rows.extend(rows)
                
                if len(rows) < limit:
                    break
                
                offset += limit
                
            except Exception as e:
                print(f"Error loading surveys at offset {offset}: {e}")
                break
        
        df = pd.DataFrame(all_rows)
        
        # Cache the result
        st.session_state[cache_key] = df
        st.session_state[cache_time_key] = current_time
        
        return df
    
    except Exception as e:
        print(f"Error loading survey data: {e}")
        return pd.DataFrame()

# ==================== OPTIMIZED: Load Filters ====================
def load_filters(section_no=None, force_reload=False):
    """
    Load filters with caching (10 minutes - filters rarely change)
    """
    cache_key = f"filters_data_{section_no}"
    cache_time_key = f"{cache_key}_time"
    
    current_time = time.time()
    cached_time = st.session_state.get(cache_time_key, 0)
    
    if (not force_reload and 
        cache_key in st.session_state and 
        current_time - cached_time < 600):  # 10 minutes
        return st.session_state[cache_key]
    
    try:
        api = get_api_client()
        filters = api.get_voter_filters()
        
        # Cache the result
        st.session_state[cache_key] = filters
        st.session_state[cache_time_key] = current_time
        
        return filters
    
    except Exception as e:
        print(f"Error loading filters: {e}")
        return {}


# ==================== OPTIMIZED: Load Summary ====================
def load_summary(section_no=None, force_reload=False):
    """
    Load summary with caching (5 minutes)
    """
    cache_key = f"summary_data_{section_no}"
    cache_time_key = f"{cache_key}_time"
    
    current_time = time.time()
    cached_time = st.session_state.get(cache_time_key, 0)
    
    if (not force_reload and 
        cache_key in st.session_state and 
        current_time - cached_time < 300):  # 5 minutes
        return st.session_state[cache_key]
    
    try:
        api = get_api_client()
        summary = api.get_voter_summary()
        
        # Cache the result
        st.session_state[cache_key] = summary
        st.session_state[cache_time_key] = current_time
        
        return summary
    
    except Exception as e:
        print(f"Error loading summary: {e}")
        return {}

# ==================== CLEAR FUNCTIONS ====================
def clear_voter_data():
    """Clear only voter data cache"""
    keys_to_clear = [k for k in st.session_state.keys() if k.startswith("voter_data_")]
    for key in keys_to_clear:
        del st.session_state[key]
        time_key = f"{key}_time"
        if time_key in st.session_state:
            del st.session_state[time_key]

def clear_survey_data():
    """Clear only survey data cache"""
    keys_to_clear = [k for k in st.session_state.keys() if k.startswith("survey_data_")]
    for key in keys_to_clear:
        del st.session_state[key]
        time_key = f"{key}_time"
        if time_key in st.session_state:
            del st.session_state[time_key]

def clear_all_data():
    """Clear all cached data"""
    keys_to_clear = [
        k for k in st.session_state.keys() 
        if any(k.startswith(prefix) for prefix in 
            ["voter_data_", "survey_data_", "filters_data_", "summary_data_"])
    ]
    
    for key in keys_to_clear:
        del st.session_state[key]

# ==================== FORCE RELOAD FUNCTIONS ====================
def force_reload_voters():
    """Force reload voter data on next call"""
    clear_voter_data()

def force_reload_surveys():
    """Force reload survey data on next call"""
    clear_survey_data()

def force_reload_all():
    """Force reload all data on next call"""
    clear_all_data()