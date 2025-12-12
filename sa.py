# # sa.py (PostgreSQL-safe, keeps original layout/UI)
# import streamlit as st
# import urllib.parse
# import pandas as pd
# import plotly.express as px
# from io import BytesIO
# from reportlab.lib.pagesizes import A4
# from reportlab.pdfbase import pdfmetrics
# from reportlab.pdfbase.ttfonts import TTFont
# from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, SimpleDocTemplate
# from reportlab.lib.styles import ParagraphStyle
# from reportlab.lib import colors
# from dashboard import dashboard_page
# from survey import survey_page
# # from router import get_connection
# from api_client import APIClient
# import streamlit as st
# import os
# from types import SimpleNamespace
# import requests

# # ------------------- APP CONFIG -------------------
# st.set_page_config(page_title="Election Management Software",
#                    page_icon="favicon.png", layout="wide")

# # ------------------- Helpers -------------------

# def dict_row_to_namespace(d: dict):
#     """Convert dict from psycopg (dict_row) to SimpleNamespace with alias fields."""
#     if d is None:
#         return None

#     ns = SimpleNamespace(**d)

#     # Aliases for compatibility
#     alias_map = {
#         "UserID": "UserId",
#         "UserId": "UserID",
#         "Username": "UserName",
#         "UserName": "Username",
#         "ParentID": "ParentId",
#         "ParentId": "ParentID"
#     }

#     for original, alias in alias_map.items():
#         if original in d and not hasattr(ns, alias):
#             setattr(ns, alias, d.get(original))

#     return ns



# # (DB-based validate_user removed — use API login endpoint instead)
# def get_api_client():
#     """Return an APIClient configured with base URL and session token from Streamlit state."""
#     base = os.getenv("API_URL", "http://127.0.0.1:8000")
#     token = st.session_state.get("access_token") or st.session_state.get("token")
#     return APIClient(base_url=base, token=token)


# def fetch_all_voters_api(limit=1000):
#     """Fetch all voters from the backend by paginating `/voters`.

#     Returns a list of dicts (rows). On error returns empty list and shows an error.
#     """
#     client = get_api_client()
#     all_rows = []
#     offset = 0
#     try:
#         while True:
#             # prefer client.get_voters if implemented
#             if hasattr(client, "get_voters"):
#                 resp = client.get_voters(limit=limit, offset=offset)
#                 rows = resp.get("rows", resp)
#             else:
#                 # fallback: direct requests to known endpoint
#                 url = f"{client.base_url.rstrip('/')}/voters"
#                 headers = {"Authorization": f"Bearer {st.session_state.get('access_token')}"} if st.session_state.get('access_token') else {}
#                 r = requests.get(url, params={"limit": limit, "offset": offset}, headers=headers, timeout=30)
#                 r.raise_for_status()
#                 rows = r.json().get("rows", r.json())

#             if not rows:
#                 break
#             all_rows.extend(rows)
#             if len(rows) < limit:
#                 break
#             offset += limit

#         return all_rows
#     except Exception as e:
#         st.error(f"❌ API Error fetching voters: {e}")
#         return []


# def fetch_all_surveys_api(limit=1000):
#     """Fetch all surveys by paginating `/surveys`. Returns list of dicts."""
#     client = get_api_client()
#     all_rows = []
#     offset = 0
#     try:
#         while True:
#             if hasattr(client, "get_surveys"):
#                 resp = client.get_surveys(limit=limit, offset=offset)
#                 rows = resp.get("rows", resp)
#             else:
#                 url = f"{client.base_url.rstrip('/')}/surveys"
#                 headers = {"Authorization": f"Bearer {st.session_state.get('access_token')}"} if st.session_state.get('access_token') else {}
#                 r = requests.get(url, params={"limit": limit, "offset": offset}, headers=headers, timeout=30)
#                 r.raise_for_status()
#                 rows = r.json().get("rows", r.json())

#             if not rows:
#                 break
#             all_rows.extend(rows)
#             if len(rows) < limit:
#                 break
#             offset += limit

#         return all_rows
#     except Exception as e:
#         st.error(f"❌ API Error fetching surveys: {e}")
#         return []


# # ------------------- FETCH VOTERS -------------------
# def fetch_voters():
#     """Compatibility wrapper used by UI search: return list of SimpleNamespace voters."""
#     dict_rows = fetch_all_voters_api()
#     ns_rows = []
#     for d in dict_rows:
#         if isinstance(d, dict):
#             ns_rows.append(dict_row_to_namespace(d))
#         else:
#             # already namespace-like
#             try:
#                 ns_rows.append(SimpleNamespace(**d))
#             except Exception:
#                 ns_rows.append(d)
#     return ns_rows



# # ------------------- BACKGROUND IMAGE -------------------
# def add_bg_from_local(image_file):
#     with open(image_file, "rb") as f:
#         data = f.read()
#     import base64
#     encoded = base64.b64encode(data).decode()
#     st.markdown(
#         f"""
#         <style>
#         .stApp {{
#             background-image: linear-gradient(rgba(255,255,255,0.50), rgba(255,255,255,0.80)),url("data:image/png;base64,{encoded}");
#             background-size: cover;
#             background-position: center;
#             background-attachment: fixed;
#         }}
#         </style>
#         """,
#         unsafe_allow_html=True
#     )

# # ------------------- FOOTER -------------------
# st.markdown("""
#     <style>
#     .footer {
#         position: fixed;
#         left: 0;
#         bottom: 0;
#         width: 100%;
#         background: rgba(255, 255, 255, 0.9);
#         color: black;
#         text-align: center;
#         padding: 8px 20px;
#         font-size: 14px;
#         border-top: 1px solid #ddd;
#         display: flex;
#         align-items: center;
#         justify-content: center;
#         z-index: 1000;
#     }
#     </style>

