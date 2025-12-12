from login_api import DATABASE_URL, get_connection

print('Using DATABASE_URL:', DATABASE_URL)
try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT 1')
    print('DB test query result:', cur.fetchone())
    cur.close()
    conn.close()
    print('Connection successful')
except Exception as e:
    print('Connection failed:', repr(e))
