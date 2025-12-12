import streamlit as st
from api_client import APIClient
import requests
from types import SimpleNamespace
import os
import pandas as pd
from dashboard import load_voter_data_from_api


def get_api_client():
    base = os.getenv("API_URL", "https://election-are-near-backend.onrender.com")
    token = st.session_state.get("access_token") or st.session_state.get("token")
    return APIClient(base_url=base, token=token)


def survey_page():
    main_admin_id = st.session_state.get("main_admin_id")

    # VERSION RESETTER (FOR CLEARING WIDGETS)
    if "widget_version" not in st.session_state:
        st.session_state.widget_version = 1

    V = st.session_state.widget_version

    st.subheader("📋 सर्वेक्षण फॉर्म")

    # Load all voter data from cache (same as dashboard.py)
    try:
        df_voters_all = load_voter_data_from_api()
    except Exception as e:
        st.error(f"❌ Error loading voter data: {e}")
        return

    # Ensure visited column mapping
    visited_col = f"Visited_{main_admin_id}" if main_admin_id else "Visited"
    if visited_col in df_voters_all.columns:
        df_voters_all["Visited"] = pd.to_numeric(df_voters_all[visited_col], errors="coerce").fillna(0).astype(int)
    elif "Visited" in df_voters_all.columns:
        df_voters_all["Visited"] = pd.to_numeric(df_voters_all["Visited"], errors="coerce").fillna(0).astype(int)
    else:
        df_voters_all["Visited"] = 0

    # Ensure columns exist
    for col in ["EName", "VEName", "Address", "PartNo", "Age", "Sex", "VAddress", "VoterID", "HouseNo"]:
        if col not in df_voters_all.columns:
            df_voters_all[col] = None

    # Create full label for display (with visited mark)
    def _full_label(row):
        try:
            visited_flag = int(row.get("Visited", 0))
        except Exception:
            visited_flag = 0
        ename = row.get("EName") or ""
        vname = row.get("VEName") or ""
        addr = row.get("Address") or ""
        prefix = "✅ " if visited_flag == 1 else ""
        label = f"{vname} / {ename} – {addr}" if (vname or ename) else ""
        return f"{prefix}{label}" if label else ""

    df_voters_all["FullLabel"] = df_voters_all.apply(_full_label, axis=1)
    df_v = df_voters_all.copy()

    # Search bar (same as dashboard)
    global_search = st.text_input("", placeholder="Search by Name / Surname...", key=f"global_search_{V}", label_visibility="collapsed")

    if global_search and global_search.strip():
        kw = global_search.strip().lower()
        df_v = df_v[df_v["EName"].fillna("").str.lower().str.contains(kw, na=False)]

    # Multiselect for family members (same as dashboard)
    family_selected = st.multiselect(
        "",
        options=df_v["FullLabel"].tolist(),
        key=f"family_select_{V}",
        label_visibility="collapsed",
        placeholder="Select Family Members"
    )

    # Extract selected voter IDs and build merged_options map
    merged_options = {}
    selected_family_ids = []
    if family_selected:
        # Build a map from FullLabel to VoterID for selected rows
        for _, row in df_v.iterrows():
            if row["FullLabel"] in family_selected:
                merged_options[row["FullLabel"]] = row["VoterID"]
                selected_family_ids.append(row["VoterID"])
    
    # Get actual voter results from selected_family_ids
    voter_results = df_voters_all[df_voters_all["VoterID"].isin(selected_family_ids)].to_dict('records')

    # Default values
    family_head_id = None
    head_sex = ""
    head_age = None
    head_part = None
    section_no = ""
    address_autofill = ""
    total_voters = 0
    male_count = 0
    female_count = 0

    # HEAD SELECTION & AUTO-FILL (from selected voter results)
    if selected_family_ids:

        head_choice = st.selectbox(
            "Select Head of Family",
            family_selected,
            key=f"head_select_{V}"
        )

        family_head_id = merged_options[head_choice]

        # Find rows from the voter results
        fam_rows = [r for r in voter_results if str(r.get('VoterID')) in [str(x) for x in selected_family_ids]]

        # Count summary
        total_voters = len(fam_rows)
        male_count = len([r for r in fam_rows if str(r.get('Sex','')).upper() == 'M'])
        female_count = len([r for r in fam_rows if str(r.get('Sex','')).upper() == 'F'])

        # Head details
        head = next((r for r in fam_rows if str(r.get('VoterID')) == str(family_head_id)), None)
        if head:
            section_no = head.get('SectionNo') or ''
            head_sex = head.get('Sex') or ''
            head_age = head.get('Age') or None
            head_part = head.get('PartNo') or None
            address_autofill = head.get('VAddress') or ''

    # FAMILY DETAIL WIDGETS (right column)
    col1, col2 = st.columns(2)

    with col2:
        house_number = st.text_input("घर क्रमांक", "", key=f"house_{V}")

        mob_input = st.text_input("Enter Mobile Number (10 digits)", key=f"mobile_{V}")

        mobile = None
        if mob_input:
            if mob_input.isdigit() and len(mob_input) == 10:
                mobile = mob_input
            else:
                st.error("Invalid — only digits allowed and must be exactly 10 digits")

        landmark = st.text_input("Landmark", key=f"lm_{V}")
        caste = st.text_input("जात (Optional)", key=f"caste_{V}")

    with col1:
        left, right = st.columns(2)
        left.number_input("एकूण मतदार", value=total_voters, disabled=True, key=f"tot_{V}")
        right.text_input("सेक्शन क्रमांक", value=section_no, disabled=True, key=f"sec_{V}")
        left.number_input("पुरुष", value=male_count, disabled=True, key=f"m_{V}")
        right.number_input("स्त्री", value=female_count, disabled=True, key=f"f_{V}")
        address = st.text_area("पत्ता", value=address_autofill, disabled=True, key=f"addr_{V}")

    visited = st.radio("Visited?", ("Yes"), key=f"visited_{V}")
    visited_value = 1 if visited == "Yes" else 0

    # SUBMIT BUTTON (MODIFIED TO USE API)
    if st.button("Submit Survey", key=f"submit_{V}"):

        if not selected_family_ids:
            st.error("❌ कृपया किमान एक कुटुंब सदस्य निवडा!")
            return

        if not mobile:
            st.error("❌ कृपया मोबाईल नंबर द्या!")
            return

        try:
            # Initialize API client
            api_client = get_api_client()
            
            # Prepare survey data for API
            survey_data = {
                "family_head_id": int(family_head_id),
                "selected_family_ids": [int(vid) for vid in selected_family_ids],
                "house_number": house_number,
                "landmark": landmark or "",
                "mobile": mobile,
                "caste": caste or "",
                "visited": visited_value,
                "main_admin_id": main_admin_id
            }
            
            # Submit via API (POST /submit-survey)
            if hasattr(api_client, 'submit_survey'):
                result = api_client.submit_survey(survey_data)
            else:
                url = f"{api_client.base_url.rstrip('/')}/submit-survey"
                headers = {"Authorization": f"Bearer {st.session_state.get('access_token')}"} if st.session_state.get('access_token') else {}
                r = requests.post(url, json=survey_data, headers=headers, timeout=15)
                if r.status_code in (200,201):
                    try:
                        result = r.json()
                    except Exception:
                        result = {"success": True}
                else:
                    result = {"success": False, "message": r.text}
            
            if result.get("success"):
                st.success("✅ सर्वेक्षण फॉर्म सबमिट झाला!")
                
                # Reset UI
                st.session_state.widget_version += 1
                st.rerun()
            else:
                st.error(f"❌ Error: {result.get('message', 'Unknown error')}")
        
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Cannot connect to server. Please check if API is running.")
        except Exception as e:
            st.error(f"❌ Error: {e}")