#     <div class="footer">
#         <span><b>Developed by:</b> <a href="https://clickerpservices.com/" target="_blank">CLICK ERP SERVICES PVT LTD</a> | 📞 +91-9028568867 | ✉️ yogesh.kale@clickerpservices.com</span>
#     </div>
# """, unsafe_allow_html=True)

# # Remove Streamlit top padding / margin (unchanged)
# st.markdown("""
# <style>
# /* Remove global top padding */
# #root > div:nth-child(1) > div > div > div > div {
#     padding-top: 0 !important;
#     padding-bottom: 0 !important;
# }

# /* Remove extra blank space before the title */
# .block-container {
#     padding-top: 0 !important;  /* Reduce to smallest safe value */
#     padding-bottom: 1 !important;
# }

# /* Remove default header spacing */
# header[data-testid="stHeader"] {
#     height: 0 !important;
#     padding: 0 !important;
# }

# /* Also remove the top banner shadow */
# header[data-testid="stHeader"]::before {
#     display: none !important;
# }
# </style>
# """, unsafe_allow_html=True)

# # ------------------- CSS (unchanged) -------------------
# st.markdown("""
#     <style>
#     .main-title {
#         text-align: center;
#         font-size: 26px;
#         font-weight: bold;
#         background: linear-gradient(90deg, #ff6a00, #ff9a00);
#         padding: 12px;
#         border-radius: 10px;
#         margin-bottom: 20px;
#     }
#     .stButton > button {
#         width: 350px !important;
#         height: 80px !important;
#         font-size: 18px !important;
#         border-radius: 16px !important;
#         margin: 10px auto !important;
#         display: flex;
#         flex-direction: column;
#         justify-content: center;
#         align-items: center;
#         text-align: center;

#         border: 1px solid #ddd;
#         box-shadow: 0 2px 4px rgba(0,0,0,0.1);
#     }
#     .stButton > button:hover {
#         background-color: #ffe5cc !important;
#         border: 1px solid #ff8800 !important;
#         transform: scale(1.05);
#         transition: all 0.2s ease-in-out;
#     }
#     div[data-testid="column"] { display: flex; justify-content: center; }
    
    
#     .fixed-back-btn {
#         position: sticky;
#         top: 0;
#         z-index: 100;
#         padding: 5px 0;
#     }
#     </style>
# """, unsafe_allow_html=True)

# st.markdown(  """
# <style>
# .voter-card {
#         display: flex;
#         align-items: center;
#         background: #b39334 ;
#         border-radius: 10px;
#         padding: 10px;
#         margin-bottom: 10px;
#         box-shadow: 0 2px 4px rgba(0,0,0,0.1);
#     }
# .voter-img {
#         width: 60px;
#         height: 60px;
#         border-radius: 50%;
#         object-fit: cover;
#         margin-right: 12px;
#         border: 2px solid #ff8800;
#     }
#     .voter-info { flex: 1; }
#     .voter-name { font-size: 16px; font-weight: bold; }
#     .voter-details { font-size: 13px; color: gray; }
#     .scroll-container {
#         max-height: 500px;
#         overflow-y: auto;
#         padding-right: 8px;
#     }
# </style>
#             """  ,unsafe_allow_html=True)

# st.markdown("""
# <style>
# /* Make sidebar buttons smaller and streamlined */
# .sidebar .stButton>button, .stButton>button {
#     width: 180px !important;   /* Standard side width */
#     height: 40px !important;   /* Much smaller height */
#     font-size: 14px !important;
#     padding: 6px 12px !important;
#     border-radius: 8px !important;
#     margin: 6px 0 !important;
# }

# /* Hover effect */
# .sidebar .stButton>button:hover {
#     background-color: #ffe5cc !important;
#     border: 1px solid #ff8800 !important;
#     transform: scale(1.02) !important;
#     transition: 0.2s;
# }
# </style>
# """, unsafe_allow_html=True)

# st.markdown("""
# <style>
# :root, [data-theme="light"], [data-theme="dark"] {
#     --text-color: purple !important;
# }
# </style>
# """, unsafe_allow_html=True)


# # ------------------- SESSION STATES -------------------
# if "page" not in st.session_state:
#     st.session_state.page = "login"
# if "logged_in" not in st.session_state:
#     st.session_state.logged_in = False
# if "user_id" not in st.session_state:
#     st.session_state.user_id = None
# if "role" not in st.session_state:
#     st.session_state.role = None

# def go_to(page):
#     st.session_state.page = page

# # ------------------- LOGIN PAGE (MODIFIED) -------------------
# if st.session_state.page == "login" and not st.session_state.logged_in:
#     add_bg_from_local("Election.png")
#     st.markdown('<div class="main-title">🔐 Election Management Software</div>', unsafe_allow_html=True)

#     col1, col2, col3 = st.columns(3)
#     with col2:
#         username = st.text_input("👤 Username")
#         password = st.text_input("🔑 Password", type="password")

#         if st.button("Login"):
#             try:
#                 # USE API FOR LOGIN
#                 api_client = APIClient(base_url=os.getenv("API_URL", "http://127.0.0.1:8000"))
#                 result = api_client.login(username, password)
                
#                 if result:
#                     st.success("✅ Login Successful!")
                    
#                     # Save all session data
#                     st.session_state.logged_in = True
#                     st.session_state.page = "dashboard"
#                     st.session_state.access_token = result["access_token"]
#                     st.session_state.token = result["access_token"]
#                     st.session_state.user_id = result["user_id"]
#                     st.session_state.role = result["role"]
#                     st.session_state.main_admin_id = result["main_admin_id"]
                    
