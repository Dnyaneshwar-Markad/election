
import psycopg2
def go_to(page):
    return page

def get_connection():
    return psycopg2.connect(
        host="dpg-d4ju0ji4d50c73d4mndg-a.oregon-postgres.render.com",
        database="dnyaneshwar",
        user="dnyaneshwar_user",
        password="83DePVbb07mAGJRvlAsbfA1LygFOBt2q",
        port="5432"
    )
    # return pyodbc.connect(
    #     "DRIVER={ODBC Driver 17 for SQL Server};"
    #     "SERVER=DNYANESHWAR\\MSSQLSERVER02;"
    #     "DATABASE=Maharashtra;"
    #     "UID=sa;"
    #     "PWD=sa@123;"
    # )