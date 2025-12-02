# import streamlit as st
# import pyodbc
# import pandas as pd
# import plotly.express as px
# from reportlab.lib.utils import ImageReader
# from PIL import Image, ImageDraw, ImageFont
# from reportlab.pdfgen import canvas
# from reportlab.lib.pagesizes import A4
# import io
# import textwrap
# from PyPDF2 import PdfReader, PdfWriter


# # --------------------------------------
# # Database Connection
# # --------------------------------------
# def get_connection():
#     return pyodbc.connect(
#         "DRIVER={ODBC Driver 17 for SQL Server};"
#         "SERVER=DNYANESHWAR\\MSSQLSERVER02;"
#         "DATABASE=Maharashtra;"
#         "UID=sa;"
#         "PWD=sa@123;"
#     )


# # --------------------------------------
# # Load Data
# # --------------------------------------
# @st.cache_data
# def load_voter_data():
#     conn = get_connection()
#     query = """
#         SELECT 
#             VoterID,
#             PartNo,
#             SectionNo,
#             EName,
#             VEName,
#             Sex,
#             Age,
#             Address,
#             VAddress
#         FROM VoterList
#     """
#     df = pd.read_sql(query, conn)
#     return df


# # ------------------------------------------------------
# # Convert DataFrame CHUNK (30 rows) → Image (Scan Style)
# # ------------------------------------------------------
# def dataframe_to_image(df_chunk):
#     """
#     Convert a chunk (<=30 rows) into a clean, readable table-style image.
#     Includes:
#     - Wider spacing
#     - Better padding between rows/columns
#     - Auto text wrapping
#     """

#     font = ImageFont.truetype("NotoSansDevanagari.ttf", 20)

#     # ⬇️ Adjust Column Widths (wider spacing)
#     col_widths = {
#         "VoterID": 140,
#         "PartNo": 100,
#         "SectionNo": 140,
#         "VEName": 600,
#         "Sex": 60,
#         "Age": 60,
#         "VAddress": 1100
#     }

#     row_height = 60       # ⬆️ More spacing per row
#     padding_x = 40        # ⬆️ More left-right padding
#     padding_y = 50        # ⬆️ More top-bottom padding

#     img_width = sum(col_widths.values()) + padding_x * 2
#     img_height = padding_y * 2 + row_height * (len(df_chunk) + 1)

#     img = Image.new("RGB", (img_width, img_height), "white")
#     draw = ImageDraw.Draw(img)

#     # ---------------- HEADER ----------------
#     x = padding_x
#     y = padding_y
#     for col, width in col_widths.items():
#         draw.text((x, y), col, fill="black", font=font)
#         x += width

#     # ---------------- ROWS ----------------
#     y += row_height
#     for _, row in df_chunk.iterrows():
#         x = padding_x
#         for col, width in col_widths.items():
#             value = str(row[col])
#             wrapped = textwrap.fill(value, width=32)  # ⬅️ better wrapping
#             draw.text((x, y), wrapped, fill="black", font=font)
#             x += width
#         y += row_height

#     return img



# # ------------------------------------------------------
# # Convert ALL images → Multi-page Read-Only PDF
# # ------------------------------------------------------
# def images_to_pdf(images):
#     pdf_buffer = io.BytesIO()
#     c = canvas.Canvas(pdf_buffer, pagesize=A4)
#     page_w, page_h = A4

#     for img in images:
#         # Convert image to PNG bytes
#         buf = io.BytesIO()
#         img.save(buf, format="PNG")
#         buf.seek(0)
#         img_reader = ImageReader(buf)

#         img_w, img_h = img.size

#         # Fit image to PDF width (keep aspect ratio)
#         max_width = page_w - 40  # keep margins
#         scale = max_width / img_w

#         draw_w = img_w * scale
#         draw_h = img_h * scale

#         # Center horizontally, place near top
#         x = (page_w - draw_w) / 2
#         y = page_h - draw_h - 30

#         # IMPORTANT: image only → no selectable text
#         c.drawImage(img_reader, x, y, width=draw_w, height=draw_h, mask='auto')
#         c.showPage()

#     c.save()
#     pdf_buffer.seek(0)
#     return pdf_buffer

# # ------------------------------------------------------
# # Disable copying from pdf
# # ------------------------------------------------------

# def disable_copy(pdf_bytes, user_password="asdfg", owner_password="asdfghjkl"):
#     reader = PdfReader(io.BytesIO(pdf_bytes))
#     writer = PdfWriter()

#     # Copy pages
#     for page in reader.pages:
#         writer.add_page(page)

#     # Encryption: disable copying unless owner password is used
#     writer.encrypt(
#         user_pwd=user_password,
#         owner_pwd=owner_password,
#         use_128bit=True
#     )

