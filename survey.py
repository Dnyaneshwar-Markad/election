import streamlit as st
import pyodbc
from router import go_to

def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=DNYANESHWAR\\MSSQLSERVER02;"
        "DATABASE=Maharashtra;"
        "UID=sa;"
        "PWD=sa@123;"
    )


def survey_page():
    # -----------------------------------------------------
    # WIDGET VERSION HANDLER (MAIN LOGIC)
    # -----------------------------------------------------
    if "widget_version" not in st.session_state:
        st.session_state.widget_version = 1

    V = st.session_state.widget_version   # short alias

    st.subheader("📋 सर्वेक्षण फॉर्म")

    conn = get_connection()
    cursor = conn.cursor()

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
            SELECT VoterID, EName, VEName, HouseNo, SectionNo, Sex, VAddress 
            FROM VoterList
            WHERE EName LIKE ?
        """, ('%' + search_name + '%',))
        voter_results = cursor.fetchall()

    merged_options = {
        f"{row.EName} ({row.VEName}) - {row.HouseNo}": row.VoterID
        for row in voter_results
    }

    family_selected = st.multiselect(
        "Select Family Members",
        options=list(merged_options.keys()),
        key=f"family_select_{V}"
    )

    selected_family_ids = [merged_options[x] for x in family_selected]

    head_name_display = ""
    family_head_id = None
    section_no = ""
    address_autofill = ""
    total_voters = 0
    male_count = 0
    female_count = 0

    if selected_family_ids:

        head_choice = st.selectbox(
            "Select Head of Family",
            family_selected,
            key=f"head_select_{V}"
        )

        family_head_id = merged_options[head_choice]
        head_name_display = head_choice

        placeholder = ",".join("?" * len(selected_family_ids))
        cursor.execute(
            f"SELECT VoterID, Sex, SectionNo, VAddress FROM VoterList WHERE VoterID IN ({placeholder})",
            selected_family_ids
        )
        fam_rows = cursor.fetchall()

        total_voters = len(fam_rows)
        male_count = len([r for r in fam_rows if r.Sex == "M"])
        female_count = len([r for r in fam_rows if r.Sex == "F"])

        cursor.execute(
            "SELECT SectionNo, VAddress FROM VoterList WHERE VoterID = ?",
            (family_head_id,)
        )
        head_row = cursor.fetchone()
        if head_row:
            section_no = head_row.SectionNo
            address_autofill = head_row.VAddress

    col1, col2 = st.columns(2)

    # -----------------------------------------------------
    # FAMILY DETAILS
    # -----------------------------------------------------
    with col2:
        house_number = st.text_input("घर क्रमांक", "", key=f"house_{V}")
        mobile = st.text_input("मोबाईल नंबर", key=f"mobile_{V}")
        landmark = st.text_input("Landmark", key=f"lm_{V}")
        caste = st.text_input("जात (Optional)", key=f"caste_{V}")

    with col1:
        left, right = st.columns(2)
        left.number_input("एकूण मतदार", value=total_voters, disabled=True, key=f"tot_{V}")
        right.text_input("सेक्शन क्रमांक", value=section_no, disabled=True, key=f"sec_{V}")
        left.number_input("पुरुष", value=male_count, disabled=True, key=f"m_{V}")
        right.number_input("स्त्री", value=female_count, disabled=True, key=f"f_{V}")
        address = st.text_area("पत्ता", value=address_autofill, disabled=True, key=f"addr_{V}")

    visited = st.radio(
        "Visited?",
        ("Yes", "No"),
        key=f"visited_{V}"
    )
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
            cursor.execute("""
                INSERT INTO SurveyData 
                (HeadName, HouseNumber, Landmark, Address, Mobile, 
                PrabhagNumber, VotersCount, Male, Female, Caste)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                head_name_display, house_number, landmark, address_autofill, mobile,
                section_no, total_voters, male_count, female_count, caste
            ))

            placeholder = ",".join("?" * len(selected_family_ids))
            cursor.execute(
                f"UPDATE VoterList SET Visited = ? WHERE VoterID IN ({placeholder})",
                [visited_value] + selected_family_ids
            )

            conn.commit()
            st.success("✅ सर्वेक्षण फॉर्म सबमिट झाला!")

            # -----------------------------------------------------
            # RESET ALL WIDGETS BY CHANGING VERSION
            # -----------------------------------------------------
            st.session_state.widget_version += 1
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error: {e}")

        finally:
            cursor.close()
            conn.close()