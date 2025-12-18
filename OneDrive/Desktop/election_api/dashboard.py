# dashboard.py
import streamlit as st
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
from api_client import APIClient
from data_loader import load_voter_data, load_survey_data, load_filters, load_summary, clear_all_data
import os

# Register font used by PDF watermark/ReportLab
FONT_PATH = "NotoSansDevanagari.ttf"  # ensure this file exists in project folder or update path
try:
    pdfmetrics.registerFont(TTFont("Deva", FONT_PATH))
except Exception:
    # fallback (ReportLab will use default)
    pass

st.set_page_config(layout="wide", page_title="Voter Dashboard (API)")

# ---------- Helper: API factory ----------
def get_api_client() -> APIClient:
    base = os.getenv("API_URL", "https://election-are-near-backend.onrender.com")
    token = st.session_state.get("access_token") or st.session_state.get("token")
    return APIClient(base_url=base, token=token)

# ------------------- DATA LOADERS (cache) -------------------
# @st.cache_data(show_spinner=False)
# def load_voter_data_from_api(section_no=None):
#     """Load voter data - cached per section"""
#     api = get_api_client()
#     all_rows = []
#     limit = 3000
#     offset = 0
#     while True:
#         res = api.get_voters(limit=limit, offset=offset)
#         rows = res.get("rows", [])
#         all_rows.extend(rows)
#         if len(rows) < limit:
#             break
#         offset += limit
    
#     df = pd.DataFrame(all_rows)
    
#     # Filter by section if provided
#     if section_no is not None and not df.empty and "SectionNo" in df.columns:
#         df = df[df["SectionNo"] == section_no]
    
#     return df

# @st.cache_data(show_spinner=False)
# def load_survey_data_from_api(user_id=None):
#     """Load survey data - cached per user"""
#     api = get_api_client()
#     all_rows = []
#     limit = 1000
#     offset = 0
#     while True:
#         res = api.get_surveys(limit=limit, offset=offset)
#         rows = res.get("rows", [])
#         all_rows.extend(rows)
#         if len(rows) < limit:
#             break
#         offset += limit
#     return pd.DataFrame(all_rows)


# @st.cache_data(show_spinner=False)
# def load_filters_from_api(section_no=None):
#     """Load filters - cached per section"""
#     api = get_api_client()
#     return api.get_voter_filters()

# @st.cache_data(show_spinner=False)
# def load_summary_from_api(section_no=None):
#     """Load summary - cached per section"""
#     api = get_api_client()
#     return api.get_voter_summary()

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

