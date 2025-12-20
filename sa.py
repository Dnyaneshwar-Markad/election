# sa.py (PostgreSQL-safe, keeps original layout/UI)
import streamlit as st
import urllib.parse
import pandas as pd
import plotly.express as px
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, SimpleDocTemplate
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.colors import Color, black
import time
from datetime import datetime, timedelta
from api_client import APIClient
from data_loader import clear_all_data
import io
import textwrap
import os
from types import SimpleNamespace
import requests

# ==================== CONFIGURATION ====================
<<<<<<< HEAD
INACTIVITY_TIMEOUT_MINUTES = 15  # ⏱️ Auto-logout after 15 minutes of inactivity
SESSION_WARNING_MINUTES = 13  
=======
INACTIVITY_TIMEOUT_MINUTES = 345  # ⏱️ Auto-logout after 15 minutes of inactivity
SESSION_WARNING_MINUTES =   340
>>>>>>> f2ae72a (Add gitignore)

# ==================== SESSION STATE INITIALIZATION ====================
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        "page": "login",
        "logged_in": False,
        "user_id": None,
        "role": None,
        "access_token": None,
        "token": None,
        "main_admin_id": None,
        "section_no": None,
        "allocated": 0,
        "users": 0,
        "last_session_refresh": 0,
        "session_validation_time": 0,
        "last_activity_time": time.time(),  # ✅ NEW
        "activity_warning_shown": False,
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
            
# ==================== API CLIENT ====================
@st.cache_resource
def get_api_client_singleton():
    """Create a single API client instance"""
    base = os.getenv("API_URL", "https://election-are-near-backend.onrender.com")
    return APIClient(base_url=base)

def get_api_client():
    """Get API client with current token"""
    client = get_api_client_singleton()
    client.token = st.session_state.get("access_token") or st.session_state.get("token")
    return client

# ==================== ACTIVITY TRACKING ====================
def update_activity():
    """Update last activity timestamp"""
    st.session_state.last_activity_time = time.time()
    st.session_state.activity_warning_shown = False

def get_inactivity_duration():
    """Get duration of inactivity in seconds"""
    return time.time() - st.session_state.get("last_activity_time", time.time())

def get_time_until_logout():
    """Get remaining time until auto-logout in seconds"""
    inactive_seconds = get_inactivity_duration()
    timeout_seconds = INACTIVITY_TIMEOUT_MINUTES * 60
    return max(0, timeout_seconds - inactive_seconds)