#     output = io.BytesIO()
#     writer.write(output)
#     output.seek(0)
#     return output





# # --------------------------------------
# # Dashboard Page
# # --------------------------------------
# def dashboard_page():

#     # st.title("📊 Voter Analytics Dashboard")

#     df = load_voter_data()

#     # ------------------------------------------------------
#     # FILTERS
#     # ------------------------------------------------------
#     col1,  col3, col4, col5, col6 = st.columns([2,1,1,1,1])

#     with col1:

#         min_age = int(df["Age"].min())
#         max_age = int(df["Age"].max())

#         age_range = st.slider(
#             "Age Range",
#             min_age,
#             max_age,
#             (min_age, max_age)
#         )
        

#     with col3:
#         gender = st.selectbox(
#             "Gender",
#             ["All"] + df["Sex"].unique().tolist()
#         )

#     with col4:
#         voter_id = st.selectbox(
#             "Voter ID",
#             ["All"] + df["VoterID"].unique().tolist()
#         )

#     with col5:
#         address = st.selectbox(
#             "Address",
#             ["All"] + df["Address"].unique().tolist()
#         )

#     with col6:
#         part_no = st.selectbox(
#             "Part No",
#             ["All"] + sorted(df["PartNo"].unique().tolist())
#         )

#     # ------------------------------------------------------
#     # APPLY FILTERS
#     # ------------------------------------------------------
#     filtered = df.copy()

#     filtered = filtered[
#         (filtered["Age"] >= age_range[0]) &
#         (filtered["Age"] <= age_range[1])
#     ]

#     if gender != "All":
#         filtered = filtered[filtered["Sex"] == gender]

#     if voter_id != "All":
#         filtered = filtered[filtered["VoterID"] == voter_id]

#     if address != "All":
#         filtered = filtered[filtered["Address"] == address]

#     if part_no != "All":
#         filtered = filtered[filtered["PartNo"] == part_no]

#     st.success(f"Filtered Records: {len(filtered)}")

#     if filtered.empty:
#         st.warning("No matching data found.")
#         return

#     # ------------------------------------------------------
#     # CHARTS
#     # ------------------------------------------------------
#     st.subheader("📊 Voter Analysis")

#     col1, col2 = st.columns(2)

#     # AGE CHART
#     with col1:
#         age_count = filtered.groupby("Age")["VoterID"].count().reset_index()
#         age_bar = px.bar(age_count, x="Age", y="VoterID", title="Age Distribution")
#         st.plotly_chart(age_bar, use_container_width=True)

#     # GENDER CHART
#     with col2:
#         gender_count = filtered.groupby("Sex")["VoterID"].count().reset_index()
#         gender_pie = px.pie(gender_count, names="Sex", values="VoterID", title="Gender Distribution")
#         st.plotly_chart(gender_pie, use_container_width=True)

#     # ADDRESS WISE CHART
#     address_count = filtered.groupby(["Address","Sex"])["VoterID"].count().reset_index()
#     address_count = address_count.sort_values("VoterID", ascending=False)

#     address_chart = px.bar(address_count, x="Address", y="VoterID",color="Sex", title="Voters by Address", barmode= "stack")
#     address_chart.update_layout(xaxis_tickangle=-45)
#     st.plotly_chart(address_chart, use_container_width=True)

#     # ------------------------------------------------------
#     # DOWNLOAD READ-ONLY PDF
#     # ------------------------------------------------------
#     st.subheader("📥 Download Filtered Voter List ")

#     if st.button("Generate PDF"):

#         images = []
#         records_per_page = 30

#         # --- Split into 30-row chunks ---
#         for start in range(0, len(filtered), records_per_page):
#             chunk_df = filtered.iloc[start:start + records_per_page]
#             img = dataframe_to_image(chunk_df)
#             images.append(img)

#         pdf_file = images_to_pdf(images)
        
#         # THEN disable copying
#         protected_pdf = disable_copy(pdf_file.getvalue())
        
        
#         st.download_button(
#             label="📄 Download PDF (Scanned, Non-Editable)",
#             data=pdf_file,
#             file_name="Filtered_Voter_List_ReadOnly.pdf",
#             mime="application/pdf"
#         )
import streamlit as st
import pyodbc
import pandas as pd
import plotly.express as px
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import Color, black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import textwrap
from PyPDF2 import PdfReader, PdfWriter
from router import get_connection
import os
    




# Load Data
@st.cache_data
def load_voter_data():
    conn = get_connection()
    query = """
        SELECT VoterID, PartNo, SectionNo, EName, VEName, Sex, Age,Address, VAddress, Visited
        FROM VoterList
    """
    return pd.read_sql(query, conn)

