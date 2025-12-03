import streamlit as st
import psycopg2
import psycopg2.extras
from router import get_connection


def survey_page():

    # -----------------------------------------------------
    # VERSION RESETTER (FOR CLEARING WIDGETS)
    # -----------------------------------------------------
    if "widget_version" not in st.session_state:
        st.session_state.widget_version = 1

    V = st.session_state.widget_version

    st.subheader("📋 सर्वेक्षण फॉर्म")

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # -----------------------------------------------------
    # SEARCH BAR
    # -----------------------------------------------------
    search_name = st.text_input(
        "मतदाराचे नाव शोधा (English Name):",
        key=f"search_name_{V}"
    )

    voter_results = []

    if search_name.strip():
        cursor.execute("""
            SELECT "VoterID", "EName", "VEName", "HouseNo", "SectionNo", "Sex", "VAddress"
            FROM "VoterList"
            WHERE "EName" ILIKE %s
        """, (f"%{search_name}%",))
        voter_results = cursor.fetchall()

    # Dropdown text → voterID mapping
    merged_options = {
        f'{row["EName"]} ({row["VEName"]}) - {row["HouseNo"]}': row["VoterID"]
        for row in voter_results
    }

    # -----------------------------------------------------
    # FAMILY SELECTION
    # -----------------------------------------------------
    family_selected = st.multiselect(
        "Select Family Members",
        options=list(merged_options.keys()),
        key=f"family_select_{V}"
    )

    selected_family_ids = [merged_options[x] for x in family_selected]

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

    # -----------------------------------------------------
    # HEAD SELECTION & AUTO-FILL
    # -----------------------------------------------------
    if selected_family_ids:

        head_choice = st.selectbox(
            "Select Head of Family",
            family_selected,
            key=f"head_select_{V}"
        )

        family_head_id = merged_options[head_choice]

        # Fetch all selected voters
        placeholder = ",".join(["%s"] * len(selected_family_ids))
        cursor.execute(
            f"""
            SELECT "VoterID", "Sex", "SectionNo", "VAddress"
            FROM "VoterList"
            WHERE "VoterID" IN ({placeholder})
            """,
            selected_family_ids
        )
        fam_rows = cursor.fetchall()

        # Count summary
        total_voters = len(fam_rows)
        male_count = len([r for r in fam_rows if r["Sex"] == "M"])
        female_count = len([r for r in fam_rows if r["Sex"] == "F"])

        # Head details
        cursor.execute("""
            SELECT "SectionNo", "Sex", "Age", "VAddress", "PartNo"
            FROM "VoterList"
            WHERE "VoterID" = %s
        """, (family_head_id,))
        head = cursor.fetchone()

        if head:
            section_no = head["SectionNo"]
            head_sex = head["Sex"]
            head_age = head["Age"]
            head_part = head["PartNo"]
            address_autofill = head["VAddress"]

    # -----------------------------------------------------
    # FAMILY DETAIL WIDGETS (right column)
    # -----------------------------------------------------
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

    visited = st.radio("Visited?", ("Yes", "No"), key=f"visited_{V}")
    visited_value = 1 if visited == "Yes" else 0

    # -----------------------------------------------------
    # SUBMIT BUTTON
    # -----------------------------------------------------
    if st.button("Submit Survey", key=f"submit_{V}"):

        if not selected_family_ids:
            st.error("❌ कृपया किमान एक कुटुंब सदस्य निवडा!")
            return

        if not mobile:
            st.error("❌ कृपया मोबाईल नंबर द्या!")
            return

        try:
            # Insert into SurveyData
            cursor.execute("""
                INSERT INTO "SurveyData"
                ("VoterID", "VEName", "HouseNo", "Landmark", "VAddress", "Mobile",
                 "SectionNo", "VotersCount", "Male", "Female", "Caste",
                 "Sex", "PartNo", "Age")
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                family_head_id, head_choice, house_number, landmark, address_autofill,
                mobile, section_no, total_voters, male_count, female_count,
                caste, head_sex, head_part, head_age
            ))

            # Mark visited in VoterList
            placeholder = ",".join(["%s"] * len(selected_family_ids))
            cursor.execute(
                f"""UPDATE "VoterList" SET "Visited" = %s WHERE "VoterID" IN ({placeholder})""",
                [visited_value] + selected_family_ids
            )

            conn.commit()
            st.success("✅ सर्वेक्षण फॉर्म सबमिट झाला!")

            # Reset UI
            st.session_state.widget_version += 1
            st.rerun()

        except Exception as e:
            conn.rollback()
            st.error(f"❌ Error: {e}")

        finally:
            cursor.close()
            conn.close()