def format_time_remaining(seconds):
    """Format seconds into MM:SS"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

# ==================== INACTIVITY MONITOR ====================
def check_inactivity():
    """
    Check for user inactivity and handle auto-logout
    Returns True if session is active, False if should logout
    """
    if not st.session_state.get("logged_in"):
        return True
    
    inactive_seconds = get_inactivity_duration()
    timeout_seconds = INACTIVITY_TIMEOUT_MINUTES * 60
    warning_seconds = SESSION_WARNING_MINUTES * 60
    
    # ⏱️ CHECK IF TIMEOUT EXCEEDED
    if inactive_seconds >= timeout_seconds:
        st.error(f"⏱️ Session expired due to {INACTIVITY_TIMEOUT_MINUTES} minutes of inactivity")
        force_logout_due_to_inactivity()
        return False
    
    # ⚠️ SHOW WARNING IF APPROACHING TIMEOUT
    elif inactive_seconds >= warning_seconds and not st.session_state.get("activity_warning_shown"):
        time_remaining = get_time_until_logout()
        st.warning(f"⚠️ Your session will expire in {format_time_remaining(time_remaining)} due to inactivity. Click anywhere to stay logged in.")
        st.session_state.activity_warning_shown = True
    
    return True

# ==================== FORCE LOGOUT ====================
def force_logout_due_to_inactivity():
    """Force logout due to inactivity"""
    try:
        # Call API logout
        api_client = get_api_client()
        requests.post(
            f"{api_client.base_url}/logout",
            headers=api_client.headers(),
            timeout=5
        )
    except Exception as e:
        print(f"Logout API error: {e}")
    
    # Clear session
    clear_session()
    st.session_state.logged_in = False
    st.session_state.page = "login"
    
    time.sleep(1)
    st.rerun()
    
    
# ==================== API CLIENT (SINGLETON) ====================
@st.cache_resource
def get_api_client_singleton():
    """Create a single API client instance - CACHED"""
    base = os.getenv("API_URL", "https://election-are-near-backend.onrender.com")
    return APIClient(base_url=base)

def get_api_client():
    """Get API client with current token"""
    client = get_api_client_singleton()
    client.token = st.session_state.get("access_token") or st.session_state.get("token")
    return client

# ==================== SESSION VALIDATION ====================
def validate_session():
    """Validate current session with caching"""
    if not st.session_state.get("access_token"):
        return False
    
    # Cache validation for 30 seconds
    current_time = time.time()
    last_validation = st.session_state.get("session_validation_time", 0)
    
    if current_time - last_validation < 30:
        return True
    
    try:
        api_client = get_api_client()
        
        response = requests.get(
            f"{api_client.base_url}/session/status",
            headers=api_client.headers(),
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("valid"):
                st.session_state.session_validation_time = current_time
                return True
            else:
                st.error(f"❌ Session invalid: {data.get('reason', 'Unknown')}")
                return False
        else:
            st.error("❌ Session expired - please login again")
            return False
            
    except requests.exceptions.Timeout:
        return True
    except requests.exceptions.HTTPError as e:
        if e.response and e.response.status_code == 401:
            st.error("❌ Session expired - please login again")
        return False
    except Exception as e:
        print(f"Session validation error: {e}")
        return True
    

# ==================== SESSION REFRESH ====================
def setup_session_refresh():
    """Auto-refresh session every 30 minutes"""
    if "last_session_refresh" not in st.session_state:
        st.session_state.last_session_refresh = time.time()
    
    current_time = time.time()
    if current_time - st.session_state.last_session_refresh > 1800:  # 30 minutes
        try:
            api_client = get_api_client()
            response = requests.post(
                f"{api_client.base_url}/refresh-session",
                headers=api_client.headers(),
                timeout=5
            )
            
            if response.status_code == 200:
                st.session_state.last_session_refresh = current_time
                print(f"✅ Session refreshed at {time.strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"❌ Failed to refresh session: {e}")


# ==================== CLEAR SESSION ====================
def clear_session():
    """Clear all session state"""
    keys_to_clear = [
        "logged_in", "page", "user_id", "role", "access_token", 
        "token", "main_admin_id", "section_no", "allocated", 
        "users", "last_session_refresh", "session_validation_time",
        "voter_data", "survey_data", "filters_data", "summary_data",
        "last_activity_time", "activity_warning_shown"
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    st.cache_data.clear()
    st.cache_resource.clear()

# ==================== ACTIVITY TRACKER UI ====================
def show_activity_tracker():
    """Display activity tracker in sidebar"""
    time_remaining = get_time_until_logout()
    inactive_minutes = int(get_inactivity_duration() / 60)
    
    # Color coding based on time remaining
    if time_remaining < 120:  # Less than 2 minutes
        color = "🔴"
        status = "expiring soon"
    elif time_remaining < 300:  # Less than 5 minutes
        color = "🟡"
        status = "active"
    else:
        color = "🟢"
        status = "active"
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    <div style='text-align: center; padding: 10px; background-color: rgba(255,255,255,0.1); border-radius: 10px;'>
        <div style='font-size: 12px; color: gray;'>Session Status</div>
        <div style='font-size: 24px; font-weight: bold;'>{color} {status.upper()}</div>
        <div style='font-size: 14px; margin-top: 5px;'>
            Auto-logout in: <b>{format_time_remaining(time_remaining)}</b>
        </div>
        <div style='font-size: 11px; color: gray; margin-top: 5px;'>
            Inactive: {inactive_minutes} min
        </div>
    </div>
    """, unsafe_allow_html=True)
    
# ==================== AUTO-REFRESH TIMER ====================
def setup_auto_refresh():
    """Setup auto-refresh to check inactivity"""
    # Refresh every 10 seconds to check inactivity
    st.markdown("""
    <script>
        // Auto-refresh every 10 seconds
        setTimeout(function() {
            window.location.reload();
        }, 10000);
        
        // Track user activity
        let activityEvents = ['mousedown', 'keydown', 'scroll', 'touchstart', 'click'];
        
        activityEvents.forEach(function(eventName) {
            document.addEventListener(eventName, function() {
                // Send activity signal to Streamlit
                window.parent.postMessage({type: 'streamlit:setComponentValue', value: Date.now()}, '*');
            }, true);
        });
    </script>
    """, unsafe_allow_html=True)

    
# ------------------- APP CONFIG -------------------
st.set_page_config(page_title="Election Management Software",
                page_icon="logo.png", layout="wide")

## Initialize session state
init_session_state() 

# ------------------- Helpers -------------------
def dict_row_to_namespace(d: dict):
    """Convert dict from psycopg (dict_row) to SimpleNamespace with alias fields."""
    if d is None:
        return None

    ns = SimpleNamespace(**d)

    # Aliases for compatibility
    alias_map = {
        "UserID": "UserId",
        "UserId": "UserID",
        "Username": "UserName",
        "UserName": "Username",
        "ParentID": "ParentId",
        "ParentId": "ParentID"
    }

    for original, alias in alias_map.items():
        if original in d and not hasattr(ns, alias):
            setattr(ns, alias, d.get(original))

    return ns

FONT_PATH = "NotoSansDevanagari.ttf" 

# (DB-based validate_user removed — use API login endpoint instead)
def get_api_client():
    """Return an APIClient configured with base URL and session token from Streamlit state."""
    base = os.getenv("API_URL", "https://election-are-near-backend.onrender.com")
    token = st.session_state.get("access_token") or st.session_state.get("token")
    return APIClient(base_url=base, token=token)