@st.cache_data
def load_survey_data():
    conn = get_connection()
    query = """
        SELECT SurveyNo,VoterID,VEName,Sex,HouseNo,Landmark,VAddress, Mobile,PartNo,SectionNo,VotersCount,Male, Female,Caste,Submission_Time,Age FROM SurveyData
    """
    return pd.read_sql(query, conn)

# Convert DataFrame CHUNK (30 rows) → Image (Scan Style)
def dataframe_to_image(df_chunk):
    """
    Convert a chunk (<=30 rows) into a clean, readable table-style image.
    Includes:
    - Wider spacing
    - Better padding between rows/columns
    - Auto text wrapping
    """

    font = ImageFont.truetype("NotoSansDevanagari.ttf", 20)

    # ⬇️ Adjust Column Widths (wider spacing)
    col_widths = {
        "VoterID": 140,
        "PartNo": 100,
        "SectionNo": 140,
        "VEName": 300,
        "Sex": 60,
        "Age": 60,
        "VAddress": 600
    }

    row_height = 70       # ⬆️ More spacing per row
    padding_x = 50        # ⬆️ More left-right padding
    padding_y = 20        # ⬆️ More top-bottom padding

    img_width = sum(col_widths.values()) + padding_x * 2
    img_height = padding_y * 2 + row_height * (len(df_chunk) + 1)

    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    # ---------------- HEADER ----------------
    x = padding_x
    y = padding_y
    for col, width in col_widths.items():
        draw.text((x, y), col, fill="black", font=font)
        x += width

    # ---------------- ROWS ----------------
    y += row_height
    for _, row in df_chunk.iterrows():
        x = padding_x
        for col, width in col_widths.items():
            value = str(row[col])
            wrapped = textwrap.fill(value, width=32)  # ⬅️ better wrapping
            draw.text((x, y), wrapped, fill="black", font=font)
            x += width
        y += row_height

    return img

# ------------------------------------------------------
# Convert ALL images → Multi-page Read-Only PDF
# ------------------------------------------------------
# Register a clean font for watermark
pdfmetrics.registerFont(TTFont("Deva", "NotoSansDevanagari.ttf"))

def images_to_pdf(images):
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)

    page_w, page_h = A4

    # Watermark settings
    watermark_text = "CLICK ERP"
    watermark_font = "Deva"
    watermark_size = 38          # big enough to look like ERP stamps
    watermark_opacity = 0.08     # very light
    watermark_angle = 40         # diagonal

    # Increase clarity (scale images more precisely)
    max_width = page_w - 60      # slightly larger margins for visual balance

    for img in images:

        # Convert PIL image to PNG buffer
        buf = io.BytesIO()
        img.save(buf, format="PNG")  # PNG preserves max clarity
        buf.seek(0)
        img_reader = ImageReader(buf)

        img_w, img_h = img.size

        # Scale to A4 width (high clarity)
        scale = max_width / img_w
        draw_w = img_w * scale
        draw_h = img_h * scale

        # Center image
        x = (page_w - draw_w) / 2
        y = (page_h - draw_h) / 2

        # DRAW IMAGE
        c.drawImage(img_reader, x, y, width=draw_w, height=draw_h, mask='auto')

        # DRAW BLACK BORDER  
        border_margin = 15
        c.setStrokeColor(black)
        c.setLineWidth(3)
        c.rect(
            border_margin,
            border_margin,
            page_w - border_margin * 2,
            page_h - border_margin * 2
        )

        # REPEATING WATERMARK (CLICK ERP)
        c.saveState()
        c.setFillColor(Color(0, 0, 0, alpha=watermark_opacity))
        c.setFont(watermark_font, watermark_size)

        # Rotate the canvas for diagonal text
        c.translate(page_w / 2, page_h / 2)
        c.rotate(watermark_angle)

        # Watermark repetition grid
        cols = 5
        rows = 8
        spacing_x = 250
        spacing_y = 120

        for i in range(-cols, cols + 1):
            for j in range(-rows, rows + 1):
                c.drawString(i * spacing_x, j * spacing_y, watermark_text)

        c.restoreState()

        # New PDF page
        c.showPage()

    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer

# Dashboard Page
# def dashboard_page():
    
#     df = load_voter_data()
#     # FILTERS — moved into collapsible panel
#     left, right = st.columns([2,1],gap='small',vertical_alignment='top',border=False)
    
#     with left:
#         if st.button("🔄 Refresh Data"):
#             st.cache_data.clear()

#         with st.expander("🔍 Filters / शोध पर्याय", expanded=True):
            
#             address_list = sorted(df["Address"].unique().tolist())

#             # Multi-select filter
#             address = st.multiselect(
#                 "पत्ता",
#                 options=address_list,
#                 default=None,
#                 placeholder="Choose one or more addresses",
#                 help="खाली दिलेला पत्ता निवडा.."                   
#             )
            
