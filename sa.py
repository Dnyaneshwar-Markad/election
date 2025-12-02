import streamlit as st
import pyodbc
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
from router import get_connection
import os
# ------------------- APP CONFIG -------------------
st.set_page_config(page_title="Election Management Software", page_icon="favicon.png", layout="wide")

# ------------------- DB CONNECTION -------------------

# ------------------- FETCH VOTERS -------------------
def fetch_voters():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT VEName, HouseNo, VPSName, EName, PSName, VAddress, SectionNo, Sex, Age, IDCardNo
        FROM VoterList
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

# ------------------- VALIDATE USER -------------------
def validate_user(username, password):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT UserId, UserName, Role, ParentId FROM Users WHERE UserName=? AND Password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        return user
    except Exception as e:
        st.error(f"❌ DB Error: {e}")
        return None
    

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

# Call the function with your image
# add_bg_from_local("Election.png")


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

# Remove Streamlit top padding / margin
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

# ------------------- CSS -------------------
# The above code is using HTML and CSS styling within a Python script to customize the appearance of
# elements in a Streamlit web application.

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
            """  ,unsafe_allow_html=True)

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

# st.markdown("""
# <style>

# /* 🔹 Make all input labels white + bold */
# .stTextInput label, 
# .stSelectbox label,
# .stMultiSelect label,
# .stNumberInput label,
# .stTextArea label,
# .stDateInput label,
# .stTimeInput label,
# .streamlit-expanderHeader,
# .stRadio > label, 
# .stCheckbox > label,
# .stSlider > label {
#     color: #f1f140 !important;
#     font-weight: 700 !important;
# }

# /* Optional: change default text color of all elements */
# body, .stMarkdown, .css-ffhzg2 {
#     color: white !important;
# }

# h1{
#     color: #03b6fc !important;

# }

# </style>
# """, unsafe_allow_html=True)
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



# ------------------- LOGIN PAGE -------------------
if st.session_state.page == "login" and not st.session_state.logged_in:
    add_bg_from_local("Election.png")
    st.markdown('<div class="main-title">🔐 Election Management Software</div>', unsafe_allow_html=True,)
    col1, col2, col3 = st.columns(3)
    with col2:
        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")

        if st.button("Login"):
            user = validate_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.success("✅ Login Successful!")           
                st.session_state.page = "dashboard"
                st.session_state.user_id = user.UserId
                st.session_state.role = user.Role            
                st.rerun()
            else:
                st.error("❌ Invalid Username or Password")
                

