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
    
# Database Connection
def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=DNYANESHWAR\\MSSQLSERVER02;"
        "DATABASE=Maharashtra;"
        "UID=sa;"
        "PWD=sa@123;"
    )

# Load Data
@st.cache_data
def load_voter_data():
    conn = get_connection()
    query = """
        SELECT 
            VoterID,
            PartNo,
            SectionNo,
            EName,
            VEName,
            Sex,
            Age,
            Address,
            VAddress,
            Visited
        FROM VoterList
    """
    df = pd.read_sql(query, conn)
    return df

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
def dashboard_page():
    
    df = load_voter_data()
    # FILTERS — moved into collapsible panel
    left, right = st.columns([2,1],gap='small',vertical_alignment='top',border=False)
    
    with left:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()

        with st.expander("🔍 Filters / शोध पर्याय", expanded=True):
            
            address_list = sorted(df["Address"].unique().tolist())

            # Multi-select filter
            address = st.multiselect(
                "पत्ता",
                options=address_list,
                default=None,
                placeholder="Choose one or more addresses",
                help="खाली दिलेला पत्ता निवडा.."                   
            )
            
            col1, col2, col3 = st.columns([1,2,1])
            with col1:
                gender = st.selectbox(
                    "लिंग",
                    ["सर्व"] + df["Sex"].unique().tolist(),
                    help="स्त्री किंवा पुरुष.."
                )
            with col2:
                min_age = int(df["Age"].min())
                max_age = int(df["Age"].max())

                age_range = st.slider(
                    "मतदारांचे वय तपासा..",
                    min_age,
                    max_age,
                    (min_age, max_age),
                    help="वय श्रेणी निवडा.."
                )
                
            with col3:
                part_no = st.selectbox(
                    "भाग क्र",
                    ["सर्व"] + sorted(df["PartNo"].unique().tolist()),
                    help="खाली दिलेला भाग क्रमांक निवडा.."
                )

        # APPLY FILTERS
        filtered = df.copy()

        filtered = filtered[
            (filtered["Age"] >= age_range[0]) &
            (filtered["Age"] <= age_range[1])
        ]

        if gender != "सर्व":
            filtered = filtered[filtered["Sex"] == gender]

        if address :
            filtered = filtered[filtered["Address"].isin(address) ]

        if part_no != "सर्व":
            filtered = filtered[filtered["PartNo"] == part_no]

        st.write(f"### ***Filtered Records: {len(filtered)}***")

        if filtered.empty:
            st.warning("No matching data found.")
            return

    with right:
        # VISITED PIE CHART
        filtered["VisitedLabel"] = filtered["Visited"].apply(
            lambda x: "Visited" if x == 1 else "Not Visited"
        )

        visited_count = filtered["VisitedLabel"].value_counts().reset_index()
        visited_count.columns = ["Status", "Count"]
        
        visited_pie = px.pie(
            visited_count,
            names="Status",
            values="Count",
            # title="Visited vs Total Population",
            hole=0.45,
            color="Status",
            color_discrete_map={
                "Visited": "#2ecc71",
                "Not Visited": "#e74c3c"},
            height=300,
            width=300
        )
        st.plotly_chart(visited_pie, use_container_width=True)

    # ADDRESS CHART
    address_count = filtered.groupby(["Address", "Sex"])["VoterID"].count().reset_index()
    address_count = address_count.sort_values("VoterID", ascending=False)

    address_chart = px.bar(
        address_count,
        x="Address",
        y="VoterID",
        color="Sex",
        title="पत्त्यानुसार मतदारांची संख्या..",
        barmode="group",
        color_discrete_map={
            "F": "#ff69b4",
            "Female": "#ff69b4",
            "M": "#87CEFA",
            "Male": "#87CEFA"
        }
    )
    address_chart.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(address_chart, use_container_width=True)

    # Row with Age and Gender charts
    colA, colB = st.columns(2)

    # AGE CHART
    with colA:
        age_count = filtered.groupby("Age")["VoterID"].count().reset_index()
        age_bar = px.bar(age_count, x="Age", y="VoterID", title="वयानुसार मतदारांची संख्या..")
        st.plotly_chart(age_bar, use_container_width=True)

    # GENDER CHART
    with colB:
        gender_count = filtered.groupby("Sex")["VoterID"].count().reset_index()
        gender_pie = px.pie(
            gender_count,
            names="Sex",
            values="VoterID",
            title="लिंगानुसार मतदारांची संख्या",
            hole=0.4,
            color="Sex",
            color_discrete_map={
                "F": "#fa9ebc",
                "Female": "#fa9ebc",
                "M": "#5784e6",
                "Male": "#5784e6"
            }
        )
        st.plotly_chart(gender_pie, use_container_width=True)

    # DOWNLOAD PDF BUTTON (full width)
    st.subheader("📥 निवडक मतदार यादी डाउनलोड करा ")

    if st.button("यादी तयार करा"):

        images = []
        records_per_page = 30

        for start in range(0, len(filtered), records_per_page):
            chunk_df = filtered.iloc[start:start + records_per_page]
            img = dataframe_to_image(chunk_df)
            images.append(img)

        pdf_file = images_to_pdf(images)

        st.download_button(
            label="📄 यादी डाउनलोड करा",
            data=pdf_file,
            file_name="Filtered_Voter_List_ReadOnly.pdf",
            mime="application/pdf"
        )