#             col1, col2, col3 = st.columns([1,2,1])
#             with col1:
#                 gender = st.selectbox(
#                     "लिंग",
#                     ["सर्व"] + df["Sex"].unique().tolist(),
#                     help="स्त्री किंवा पुरुष.."
#                 )
#             with col2:
#                 min_age = int(df["Age"].min())
#                 max_age = int(df["Age"].max())

#                 age_range = st.slider(
#                     "मतदारांचे वय तपासा..",
#                     min_age,
#                     max_age,
#                     (min_age, max_age),
#                     help="वय श्रेणी निवडा.."
#                 )
                
#             with col3:
#                 part_no = st.selectbox(
#                     "भाग क्र",
#                     ["सर्व"] + sorted(df["PartNo"].unique().tolist()),
#                     help="खाली दिलेला भाग क्रमांक निवडा.."
#                 )

#         # APPLY FILTERS
#         filtered = df.copy()

#         filtered = filtered[
#             (filtered["Age"] >= age_range[0]) &
#             (filtered["Age"] <= age_range[1])
#         ]

#         if gender != "सर्व":
#             filtered = filtered[filtered["Sex"] == gender]

#         if address :
#             filtered = filtered[filtered["Address"].isin(address) ]

#         if part_no != "सर्व":
#             filtered = filtered[filtered["PartNo"] == part_no]

#         st.write(f"### ***Filtered Records: {len(filtered)}***")

#         if filtered.empty:
#             st.warning("No matching data found.")
#             return

#     with right:
#         # VISITED PIE CHART
#         filtered["VisitedLabel"] = filtered["Visited"].apply(
#             lambda x: "Visited" if x == 1 else "Not Visited"
#         )

#         visited_count = filtered["VisitedLabel"].value_counts().reset_index()
#         visited_count.columns = ["Status", "Count"]
        
#         visited_pie = px.pie(
#             visited_count,
#             names="Status",
#             values="Count",
#             # title="Visited vs Total Population",
#             hole=0.45,
#             color="Status",
#             color_discrete_map={
#                 "Visited": "#2ecc71",
#                 "Not Visited": "#e74c3c"},
#             height=300,
#             width=300
#         )
#         st.plotly_chart(visited_pie, use_container_width=True)

#     # ADDRESS CHART
#     address_count = filtered.groupby(["Address", "Sex"])["VoterID"].count().reset_index()
#     address_count = address_count.sort_values("VoterID", ascending=False)

#     address_chart = px.bar(
#         address_count,
#         x="Address",
#         y="VoterID",
#         color="Sex",
#         title="पत्त्यानुसार मतदारांची संख्या..",
#         barmode="group",
#         color_discrete_map={
#             "F": "#ff69b4",
#             "Female": "#ff69b4",
#             "M": "#87CEFA",
#             "Male": "#87CEFA"
#         }
#     )
#     address_chart.update_layout(xaxis_tickangle=-45)

#     st.plotly_chart(address_chart, use_container_width=True)

#     # Row with Age and Gender charts
#     colA, colB = st.columns(2)

#     # AGE CHART
#     with colA:
#         age_count = filtered.groupby("Age")["VoterID"].count().reset_index()
#         age_bar = px.bar(age_count, x="Age", y="VoterID", title="वयानुसार मतदारांची संख्या..")
#         st.plotly_chart(age_bar, use_container_width=True)

#     # GENDER CHART
#     with colB:
#         gender_count = filtered.groupby("Sex")["VoterID"].count().reset_index()
#         gender_pie = px.pie(
#             gender_count,
#             names="Sex",
#             values="VoterID",
#             title="लिंगानुसार मतदारांची संख्या",
#             hole=0.4,
#             color="Sex",
#             color_discrete_map={
#                 "F": "#fa9ebc",
#                 "Female": "#fa9ebc",
#                 "M": "#5784e6",
#                 "Male": "#5784e6"
#             }
#         )
#         st.plotly_chart(gender_pie, use_container_width=True)

    # # DOWNLOAD PDF BUTTON (full width)
    # st.subheader("📥 निवडक मतदार यादी डाउनलोड करा ")

    # if st.button("यादी तयार करा"):

    #     images = []
    #     records_per_page = 30

    #     for start in range(0, len(filtered), records_per_page):
    #         chunk_df = filtered.iloc[start:start + records_per_page]
    #         img = dataframe_to_image(chunk_df)
    #         images.append(img)

    #     pdf_file = images_to_pdf(images)

    #     st.download_button(
    #         label="📄 यादी डाउनलोड करा",
    #         data=pdf_file,
    #         file_name="Filtered_Voter_List_ReadOnly.pdf",
    #         mime="application/pdf"
    #     )