# ------------------- MAIN APP AFTER LOGIN -------------------
elif st.session_state.logged_in:

    # ---------------- SIDEBAR NAVIGATION ----------------
    with st.sidebar:

        if st.button(" Dashboard"):
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
        if st.session_state.role == "admin":
            if st.button("⚙️\nसेटिंग्स"):
                st.session_state.page = "settings"

            if st.button("💬\nव्हॉट्सॲप"):
                st.session_state.page = "whatsapp"

        # Logout Button
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.page = "login"
            st.session_state.user_id = None
            st.session_state.role = None
            st.rerun()

    # --------------- LOAD THE DEFAULT PAGE ----------------
    if st.session_state.page == "dashboard":
        dashboard_page()

    # The above code is a Python script that handles a survey form submission in a Streamlit web
    # application. Here is a breakdown of what the code does:
    elif st.session_state.page == "survey":
        st.markdown('<div class="fixed-back-btn">', unsafe_allow_html=True)
        survey_page()
        if st.button("⬅️ Back"): 
            go_to("dashboard")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.page == "search":
        # Streamlit back button handler
        if st.button("⬅️ Back"):
            go_to("dashboard")
            st.rerun()

        st.subheader("🔍 शोधा पृष्ठ")
        try:
            rows = fetch_voters()
            st.info(f"एकूण मतदार : **{len(rows)}**")
        except Exception as e:
            st.error(f"❌ डेटाबेस एरर: {e}")
            rows = []

        query = st.text_input("Search", "")
        filtered = []

        def normalize_text(text): return str(text).strip().lower()

        if query.strip():
            nq = normalize_text(query)
            for r in rows:
                if (
                nq in normalize_text(r.VEName) or
                nq in normalize_text(r.VPSName) or
                nq in normalize_text(r.EName) or
                nq in normalize_text(r.PSName)
            ):
                    filtered.append(r)
        else:
            filtered = rows

        dummy_img = "https://cdn-icons-png.flaticon.com/512/1946/1946429.png"
        selected_voters = []

        st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
        for r in filtered:
            mobile_no = str(getattr(r, "VAddress", "")).strip()
            voter_name = r.VEName

            col1, col2 = st.columns([1, 6])
            with col1:
                if mobile_no:
                    if st.checkbox("✔", key=f"chk_{voter_name}_{mobile_no}"):
                        selected_voters.append({
                        "name": voter_name,
                        "house": r.HouseNo,
                        "psname": r.VPSName,
                        "mobile": mobile_no,
                        "SlNo": getattr(r, "SectionNo", ""),   # Add section number
                        "IDCardNo": getattr(r, "IDCardNo", "")
                        })
            with col2:
                st.markdown(f"""
                    <div class="voter-card">
                        <img src="{dummy_img}" class="voter-img"/>
                        <div class="voter-info">
                            <div class="voter-name">{voter_name}</div>
                            <div class="voter-details"><b>घर क्रमांक:</b> {r.HouseNo} </div>
                            <div class="voter-details"><b>पत्ता:</b> {r.VAddress}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 🔗 Show Share Button on Top if voters selected
        if selected_voters:
            st.success(f"✅ निवडलेले {len(selected_voters)} मतदार")

        # Share button on top (below back button)
            if "show_share_form" not in st.session_state:
                st.session_state.show_share_form = False

            if st.button("📤 Share", key="top_share_btn"):
                st.session_state.show_share_form = not st.session_state.show_share_form

            if st.session_state.show_share_form:
                with st.form("share_form_top"):
                    recipient = st.text_input("📱 प्राप्तकर्ता मोबाईल नंबर (Without +91)")
                    send_btn = st.form_submit_button("📤 Send on WhatsApp")

                    if send_btn and recipient.strip():
                        fixed_message = "नमस्कार,\n\n"
                        details = "\n".join(
                            [f"*नाव :* {v['name']} \n*यादीभाग :* {v['SlNo']} \n*मतदान कार्ड :* {v['IDCardNo']}  \n*मतदान केंद्र :* {v['psname']} \n"
                            for v in selected_voters]
                        )
                        full_message = fixed_message + details

                        encoded_msg = urllib.parse.quote(full_message)
                        wa_link = f"https://wa.me/91{recipient}?text={encoded_msg}"

                        st.markdown(f"[👉 WhatsApp वर संदेश पाठवा]({wa_link})", unsafe_allow_html=True)


    # ------------------- LIST PAGE -------------------
    elif st.session_state.page == "list":
        st.markdown('<div class="fixed-back-btn">', unsafe_allow_html=True)
        if st.button("⬅️ Back"): go_to("dashboard")
        st.markdown('</div>', unsafe_allow_html=True)
        st.subheader("📝 मतदार यादी")

        try:
            conn = get_connection()
            df = pd.read_sql("SELECT * FROM VoterList", conn)
            conn.close()
        except Exception as e:
            st.error(f"❌ डेटाबेस एरर: {e}")
            df = pd.DataFrame()

        if not df.empty:
            section_no = st.selectbox("विभाग क्रमांक", ["All"] + sorted(df["SectionNo"].dropna().unique()))
            filtered_df = df if section_no == "All" else df[df["SectionNo"] == section_no]

            sex_filter = st.selectbox("लिंग", ["All"] + sorted(filtered_df["Sex"].dropna().unique()))
            if sex_filter != "All":
                filtered_df = filtered_df[filtered_df["Sex"] == sex_filter]

            if "Age" in filtered_df.columns:
                age_filter = st.slider("वय", min_value=int(filtered_df["Age"].min()),
                                        max_value=int(filtered_df["Age"].max()),
                                        value=(int(filtered_df["Age"].min()), int(filtered_df["Age"].max())))
                filtered_df = filtered_df[(filtered_df["Age"] >= age_filter[0]) & (filtered_df["Age"] <= age_filter[1])]

            st.info(f"🔎 सापडलेले मतदार: **{len(filtered_df)}**")

            # --- EXPORT TO PDF ---
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
            for i, (_, r) in enumerate(filtered_df.iterrows(), start=1):
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

            # Show voters
            st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
            for _, r in filtered_df.iterrows():
                st.markdown(f"""
                    <div class="voter-card">
                        <img src="https://cdn-icons-png.flaticon.com/512/1946/1946429.png" class="voter-img"/>
                        <div class="voter-info">
                            <div class="voter-name">{r.get('VEName','')}</div>
                            <div class="voter-details">घर क्रमांक: {r.get('HouseNo','')} | विभाग: {r.get('SectionNo','')}<br/>लिंग: {r.get('Sex','')} | वय: {r.get('Age','')}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("⚠️ डेटा उपलब्ध नाही")
        # your full search page code here
        ...

    elif st.session_state.page == "data":
        st.markdown('<div class="fixed-back-btn">', unsafe_allow_html=True)
        if st.button("⬅️ Back"): go_to("dashboard")
        st.markdown('</div>', unsafe_allow_html=True)
        st.subheader("📊 डेटा पृष्ठ")

        try:
            conn = get_connection()
            df = pd.read_sql("SELECT SUM(Male) AS TotalMale, SUM(Female) AS TotalFemale FROM SurveyData", conn)
            caste_df = pd.read_sql("SELECT Caste, SUM(VotersCount) AS TotalVoters FROM SurveyData GROUP BY Caste", conn)
            conn.close()
        except Exception as e:
            st.error(f"❌ डेटाबेस एरर: {e}")
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
        # your data page
        ...

    elif st.session_state.page == "settings":
            # ✅ Only admin can access
            if st.session_state.role.lower() != "admin":
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
                                conn = get_connection()
                                cursor = conn.cursor()
                                cursor.execute("""
                                    INSERT INTO Users (UserName, Password, Role, ParentId, CreatedAt)
                                    VALUES (?, ?, ?, ?, GETDATE())
                                """, (new_username, new_password, new_role.lower(), st.session_state.user_id))
                                conn.commit()
                                st.success(f"✅ युजर '{new_username}' यशस्वीरित्या तयार झाला")
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                            finally:
                                cursor.close()
                                conn.close()
                        else:
                            st.warning("⚠️ कृपया युजरनेम आणि पासवर्ड भरा")

                # ✅ Show list of users created under this admin
                st.markdown("---")
                st.subheader("👥 तुमच्या अंतर्गत युजर")

                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT UserID, UserName, Role, CreatedAt 
                        FROM Users 
                        WHERE ParentId = ?
                        ORDER BY CreatedAt DESC
                    """, (st.session_state.user_id,))
                    rows = cursor.fetchall()
                    if rows:
                        for r in rows:
                            st.markdown(f"""
                                - 👤 **{r.UserName}**  
                                    🛡️ भूमिका: {r.Role}  
                                    📅 तयार दिनांक: {r.CreatedAt}
                            """)
                    else:
                        st.info("❕ अजून कोणतेही युजर तयार नाहीत")
                except Exception as e:
                    st.error(f"❌ Error fetching users: {e}")
                finally:
                    cursor.close()
                    conn.close()

    elif st.session_state.page == "whatsapp":
        if st.session_state.role.lower() != "admin":
                st.warning("⚠️ तुम्हाला सेटिंग्ज पृष्ठावर प्रवेश नाही")
                go_to("home")
        else:
            st.markdown('<div class="fixed-back-btn">', unsafe_allow_html=True)
            if st.button("⬅️ Back"): 
                go_to("dashboard")
            st.markdown('</div>', unsafe_allow_html=True)
            st.title("💬 WhatsApp Tools")
            st.write("WhatsApp automation features")

    # ------------------- ADVANCED SEARCH PAGE -------------------
    elif st.session_state.page == "adv_search":
        st.markdown('<div class="fixed-back-btn">', unsafe_allow_html=True)
        if st.button("⬅️ Back"): go_to("dashboard")
        st.markdown('</div>', unsafe_allow_html=True)
        st.subheader("🔎 आधुनिक पद्धतीने शोध")

        try:
            conn = get_connection()
            df = pd.read_sql("SELECT * FROM VoterList", conn)
            conn.close()
        except Exception as e:
            st.error(f"❌ डेटाबेस एरर: {e}")
            df = pd.DataFrame()

        if not df.empty:
            with st.form("adv_search_form"):
                col1, col2, col3 = st.columns(3)
                section_filter = col1.selectbox("विभाग क्रमांक", ["All"] + sorted(df["SectionNo"].dropna().unique()))
                age_filter = col2.number_input("वय", min_value=0, max_value=120, value=0)
                sex_filter = col3.selectbox("लिंग", ["All"] + sorted(df["Sex"].dropna().unique()))
                submitted = st.form_submit_button("🔍 शोधा")

            filtered_df = df.copy()
            if submitted:
                if section_filter != "All": filtered_df = filtered_df[filtered_df["SectionNo"] == section_filter]
                if age_filter > 0: filtered_df = filtered_df[filtered_df["Age"] == age_filter]
                if sex_filter != "All": filtered_df = filtered_df[filtered_df["Sex"] == sex_filter]

            st.info(f"🔎 सापडलेले मतदार: **{len(filtered_df)}**")

            st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
            for _, r in filtered_df.iterrows():
                st.markdown(f"""
                    <div class="voter-card">
                        <img src="https://cdn-icons-png.flaticon.com/512/1946/1946429.png" class="voter-img"/>
                        <div class="voter-info">
                            <div class="voter-name">{r.get('VEName','')}</div>
                            <div class="voter-details">घर क्रमांक: {r.get('HouseNo','')} | विभाग: {r.get('SectionNo','')}<br/>लिंग: {r.get('Sex','')} | वय: {r.get('Age','')}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("⚠️ डेटा उपलब्ध नाही")



#         # ------------------- SETTINGS PAGE -------------------
    