# ------------------- IMAGE / PDF helpers (kept from your code) -------------------
def dataframe_to_image(df_chunk: pd.DataFrame):
    # try load font; fallback to default PIL font
    try:
        font = ImageFont.truetype(FONT_PATH, 20)
    except Exception:
        font = ImageFont.load_default()

    col_widths = {
        "VoterID": 140,
        "PartNo": 100,
        "SectionNo": 140,
        "VEName": 300,
        "Sex": 60,
        "Age": 60,
        "VAddress": 600
    }

    row_height = 70
    padding_x = 50
    padding_y = 20

    img_width = sum(col_widths.values()) + padding_x * 2
    img_height = padding_y * 2 + row_height * (len(df_chunk) + 1)
    img = Image.new("RGB", (int(img_width), int(img_height)), "white")
    draw = ImageDraw.Draw(img)

    x = padding_x
    y = padding_y
    for col, width in col_widths.items():
        draw.text((x, y), col, fill="black", font=font)
        x += width

    y += row_height
    for _, row in df_chunk.iterrows():
        x = padding_x
        for col, width in col_widths.items():
            value = str(row.get(col, "") or "")
            wrapped = textwrap.fill(value, width=32)
            draw.text((x, y), wrapped, fill="black", font=font)
            x += width
        y += row_height

    return img

def images_to_pdf(images: list):
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    page_w, page_h = A4

    watermark_text = "CLICK ERP"
    watermark_font = "Deva" if "Deva" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
    watermark_size = 38
    watermark_opacity = 0.08
    watermark_angle = 40
    max_width = page_w - 60

    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        img_reader = ImageReader(buf)
        img_w, img_h = img.size
        scale = max_width / img_w
        draw_w = img_w * scale
        draw_h = img_h * scale
        x = (page_w - draw_w) / 2
        y = (page_h - draw_h) / 2
        c.drawImage(img_reader, x, y, width=draw_w, height=draw_h, mask='auto')

        border_margin = 15
        c.setStrokeColor(black)
        c.setLineWidth(3)
        c.rect(border_margin, border_margin, page_w - border_margin * 2, page_h - border_margin * 2)

        c.saveState()
        c.setFillColor(Color(0, 0, 0, alpha=watermark_opacity))
        c.setFont(watermark_font, watermark_size)
        c.translate(page_w / 2, page_h / 2)
        c.rotate(watermark_angle)

        cols = 5
        rows = 8
        spacing_x = 250
        spacing_y = 120

        for i in range(-cols, cols + 1):
            for j in range(-rows, rows + 1):
                c.drawString(i * spacing_x, j * spacing_y, watermark_text)

        c.restoreState()
        c.showPage()

    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer


# ------------------- PAGINATED VOTER FETCH -------------------
@st.cache_data(ttl=10)
def fetch_voters_page(search: str = "", limit: int = 100, offset: int = 0, section_no=None):
    """
    Fetch a page of voters - cached per section
    """
    client = get_api_client()
    params = {"limit": limit, "offset": offset}
    if search:
        params["search"] = search

    headers = {}
    if st.session_state.get("access_token"):
        headers["Authorization"] = f"Bearer {st.session_state.get('access_token')}"

    try:
        if hasattr(client, "get_voters"):
            resp = client.get_voters(limit=limit, offset=offset, search=search)
            # Common API patterns: either list or {"rows": [...], "total": 12345}
            if isinstance(resp, dict) and "rows" in resp:
                rows = resp.get("rows", [])
                total = resp.get("total") or resp.get("count") or None
            else:
                rows = resp if isinstance(resp, list) else []
                total = None
        else:
            url = f"{client.base_url.rstrip('/')}/voters"
            r = requests.get(url, params=params, headers=headers, timeout=30)
            r.raise_for_status()
            jsonr = r.json()
            if isinstance(jsonr, dict) and "rows" in jsonr:
                rows = jsonr.get("rows", [])
                total = jsonr.get("total") or jsonr.get("count") or None
            elif isinstance(jsonr, list):
                rows = jsonr
                total = None
            else:
                rows = []
                total = None

        df = pd.DataFrame(rows) if rows else pd.DataFrame()
        
        # FILTER BY SECTION
        if section_no is not None and not df.empty and "SectionNo" in df.columns:
            df = df[df["SectionNo"] == section_no]
            if total is not None:
                total = len(df)  # Update total after filtering
        return df, total
    except Exception as e:
        # Return empty df on error and show when used
        return pd.DataFrame(), None


