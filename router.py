import streamlit as st
from types import SimpleNamespace
import psycopg
from psycopg.rows import dict_row

def go_to(page):
    return page

def get_connection():
    return psycopg.connect(
        host="ep-royal-smoke-a1gha9pb-pooler.ap-southeast-1.aws.neon.tech",
        dbname="neondb",        # ⭐ FIXED: psycopg3 uses dbname, not database
        user="neondb_owner",
        password="npg_rs1bVogh7EtU",
        port="5432"
    )

    # return pyodbc.connect(
    #     "DRIVER={ODBC Driver 17 for SQL Server};"
    #     "SERVER=DNYANESHWAR\\MSSQLSERVER02;"
    #     "DATABASE=Maharashtra;"
    #     "UID=sa;"
    #     "PWD=sa@123;"
    # )

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




# ------------------- VALIDATE USER -------------------
def validate_user(username, password):
    try:
        with get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT "UserID", "Username", "Password", "Role",
                    "ParentID", "CreatedAt"
                    FROM "User"
                    WHERE "Username" = %s AND "Password" = %s
                    LIMIT 1
                """, (username, password))

                result = cur.fetchone()
                return dict_row_to_namespace(result) if result else None

    except Exception as e:
        st.error(f"❌ DB Error: {e}")
        return None
# ------------------- FETCH VOTERS -------------------
def fetch_voters():
    try:
        with get_connection() as conn:
            # psycopg3 method → row_factory=dict_row
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT "VEName", "HouseNo", "VPSName", "EName",
                           "PSName", "VAddress", "SectionNo", "Sex",
                           "Age", "IDCardNo"
                    FROM "VoterList"
                """)

                rows = cur.fetchall()  # already list of dicts
                return [dict_row_to_namespace(r) for r in rows]

    except Exception as e:
        st.error(f"❌ DB Error: {e}")
        return []