#                     st.rerun()
#             except requests.exceptions.RequestException as e:
#                 st.error(f"❌ Login failed: Cannot connect to server")
#             except Exception as e:
#                 st.error(f"❌ Invalid Username or Password")


# # ------------------- MAIN APP AFTER LOGIN -------------------
# elif st.session_state.logged_in:

#     # ---------------- SIDEBAR NAVIGATION ----------------
#     with st.sidebar:

#         if st.button("📊 Dashboard"):
#             st.session_state.page = "dashboard"

#         if st.button("🔍\nशोधा"):
#             st.session_state.page = "search"

#         if st.button("📝\nयादी"):
#             st.session_state.page = "list"

#         if st.button("✅\nसर्वे"):
#             st.session_state.page = "survey"

#         if st.button("📊\nडेटा"):
#             st.session_state.page = "data"

#         # Admin-only pages
#         if (st.session_state.role or "").lower() == "admin":
#             if st.button("⚙️\nसेटिंग्स"):
#                 st.session_state.page = "settings"

#             if st.button("💬\nव्हॉट्सॲप"):
#                 st.session_state.page = "whatsapp"

#         # Logout Button (MODIFIED)
#         if st.button("🚪 Logout"):
#             try:
#                 api_client = get_api_client()
#                 api_client.logout()
#             except:
#                 pass  # Continue logout even if API fails
            
#             st.session_state.logged_in = False
#             st.session_state.page = "login"
#             st.session_state.user_id = None
#             st.session_state.role = None
#             st.session_state.access_token = None
#             st.session_state.token = None
#             st.session_state.main_admin_id = None
#             st.cache_data.clear()
#             st.rerun()

#     # --------------- LOAD THE DEFAULT PAGE ----------------
#     if st.session_state.page == "dashboard":
#         dashboard_page()

#     elif st.session_state.page == "survey":
#         st.markdown('<div class="fixed-back-btn">', unsafe_allow_html=True)
#         survey_page()
#         if st.button("⬅️ Back"):
#             go_to("dashboard")
#             st.rerun()
#         st.markdown('</div>', unsafe_allow_html=True)

#     elif st.session_state.page == "search":
#         # Streamlit back button handler
#         if st.button("⬅️ Back"):
#             go_to("dashboard")
#             st.rerun()

#         st.subheader("🔍 शोधा पृष्ठ")
#         try:
#             rows = fetch_voters()
#             st.info(f"एकूण मतदार : **{len(rows)}**")
#         except Exception as e:
#             st.error(f"❌ डेटाबेस एरर: {e}")
#             rows = []

#         query = st.text_input("Search", "")
#         filtered = []

#         def normalize_text(text): return str(text).strip().lower()

#         if query.strip():
#             nq = normalize_text(query)
#             for r in rows:
#                 # r is SimpleNamespace so attribute access remains same
#                 if (
#                     nq in normalize_text(getattr(r, "VEName", "")) or
#                     nq in normalize_text(getattr(r, "VPSName", "")) or
#                     nq in normalize_text(getattr(r, "EName", "")) or
#                     nq in normalize_text(getattr(r, "PSName", ""))
#                 ):
#                     filtered.append(r)
#         else:
#             filtered = rows

#         dummy_img = "https://cdn-icons-png.flaticon.com/512/1946/1946429.png"
#         selected_voters = []

#         st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
#         for r in filtered:
#             mobile_no = str(getattr(r, "VAddress", "")).strip()
#             voter_name = getattr(r, "VEName", "")

#             col1, col2 = st.columns([1, 6])
#             with col1:
#                 if mobile_no:
#                     if st.checkbox("✔", key=f"chk_{voter_name}_{mobile_no}"):
#                         selected_voters.append({
#                             "name": voter_name,
#                             "house": getattr(r, "HouseNo", ""),
#                             "psname": getattr(r, "VPSName", ""),
#                             "mobile": mobile_no,
#                             "SlNo": getattr(r, "SectionNo", ""),   # Add section number
#                             "IDCardNo": getattr(r, "IDCardNo", "")
#                         })
#             with col2:
#                 st.markdown(f"""
#                     <div class="voter-card">
#                         <img src="{dummy_img}" class="voter-img"/>
#                         <div class="voter-info">
#                             <div class="voter-name">{voter_name}</div>
#                             <div class="voter-details"><b>घर क्रमांक:</b> {getattr(r, "HouseNo", "")} </div>
#                             <div class="voter-details"><b>पत्ता:</b> {getattr(r, "VAddress", "")}</div>
#                         </div>
#                     </div>
#                 """, unsafe_allow_html=True)
#         st.markdown("</div>", unsafe_allow_html=True)

#         # 🔗 Show Share Button on Top if voters selected
#         if selected_voters:
#             st.success(f"✅ निवडलेले {len(selected_voters)} मतदार")

#             if "show_share_form" not in st.session_state:
#                 st.session_state.show_share_form = False

#             if st.button("📤 Share", key="top_share_btn"):
#                 st.session_state.show_share_form = not st.session_state.show_share_form

#             if st.session_state.show_share_form:
#                 with st.form("share_form_top"):
#                     recipient = st.text_input("📱 प्राप्तकर्ता मोबाईल नंबर (Without +91)")
#                     send_btn = st.form_submit_button("📤 Send on WhatsApp")

#                     if send_btn and recipient.strip():
#                         fixed_message = "नमस्कार,\n\n"
#                         details = "\n".join(
#                             [f"*नाव :* {v['name']} \n*यादीभाग :* {v['SlNo']} \n*मतदान कार्ड :* {v['IDCardNo']}  \n*मतदान केंद्र :* {v['psname']} \n"
#                              for v in selected_voters]
#                         )
#                         full_message = fixed_message + details