def fetch_all_voters_api(limit=1000):
    """Fetch all voters from the backend by paginating `/voters`. (Kept for compatibility)"""
    client = get_api_client()
    all_rows = []
    offset = 0
    try:
        while True:
            # prefer client.get_voters if implemented
            if hasattr(client, "get_voters"):
                resp = client.get_voters(limit=limit, offset=offset)
                rows = resp.get("rows", resp)
            else:
                # fallback: direct requests to known endpoint
                url = f"{client.base_url.rstrip('/')}/voters"
                headers = {"Authorization": f"Bearer {st.session_state.get('access_token')}"} if st.session_state.get('access_token') else {}
                r = requests.get(url, params={"limit": limit, "offset": offset}, headers=headers, timeout=30)
                r.raise_for_status()
                rows = r.json().get("rows", r.json())

            if not rows:
                break
            all_rows.extend(rows)
            if len(rows) < limit:
                break
            offset += limit

        return all_rows
    except Exception as e:
        st.error(f"❌ API Error fetching voters: {e}")
        return []


def fetch_all_surveys_api(limit=1000):
    """Fetch all surveys by paginating `/surveys`. Returns list of dicts."""
    client = get_api_client()
    all_rows = []
    offset = 0
    try:
        while True:
            if hasattr(client, "get_surveys"):
                resp = client.get_surveys(limit=limit, offset=offset)
                rows = resp.get("rows", resp)
            else:
                url = f"{client.base_url.rstrip('/')}/surveys"
                headers = {"Authorization": f"Bearer {st.session_state.get('access_token')}"} if st.session_state.get('access_token') else {}
                r = requests.get(url, params={"limit": limit, "offset": offset}, headers=headers, timeout=30)
                r.raise_for_status()
                rows = r.json().get("rows", r.json())

            if not rows:
                break
            all_rows.extend(rows)
            if len(rows) < limit:
                break
            offset += limit

        return all_rows
    except Exception as e:
        st.error(f"❌ API Error fetching surveys: {e}")
        return []



# ------------------- BACKGROUND IMAGE -------------------
def add_bg_from_local(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    import base64
    encoded = base64.b64encode(data).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(255,255,255,0.50), rgba(255,255,255,0.80)),url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# ------------------- FOOTER -------------------
st.markdown("""
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background: rgba(255, 255, 255, 0.9);
        color: black;
        text-align: center;
        padding: 8px 20px;
        font-size: 14px;
        border-top: 1px solid #ddd;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }
    </style>

    <div class="footer">
        <span><b>Developed by:</b> <a href="https://clickerpservices.com/" target="_blank">CLICK ERP SERVICES PVT LTD</a> | 📞 +91-9028568867 | ✉️ yogesh.kale@clickerpservices.com</span>
    </div>
""", unsafe_allow_html=True)

