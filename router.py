import pyodbc
def go_to(page):
    return page

def get_connection():
    return pyodbc.connect(
        HOST = "dpg-d4ju0ji4d50c73d4mndg-a.oregon-postgres.render.com"
        DATABASE = "dnyaneshwar"
        USER = "dnyaneshwar_user"
        PASSWORD = "83DePVbb07mAGJRvlAsbfA1LygFOBt2q"
    )
    #     return pyodbc.connect(
    #     "DRIVER={ODBC Driver 17 for SQL Server};"
    #     "SERVER=DNYANESHWAR\\MSSQLSERVER02;"
    #     "DATABASE=Maharashtra;"
    #     "UID=sa;"
    #     "PWD=sa@123;"
    # )