#                         encoded_msg = urllib.parse.quote(full_message)
#                         wa_link = f"https://wa.me/91{recipient}?text={encoded_msg}"

#                         st.markdown(f"[👉 WhatsApp वर संदेश पाठवा]({wa_link})", unsafe_allow_html=True)

#     # ------------------- LIST PAGE -------------------
#     elif st.session_state.page == "list":
#         st.markdown('<div class="fixed-back-btn">', unsafe_allow_html=True)
#         if st.button("⬅️ Back"): go_to("dashboard")
#         st.markdown('</div>', unsafe_allow_html=True)
#         st.subheader("📝 मतदार यादी")

#         try:
#             rows = fetch_all_voters_api()
#             df = pd.DataFrame(rows) if rows else pd.DataFrame()
#         except Exception as e:
#             st.error(f"❌ API Error loading voter list: {e}")
#             df = pd.DataFrame()

#         if not df.empty:
#             section_no = st.selectbox("विभाग क्रमांक", ["All"] + sorted(df["SectionNo"].dropna().unique()))
#             filtered_df = df if section_no == "All" else df[df["SectionNo"] == section_no]

#             sex_filter = st.selectbox("लिंग", ["All"] + sorted(filtered_df["Sex"].dropna().unique()))
#             if sex_filter != "All":
#                 filtered_df = filtered_df[filtered_df["Sex"] == sex_filter]

#             if "Age" in filtered_df.columns:
#                 age_filter = st.slider("वय", min_value=int(filtered_df["Age"].min()),
#                                         max_value=int(filtered_df["Age"].max()),
#                                         value=(int(filtered_df["Age"].min()), int(filtered_df["Age"].max())))
#                 filtered_df = filtered_df[(filtered_df["Age"] >= age_filter[0]) & (filtered_df["Age"] <= age_filter[1])]

#             st.info(f"🔎 सापडलेले मतदार: **{len(filtered_df)}**")

#             # --- EXPORT TO PDF ---
#             buffer = BytesIO()
#             doc = SimpleDocTemplate(buffer, pagesize=A4)
#             elements = []
#             font_path = "C:\\Windows\\Fonts\\Mangal.ttf"
#             if os.path.exists(font_path):
#                 pdfmetrics.registerFont(TTFont("Mangal", font_path))
#                 font_name = "Mangal"
#             else:
#                 font_name = "Helvetica"
#             title_style = ParagraphStyle("Title", fontName=font_name, fontSize=14, alignment=1)
#             elements.append(Paragraph("मतदार यादी", title_style))
#             elements.append(Spacer(1, 12))

#             table_data = [["SR NO", "घर क्रमांक", "नाव", "पत्ता"]]
#             for i, (_, r) in enumerate(filtered_df.iterrows(), start=1):
#                 table_data.append([str(i), str(r.get("HouseNo","")), str(r.get("EName","")), str(r.get("VAddress",""))])

#             table = Table(table_data, colWidths=[50, 80, 150, 200])
#             table.setStyle(TableStyle([
#                 ("BACKGROUND", (0, 0), (-1, 0), colors.orange),
#                 ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
#                 ("ALIGN", (0, 0), (-1, -1), "CENTER"),
#                 ("FONTNAME", (0, 0), (-1, -1), font_name),
#                 ("FONTSIZE", (0, 0), (-1, -1), 10),
#                 ("GRID", (0, 0), (-1, -1), 0.5, colors.black)
#             ]))
#             elements.append(table)
#             doc.build(elements)
#             st.download_button("⬇️ PDF निर्यात करा", data=buffer.getvalue(), file_name="voter_list.pdf", mime="application/pdf")

#             # Show voters
#             st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
#             for _, r in filtered_df.iterrows():
#                 st.markdown(f"""
#                     <div class="voter-card">
#                         <img src="https://cdn-icons-png.flaticon.com/512/1946/1946429.png" class="voter-img"/>
#                         <div class="voter-info">
#                             <div class="voter-name">{r.get('VEName','')}</div>
#                             <div class="voter-details">घर क्रमांक: {r.get('HouseNo','')} | विभाग: {r.get('SectionNo','')}<br/>लिंग: {r.get('Sex','')} | वय: {r.get('Age','')}</div>
#                         </div>
#                     </div>
#                 """, unsafe_allow_html=True)
#             st.markdown("</div>", unsafe_allow_html=True)
#         else:
#             st.warning("⚠️ डेटा उपलब्ध नाही")

#     # ------------------- DATA PAGE -------------------
#     elif st.session_state.page == "data":
#         st.markdown('<div class="fixed-back-btn">', unsafe_allow_html=True)
#         if st.button("⬅️ Back"): go_to("dashboard")
#         st.markdown('</div>', unsafe_allow_html=True)
#         st.subheader("📊 डेटा पृष्ठ")

#         try:
#             surveys = fetch_all_surveys_api()
#             df_surveys = pd.DataFrame(surveys) if surveys else pd.DataFrame()
#             total_male = int(df_surveys['Male'].sum()) if 'Male' in df_surveys.columns else 0
#             total_female = int(df_surveys['Female'].sum()) if 'Female' in df_surveys.columns else 0
#             caste_df = df_surveys.groupby('Caste')['VotersCount'].sum().reset_index(name='TotalVoters') if 'Caste' in df_surveys.columns else pd.DataFrame()
#             df = pd.DataFrame([{"TotalMale": total_male, "TotalFemale": total_female}])
#         except Exception as e:
#             st.error(f"❌ API Error loading survey data: {e}")
#             df, caste_df = pd.DataFrame(), pd.DataFrame()

