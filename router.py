
import psycopg


def go_to(page):
    return page

def get_connection():
    #For NeonDB
    return psycopg.connect(
        "postgresql://neondb_owner:npg_rs1bVogh7EtU@ep-weathered-math-a1pj9ocn-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    )
    
    # ## For Local Postgres DB
    # return psycopg.connect(
    #     host="localhost",
    #     dbname="Maharashta",      # your db name
    #     user="postgres",             # your postgres username
    #     password="sa@123",        # your postgres password
    #     port=5432
    # )

    # return pyodbc.connect(
    #     "DRIVER={ODBC Driver 17 for SQL Server};"
    #     "SERVER=DNYANESHWAR\\MSSQLSERVER02;"
    #     "DATABASE=Maharashtra;"
    #     "UID=sa;"
    #     "PWD=sa@123;"
    # )