# Remove Streamlit top padding / margin (unchanged)
st.markdown("""
<style>
/* Remove global top padding */
#root > div:nth-child(1) > div > div > div > div {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

/* Remove extra blank space before the title */
.block-container {
    padding-top: 0 !important;  /* Reduce to smallest safe value */
    padding-bottom: 1 !important;
}

/* Remove default header spacing */
header[data-testid="stHeader"] {
    height: 0 !important;
    padding: 0 !important;
}

/* Also remove the top banner shadow */
header[data-testid="stHeader"]::before {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# ------------------- CSS (unchanged) -------------------
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        font-size: 26px;
        font-weight: bold;
        background: linear-gradient(90deg, #ff6a00, #ff9a00);
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .stButton > button {
        width: 350px !important;
        height: 80px !important;
        font-size: 18px !important;
        border-radius: 16px !important;
        margin: 10px auto !important;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;

        border: 1px solid #ddd;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton > button:hover {
        background-color: #ffe5cc !important;
        border: 1px solid #ff8800 !important;
        transform: scale(1.05);
        transition: all 0.2s ease-in-out;
    }
    div[data-testid="column"] { display: flex; justify-content: center; }
    
    
    .fixed-back-btn {
        position: sticky;
        top: 0;
        z-index: 100;
        padding: 5px 0;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown(  """
<style>
.voter-card {
        display: flex;
        align-items: center;
        background: #b39334 ;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
.voter-img {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        object-fit: cover;
        margin-right: 12px;
        border: 2px solid #ff8800;
    }
    .voter-info { flex: 1; }
    .voter-name { font-size: 16px; font-weight: bold; }
    .voter-details { font-size: 13px; color: gray; }
    .scroll-container {
        max-height: 500px;
        overflow-y: auto;
        padding-right: 8px;
    }
</style>
            """,unsafe_allow_html=True)

st.markdown("""
<style>
/* Make sidebar buttons smaller and streamlined */
.sidebar .stButton>button, .stButton>button {
    width: 180px !important;   /* Standard side width */
    height: 40px !important;   /* Much smaller height */
    font-size: 14px !important;
    padding: 6px 12px !important;
    border-radius: 8px !important;
    margin: 6px 0 !important;
}

/* Hover effect */
.sidebar .stButton>button:hover {
    background-color: #ffe5cc !important;
    border: 1px solid #ff8800 !important;
    transform: scale(1.02) !important;
    transition: 0.2s;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
:root, [data-theme="light"], [data-theme="dark"] {
    --text-color: purple !important;
}
</style>
""", unsafe_allow_html=True)


# ------------------- SESSION STATES -------------------
if "page" not in st.session_state:
    st.session_state.page = "login"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "role" not in st.session_state:
    st.session_state.role = None

def go_to(page):
    st.session_state.page = page

# ==================== LOGIN PAGE ====================
if st.session_state.page == "login" and not st.session_state.logged_in:
    add_bg_from_local("Election.png")
    st.markdown('<div class="main-title">🔐 Election Management Software</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col2:
        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")
        
        if st.button("Login", use_container_width=True):
            if not username or not password:
                st.error("❌ Please enter both username and password")
            else:
                try:
                    api_client = get_api_client_singleton()
                    
                    with st.spinner("Logging in..."):
                        result = api_client.login(username, password)
                    
                    if result:
                        st.success("✅ Login Successful!")
                        
                        # Save session data
                        st.session_state.logged_in = True
                        st.session_state.page = "dashboard"
                        st.session_state.access_token = result["access_token"]
                        st.session_state.token = result["access_token"]
                        st.session_state.user_id = result["user_id"]
                        st.session_state.role = result["role"]
                        st.session_state.main_admin_id = result["main_admin_id"]
                        st.session_state.section_no = result.get("section_no")
                        st.session_state.allocated = result.get("allocated", 0)
                        st.session_state.users = result.get("users", 0)
                        
                        # ✅ RESET ACTIVITY TRACKING
                        st.session_state.last_activity_time = time.time()
                        st.session_state.activity_warning_shown = False
                        st.session_state.last_session_refresh = time.time()
                        st.session_state.session_validation_time = time.time()
                        
                        time.sleep(0.5)
                        st.rerun()
                        
                except requests.exceptions.HTTPError as e:
                    if e.response is not None:
                        status = e.response.status_code
                        if status == 403:
                            st.error("❌ This account is already logged in from another device!")
                            st.info("💡 Please logout from the other device first, or wait for the session to expire.")
                        elif status == 401:
                            st.error("❌ Invalid Username or Password")
                        else:
                            try:
                                error_detail = e.response.json().get("detail", "Login failed")
                                st.error(f"❌ {error_detail}")
                            except:
                                st.error("❌ Login failed")
                    else:
                        st.error("❌ Cannot connect to server")
                
                except requests.exceptions.Timeout:
                    st.error("❌ Login timeout - server is not responding")
                
                except requests.exceptions.RequestException:
                    st.error("❌ Cannot connect to server")
                
                except Exception as e:
                    st.error(f"❌ Login error: {str(e)}")



# ------------------- MAIN APP AFTER LOGIN -------------------
elif st.session_state.logged_in:
    
    # ✅ UPDATE ACTIVITY ON ANY INTERACTION
    update_activity()
    
    # ✅ CHECK INACTIVITY
    if not check_inactivity():
        st.stop()
        
    # ✅ VALIDATE SESSION ON PAGE LOAD
    if not validate_session():
        st.warning("⚠️ Your session has expired or is invalid")
        clear_session()
        st.session_state.page = "login"
        st.session_state.logged_in = False
        time.sleep(1)
        st.rerun()
        
    # ✅ AUTO-REFRESH SESSION
    setup_session_refresh()
    
    # ✅ SETUP AUTO-REFRESH TIMER
    setup_auto_refresh()

    # ==================== SIDEBAR ====================
    with st.sidebar:
        st.markdown("### Navigation")
        
        if st.button("📊 Dashboard", use_container_width=True):
            update_activity() 
            st.session_state.page = "dashboard"
            st.rerun()
        
        if st.button("🔍\nशोधा", use_container_width=True):
            update_activity() 
            st.session_state.page = "search"
            st.rerun()
        
        if st.button("📄\nयादी", use_container_width=True):
            update_activity() 
            st.session_state.page = "list"
            st.rerun()
        
        if st.button("✅\nसर्वे", use_container_width=True):
            update_activity() 
            st.session_state.page = "survey"
            st.rerun()
        
        if st.button("📊\nडेटा", use_container_width=True):
            update_activity() 
            st.session_state.page = "data"
            st.rerun()
        
        # Admin-only pages
        if (st.session_state.role or "").lower() == "admin":
            if st.button("⚙️\nसेटिंग्स", use_container_width=True):
                update_activity() 
                st.session_state.page = "settings"
                st.rerun()
        
        st.markdown("---")
        
        # ✅ IMPROVED LOGOUT BUTTON
        if st.button("🚪 Logout", use_container_width=True, type="primary"):
            try:
                # Call API logout
                api_client = get_api_client()
                
                with st.spinner("Logging out..."):
                    response = requests.post(
                        f"{api_client.base_url}/logout",
                        headers=api_client.headers(),
                        timeout=5
                    )
                
                if response.status_code == 200:
                    st.success("✅ Logged out successfully")
                else:
                    st.warning("⚠️ Logout may have failed")
                    
            except Exception as e:
                print(f"Logout API error: {e}")
                st.warning("⚠️ Logged out locally")
            
            # Clear session regardless of API response
            clear_session()
            st.session_state.logged_in = False
            st.session_state.page = "login"
            
            time.sleep(0.5)
            st.rerun()
            
    # --------------- LOAD THE DEFAULT PAGE ----------------
    if st.session_state.page == "dashboard":
        from dashboard import dashboard_page
        dashboard_page()

    elif st.session_state.page == "survey":
        from survey import survey_page
        st.markdown('<div class="fixed-back-btn">', unsafe_allow_html=True)
        survey_page()
        if st.button("⬅️ Back"):
            update_activity()
            go_to("dashboard")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.page == "search":

        # Back button
        if st.button("⬅️ Back"):
            update_activity()
            go_to("dashboard")
            st.rerun()

        st.subheader("🔍 शोधा पृष्ठ")

        # ---------------------- SEARCH + PAGINATION ----------------------
        col_s1, col_s2, col_s3 = st.columns([4, 1, 1])
        with col_s1:
            query = st.text_input("Search (नाव / आडनाव )", value="", key="search_input")
        with col_s2:
            page_size =100     #st.selectbox("Page Size", options=[100, 500, 1000], index=2
            st.write("")  # spacing
            st.write("##### Page size 100")
        with col_s3:
            page_num = st.number_input("Page", min_value=0, value=0, step=1)

        offset = page_num * page_size

        # API FETCH (cached)
        section_no = st.session_state.get("section_no")
        df_page, total_estimate = fetch_voters_page(
            search=query.strip(),
            limit=page_size,
            offset=offset,
            section_no=section_no 
        )

        if df_page is None or df_page.empty:
            st.info("कोणतेही परिणाम आढळले नाहीत.")
        else:

            total_text = f" (showing {len(df_page)} rows)"
            if total_estimate:
                total_text = f" ({len(df_page)} rows — total: {int(total_estimate)})"

            st.info(f"🔎 सापडलेले मतदार{total_text}")

            # ------------ CUSTOM CARD UI INSTEAD OF DATAFRAME ------------
            st.write("")  # spacing

            selected_voters = []

            for idx, row in df_page.iterrows():
                voter_name = row.get('VEName', 'N/A')
                house_no = row.get('HouseNo', 'NA')
                address = row.get('VAddress', 'N/A')
                age = row.get("Age", "")
                sex = row.get("Sex", "")
                voter_id = row.get("VoterID", "")
                visited = row.get("Visited", "")

                # Unique key for checkbox
                checkbox_key = f"chk_{voter_id}_{idx}"

                # Layout: checkbox + card
                col1, col2 = st.columns([1, 12])

                # Checkbox column
                with col1:
                    selected = st.checkbox("", key=checkbox_key)

                # Card Column
                with col2:
                    st.markdown(
                        f"""
                        <div style="
                            background-color: #b18c25;
                            padding: 12px;
                            border-radius: 15px;
                            margin-bottom: 12px;
                            display: flex;
                            align-items: center;
                        ">
                            <div style="
                                width: 60px;
                                height: 60px;
                                border-radius: 50%;
                                border: 4px solid black;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                background-color: #e5b73b;
                                margin-right: 15px;
                                font-size: 28px;
                            ">
                                👤
                            </div>
                            <div style="color: white; line-height: 1.4;">
                                <b style="font-size: 20px;">{voter_name}</b><br>
                                <span>घर क्रमांक: {house_no}</span><br>
                                <span>पत्ता: {address}</span><br>
                                <span>वय: {age} | लिंग: {sex}</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                if selected:
                    selected_voters.append(row.to_dict())

            # ------------ SHOW SELECTED VOTERS + WHATSAPP SHARE -----------

            if selected_voters:
                st.success(f"✅ निवडलेले मतदार: {len(selected_voters)}")

                with st.form("share_form_cards"):
                    recipient = st.text_input(
                        "📱 प्राप्तकर्ता मोबाईल नंबर (Without +91)",
                        placeholder="9876543210"
                    )

                    send_btn = st.form_submit_button("📤 Share on WhatsApp")

                    if send_btn:
                        if not recipient.strip():
                            st.warning("⚠️ कृपया मोबाईल नंबर टाका")
                        else:
                            fixed_message = "नमस्कार,\n\n"

                            details = "\n".join(
                                [
                                    f"नाव: {v.get('VEName','')}\n"
                                    f"घर क्रमांक: {v.get('HouseNo','')}\n"
                                    f"पत्ता: {v.get('VAddress','')}\n"
                                    for v in selected_voters
                                ]
                            )

                            full_message = fixed_message + details
                            encoded_msg = urllib.parse.quote(full_message)

                            wa_link = f"https://wa.me/91{recipient}?text={encoded_msg}"

                            st.success("✅ WhatsApp link तयार आहे")
                            st.markdown(
                                f"""
                                <a href="{wa_link}" target="_blank">
                                    👉 WhatsApp वर संदेश पाठवा
                                </a>
                                """,
                                unsafe_allow_html=True
                            )


    # ------------------- LIST PAGE -------------------
    elif st.session_state.page == "list":
        st.markdown('<div class="fixed-back-btn">', unsafe_allow_html=True)
        if st.button("⬅️ Back"):
            update_activity()
            go_to("dashboard")
        st.markdown('</div>', unsafe_allow_html=True)
        st.subheader("📝 मतदार यादी")

        # Pagination controls
        list_col1, list_col2,list_col3, list_col4 = st.columns(4)
        with list_col1:
            section_no = st.selectbox("विभाग क्रमांक", ["All"])

        with list_col3:
            list_page_num = st.number_input(
                "Page",
                min_value=0,    
                value=0,
                step=1,
                key="list_page"
            )
        with list_col4:
            list_page_size = 100
            
            
        # Fetch paginated data
        df_list_page, total_estimate_list = fetch_voters_page(
            search="",
            limit=list_page_size,
            offset=list_page_num * list_page_size
        )

        if df_list_page is None or df_list_page.empty:
            st.warning("⚠️ डेटा उपलब्ध नाही")
            st.stop()

        # ------------------- FILTERING -------------------
        if section_no != "All" and "SectionNo" in df_list_page.columns:
            display_df = df_list_page[df_list_page["SectionNo"] == section_no]
        else:
            display_df = df_list_page.copy()
        with list_col2: 
            if "Sex" in display_df.columns:
                sex_filter = st.selectbox(
                    "लिंग",
                    ["All"] + sorted(display_df["Sex"].dropna().unique())
                )
                if sex_filter != "All":
                    display_df = display_df[display_df["Sex"] == sex_filter]

        if "Age" in display_df.columns and not display_df["Age"].dropna().empty:
            age_min = int(display_df["Age"].min())
            age_max = int(display_df["Age"].max())
            age_filter = st.slider(
                "वय",
                min_value=age_min,
                max_value=age_max,
                value=(age_min, age_max)
            )
            display_df = display_df[
                (display_df["Age"] >= age_filter[0]) &
                (display_df["Age"] <= age_filter[1])
            ]

        st.info(f"🔎 सापडलेले मतदार ({len(display_df)} rows — total: {total_estimate_list})")
        st.markdown("### 🗂️ मतदार सूची")

        # ------------------- CARD VIEW (NO CHECKBOX) -------------------
        for _, row in display_df.iterrows():
            st.markdown(
                f"""
                <div style="
                    background-color: #b18c25;
                    padding: 12px;
                    border-radius: 15px;
                    margin-bottom: 12px;
                    display: flex;
                    align-items: center;
                ">
                    <div style="
                        width: 60px;
                        height: 60px;
                        border-radius: 50%;
                        border: 4px solid black;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        background-color: #e5b73b;
                        margin-right: 15px;
                        font-size: 28px;
                    ">👤</div>
                    <div style="color: white; line-height: 1.4;">
                        <b style="font-size: 20px;">{row.get("VEName","N/A")}</b><br>
                        <span>घर क्रमांक: {row.get("HouseNo","NA")}</span><br>
                        <span>पत्ता: {row.get("VAddress","NA")}</span><br>
                        <span>वय: {row.get("Age","NA")} | लिंग: {row.get("Sex","NA")}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # ------------------- EXPORT TO PDF (IMAGE BASED) -------------------
        st.markdown("---")

        if st.button("⬇️ PDF निर्यात करा"):

            export_columns = [
                "VoterID", "PartNo", "SectionNo",
                "VEName", "Sex", "Age", "VAddress"
            ]

            export_df = display_df[
                [c for c in export_columns if c in display_df.columns]
            ]

            images = []
            chunk_size = 12  # rows per image

            for i in range(0, len(export_df), chunk_size):
                img = dataframe_to_image(export_df.iloc[i:i + chunk_size])
                images.append(img)

            pdf_buffer = images_to_pdf(images)

            st.download_button(
                "📄 PDF डाउनलोड करा",
                data=pdf_buffer,
                file_name="voter_list.pdf",
                mime="application/pdf"
            )

    # ------------------- DATA PAGE -------------------
    elif st.session_state.page == "data":
        st.markdown('<div class="fixed-back-btn">', unsafe_allow_html=True)
        if st.button("⬅️ Back"):
            update_activity()
            go_to("dashboard")
        st.markdown('</div>', unsafe_allow_html=True)
        st.subheader("📊 डेटा पृष्ठ")

        try:
            surveys = fetch_all_surveys_api()
            df_surveys = pd.DataFrame(surveys) if surveys else pd.DataFrame()
            total_male = int(df_surveys['Male'].sum()) if 'Male' in df_surveys.columns else 0
            total_female = int(df_surveys['Female'].sum()) if 'Female' in df_surveys.columns else 0
            caste_df = df_surveys.groupby('Caste')['VotersCount'].sum().reset_index(name='TotalVoters') if 'Caste' in df_surveys.columns else pd.DataFrame()
            df = pd.DataFrame([{"TotalMale": total_male, "TotalFemale": total_female}])
        except Exception as e:
            st.error(f"❌ API Error loading survey data: {e}")
            df, caste_df = pd.DataFrame(), pd.DataFrame()

        if not df.empty:
            gender_data = pd.DataFrame({"Category": ["Male","Female"], "Count":[int(df["TotalMale"][0] or 0), int(df["TotalFemale"][0] or 0)]})
            st.markdown("### 👨‍👩‍👧‍👦 Gender Distribution")
            st.plotly_chart(px.pie(gender_data, names="Category", values="Count", hole=0.4), use_container_width=True)
            if not caste_df.empty:
                st.markdown("### 🏷️ Caste Distribution")
                st.plotly_chart(px.pie(caste_df, names="Caste", values="TotalVoters", hole=0.4), use_container_width=True)
        else:
            st.warning("⚠️ डेटा उपलब्ध नाही")

    # ------------------- SETTINGS -------------------
    elif st.session_state.page == "settings":
        # ✅ Only admin can access
        if (st.session_state.role or "").lower() != "admin":
            st.warning("⚠️ तुम्हाला सेटिंग्ज पृष्ठावर प्रवेश नाही")
            go_to("home")
        else:
            st.markdown('<div class="fixed-back-btn">', unsafe_allow_html=True)
            if st.button("⬅️ Back"):
                update_activity()
                go_to("dashboard")
            st.markdown('</div>', unsafe_allow_html=True)

            st.subheader("⚙️ युजर तयार करा")

            # ✅ SHOW ALLOCATION STATUS
            allocated = st.session_state.get("allocated", 0)
            users = st.session_state.get("users", 0)
            remaining = max(0, allocated - users)
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("📊 Allocated", allocated)
            with col_b:
                st.metric("👥 Current Users", users)
            with col_c:
                st.metric("✅ Remaining", remaining, delta=remaining if remaining > 0 else "LIMIT REACHED")
            
            if remaining <= 0:
                st.error("❌ You have reached your subuser creation limit!")
                st.info("💡 Contact your administrator to increase your allocation.")
            
            st.markdown("---")
            # ================= CREATE SUBUSER =================
            with st.form("create_user_form"):
                new_username = st.text_input("👤 नवीन युजरनेम")
                new_password = st.text_input("🔑 पासवर्ड", type="password")

                submit_user = st.form_submit_button("➕ युजर तयार करा")

                if submit_user:
                    if remaining <= 0:
                        st.error("❌ Cannot create more subusers. Limit exceeded!")
                    elif new_username and new_password:
                        try:
                            client = get_api_client()

                            # ✅ Call /add-subuser API
                            client.create_user(
                                username=new_username,
                                password=new_password
                            )

                            st.success(f"✅ युजर '{new_username}' यशस्वीरित्या तयार झाला")
                            # Update session state
                            st.session_state.users = users + 1
                            st.rerun()
                            
                        except requests.exceptions.HTTPError as e:
                            if e.response is not None:
                                st.error(
                                    f"❌ {e.response.json().get('detail', e.response.text)}"
                                )
                            else:
                                st.error("❌ Server error while creating user")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                    else:
                        st.warning("⚠️ कृपया युजरनेम आणि पासवर्ड भरा")

            # ================= LIST SUBUSERS =================
            st.markdown("---")
            st.subheader("👥 तुमच्या अंतर्गत युजर")

            try:
                client = get_api_client()
                rows = client.get_users(parent_id=st.session_state.user_id)

                if rows:
                    for r in rows:
                        uname = r.get("Username") or r.get("username", "")
                        role = r.get("Role") or r.get("role", "")
                        created = r.get("CreatedAt") or r.get("created_at", "")

                        st.markdown(f"""
                            - 👤 **{uname}**  
                            🛡️ भूमिका: {role}  
                            📅 तयार दिनांक: {created}
                        """)
                else:
                    st.info("❕ अजून कोणतेही युजर तयार नाहीत")

            except Exception as e:
                st.error(f"❌ Error fetching users: {e}")

    # # ------------------- WHATSAPP -------------------
    # elif st.session_state.page == "whatsapp":
    #     if (st.session_state.role or "").lower() != "admin":
    #         st.warning("⚠️ तुम्हाला सेटिंग्ज पृष्ठावर प्रवेश नाही")
    #         go_to("home")
    #     else:
    #         st.markdown('<div class="fixed-back-btn">', unsafe_allow_html=True)
    #         if st.button("⬅️ Back"):
    #             go_to("dashboard")
    #         st.markdown('</div>', unsafe_allow_html=True)
    #         st.title("💬 WhatsApp Tools")
    #         st.write("WhatsApp automation features")

# End of sa.py