def dashboard_page():
    # verify login
    if "token" not in st.session_state or not st.session_state.get("token"):
        st.error("❌ No authenticated session. Please login.")
        return

    api = get_api_client()
    
    section_no = st.session_state.get("section_no")
    main_admin_id = st.session_state.get("main_admin_id")
    # Top controls
    colA, colB = st.columns([1, 1])

    # with colA:
    #     if st.button("🔄 Refresh "):
    #         st.cache_data.clear()

    with colB:
        global_search = st.text_input("", placeholder="Search by Name / Surname...", key="global_search", label_visibility="collapsed")

    # Load data (from API caches)
    try:
        # Summary used for KPIs
        summary = load_summary(section_no=section_no)
    except Exception as e:
        st.error(f"Error fetching summary: {e}")
        return

    # Load bulk tables (may be large)
    df_voters_all = load_voter_data(section_no=section_no)
    # Load surveys WITH USER ID
    user_id = st.session_state.get("user_id")
    df_survey = load_survey_data(user_id=user_id)

    # Ensure visited column mapping
    
    visited_col = f"Visited_{main_admin_id}" if main_admin_id else "Visited"

    if visited_col in df_voters_all.columns:
        df_voters_all["Visited"] = pd.to_numeric(df_voters_all[visited_col], errors="coerce").fillna(0).astype(int)
    elif "Visited" in df_voters_all.columns:
        df_voters_all["Visited"] = pd.to_numeric(df_voters_all["Visited"], errors="coerce").fillna(0).astype(int)
    else:
        df_voters_all["Visited"] = 0

    # Ensure columns exist
    for col in ["EName", "Address", "PartNo", "Age", "Sex", "VAddress", "VoterID"]:
        if col not in df_voters_all.columns:
            df_voters_all[col] = None

    def _full_label(row):
        try:
            visited_flag = int(row.get("Visited", 0))
        except Exception:
            visited_flag = 0
        name = row.get("EName") or ""
        vname = row.get("VEName") or ""
        addr = row.get("Address") or ""
        prefix = "✅ " if visited_flag == 1 else ""
        return f"{prefix}{vname} / {name} – {addr}" if name else ""

    df_voters_all["FullLabel"] = df_voters_all.apply(_full_label, axis=1)
    df_v = df_voters_all.copy()

    if global_search and global_search.strip():
        kw = global_search.strip().lower()
        df_v = df_v[df_v["EName"].fillna("").str.lower().str.contains(kw, na=False)]

    voter_picker = st.multiselect("", options=df_v["FullLabel"].tolist(), key="voter_picker", label_visibility="collapsed", placeholder="Selected Voters")
    if voter_picker:
        selected_names = [x.split(" – ")[0].replace("✅ ", "").strip() for x in voter_picker]
        df_v = df_v[df_v["EName"].isin(selected_names)]

    address_list_voters = sorted(df_v["Address"].dropna().unique().tolist())
    part_list_voters = sorted(df_v["PartNo"].dropna().unique().tolist())
    min_age_all = int(df_v["Age"].min()) if (df_v["Age"].notna().any()) else 0
    max_age_all = int(df_v["Age"].max()) if (df_v["Age"].notna().any()) else 100

    # Top KPI row
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        st.markdown("<h3 style='text-align:center; color:#b39334'>Voter</h3>", unsafe_allow_html=True)
        df_v["VisitedLabel"] = df_v["Visited"].apply(lambda x: "Visited" if int(x) == 1 else "Not Visited")
        visit_count = df_v["VisitedLabel"].value_counts().reset_index()
        visit_count.columns = ["Status", "Count"]
        visited_pie = px.pie(visit_count, values="Count", hole=0.45, color="Status", height=250,color_discrete_map={"Visited": "#00c853", "Not Visited": "#f34f4f"})
        visited_pie.update_layout(margin=dict(t=60, b=20, l=20, r=20))
        st.plotly_chart(visited_pie, use_container_width=True)

    with col2:
        st.markdown("<h3 style='text-align:center; color:#b39334'>Male</h3>", unsafe_allow_html=True)
        males = df_v[df_v["Sex"].isin(["M", "Male"])]
        visited_males = int(pd.to_numeric(males["Visited"], errors="coerce").fillna(0).sum())
        not_visited_males = max(0, males.shape[0] - visited_males)
        male_df = pd.DataFrame({"Status": ["Visited", "Not Visited"], "Count": [visited_males, not_visited_males]})
        fig_male_pie = px.pie(male_df, values="Count", hole=0.45,color="Status", height=250,color_discrete_map={"Visited": "#00c853", "Not Visited": "#2c86df"})
        fig_male_pie.update_layout(margin=dict(t=60, b=20, l=20, r=20))
        st.plotly_chart(fig_male_pie, use_container_width=True)

    with col3:
        st.markdown("<h3 style='text-align:center; color:#b39334'>Female</h3>", unsafe_allow_html=True)
        females = df_v[df_v["Sex"].isin(["F", "Female"])]
        visited_females = int(pd.to_numeric(females["Visited"], errors="coerce").fillna(0).sum())
        not_visited_females = max(0, females.shape[0] - visited_females)
        female_df = pd.DataFrame({"Status": ["Visited", "Not Visited"], "Count": [visited_females, not_visited_females]})
        fig_female_pie = px.pie(female_df, values="Count", hole=0.45,color="Status", height=250,color_discrete_map={"Visited": "#00c853", "Not Visited": "#ff62f7"})
        fig_female_pie.update_layout(margin=dict(t=60, b=20, l=20, r=20))
        st.plotly_chart(fig_female_pie, use_container_width=True)

    with col4:
        st.markdown("<h3 style='text-align:center;color:#b39334;'>Survey</h3>", unsafe_allow_html=True)
        total_surveys = len(df_survey)
        estimated_voters = int(df_survey["VotersCount"].sum()) if "VotersCount" in df_survey.columns else 0
        st.markdown(f"<h1 style='text-align:center; color:#00c853;'>🏘️{total_surveys}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; color:#00c853;'>=================</p>", unsafe_allow_html=True)        
        st.markdown(f"<h1 style='text-align:center; color:#00c853;'>👥{estimated_voters}</h1>", unsafe_allow_html=True)

    # Tabs (Voters, Male, Female, Survey)
    # ---- TAB styles (kept unchanged) ----
    st.markdown(
        """
        <style>
        div[data-baseweb="tab-list"] {
            display: flex !important;
            justify-content: space-between !important;
            width: 80% !important;
            margin-left: 10% !important;
            margin-right: 10% !important;
        }
        div[data-baseweb="tab"] {
            flex: 1 !important;
            text-align: center !important;
            font-size: 17px !important;
            font-weight: 600 !important;
            padding: 12px 0 !important;
            border-radius: 6px !important;
        }
        div[data-baseweb="tab"]:hover { background-color: #ebebeb50 !important; }
        div[data-baseweb="tab"][aria-selected="true"] { background-color: #0055ff20 !important; border-bottom: 3px solid orange !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    tab1, tab2, tab3, tab4 = st.tabs(["Voters ", "Male", "Female", "Survey"])

    # TAB 1 - Voters
    with tab1:
        st.subheader("📊 Voter Dashboard")
        left, right = st.columns([3, 1])

        with right:
            # compute filter lists from API if possible (fallback to df)
            try:
                filters = load_filters(section_no=section_no)
                address_list = filters.get("address_list", []) if isinstance(filters, dict) else sorted(df_v["Address"].dropna().unique().tolist())
                part_list = filters.get("part_list", []) if isinstance(filters, dict) else sorted(df_v["PartNo"].dropna().unique().tolist())
                min_age = filters.get("min_age", int(df_v["Age"].min()) if df_v["Age"].notna().any() else 0)
                max_age = filters.get("max_age", int(df_v["Age"].max()) if df_v["Age"].notna().any() else 100)
            except Exception:
                address_list = sorted(df_v["Address"].dropna().unique().tolist())
                part_list = sorted(df_v["PartNo"].dropna().unique().tolist())
                min_age, max_age = (int(df_v["Age"].min()), int(df_v["Age"].max())) if df_v["Age"].notna().any() else (0, 100)

            address = st.multiselect("पत्ता", options=address_list)
            part_no = st.selectbox("भाग क्र", ["सर्व"] + part_list)

            if min_age == max_age:
                age_range = (min_age, max_age)
                st.info(f"All voters are age {min_age}.")
            else:
                age_range = st.slider("वयानुसार शोध", min_value=int(min_age), max_value=int(max_age), value=(int(min_age), int(max_age)))

            df_v = df_v[(df_v["Age"] >= age_range[0]) & (df_v["Age"] <= age_range[1])]
            if address:
                df_v = df_v[df_v["Address"].isin(address)]
            if part_no != "सर्व":
                df_v = df_v[df_v["PartNo"] == part_no]

            st.write(f"### Total Records : {len(df_v)}")

            if st.button("यादी तयार करा - Voters"):
                images = []
                records_per_page = 30
                for start in range(0, len(df_v), records_per_page):
                    chunk_df = df_v.iloc[start:start+records_per_page]
                    images.append(dataframe_to_image(chunk_df))
                pdf_file = images_to_pdf(images)
                st.download_button(label="📄 Download Voter List", data=pdf_file, file_name="Voters_Filtered_List.pdf", mime="application/pdf")

        with left:
            total = df_v.groupby("Address")["VoterID"].count().reset_index(name="Total")
            visited = df_v[df_v["Visited"] == 1].groupby("Address")["VoterID"].count().reset_index(name="Visited")
            not_visited = df_v[df_v["Visited"] == 0].groupby("Address")["VoterID"].count().reset_index(name="NotVisited")
            merged = total.merge(visited, on="Address", how="left").merge(not_visited, on="Address", how="left").fillna(0)
            merged[["Total", "Visited", "NotVisited"]] = merged[["Total", "Visited", "NotVisited"]].astype(int)
            merged = merged.sort_values(ascending=False, by="Total").reset_index(drop=True)
            selected_merged = merged.head(10)
            final_df = selected_merged.melt(id_vars="Address", value_vars=["Visited", "Total", "NotVisited"], var_name="Category", value_name="Count")

            fig = px.bar(final_df, x="Address", y="Count", color="Category", barmode="group", title="🏠 Address wise – Visited vs Not Visited vs Total", height=650, color_discrete_map={"Visited": "#00c853", "NotVisited": "#ff5252", "Total": "#4285F4"})
            fig.update_layout(xaxis_title="", legend_title_text="📊 Status")
            st.plotly_chart(fig, use_container_width=True)

    # TAB 2 - Male
    with tab2:
        st.subheader("📊 Male Voters")
        left1, right1 = st.columns([3, 1])

        with right1:
            address_m = st.multiselect("पत्ता", options=address_list_voters, key="addr_male")
            part_m = st.selectbox("भाग क्र", ["सर्व"] + part_list_voters, key="part_male")

            if min_age_all == max_age_all:
                age_m = (min_age_all, max_age_all)
                st.info(f"All voters are age {min_age_all}.")
            else:
                age_m = st.slider("वयानुसार शोध", min_value=min_age_all, max_value=max_age_all, value=(min_age_all, max_age_all), key="age_male")

            filtered_m = df_v[df_v["Sex"].isin(["M", "Male"])].copy()
            filtered_m = filtered_m[(filtered_m["Age"] >= age_m[0]) & (filtered_m["Age"] <= age_m[1])]
            if address_m:
                filtered_m = filtered_m[filtered_m["Address"].isin(address_m)]
            if part_m != "सर्व":
                filtered_m = filtered_m[filtered_m["PartNo"] == part_m]

            st.write(f"### Total Male Records : {len(filtered_m)}")

            if st.button("यादी तयार करा - Male"):
                images = []
                for start in range(0, len(filtered_m), 30):
                    chunk = filtered_m.iloc[start:start+30]
                    images.append(dataframe_to_image(chunk))
                pdf_file = images_to_pdf(images)
                st.download_button(label="📄 Download Male Voter List", data=pdf_file, file_name="Male_Filtered_List.pdf", mime="application/pdf")

        with left1:
            count_m = filtered_m.groupby("Address")["VoterID"].count().reset_index(name="Count")
            count_vm = filtered_m[filtered_m["Visited"] == 1].groupby("Address")["VoterID"].count().reset_index(name="Visited_Male")
            male_data = count_m.merge(count_vm, on="Address", how="left").fillna(0)
            male_data = male_data.sort_values("Count", ascending=False).head(10)
            male_long = male_data.melt(id_vars="Address", value_vars=["Count", "Visited_Male"], var_name="Category", value_name="Total")

            fig_m = px.bar(male_long, x="Address", y="Total", color="Category", barmode="group", title="Male vs Visited Male by Address (Top 10)", height=650,color_discrete_map={"Count": "#4285F4", "Visited_Male": "#00c853"})
            fig_m.update_layout(xaxis_title="Address", yaxis_title="Total Voters")
            st.plotly_chart(fig_m, use_container_width=True)

    # TAB 3 - Female
    with tab3:
        st.subheader("📊 Female Voters")
        left2, right2 = st.columns([3, 1])

        with right2:
            address_f = st.multiselect("पत्ता", options=address_list_voters, key="addr_female")
            part_f = st.selectbox("भाग क्र", ["सर्व"] + part_list_voters, key="part_female")

            if min_age_all == max_age_all:
                age_f = (min_age_all, max_age_all)
                st.info(f"All voters are age {min_age_all}.")
            else:
                age_f = st.slider("वयानुसार शोध", min_value=min_age_all, max_value=max_age_all, value=(min_age_all, max_age_all), key="age_female")

            filtered_f = df_v[df_v["Sex"].isin(["F", "Female"])].copy()
            filtered_f = filtered_f[(filtered_f["Age"] >= age_f[0]) & (filtered_f["Age"] <= age_f[1])]
            if address_f:
                filtered_f = filtered_f[filtered_f["Address"].isin(address_f)]
            if part_f != "सर्व":
                filtered_f = filtered_f[filtered_f["PartNo"] == part_f]

            st.write(f"### Total Female Records : {len(filtered_f)}")
            if st.button("यादी तयार करा - Female"):
                images = []
                for start in range(0, len(filtered_f), 30):
                    chunk = filtered_f.iloc[start:start+30]
                    images.append(dataframe_to_image(chunk))
                pdf_file = images_to_pdf(images)
                st.download_button(label="📄 Download Female Voter List", data=pdf_file, file_name="Female_Filtered_List.pdf", mime="application/pdf")

        with left2:
            count_f = filtered_f.groupby("Address")["VoterID"].count().reset_index(name="Count")
            count_vf = filtered_f[filtered_f["Visited"] == 1].groupby("Address")["VoterID"].count().reset_index(name="Visited_Female")
            female_data = count_f.merge(count_vf, on="Address", how="left").fillna(0)
            female_data = female_data.sort_values("Count", ascending=False).head(10)
            female_long = female_data.melt(id_vars="Address", value_vars=["Count", "Visited_Female"], var_name="Category", value_name="Total")

            fig_f = px.bar(female_long, x="Address", y="Total", color="Category", barmode="group", title="Female & Visited Female by Address (Top 10)", height=650, color_discrete_map={"Count": "#ff69b4", "Visited_Female": "#00c853"},)
            fig_f.update_layout(xaxis_title="Address", yaxis_title="Total Voters")
            st.plotly_chart(fig_f, use_container_width=True)

    # TAB 4 - Survey
    with tab4:
        st.subheader("📋 Survey Analysis")
        left3, right3 = st.columns([3, 1])

        with right3:
            address_list_survey = sorted(df_survey["VAddress"].dropna().unique().tolist()) if "VAddress" in df_survey.columns else []
            prabhag_list = sorted(df_survey["PartNo"].dropna().unique().tolist()) if "PartNo" in df_survey.columns else []

            addr_s = st.multiselect("पत्ता", options=address_list_survey, key="addr_survey")
            prabhag_s = st.selectbox("प्रभाग क्र", ["सर्व"] + prabhag_list, key="part_survey")

            survey_filtered = df_survey.copy()
            if addr_s:
                survey_filtered = survey_filtered[survey_filtered["VAddress"].isin(addr_s)]
            if prabhag_s != "सर्व":
                survey_filtered = survey_filtered[survey_filtered["PartNo"] == prabhag_s]

            st.write(f"### Total Surveys : {len(survey_filtered)}")
            st.write(f"### Estimated Voters (surveyed) : {int(survey_filtered['VotersCount'].sum() if 'VotersCount' in survey_filtered.columns else 0)}")

            if st.button("यादी तयार करा - Survey"):
                images = []
                for start in range(0, len(survey_filtered), 30):
                    chunk = survey_filtered.iloc[start:start+30]
                    images.append(dataframe_to_image(chunk))
                pdf_file = images_to_pdf(images)
                st.download_button(label="📄 Download Survey Report", data=pdf_file, file_name="Survey_Report.pdf", mime="application/pdf")

        with left3:
            survey_group = survey_filtered.groupby("VAddress")["VoterID"].count().reset_index(name="Count") if "VoterID" in survey_filtered.columns else pd.DataFrame(columns=["VAddress", "Count"])
            survey_group = survey_group.sort_values("Count", ascending=False)
            fig_survey = px.bar(survey_group, x="VAddress", y="Count", title="Address-wise Survey Count", height=650,color_discrete_sequence=["#00cc88"])
            fig_survey.update_layout(xaxis_title="")
            st.plotly_chart(fig_survey, use_container_width=True)

# ------------------- App entry -------------------