#         if not df.empty:
#             gender_data = pd.DataFrame({"Category": ["Male","Female"], "Count":[int(df["TotalMale"][0] or 0), int(df["TotalFemale"][0] or 0)]})
#             st.markdown("### 👨‍👩‍👧‍👦 Gender Distribution")
#             st.plotly_chart(px.pie(gender_data, names="Category", values="Count", hole=0.4), use_container_width=True)
#             if not caste_df.empty:
#                 st.markdown("### 🏷️ Caste Distribution")
#                 st.plotly_chart(px.pie(caste_df, names="Caste", values="TotalVoters", hole=0.4), use_container_width=True)
#         else:
#             st.warning("⚠️ डेटा उपलब्ध नाही")

#     # ------------------- SETTINGS -------------------
#     elif st.session_state.page == "settings":
#         # ✅ Only admin can access
#         if (st.session_state.role or "").lower() != "admin":
#             st.warning("⚠️ तुम्हाला सेटिंग्ज पृष्ठावर प्रवेश नाही")
#             go_to("home")
#         else:
#             st.markdown('<div class="fixed-back-btn">', unsafe_allow_html=True)
#             if st.button("⬅️ Back"):
#                 go_to("dashboard")
#             st.markdown('</div>', unsafe_allow_html=True)

#             st.subheader("⚙️ युजर तयार करा")

#             with st.form("create_user_form"):
#                 new_username = st.text_input("👤 नवीन युजरनेम")
#                 new_password = st.text_input("🔑 पासवर्ड", type="password")
#                 new_role = st.selectbox("🛡️ भूमिका निवडा", ["subuser"])  # ✅ restrict to 'user' only
#                 submit_user = st.form_submit_button("➕ युजर तयार करा")

#                 if submit_user:
#                     if new_username and new_password:
#                         try:
#                             client = get_api_client()
#                             if hasattr(client, 'create_user'):
#                                 client.create_user(username=new_username, password=new_password, role=new_role.lower(), parent_id=st.session_state.user_id)
#                                 st.success(f"✅ युजर '{new_username}' यशस्वीरित्या तयार झाला")
#                             else:
#                                 # fallback to direct POST if create_user not present
#                                 url = f"{client.base_url.rstrip('/')}/users"
#                                 headers = {"Authorization": f"Bearer {st.session_state.get('access_token')}"} if st.session_state.get('access_token') else {}
#                                 r = requests.post(url, json={"username": new_username, "password": new_password, "role": new_role.lower(), "parent_id": st.session_state.user_id}, headers=headers, timeout=15)
#                                 if r.status_code in (200,201):
#                                     st.success(f"✅ युजर '{new_username}' यशस्वीरित्या तयार झाला")
#                                 else:
#                                     st.error(f"❌ Create user failed: {r.status_code} {r.text}")
#                         except Exception as e:
#                             st.error(f"❌ Error: {e}")
#                     else:
#                         st.warning("⚠️ कृपया युजरनेम आणि पासवर्ड भरा")

#             # ✅ Show list of users created under this admin
#             st.markdown("---")
#             st.subheader("👥 तुमच्या अंतर्गत युजर")

#             try:
#                 client = get_api_client()
#                 if hasattr(client, 'get_users'):
#                     rows = client.get_users(parent_id=st.session_state.user_id)
#                 else:
#                     url = f"{client.base_url.rstrip('/')}/users"
#                     headers = {"Authorization": f"Bearer {st.session_state.get('access_token')}"} if st.session_state.get('access_token') else {}
#                     r = requests.get(url, params={"parent_id": st.session_state.user_id}, headers=headers, timeout=15)
#                     r.raise_for_status()
#                     rows = r.json()

#                 if rows:
#                     for r in rows:
#                         uname = r.get('Username') or r.get('username') or r.get('Username')
#                         role = r.get('Role') or r.get('role')
#                         created = r.get('CreatedAt') or r.get('created_at')
#                         st.markdown(f"""
#                             - 👤 **{uname or ''}**  
#                                 🛡️ भूमिका: {role or ''}  
#                                 📅 तयार दिनांक: {created or ''}
#                         """)
#                 else:
#                     st.info("❕ अजून कोणतेही युजर तयार नाहीत")
#             except Exception as e:
#                 st.error(f"❌ Error fetching users: {e}")

#     # ------------------- WHATSAPP -------------------
#     elif st.session_state.page == "whatsapp":
#         if (st.session_state.role or "").lower() != "admin":
#             st.warning("⚠️ तुम्हाला सेटिंग्ज पृष्ठावर प्रवेश नाही")
#             go_to("home")
#         else:
#             st.markdown('<div class="fixed-back-btn">', unsafe_allow_html=True)
#             if st.button("⬅️ Back"):
#                 go_to("dashboard")
#             st.markdown('</div>', unsafe_allow_html=True)
#             st.title("💬 WhatsApp Tools")
#             st.write("WhatsApp automation features")

# # End of sa.py



# sa.py (PostgreSQL-safe, keeps original layout/UI)
import streamlit as st
import urllib.parse
import pandas as pd
import plotly.express as px
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, SimpleDocTemplate
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from dashboard import dashboard_page
from survey import survey_page
# from router import get_connection
from api_client import APIClient
import os
from types import SimpleNamespace
import requests

# NEW: AgGrid imports
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# ------------------- APP CONFIG -------------------
st.set_page_config(page_title="Election Management Software",
                   page_icon="favicon.png", layout="wide")

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