# ================================================================
#  MAIN DASHBOARD FUNCTION
# ================================================================
def dashboard_page():
    colA, colB = st.columns([1, 1])
    df_voters_all = load_voter_data()
    df_survey = load_survey_data()
    with colA:
        if st.button("🔄 Refresh", key="refresh_btn", use_container_width=True):
            st.cache_data.clear()
    with colB:
        # Compact search bar CSS
        st.markdown("""
        <style>
        .stTextInput>div>div>input {
            height: 36px !important;
            padding: 4px 8px !important;
            font-size: 14px !important;
        }
        </style>
        """, unsafe_allow_html=True)

        global_search = st.text_input(
            "",
            placeholder="Search by Name / Surname...",
            key="global_search",
            label_visibility="collapsed"
        )

    # Create Picker Label
    df_voters_all["FullLabel"] = df_voters_all.apply(
        lambda row: ("✅ " if row["Visited"] == 1 else "") +
                    f"{row['EName']} — {row['Address']}",
        axis=1
    )

    # WORKING COPIES
    df_voters = df_voters_all.copy()
    
    # -------------------------------------------------------
    # 🔍 1. APPLY SEARCH FIRST (PRIMARY FILTER)
    # -------------------------------------------------------
    if global_search.strip():
        keyword = global_search.strip().lower()

        df_voters = df_voters[
            df_voters["EName"].str.lower().str.contains(keyword, na=False)
        ]
        

    # -------------------------------------------------------
    # 🎯 2. MULTISELECT SHOWS ONLY SEARCHED VOTERS
    # -------------------------------------------------------
    voter_picker = st.multiselect(
        "",
        options=df_voters["FullLabel"].tolist(),     # dynamic options
        key="voter_picker",
        label_visibility="collapsed",
        placeholder="Selected Voters"
    )
    
    # -------------------------------------------------------
    # 🎯 3. APPLY MULTISELECT FILTER
    # -------------------------------------------------------
    if voter_picker:

        selected_names = [
            x.split(" — ")[0].strip()
            for x in voter_picker
        ]

        df_voters = df_voters[df_voters["EName"].isin(selected_names)]
    df_v = df_voters.copy()
    
    address_list_voters = sorted(df_v["Address"].dropna().unique().tolist())
    part_list_voters = sorted(df_v["PartNo"].dropna().unique().tolist())
    min_age_all = int(df_v["Age"].min()) if not df_voters["Age"].isna().all() else 0
    max_age_all = int(df_v["Age"].max()) if not df_voters["Age"].isna().all() else 100

    col1, col2, col3, col4 = st.columns([1,1,1,1])
    with col1:
        st.markdown("<h3 style='text-align:center; color:#b39334'>Voter</h3>", unsafe_allow_html=True)   # OR df_voters if you want entire dataset chart

        df_v["VisitedLabel"] = df_v["Visited"].apply(
            lambda x: "Visited" if x == 1 else "Not Visited"
        )
        visit_count = df_v["VisitedLabel"].value_counts().reset_index()
        visit_count.columns = ["Status", "Count"]

        visited_pie = px.pie(
            visit_count,
            # names="Status",
            values="Count",
            # title="🔵 Visited vs Not Visited",
            hole=0.45,
            color="Status",
            height=250,
            color_discrete_map={
                "Visited": "#00c853",      # Green
                "Not Visited": "#f34f4f"   # Red
            }
        )

        visited_pie.update_layout(
            # legend_title="Visit Status",
            margin=dict(t=60, b=20, l=20, r=20)
        )
        st.plotly_chart(visited_pie, use_container_width=True)

    with col2:        
        st.markdown("<h3 style='text-align:center; color:#b39334'>Male</h3>", unsafe_allow_html=True)

        total_males = len(df_v[df_v.Sex.isin(["M", "Male"])])
        visited_males = len(df_v[(df_v.Sex.isin(["M", "Male"])) & (df_v.Visited == 1)])
        not_visited_males = total_males - visited_males

        # Create labels + values as dict format
        labels = ["Visited", "Not Visited"]
        values = [visited_males, not_visited_males]

        fig_male_pie = px.pie(
            # names=labels,
            values=values,
            hole=0.45,              # donut style
            height=250,
            color=labels,           # enable custom colors
            color_discrete_map={
                "Visited": "#00c853",      # Green
                "Not Visited": "#2c86df"   # Blue
            }
        )

        fig_male_pie.update_layout(
            # legend_title=labels
            margin=dict(t=60, b=20, l=20, r=20)
        )

        st.plotly_chart(fig_male_pie, use_container_width=True)

    with col3:        
        st.markdown("<h3 style='text-align:center; color:#b39334'>Female</h3>", unsafe_allow_html=True)

        total_females = len(df_v[df_v.Sex.isin(["F", "Female"])])
        visited_females = len(df_v[(df_v.Sex.isin(["F", "Female"])) & (df_v.Visited == 1)])
        not_visited_females = total_females - visited_females

        # Create labels + values as dict format
        labels = ["Visited", "Not Visited"]
        values = [visited_females, not_visited_females]

        fig_female_pie = px.pie(
            # names=labels,
            values=values,
            hole=0.45,              # donut style
            height=250,
            color=labels,           # enable custom colors
            color_discrete_map={
                "Visited": "#00c853",      # Green
                "Not Visited": "#ff62f7"   # Blue
            }
        )

        fig_female_pie.update_layout(
            # legend_title=labels
            margin=dict(t=60, b=20, l=20, r=20)
        )

        st.plotly_chart(fig_female_pie, use_container_width=True)
    with col4:
        st.markdown("<h3 style='text-align:center;color:#b39334;'>Survey</h3>", unsafe_allow_html=True)
        total_surveys = len(df_survey)
        estimated_voters = sum(df_survey.VotersCount)
        st.markdown(f"<h1 style='text-align:center; color:#00c853;'>🏘️{total_surveys}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; color:#00c853;'>=================</p>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align:center; color:#00c853;'>👥{estimated_voters}</h1>", unsafe_allow_html=True)
    # ========================= TAB FULL WIDTH STYLING =========================
    st.markdown("""
    <style>

    div[data-baseweb="tab-list"] {
        display: flex !important;
        justify-content: space-between !important;      /* Center align entire tab group */
        width: 80% !important;                    /* Occupy only 75% width */
        margin-left: 10% !important;            /* Space left */
        margin-right: 10% !important;           /* Space right */
    }

    /* Individual tab size equal */
    div[data-baseweb="tab"] {
        flex: 1 !important;
        text-align: center !important;
        font-size: 17px !important;
        font-weight: 600 !important;
        padding: 12px 0 !important;
        border-radius: 6px !important;
    }

    /* Hover & Active Styling */
    div[data-baseweb="tab"]:hover {
        background-color: #ebebeb50 !important;
    }
    div[data-baseweb="tab"][aria-selected="true"] {
        background-color: #0055ff20 !important;
        border-bottom: 3px solid orange !important;
    }

    </style>
    """, unsafe_allow_html=True)


    # -------------------- 4 TABS  --------------------
    tab1, tab2, tab3, tab4 = st.tabs(["Voters ", "Male", "Female", "Survey"])

    # ================================================================
    # TAB 1 — VOTERS (PRIMARY DASHBOARD)
    # ================================================================
    with tab1:
        st.subheader("📊 Voter Dashboard")
        left, right = st.columns([3,1])
        # ---------------- FILTER PANEL ----------------
        with right:
            address_list = sorted(df_v["Address"].unique().tolist())
            address = st.multiselect("पत्ता", options=address_list)

            part_no = st.selectbox(
                "भाग क्र",
                ["सर्व"] + sorted(df_v["PartNo"].unique().tolist())
            )
        
            min_age, max_age = int(df_v.Age.min()), int(df_v.Age.max())
            # Ensure min and max age are valid
            if min_age == max_age:
                age_range = (min_age, max_age)   # no slider needed (single age)
                st.info(f"All voters are age {min_age}.")
            else:
                age_range = st.slider(
                    "वयानुसार शोध",
                    min_value=min_age,
                    max_value=max_age,
                    value=(min_age, max_age)
                )


            # ---------------- APPLY FILTERS --------------
            df_v = df_v[(df_v.Age >= age_range[0]) & (df_v.Age <= age_range[1])]
            if address: df_v = df_v[df_v.Address.isin(address)]
            if part_no != "सर्व": df_v = df_v[df_v.PartNo == part_no]
            st.write(f"### Total Records : {len(df_v)}")
            # ===== PDF DOWNLOAD INSIDE TAB 1 =====

            if st.button("यादी तयार करा - Voters"):
                images = []
                records_per_page = 30

                for start in range(0, len(df_v), records_per_page):
                    chunk_df = df_v.iloc[start:start + records_per_page]
                    img = dataframe_to_image(chunk_df)       # <-- your existing fn
                    images.append(img)

                pdf_file = images_to_pdf(images)             # <-- your existing fn

                st.download_button(
                    label="📄 Download Voter List",
                    data=pdf_file,
                    file_name="Voters_Filtered_List.pdf",
                    mime="application/pdf"
                )

        with left:
            # ---------------- BAR CHART -------------------
            total = df_v.groupby("Address")["VoterID"].count().reset_index(name="Total")
            visited = df_v[df_v["Visited"] == 1].groupby("Address")["VoterID"].count().reset_index(name="Visited")
            not_visited = df_v[df_v["Visited"] == 0].groupby("Address")["VoterID"].count().reset_index(name="NotVisited")
            merged = total.merge(visited, on="Address", how="left").merge(not_visited, on="Address", how="left").fillna(0)
            merged[["Total","Visited","NotVisited"]] = merged[["Total","Visited","NotVisited"]].astype(int)

            merged = merged.sort_values(ascending=False, by="Total").reset_index(drop=True)
            selected_merged = merged.head(10)
            # Melt data for plotly grouped bar format
            final_df = selected_merged.melt(id_vars="Address", 
                                value_vars=["Visited","Total","NotVisited"],
                                var_name="Category", 
                                value_name="Count")

            # Plot grouped bar
            fig = px.bar(
                final_df,
                x="Address",
                y="Count",
                color="Category",
                barmode="group",
                title="🏠 Address wise — Visited vs Not Visited vs Total",
                color_discrete_map={
                    "Visited": "#00c853",        # green
                    "NotVisited": "#ff5252",     # red
                    "Total": "#4285F4"           # blue
                },
                height=750
            )

            fig.update_layout(
                xaxis_title="",
                legend_title_text="📊 Status"
            )

            st.plotly_chart(fig, use_container_width=True)


    # ================================================================
    # TAB 2 — MALE VOTERS
    # ================================================================
    with tab2:
            st.subheader("📊 Male Voters")
            left1, right1 = st.columns([3,1])
            with right1:
                # use values from overall lists but unique keys
                address_m = st.multiselect("पत्ता", options=address_list_voters, key="addr_male")
                part_m = st.selectbox("भाग क्र", ["सर्व"] + part_list_voters, key="part_male")
                # Ensure min and max age are valid
                if min_age == max_age:
                    age_m = (min_age, max_age)   # no slider needed (single age)
                    st.info(f"All voters are age {min_age}.")
                else:
                    age_m = st.slider(
                        "वयानुसार शोध",
                        min_value=min_age,
                        max_value=max_age,
                        value=(min_age, max_age), key="age_male"
                    )


                filtered_m = df_v[df_v["Sex"].isin(["M", "Male"])].copy()
                filtered_m = filtered_m[(filtered_m["Age"] >= age_m[0]) & (filtered_m["Age"] <= age_m[1])]
                if address_m:
                    filtered_m = filtered_m[filtered_m["Address"].isin(address_m)]
                if part_m != "सर्व":
                    filtered_m = filtered_m[filtered_m["PartNo"] == part_m]

                st.write(f"### Total Male Records : {len(filtered_m)}")

                if st.button("यादी तयार करा - Male"):
                    filtered_male = df_v[df_v.Sex.isin(["M","Male"])]

                    images = []
                    for start in range(0, len(filtered_male), 30):
                        chunk = filtered_male.iloc[start:start+30]
                        img = dataframe_to_image(chunk)
                        images.append(img)

                    pdf_file = images_to_pdf(images)

                    st.download_button(
                        label="📄 Download Male Voter List",
                        data=pdf_file,
                        file_name="Male_Filtered_List.pdf",
                        mime="application/pdf"
                    )

            with left1:
                count_m = filtered_m.groupby("Address")["VoterID"].count().reset_index(name="Count")
                count_vm = filtered_m[filtered_m["Visited"] == 1].groupby("Address")["VoterID"].count().reset_index(name="Visited_Male")

                # merge
                male_data = count_m.merge(count_vm, on="Address", how="left").fillna(0)

                # top 10
                male_data = male_data.sort_values("Count", ascending=False).head(10)

                # convert to long format for dual bar graph
                male_long = male_data.melt(id_vars="Address", 
                                        value_vars=["Count", "Visited_Male"],
                                        var_name="Category", 
                                        value_name="Total")

                fig_m = px.bar(
                    male_long,
                    x="Address",
                    y="Total",
                    color="Category",
                    barmode="group",
                    title="Male vs Visited Male by Address (Top 10)",
                    color_discrete_map={
                        "Count": "#4285F4",        # Blue – total males
                        "Visited_Male": "#00c853"  # Green – visited males
                    },
                    height=750
                )

                fig_m.update_layout(xaxis_title="Address", yaxis_title="Total Voters")
                st.plotly_chart(fig_m, use_container_width=True)


    # ================================================================
    # TAB 3 — FEMALE VOTERS
    # ================================================================
    with tab3:
            st.subheader("📊 Female Voters")
            left2, right2 = st.columns([3,1])
            with right2:
                address_f = st.multiselect("पत्ता", options=address_list_voters, key="addr_female")
                part_f = st.selectbox("भाग क्र", ["सर्व"] + part_list_voters, key="part_female")
                # Ensure min and max age are valid
                if min_age == max_age:
                    age_f = (min_age, max_age)   # no slider needed (single age)
                    st.info(f"All voters are age {min_age}.")
                else:
                    age_f = st.slider(
                        "वयानुसार शोध",
                        min_value=min_age,
                        max_value=max_age,
                        value=(min_age, max_age), key="age_female"
                    )

                filtered_f = df_v[df_v["Sex"].isin(["F", "Female"])].copy()
                filtered_f = filtered_f[(filtered_f["Age"] >= age_f[0]) & (filtered_f["Age"] <= age_f[1])]
                if address_f:
                    filtered_f = filtered_f[filtered_f["Address"].isin(address_f)]
                if part_f != "सर्व":
                    filtered_f = filtered_f[filtered_f["PartNo"] == part_f]

                st.write(f"### Total Female Records : {len(filtered_f)}")
                if st.button("यादी तयार करा - Female"):
                    filtered_female = df_v[df_v.Sex.isin(["F","Female"])]

                    images = []
                    for start in range(0, len(filtered_female), 30):
                        chunk = filtered_female.iloc[start:start+30]
                        img = dataframe_to_image(chunk)
                        images.append(img)

                    pdf_file = images_to_pdf(images)

                    st.download_button(
                        label="📄 Download Female Voter List",
                        data=pdf_file,
                        file_name="Female_Filtered_List.pdf",
                        mime="application/pdf"
                    )

            with left2:
                count_f = filtered_f.groupby("Address")["VoterID"].count().reset_index(name="Count")
                count_vf = filtered_f[filtered_f["Visited"] ==1].groupby("Address")["VoterID"].count().reset_index(name="Visited Female")
                #merging both dataframes
                female_data = count_f.merge(count_vf, on="Address", how="left").fillna(0)
                female_data = female_data.sort_values("Count", ascending=False).head(10)
                # convert to long format for dual bar graph
                female_long = female_data.melt(id_vars="Address", 
                                        value_vars=["Count", "Visited Female"],
                                        var_name="Category", 
                                        value_name="Total")                
                # show female address-wise counts  
                fig_f = px.bar(female_long, x="Address", y="Total", title="Female Voters by Address",color="Category", barmode="group",
                            color_discrete_map ={
                                "Count" :"#ff69b4",
                                "Visited Female": "#00c853",})
                fig_f.update_layout(xaxis_title="")
                st.plotly_chart(fig_f, use_container_width=True)

    # ================================================================
    # TAB 4 — SURVEY
    # ================================================================
    with tab4:
        st.subheader("📋 Survey Analysis")
        left3, right3 = st.columns([3,1])
        with right3:
            # Survey-specific address list and part (PartNo)
            address_list_survey = sorted(df_survey["VAddress"].dropna().unique().tolist())
            prabhag_list = sorted(df_survey["PartNo"].dropna().unique().tolist()) if "PartNo" in df_survey.columns else []

            # survey filters with unique keys
            addr_s = st.multiselect("पत्ता", options=address_list_survey, key="addr_survey")
            prabhag_s = st.selectbox("प्रभाग क्र", ["सर्व"] + prabhag_list, key="part_survey")

            # apply survey filters
            survey_filtered = df_survey.copy()
            if addr_s:
                survey_filtered = survey_filtered[survey_filtered["VAddress"].isin(addr_s)]
            if prabhag_s != "सर्व":
                survey_filtered = survey_filtered[survey_filtered["PartNo"] == prabhag_s]

            st.write(f"### Total Surveys : {len(survey_filtered)}")
            st.write(f"### Estimated Voters (surveyed) : {int(survey_filtered['VotersCount'].sum() if 'VotersCount' in survey_filtered.columns else 0)}")

            if st.button("यादी तयार करा - Survey"):
                
                images = []
                for start in range(0, len(df_survey), 30):
                    chunk = df_survey.iloc[start:start+30]
                    img = dataframe_to_image(chunk)
                    images.append(img)

                pdf_file = images_to_pdf(images)

                st.download_button(
                    label="📄 Download Survey Report",
                    data=pdf_file,
                    file_name="Survey_Report.pdf",
                    mime="application/pdf"
                )

        with left3:
            # address-wise survey count
            survey_group = survey_filtered.groupby("VAddress")["VoterID"].count().reset_index(name="Count")
            survey_group = survey_group.sort_values("Count", ascending=False)
            fig_survey = px.bar(survey_group, x="VAddress", y="Count", title="Address-wise Survey Count",
                                color_discrete_sequence=["#00cc88"])
            fig_survey.update_layout(xaxis_title="")
            st.plotly_chart(fig_survey, use_container_width=True)