# (DB-based validate_user removed — use API login endpoint instead)
def get_api_client():
    """Return an APIClient configured with base URL and session token from Streamlit state."""
    base = os.getenv("API_URL", "http://127.0.0.1:8000")
    token = st.session_state.get("access_token") or st.session_state.get("token")
    return APIClient(base_url=base, token=token)


# ------------------- PAGINATED VOTER FETCH -------------------
@st.cache_data(ttl=10)
def fetch_voters_page(search: str = "", limit: int = 100, offset: int = 0):
    """
    Fetch a page of voters from /voters endpoint using APIClient if available,
    otherwise falling back to requests. Returns tuple (df, total_estimate).
    total_estimate may be None if backend doesn't return a total count.
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

# ------------------- LOGIN PAGE (MODIFIED) -------------------
if st.session_state.page == "login" and not st.session_state.logged_in:
    add_bg_from_local("Election.png")
    st.markdown('<div class="main-title">🔐 Election Management Software</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col2:
        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")

        if st.button("Login"):
            try:
                # USE API FOR LOGIN
                api_client = APIClient(base_url=os.getenv("API_URL", "http://127.0.0.1:8000"))
                result = api_client.login(username, password)
                
                if result:
                    st.success("✅ Login Successful!")
                    
                    # Save all session data
                    st.session_state.logged_in = True
                    st.session_state.page = "dashboard"
                    st.session_state.access_token = result["access_token"]
                    st.session_state.token = result["access_token"]
                    st.session_state.user_id = result["user_id"]
                    st.session_state.role = result["role"]
                    st.session_state.main_admin_id = result["main_admin_id"]
                    
                    st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Login failed: Cannot connect to server")
            except Exception as e:
                st.error(f"❌ Invalid Username or Password")


# ------------------- MAIN APP AFTER LOGIN -------------------
elif st.session_state.logged_in:

    # ---------------- SIDEBAR NAVIGATION ----------------
    with st.sidebar:

        if st.button("📊 Dashboard"):
            st.session_state.page = "dashboard"

        if st.button("🔍\nशोधा"):
            st.session_state.page = "search"

        if st.button("📝\nयादी"):
            st.session_state.page = "list"

        if st.button("✅\nसर्वे"):
            st.session_state.page = "survey"

        if st.button("📊\nडेटा"):
            st.session_state.page = "data"

        # Admin-only pages
        if (st.session_state.role or "").lower() == "admin":
            if st.button("⚙️\nसेटिंग्स"):
                st.session_state.page = "settings"

            if st.button("💬\nव्हॉट्सॲप"):
                st.session_state.page = "whatsapp"

        # Logout Button (MODIFIED)
        if st.button("🚪 Logout"):
            try:
                api_client = get_api_client()
                api_client.logout()
            except:
                pass  # Continue logout even if API fails
            
            st.session_state.logged_in = False
            st.session_state.page = "login"
            st.session_state.user_id = None
            st.session_state.role = None
            st.session_state.access_token = None
            st.session_state.token = None
            st.session_state.main_admin_id = None
            st.cache_data.clear()
            st.rerun()

    # --------------- LOAD THE DEFAULT PAGE ----------------
    if st.session_state.page == "dashboard":
        dashboard_page()

    elif st.session_state.page == "survey":
        st.markdown('<div class="fixed-back-btn">', unsafe_allow_html=True)
        survey_page()
        if st.button("⬅️ Back"):
            go_to("dashboard")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # elif st.session_state.page == "search":
    #     # Streamlit back button handler
    #     if st.button("⬅️ Back"):
    #         go_to("dashboard")
    #         st.rerun()

    #     st.subheader("🔍 शोधा पृष्ठ")

    #     # SEARCH + PAGINATION CONTROLS
    #     col_s1, col_s2, col_s3 = st.columns([4,1,1])
    #     with col_s1:
    #         query = st.text_input("Search (नाव / आडनाव )", value="", key="search_input")
    #     with col_s2:
    #         page_size = st.selectbox("Page Size", options=[100, 500, 1000], index=2)
    #     with col_s3:
    #         page_num = st.number_input("Page", min_value=0, value=0, step=1)

    #     offset = page_num * page_size

    #     # Fetch one page from API (cached)
    #     df_page, total_estimate = fetch_voters_page(search=query.strip(), limit=page_size, offset=offset)

    #     if df_page is None or df_page.empty:
    #         st.info("कोणतेही परिणाम आढळले नाहीत.")
    #     else:
    #         # Show summary
    #         total_text = f" (showing {len(df_page)} rows)"
    #         if total_estimate:
    #             total_text = f" ({len(df_page)} rows — total: {int(total_estimate)})"
    #         st.info(f"🔎 सापडलेले मतदार{total_text}")

    #         # Select only specified columns for display
    #         display_columns = [col for col in ['VoterID', 'VEName', 'SectionNo','Age', 'Sex', 'VAddress', 'Visited'] if col in df_page.columns]
    #         df_display = df_page[display_columns] if display_columns else df_page

    #         # Build AgGrid options
    #         gb = GridOptionsBuilder.from_dataframe(df_display)
    #         gb.configure_default_column(resizable=True, sortable=True, filter=True)
    #         # enable multiple row selection
    #         gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    #         # pagination inside grid (local pagination for the current page)
    #         gb.configure_pagination(enabled=True, paginationPageSize=min(50, max(10, page_size // 2)))
    #         gb.configure_side_bar()

    #         grid_options = gb.build()

    #         # Render AgGrid and get response
    #         grid_response = AgGrid(
    #             df_display,
    #             gridOptions=grid_options,
    #             data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    #             update_mode=GridUpdateMode.SELECTION_CHANGED,
    #             allow_unsafe_jscode=True,
    #             enable_enterprise_modules=False,
    #             height=1000,
    #             fit_columns_on_grid_load=False
    #         )

    #         # Safely extract selected rows from AgGrid response without evaluating
    #         # the truthiness of potentially large objects like DataFrames.
    #         cleaned_selected = []
    #         try:
    #             if isinstance(grid_response, dict):
    #                 sel = grid_response.get("selected_rows") or []
    #             else:
    #                 # Non-dict responses (e.g. DataFrame) do not contain selected_rows
    #                 sel = []
    #         except Exception:
    #             sel = []

    #         # Normalize selected row entries (strip internal AgGrid keys)
    #         for r in sel:
    #             if isinstance(r, dict):
    #                 rr = {k: v for k, v in r.items() if not k.startswith("_")}
    #             else:
    #                 rr = r
    #             cleaned_selected.append(rr)

    #         if cleaned_selected:
    #             st.success(f"✅ निवडलेले मतदार: {len(cleaned_selected)}")
    #             # Share button
    #             if st.button("📤 Share selected on WhatsApp", key="share_selected"):
    #                 with st.form("share_form_aggrid"):
    #                     recipient = st.text_input("📱 प्राप्तकर्ता मोबाईल नंबर (Without +91)")
    #                     send_btn = st.form_submit_button("📤 Send on WhatsApp")
    #                     if send_btn and recipient.strip():
    #                         fixed_message = "नमस्कार,\n\n"
    #                         details = "\n".join(
    #                             [f"*नाव :* {v.get('VEName') or v.get('EName') or v.get('VEName','')} \n*घर क्रमांक :* {v.get('HouseNo','')} \n*मतदान कार्ड :* {v.get('IDCardNo','')} \n*मतदान केंद्र :* {v.get('PSName') or v.get('VPSName','')} \n"
    #                              for v in cleaned_selected]
    #                         )
    #                         full_message = fixed_message + details
    #                         encoded_msg = urllib.parse.quote(full_message)
    #                         wa_link = f"https://wa.me/91{recipient}?text={encoded_msg}"
    #                         st.markdown(f"[👉 WhatsApp वर संदेश पाठवा]({wa_link})", unsafe_allow_html=True)
    elif st.session_state.page == "search":

        # Back button
        if st.button("⬅️ Back"):
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
        df_page, total_estimate = fetch_voters_page(
            search=query.strip(),
            limit=page_size,
            offset=offset
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

                if st.button("📤 Share selected on WhatsApp"):
                    with st.form("share_form_cards"):
                        recipient = st.text_input("📱 प्राप्तकर्ता मोबाईल नंबर (Without +91)")
                        send_btn = st.form_submit_button("📤 Send on WhatsApp")

                        if send_btn and recipient.strip():
                            fixed_message = "नमस्कार,\n\n"
                            details = "\n".join(
                                [
                                    f"*नाव:* {v.get('VEName','')} \n"
                                    f"*घर क्रमांक:* {v.get('HouseNo','')} \n"
                                    f"*पत्ता:* {v.get('VAddress','')} \n"
                                    for v in selected_voters
                                ]
                            )
                            full_message = fixed_message + details
                            encoded_msg = urllib.parse.quote(full_message)

                            wa_link = f"https://wa.me/91{recipient}?text={encoded_msg}"

                            st.markdown(
                                f"[👉 WhatsApp वर संदेश पाठवा]({wa_link})",
                                unsafe_allow_html=True
                            )


    # ------------------- LIST PAGE -------------------
    elif st.session_state.page == "list":
        st.markdown('<div class="fixed-back-btn">', unsafe_allow_html=True)
        if st.button("⬅️ Back"): go_to("dashboard")
        st.markdown('</div>', unsafe_allow_html=True)
        st.subheader("📝 मतदार यादी")

        # We'll use paginated API to avoid loading all rows at once
        list_col1, list_col2 = st.columns([3,1])
        with list_col1:
            section_no = st.selectbox("विभाग क्रमांक", ["All"])
        with list_col2:
            list_page_size = st.selectbox("Page Size", [100,500,1000], index=1)
        list_page_num = st.number_input("Page", min_value=0, value=0, step=1, key="list_page")

        # fetch the page (unfiltered by section for speed)
        df_list_page, total_estimate_list = fetch_voters_page(search="", limit=list_page_size, offset=list_page_num * list_page_size)

        if df_list_page is None or df_list_page.empty:
            st.warning("⚠️ डेटा उपलब्ध नाही")
        else:
            # If the user wants to filter by section locally, allow that
            if section_no != "All" and "SectionNo" in df_list_page.columns:
                display_df = df_list_page[df_list_page["SectionNo"] == section_no]
            else:
                display_df = df_list_page

            # Additional filters
            if "Sex" in display_df.columns:
                sex_filter = st.selectbox("लिंग", ["All"] + sorted(display_df["Sex"].dropna().unique()))
                if sex_filter != "All":
                    display_df = display_df[display_df["Sex"] == sex_filter]

            # Age filter if present
            if "Age" in display_df.columns and not display_df["Age"].dropna().empty:
                age_min = int(display_df["Age"].min())
                age_max = int(display_df["Age"].max())
                age_filter = st.slider("वय", min_value=age_min, max_value=age_max, value=(age_min, age_max))
                display_df = display_df[(display_df["Age"] >= age_filter[0]) & (display_df["Age"] <= age_filter[1])]

            st.info(f"🔎 सापडलेले मतदार: **{len(display_df)}**")

            # Select only specified columns for display
            display_columns_list = [col for col in ['VoterID', 'VEName', 'SectionNo', 'Sex', 'VAddress', 'Visited'] if col in display_df.columns]
            df_grid_display = display_df[display_columns_list] if display_columns_list else display_df

            st.markdown("### 🗂️ मतदार सूची")


            # ---- SHOW RESULT COUNT ----
            st.info(f"🔎 सापडलेले मतदार ({len(display_df)} rows — total: {total_estimate_list})")

            # ---- LOOP AND DISPLAY AS CARDS ----
            for idx, row in display_df.iterrows():

                voter_name = row.get("VEName", "N/A")
                address = row.get("VAddress", "N/A")
                house_no = row.get("HouseNo", "NA")
                age = row.get("Age", "NA")
                sex = row.get("Sex", "NA")

                colA, colB = st.columns([0.15, 0.85])

                with colA:
                    is_selected = st.checkbox(
                        "✔",
                        key=f"chk_{voter_name}_{idx}",
                    )

                with colB:
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


            # EXPORT TO PDF (uses currently displayed display_df)
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []
            font_path = "C:\\Windows\\Fonts\\Mangal.ttf"
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont("Mangal", font_path))
                font_name = "Mangal"
            else:
                font_name = "Helvetica"
            title_style = ParagraphStyle("Title", fontName=font_name, fontSize=14, alignment=1)
            elements.append(Paragraph("मतदार यादी", title_style))
            elements.append(Spacer(1, 12))

            table_data = [["SR NO", "घर क्रमांक", "नाव", "पत्ता"]]
            for i, (_, r) in enumerate(display_df.iterrows(), start=1):
                table_data.append([str(i), str(r.get("HouseNo","")), str(r.get("EName","")), str(r.get("VAddress",""))])

            table = Table(table_data, colWidths=[50, 80, 150, 200])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.orange),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black)
            ]))
            elements.append(table)
            doc.build(elements)
            st.download_button("⬇️ PDF निर्यात करा", data=buffer.getvalue(), file_name="voter_list.pdf", mime="application/pdf")


    # ------------------- DATA PAGE -------------------
    elif st.session_state.page == "data":
        st.markdown('<div class="fixed-back-btn">', unsafe_allow_html=True)
        if st.button("⬅️ Back"): go_to("dashboard")
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
                go_to("dashboard")
            st.markdown('</div>', unsafe_allow_html=True)

            st.subheader("⚙️ युजर तयार करा")

            with st.form("create_user_form"):
                new_username = st.text_input("👤 नवीन युजरनेम")
                new_password = st.text_input("🔑 पासवर्ड", type="password")
                new_role = st.selectbox("🛡️ भूमिका निवडा", ["subuser"])  # ✅ restrict to 'user' only
                submit_user = st.form_submit_button("➕ युजर तयार करा")

                if submit_user:
                    if new_username and new_password:
                        try:
                            client = get_api_client()
                            if hasattr(client, 'create_user'):
                                client.create_user(username=new_username, password=new_password, role=new_role.lower(), parent_id=st.session_state.user_id)
                                st.success(f"✅ युजर '{new_username}' यशस्वीरित्या तयार झाला")
                            else:
                                # fallback to direct POST if create_user not present
                                url = f"{client.base_url.rstrip('/')}/users"
                                headers = {"Authorization": f"Bearer {st.session_state.get('access_token')}"} if st.session_state.get('access_token') else {}
                                r = requests.post(url, json={"username": new_username, "password": new_password, "role": new_role.lower(), "parent_id": st.session_state.user_id}, headers=headers, timeout=15)
                                if r.status_code in (200,201):
                                    st.success(f"✅ युजर '{new_username}' यशस्वीरित्या तयार झाला")
                                else:
                                    st.error(f"❌ Create user failed: {r.status_code} {r.text}")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                    else:
                        st.warning("⚠️ कृपया युजरनेम आणि पासवर्ड भरा")

            # ✅ Show list of users created under this admin
            st.markdown("---")
            st.subheader("👥 तुमच्या अंतर्गत युजर")

            try:
                client = get_api_client()
                if hasattr(client, 'get_users'):
                    rows = client.get_users(parent_id=st.session_state.user_id)
                else:
                    url = f"{client.base_url.rstrip('/')}/users"
                    headers = {"Authorization": f"Bearer {st.session_state.get('access_token')}"} if st.session_state.get('access_token') else {}
                    r = requests.get(url, params={"parent_id": st.session_state.user_id}, headers=headers, timeout=15)
                    r.raise_for_status()
                    rows = r.json()

                if rows:
                    for r in rows:
                        uname = r.get('Username') or r.get('username') or r.get('Username')
                        role = r.get('Role') or r.get('role')
                        created = r.get('CreatedAt') or r.get('created_at')
                        st.markdown(f"""
                            - 👤 **{uname or ''}**  
                                🛡️ भूमिका: {role or ''}  
                                📅 तयार दिनांक: {created or ''}
                        """)
                else:
                    st.info("❕ अजून कोणतेही युजर तयार नाहीत")
            except Exception as e:
                st.error(f"❌ Error fetching users: {e}")

    # ------------------- WHATSAPP -------------------
    elif st.session_state.page == "whatsapp":
        if (st.session_state.role or "").lower() != "admin":
            st.warning("⚠️ तुम्हाला सेटिंग्ज पृष्ठावर प्रवेश नाही")
            go_to("home")
        else:
            st.markdown('<div class="fixed-back-btn">', unsafe_allow_html=True)
            if st.button("⬅️ Back"):
                go_to("dashboard")
            st.markdown('</div>', unsafe_allow_html=True)
            st.title("💬 WhatsApp Tools")
            st.write("WhatsApp automation features")

# End of sa.py
